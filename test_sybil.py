"""Test Sybil / Device / IP / KYC Cluster Detector implementation and explainability."""
from pathlib import Path
import yaml
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.detectors.sybil import SybilDetector


def test_sybil_detector():
    """Verify detector catches R4 synthetic cluster and ignores family devices & campus Wi-Fi."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"
    thresholds_file = root_dir / "backend" / "config" / "thresholds.yaml"

    with open(thresholds_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    balanced_thresholds = config["presets"]["balanced"]["sybil"]

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    detector = SybilDetector(thresholds=balanced_thresholds)
    hits = detector.detect(fg)

    assert len(hits) >= 4
    hit_accounts = {h["account"] for h in hits}

    # 1. All 4 Sybil accounts from R4 must be detected
    for s in range(1, 5):
        sybil_acc = f"ACC_SYBIL_{s:02d}"
        assert sybil_acc in hit_accounts, f"R4 {sybil_acc} missing from sybil hits"

    # 2. Family accounts (L5) must NOT be flagged (they share device, but are >600 days old)
    for f_idx in range(1, 5):
        fam_acc = f"ACC_FAMILY_{f_idx:02d}"
        assert fam_acc not in hit_accounts, f"Family account {fam_acc} false positive"

    # 3. Campus Wi-Fi students (L8) must NOT be flagged (pure shared IP without 2nd signal)
    for s_idx in range(1, 13):
        stu_acc = f"ACC_STUDENT_{s_idx:02d}"
        assert stu_acc not in hit_accounts, f"Student account {stu_acc} false positive"

    # 4. Check evidence and explainability
    s1_hit = next(h for h in hits if h["account"] == "ACC_SYBIL_01")
    assert s1_hit["evidence"]["cluster_size"] == 4
    assert s1_hit["evidence"]["shared_device"] == "DEV_EMU_9901"
    assert s1_hit["evidence"]["account_age_days"] <= 30

    exp = detector.explain(s1_hit)
    assert "plain_reason" in exp
    assert "technical_reason" in exp
    assert "counterfactual" in exp

    # Check Rule 6: No graph jargon in plain explanation
    forbidden_terms = ["node", "edge", "graph", "vertex", "component", "bipartite"]
    plain_text = exp["plain_reason"].lower()
    for term in forbidden_terms:
        assert term not in plain_text, f"Forbidden graph term '{term}' found in plain reason"

    assert "account" in plain_text
