"""Test behavioral signals, composite risk scoring, confidence meter, and explainability."""
from pathlib import Path
import yaml
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import FanInOutDetector
from backend.signals import compute_account_signals
from backend.scoring import RiskScorer
from backend.reasons import build_explanation_dossier


def test_signals_and_composite_scoring():
    """Verify behavioral signals, score calculation, confidence meter, and counterfactuals."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"
    thresholds_file = root_dir / "backend" / "config" / "thresholds.yaml"

    with open(thresholds_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    # 1. Signals Verification
    fan_hub_id = "ACC_MULE_FAN01"
    sig = compute_account_signals(fg, fan_hub_id)
    assert sig["account_id"] == fan_hub_id
    assert sig["total_inflow"] == 405000.0
    assert sig["total_outflow"] == 390000.0
    assert sig["unique_senders"] == 5
    assert sig["unique_receivers"] == 1
    assert sig["is_new_account"] is True

    # 2. Detector and Scorer Execution
    fio_detector = FanInOutDetector(thresholds=config["presets"]["balanced"]["fan_in_out"])
    hits = fio_detector.detect(fg)
    hub_hits = [h for h in hits if h["account"] == fan_hub_id]
    assert len(hub_hits) >= 1

    scorer = RiskScorer(config=config["scoring"])
    score_data = scorer.score_account(sig, hub_hits)

    # R1 hub should have high threat score and critical band
    assert score_data["risk_score"] >= 70.0
    assert score_data["risk_band"] == "critical"
    assert score_data["confidence"] in ["medium", "high"]
    assert "drain_ratio_90" in score_data["breakdown"]["bonuses"]

    # 3. Victim Protection Test
    vic_sig = compute_account_signals(fg, "ACC_VICTIM_FAN01")
    vic_score = scorer.score_account(vic_sig, [], role_override="victim")
    assert vic_score["risk_score"] == 0.0
    assert vic_score["risk_band"] == "victim"
    assert vic_score["role"] == "victim"

    # 4. Safe Account Test
    safe_sig = compute_account_signals(fg, "ACC_RET_0001")
    safe_score = scorer.score_account(safe_sig, [])
    assert safe_score["risk_score"] == 0.0
    assert safe_score["risk_band"] == "safe"

    # 5. Explainability and Counterfactuals
    dossier = build_explanation_dossier(fan_hub_id, sig, hub_hits, score_data)
    assert "plain_reason" in dossier
    assert "technical_reason" in dossier
    assert "counterfactual" in dossier
    assert len(dossier["evidence_bullets"]) >= 3

    # Rule 6 Verification: No graph jargon in user-facing texts
    forbidden_terms = ["node", "edge", "graph", "vertex", "component"]
    for text in [dossier["plain_reason"], dossier["counterfactual"]]:
        text_lower = text.lower()
        for term in forbidden_terms:
            assert term not in text_lower, f"Forbidden graph term '{term}' found in text: {text}"

    # Banking terms check
    assert "account" in dossier["plain_reason"]
    assert "₹" in dossier["plain_reason"]
