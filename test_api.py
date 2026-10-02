"""
Acceptance Tests for MuleTrace FastAPI Backend Service
Validates API endpoints, state transitions, regulatory dossiers, and forensic operations.
"""

import pytest
from backend.api import (
    get_health,
    load_demo,
    get_summary,
    get_alerts,
    get_account_detail,
    get_graph,
    get_rings,
    get_ring_detail,
    record_verdict,
    run_replay,
    run_freeze_simulation,
    get_chase_list,
    get_presets,
    set_preset,
    get_metrics,
    get_early_warning,
    get_case_dossier,
    get_evasion_test,
    get_quantum_walk,
    get_quantum_interdiction,
    get_quantum_ring_fidelity,
    VerdictRequest,
    ReplayRequest,
    FreezeRequest,
    PresetRequest,
)
from backend.store import store


@pytest.fixture(scope="module", autouse=True)
def init_demo_store():
    """Ensures demo data is loaded into the store prior to API tests."""
    store.load_demo_data()


def test_health_and_summary():
    """Validates health check and dashboard KPI statistics."""
    health = get_health()
    assert health["status"] == "ok"
    assert health["dataset_loaded"] is True
    assert health["active_preset"] == "balanced"
    assert health["account_count"] > 100

    summary = get_summary()
    assert summary["total_accounts"] > 100
    assert summary["total_transactions"] > 500
    assert summary["flagged_accounts"] > 0
    assert summary["critical_accounts"] > 0
    assert summary["rings_detected"] >= 4
    assert summary["estimated_amount_at_risk"] > 0
    assert "₹" in summary["estimated_amount_at_risk_formatted"]
    assert "Estimated amount saved: ₹" in summary["estimated_amount_saved_formatted"]


def test_alerts_queue_filters_and_pagination():
    """Validates alerts queue retrieval, risk band filtering, and pagination."""
    # 1. Base pagination
    res = get_alerts(limit=10, offset=0)
    assert res["total"] > 0
    assert len(res["alerts"]) <= 10
    top_alert = res["alerts"][0]
    assert "account_id" in top_alert
    assert "risk_score" in top_alert
    assert "primary_reason" in top_alert
    assert "counterfactual" in top_alert

    # 2. Risk band filtering
    crit_res = get_alerts(risk_band="critical")
    for a in crit_res["alerts"]:
        assert a["risk_band"] == "critical"
        assert a["risk_score"] >= 70.0


def test_account_detail_and_analyst_verdict():
    """Validates deep account investigation and human-in-the-loop analyst feedback."""
    alerts = get_alerts(limit=5)["alerts"]
    target_id = alerts[0]["account_id"]

    detail = get_account_detail(target_id)
    assert detail["account_id"] == target_id
    assert "total_inflow" in detail
    assert "risk_score" in detail
    assert "primary_reason" in detail
    assert "counterfactual" in detail
    assert isinstance(detail["inflow_transactions"], list)

    # Submit human feedback verdict
    orig_score = detail["risk_score"]
    v_req = VerdictRequest(verdict="confirmed_mule", analyst_notes="Structuring pattern validated.")
    v_res = record_verdict(target_id, v_req)

    assert v_res["success"] is True
    assert v_res["verdict"] == "confirmed_mule"
    # Re-fetch detail to verify persisted verdict
    updated_detail = get_account_detail(target_id)
    assert updated_detail["verdict"] == "confirmed_mule"


def test_graph_extraction_and_safety_cap():
    """Validates graph extraction adhering to strict 150-node safety limit."""
    # 1. Global graph capped at 50
    graph_50 = get_graph(max_nodes=50)
    assert len(graph_50["nodes"]) <= 50
    assert isinstance(graph_50["edges"], list)

    # 2. Neighborhood graph around first alert
    alerts = get_alerts(limit=1)["alerts"]
    center_id = alerts[0]["account_id"]
    subgraph = get_graph(center_id=center_id, depth=2, max_nodes=75)
    assert len(subgraph["nodes"]) <= 75
    node_ids = {n["data"]["id"] for n in subgraph["nodes"]}
    assert center_id in node_ids


def test_rings_and_sar_dossier():
    """Validates ring autopsies, DNA matching, and regulatory SAR dossier export."""
    rings = get_rings()
    assert len(rings) >= 4
    first_ring = rings[0]
    ring_id = first_ring["ring_id"]

    ring_detail = get_ring_detail(ring_id)
    assert ring_detail["ring_id"] == ring_id
    assert "dna_vector" in ring_detail
    assert "typology_match" in ring_detail

    # SAR Dossier export
    dossier = get_case_dossier(ring_id)
    assert dossier["target_ring_id"] == ring_id
    assert "SAR-IND-2026-" in dossier["sar_reference_id"]
    assert "Synthetic demonstration data. Not a real case." in dossier["disclaimer_synthetic"]
    assert "Estimated amount saved: ₹" in dossier["disclaimer_saved_money"]
    assert len(dossier["subject_accounts"]) > 0

    # Verify Rule 6: Analyst language check (no graph jargon in plain narrative)
    narrative_text = " ".join(dossier["executive_narrative"]).lower()
    for forbidden in [" node ", " edge ", " vertex ", " vertices "]:
        assert forbidden not in narrative_text


def test_replay_and_freeze_simulation():
    """Validates funds replay timeline generation and freeze impact curve."""
    # Find a hub or relay account
    alerts = get_alerts(limit=20)["alerts"]
    seed = next((a for a in alerts if a["role"] in ["hub", "relay"]), alerts[0])
    seed_acc = seed["account_id"]

    # Replay request
    replay_req = ReplayRequest(
        source_account=seed_acc,
        start_time="2026-03-01T00:00:00+05:30",
        initial_amount=100000.0,
        freeze_hour=2.0
    )
    replay_res = run_replay(replay_req)
    assert replay_res["source_account"] == seed_acc
    assert "frames" in replay_res
    assert isinstance(replay_res["frames"], list)

    # Freeze request
    freeze_req = FreezeRequest(
        source_account=seed_acc,
        start_time="2026-03-01T00:00:00+05:30",
        initial_amount=100000.0
    )
    freeze_res = run_freeze_simulation(freeze_req)
    assert "curve" in freeze_res
    assert len(freeze_res["curve"]) == 6  # 0h, 1h, 2h, 4h, 8h, 24h
    assert "Estimated amount saved: ₹" in freeze_res["curve"][0]["estimated_saved_formatted"]
    assert "Synthetic demonstration data" in freeze_res["disclaimer"]


def test_preset_switching_and_evasion_test():
    """Validates preset toggling and sensitivity analysis on evasion ring R6."""
    presets_meta = get_presets()
    assert "balanced" in presets_meta["presets"]
    assert "strict" in presets_meta["presets"]
    assert "relaxed" in presets_meta["presets"]

    # Switch to strict
    strict_res = set_preset(PresetRequest(preset="strict"))
    assert strict_res["success"] is True
    assert strict_res["active_preset"] == "strict"

    # Run evasion test
    evasion_res = get_evasion_test()
    assert evasion_res["ring_id"] == "R6"
    assert "relaxed" in evasion_res["analysis"]
    assert "balanced" in evasion_res["analysis"]
    assert "strict" in evasion_res["analysis"]

    # Switch back to balanced
    bal_res = set_preset(PresetRequest(preset="balanced"))
    assert bal_res["active_preset"] == "balanced"


def test_metrics_and_ground_truth_isolation():
    """Validates offline evaluation metrics and enforces ground truth isolation rule."""
    metrics = get_metrics()
    assert metrics["available"] is True
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert "tp" in metrics["confusion_matrix"]
    assert "Ground truth isolation rule enforced" in metrics["isolation_disclaimer"]


def test_quantum_api_endpoints():
    """Validates MuleTrace Omega simulation endpoints: walk, interdiction, and ring fidelity."""
    # 1. Test Quantum Walk API
    walk_res = get_quantum_walk(ring_id=None, steps=20)
    assert "ring_id" in walk_res
    assert "quantum_probabilities" in walk_res
    assert "classical_probabilities" in walk_res
    assert "time_steps" in walk_res
    assert len(walk_res["time_steps"]) == 20
    assert "overlap_score_quantum" in walk_res
    assert "overlap_score_classical" in walk_res
    assert "Simulated on a classical computer" in walk_res["disclaimer"]

    # 2. Test Quantum Interdiction API
    interdict_res = get_quantum_interdiction(ring_id=None, budget=3)
    assert interdict_res["budget_K"] == 3
    assert "greedy_list" in interdict_res
    assert "optimized_set" in interdict_res
    assert "Estimated amount saved: ₹" in interdict_res["greedy_list"]["estimated_saved_formatted"]
    assert "Estimated amount saved: ₹" in interdict_res["optimized_set"]["estimated_saved_formatted"]
    assert interdict_res["winner"] in ["optimized", "greedy", "tie"]
    assert "Simulated on a classical computer" in interdict_res["disclaimer"]

    # 3. Test Quantum Ring Fidelity API
    fidelity_res = get_quantum_ring_fidelity()
    assert "rings" in fidelity_res
    assert "typologies" in fidelity_res
    assert "ring_typology_matrix" in fidelity_res
    assert "ring_ring_matrix" in fidelity_res
    assert "highest_matches" in fidelity_res
    assert len(fidelity_res["highest_matches"]) > 0
    top_match = fidelity_res["highest_matches"][0]
    assert "fidelity" in top_match
    assert 0.0 <= top_match["fidelity"] <= 1.0
    assert "plain_language_reading" in top_match
    assert "Simulated on a classical computer" in fidelity_res["disclaimer"]

