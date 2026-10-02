"""Test Taint Tracing, Replay Frames, Freeze Simulator, and Chase List."""
from pathlib import Path
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.taint import TaintTracker
from backend.chase import build_chase_list, simulate_freeze, predict_next_hop


def test_taint_and_freeze_simulation():
    """Verify haircut taint propagation, freeze savings curve, and chase list ranking."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    # Find the victim transfer into R2 chain
    r2_victim_txns = [t for t in fg.out_txns.get("ACC_VICTIM_CHAIN01", []) if t["dest"] == "ACC_CHAIN_01"]
    assert len(r2_victim_txns) >= 1
    seed_txn = r2_victim_txns[0]
    seed_txn_id = seed_txn["txn_id"]

    tracker = TaintTracker(fg)
    res = tracker.trace_taint(seed_txn_id=seed_txn_id)

    assert "replay_frames" in res
    assert len(res["replay_frames"]) >= 7  # Seed + 6 chain hops + ATM exit
    assert res["initial_theft_amount"] == 350000.0

    # Invariant check: In-circulation taint + cashed out must not exceed initial theft
    for frame in res["replay_frames"]:
        in_circulation = sum(frame["active_taint"].values())
        cashed_out = frame["cumulative_cashed_out"]
        assert round(in_circulation + cashed_out, 2) <= res["initial_theft_amount"] + 0.1

    # 1. Chase List Verification (mid-chain at frame 3)
    chase = build_chase_list(res, fg, at_frame_index=3)
    assert len(chase["ranked_accounts"]) >= 1
    top_target = chase["ranked_accounts"][0]
    assert top_target["tainted_balance"] > 0
    assert "copyable_text" in chase
    assert top_target["account_id"] in chase["copyable_text"]

    # 2. Freeze Simulation Curve Verification
    freeze = simulate_freeze(res, time_points_min=[0, 5, 10, 15, 30, 60])
    assert len(freeze["curve"]) == 6
    
    # At t=0m (immediate freeze), 100% of ₹3,50,000 is saved
    t0 = freeze["curve"][0]
    assert t0["freeze_time_minutes"] == 0
    assert t0["estimated_saved"] == 350000.0
    assert t0["percent_saved"] == 100.0
    assert "Estimated amount saved: ₹" in t0["estimated_saved_formatted"]

    # Rule 8 and Rule 7: Disclaimer present
    assert "Synthetic demonstration data" in freeze["disclaimer"]
    assert "Saved money is always an estimate" in freeze["disclaimer"]

    # 3. Next Hop Prediction
    pred = predict_next_hop("ACC_CHAIN_02", fg, pattern_type="passthrough")
    assert "predicted_account" in pred
    assert "structural pattern heuristic, not ML" in pred["basis"]
