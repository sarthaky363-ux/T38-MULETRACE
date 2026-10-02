"""Test Pass-Through Layering Detector implementation and explainability."""
from pathlib import Path
import yaml
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.detectors.passthrough import PassthroughDetector


def test_passthrough_detector():
    """Verify detector identifies R2 chain and does not flag slow reseller or normal accounts."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"
    thresholds_file = root_dir / "backend" / "config" / "thresholds.yaml"

    with open(thresholds_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    balanced_thresholds = config["presets"]["balanced"]["passthrough"]

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    detector = PassthroughDetector(thresholds=balanced_thresholds)
    hits = detector.detect(fg)

    assert len(hits) >= 6
    hit_accounts = {h["account"] for h in hits}

    # 1. All 6 chain accounts from R2 must be detected
    for c in range(1, 7):
        chain_acc = f"ACC_CHAIN_{c:02d}"
        assert chain_acc in hit_accounts, f"R2 {chain_acc} missing from hits"

    # 2. Reseller (L7) must NOT be flagged as rapid pass-through (gap was 42m > 8m)
    assert "ACC_RESELLER_01" not in hit_accounts

    # 3. Check evidence and explainability on a chain hit
    c1_hit = next(h for h in hits if h["account"] == "ACC_CHAIN_01")
    assert c1_hit["role"] == "relay"
    assert c1_hit["evidence"]["chain_length"] == 6
    assert c1_hit["evidence"]["forward_ratio"] >= 0.85
    assert c1_hit["evidence"]["hop_gap_minutes"] <= 8.0
    assert c1_hit["evidence"]["post_balance"] <= 2000.0

    exp = detector.explain(c1_hit)
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
