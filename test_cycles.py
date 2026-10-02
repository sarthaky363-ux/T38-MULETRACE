"""Test Circular Transfer (Wash Trading Loop) Detector implementation and explainability."""
from pathlib import Path
import yaml
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.detectors.cycles import CycleDetector


def test_cycle_detector():
    """Verify detector catches R3 4-hop wash cycle and ignores 2-account friend loops."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"
    thresholds_file = root_dir / "backend" / "config" / "thresholds.yaml"

    with open(thresholds_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    balanced_thresholds = config["presets"]["balanced"]["cycles"]

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    detector = CycleDetector(thresholds=balanced_thresholds)
    hits = detector.detect(fg)

    assert len(hits) >= 4
    hit_accounts = {h["account"] for h in hits}

    # 1. All 4 members of R3 circular ring must be flagged
    for l in range(1, 5):
        loop_acc = f"ACC_LOOP_{l:02d}"
        assert loop_acc in hit_accounts, f"R3 {loop_acc} missing from cycle hits"

    # 2. Friend pairs (L6) must NOT be flagged (they are 2-hop, min_len is 3)
    for p in range(1, 7):
        assert f"ACC_FRIEND_A{p}" not in hit_accounts, f"Friend pair A{p} false positive"
        assert f"ACC_FRIEND_B{p}" not in hit_accounts, f"Friend pair B{p} false positive"

    # 3. Check evidence and explainability
    l1_hit = next(h for h in hits if h["account"] == "ACC_LOOP_01")
    assert l1_hit["role"] == "cycle"
    assert l1_hit["evidence"]["cycle_length"] == 4
    assert l1_hit["evidence"]["cycle_duration_minutes"] <= 45.0
    assert l1_hit["evidence"]["max_amount_deviation"] <= 0.20

    exp = detector.explain(l1_hit)
    assert "plain_reason" in exp
    assert "technical_reason" in exp
    assert "counterfactual" in exp

    # Check Rule 6: No graph jargon in plain explanation
    forbidden_terms = ["node", "edge", "graph", "vertex"]
    plain_text = exp["plain_reason"].lower()
    for term in forbidden_terms:
        assert term not in plain_text, f"Forbidden graph term '{term}' found in plain reason"

    assert "account" in plain_text
    assert "₹" in exp["plain_reason"]
