"""
MuleTrace Behavioral Signals Engine
Computes financial velocity, turnover, identity, and counterparties features for every account.
"""

from typing import Any, Dict, List, Set
from backend.graph import FinancialGraph


def compute_account_signals(fg: FinancialGraph, acc_id: str) -> Dict[str, Any]:
    """Computes comprehensive behavioral signals for a single account."""
    node = fg.account_lookup.get(acc_id, {})
    
    in_txns = fg.in_txns.get(acc_id, [])
    out_txns = fg.out_txns.get(acc_id, [])

    # Counterparties
    senders: Set[str] = {t["source"] for t in in_txns if t["source"] != acc_id}
    receivers: Set[str] = {t["dest"] for t in out_txns if t["dest"] != acc_id}
    counterparties: Set[str] = senders | receivers

    total_inflow = node.get("total_inflow", sum(t["amount"] for t in in_txns))
    total_outflow = node.get("total_outflow", sum(t["amount"] for t in out_txns))
    total_volume = total_inflow + total_outflow

    # Age and tenure
    age_days = int(node.get("age_days", 0))
    kyc_verified = bool(node.get("kyc_verified", False))
    tenure_kyc = age_days >= 365 and kyc_verified
    is_new_account = age_days <= 30

    # Retained ratio
    retained_ratio = float(node.get("retained_ratio", 0.0))
    if total_inflow > 0 and retained_ratio == 0.0:
        retained_ratio = round((total_inflow - total_outflow) / total_inflow, 3)

    # Average balance proxy
    avg_balance = float(node.get("avg_balance", node.get("declared_monthly_income", 0.0) * 0.35 + 5000.0))
    turnover_ratio = round(total_volume / (avg_balance + 1000.0), 2)

    # Shortest outbound gap after an inbound transfer
    min_hop_gap_sec = None
    for t_in in in_txns:
        in_epoch = t_in["epoch"]
        for t_out in out_txns:
            diff = t_out["epoch"] - in_epoch
            if diff >= 0:
                if min_hop_gap_sec is None or diff < min_hop_gap_sec:
                    min_hop_gap_sec = diff
                break

    min_gap_minutes = round(min_hop_gap_sec / 60.0, 1) if min_hop_gap_sec is not None else None

    # Shared identity signals
    dev = node.get("device_id")
    pan = node.get("kyc_pan_hash")
    ip = node.get("ip_address")

    shared_dev_count = len(fg.device_accounts.get(dev, set())) if dev else 0
    shared_pan_count = len(fg.pan_accounts.get(pan, set())) if pan else 0
    shared_ip_count = len(fg.ip_accounts.get(ip, set())) if ip else 0

    return {
        "account_id": acc_id,
        "display_name": node.get("display_name", acc_id),
        "account_type": node.get("account_type", "SAVINGS"),
        "age_days": age_days,
        "is_new_account": is_new_account,
        "kyc_verified": kyc_verified,
        "tenure_kyc": tenure_kyc,
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "total_volume": round(total_volume, 2),
        "avg_balance": round(avg_balance, 2),
        "retained_ratio": retained_ratio,
        "turnover_ratio": turnover_ratio,
        "unique_senders": len(senders),
        "unique_receivers": len(receivers),
        "unique_counterparties": len(counterparties),
        "min_forward_gap_minutes": min_gap_minutes,
        "shared_device_accounts": shared_dev_count,
        "shared_pan_accounts": shared_pan_count,
        "shared_ip_accounts": shared_ip_count,
    }
