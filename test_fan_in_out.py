"""Test Fan-In/Fan-Out (Funnel Hub) detector implementation and explainability."""
from pathlib import Path
import yaml
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import FanInOutDetector


def test_fan_in_out_detector():
    """Verify detector catches R1 hub and ignores legitimate look-alikes."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"
    thresholds_file = root_dir / "backend" / "config" / "thresholds.yaml"

    with open(thresholds_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    balanced_thresholds = config["presets"]["balanced"]["fan_in_out"]

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    detector = FanInOutDetector(thresholds=balanced_thresholds)
    hits = detector.detect(fg)

    assert len(hits) >= 1
    hit_accounts = {h["account"] for h in hits}
    
    # 1. Must catch R1 hub
    assert "ACC_MULE_FAN01" in hit_accounts

    # 2. Must not catch hard negatives
    for m in range(1, 9):
        assert f"ACC_MERCHANT_{m:02d}" not in hit_accounts, f"Merchant {m} false positive"
    for p in range(1, 4):
        assert f"ACC_PAYROLL_{p:02d}" not in hit_accounts, f"Payroll {p} false positive"
    assert "ACC_WEDDING_01" not in hit_accounts
    assert "ACC_LANDLORD_01" not in hit_accounts

    # 3. Verify hit data structure and explainability
    r1_hit = next(h for h in hits if h["account"] == "ACC_MULE_FAN01")
    assert r1_hit["role"] == "hub"
    assert r1_hit["evidence"]["senders_count"] == 5
    assert r1_hit["evidence"]["total_inflow"] == 405000.0
    assert r1_hit["evidence"]["forward_ratio"] >= 0.90

    exp = detector.explain(r1_hit)
    assert "plain_reason" in exp
    assert "technical_reason" in exp
    assert "counterfactual" in exp

    # Check Rule 6: No graph jargon in plain explanation
    forbidden_terms = ["node", "edge", "graph", "vertex"]
    plain_text = exp["plain_reason"].lower()
    for term in forbidden_terms:
        assert term not in plain_text, f"Forbidden graph term '{term}' found in plain reason"

    # Must contain banking words
    assert "account" in plain_text
    assert "₹" in exp["plain_reason"]
