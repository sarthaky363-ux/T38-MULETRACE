"""
MuleTrace Chase List, Freeze Simulation, and Predictive Routing
Generates prioritized target interception lists and simulates financial savings across freeze intervention timelines.
"""

from typing import Any, Dict, List, Optional
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import format_inr


def build_chase_list(
    taint_result: Dict[str, Any],
    fg: FinancialGraph,
    at_frame_index: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ranks accounts currently holding active tainted funds in descending order.
    Generates plain-text format for the 'Copy list' button.
    """
    frames = taint_result.get("replay_frames", [])
    if not frames:
        return {"ranked_accounts": [], "copyable_text": "No active tainted funds."}

    # Select target frame
    if at_frame_index is not None and 0 <= at_frame_index < len(frames):
        target_frame = frames[at_frame_index]
    else:
        target_frame = frames[-1]

    active_taint = target_frame.get("active_taint", {})
    
    # Sort accounts by held tainted balance descending
    sorted_accounts = sorted(active_taint.items(), key=lambda x: x[1], reverse=True)

    ranked_list = []
    copy_lines = []

    for rank, (acc_id, amt) in enumerate(sorted_accounts, start=1):
        if amt < 0.01:
            continue
        acc_info = fg.account_lookup.get(acc_id, {})
        fmt_amt = format_inr(amt)
        role = acc_info.get("role", "mule")
        
        record = {
            "rank": rank,
            "account_id": acc_id,
            "display_name": acc_info.get("display_name", acc_id),
            "account_type": acc_info.get("account_type", "SAVINGS"),
            "role": role,
            "tainted_balance": round(amt, 2),
            "tainted_balance_formatted": fmt_amt,
            "kyc_verified": acc_info.get("kyc_verified", False),
            "device_id": acc_info.get("device_id", "N/A"),
            "ip_address": acc_info.get("ip_address", "N/A"),
        }
        ranked_list.append(record)
        copy_lines.append(f"{rank}. {acc_id} ({acc_info.get('display_name', acc_id)}): {fmt_amt} [{role.upper()}] - Dev: {acc_info.get('device_id', 'N/A')}")

    copyable_text = "\n".join(copy_lines) if copy_lines else "No accounts currently holding active tainted funds."

    return {
        "frame_index": target_frame.get("frame_index", 0),
        "timestamp": target_frame.get("timestamp", ""),
        "total_active_holders": len(ranked_list),
        "total_active_taint": round(sum(active_taint.values()), 2),
        "ranked_accounts": ranked_list,
        "copyable_text": copyable_text,
    }


def simulate_freeze(
    taint_result: Dict[str, Any],
    time_points_min: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Simulates early account freezing at t = 0, 5, 10, 15, 30, 60 minutes from seed theft.
    Computes estimated amount saved with mandatory synthetic disclaimer.
    """
    checkpoints = time_points_min or [0, 5, 10, 15, 30, 60]
    initial_theft = taint_result.get("initial_theft_amount", 0.0)
    seed_epoch = taint_result.get("seed_epoch", 0)
    frames = taint_result.get("replay_frames", [])

    results = []
    for delta_m in checkpoints:
        freeze_epoch = seed_epoch + delta_m * 60

        # Find cumulative cash-out that occurred strictly prior to freeze_epoch
        cashed_out = 0.0
        for f in frames:
            if f["epoch"] <= freeze_epoch:
                cashed_out = f.get("cumulative_cashed_out", 0.0)
            else:
                break

        estimated_saved = max(0.0, round(initial_theft - cashed_out, 2))
        pct_saved = round((estimated_saved / initial_theft) * 100, 1) if initial_theft > 0 else 0.0

        results.append({
            "freeze_time_minutes": delta_m,
            "freeze_epoch": freeze_epoch,
            "cashed_out_before_freeze": cashed_out,
            "cashed_out_formatted": format_inr(cashed_out),
            "estimated_saved": estimated_saved,
            "estimated_saved_formatted": f"Estimated amount saved: {format_inr(estimated_saved)}",
            "percent_saved": pct_saved,
        })

    return {
        "seed_txn_id": taint_result.get("seed_txn_id"),
        "initial_theft_amount": initial_theft,
        "initial_theft_formatted": format_inr(initial_theft),
        "curve": results,
        "disclaimer": "Synthetic demonstration data. Not a real case. Saved money is always an estimate.",
    }


def predict_next_hop(
    current_holder_id: str,
    fg: FinancialGraph,
    pattern_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Heuristically predicts likely next destination hop based on ring topology history.
    Explicitly labeled as a structural pattern heuristic, NOT machine learning.
    """
    out_txns = fg.out_txns.get(current_holder_id, [])

    if out_txns:
        # Most frequent destination from this account
        dest_counts = {}
        for t in out_txns:
            dst = t["dest"]
            dest_counts[dst] = dest_counts.get(dst, 0) + 1
        top_dest = max(dest_counts.items(), key=lambda x: x[1])[0]
        dst_info = fg.account_lookup.get(top_dest, {})

        return {
            "predicted_account": top_dest,
            "predicted_display_name": dst_info.get("display_name", top_dest),
            "account_type": dst_info.get("account_type", "SAVINGS"),
            "role": dst_info.get("role", "exit" if "EXIT" in top_dest else "relay"),
            "confidence": "medium",
            "basis": "Historical downstream transfer frequency (structural pattern heuristic, not ML)",
        }

    # If no outbound transfers yet, heuristic pattern fallback
    if pattern_type == "passthrough":
        guess_role = "Downstream relay mule or ATM cash-out point"
    elif pattern_type == "fan_in_out":
        guess_role = "Unregulated crypto OTC escrow terminal"
    else:
        guess_role = "Connected cash-out endpoint"

    return {
        "predicted_account": "PENDING_DISPERSAL",
        "predicted_display_name": guess_role,
        "account_type": "UNKNOWN",
        "role": "exit",
        "confidence": "low",
        "basis": f"Topology heuristic based on {pattern_type or 'layering'} ring behavior",
    }
