"""
MuleTrace Chronological Taint Tracing & Temporal Replay Engine
Propagates tainted illicit funds using proportional haircut mechanics and generates replay frames.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import format_inr


class TaintTracker:
    """Calculates proportional taint propagation along chronological transaction paths."""

    def __init__(self, fg: FinancialGraph):
        self.fg = fg

    def trace_taint(
        self,
        seed_txn_id: str,
        max_depth: int = 15,
        exit_accounts: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Traces chronological haircut-style proportional taint starting from seed_txn_id.
        Taint transfer = outgoing * min(1.0, tainted_balance / total_balance_before).
        Invariant: Total taint across all accounts + exits <= initial theft amount.
        """
        # Find the seed transaction
        seed_txn = None
        for u, v, key, data in self.fg.graph.edges(keys=True, data=True):
            if data["txn_id"] == seed_txn_id:
                seed_txn = data
                break

        if not seed_txn:
            return {"error": f"Seed transaction {seed_txn_id} not found."}

        initial_theft = seed_txn["amount"]
        origin_victim = seed_txn["source"]
        first_mule = seed_txn["dest"]
        seed_epoch = seed_txn["epoch"]

        # Filter all transactions occurring at or after seed_epoch
        # Sort chronologically
        relevant_txns = []
        for u, v, key, data in self.fg.graph.edges(keys=True, data=True):
            if data["epoch"] >= seed_epoch:
                relevant_txns.append(data)
        relevant_txns.sort(key=lambda x: (x["epoch"], x["txn_id"]))

        # State tracking: account_id -> current tainted balance
        taint_balances: Dict[str, float] = {first_mule: initial_theft}
        
        # Historical ledger of tainted transfers
        tainted_transfers: List[Dict[str, Any]] = []
        replay_frames: List[Dict[str, Any]] = []
        cumulative_cashed_out = 0.0

        known_exits = exit_accounts or set()

        # Initial frame (Seed transfer)
        initial_frame = {
            "frame_index": 0,
            "timestamp": seed_txn["timestamp"],
            "epoch": seed_epoch,
            "txn_id": seed_txn["txn_id"],
            "source": origin_victim,
            "dest": first_mule,
            "amount": initial_theft,
            "tainted_amount": initial_theft,
            "cumulative_cashed_out": 0.0,
            "active_taint": {first_mule: round(initial_theft, 2)},
        }
        replay_frames.append(initial_frame)

        frame_idx = 1
        for txn in relevant_txns:
            if txn["txn_id"] == seed_txn_id:
                continue  # Already captured in seed frame

            src = txn["source"]
            dst = txn["dest"]
            amt = txn["amount"]
            epoch = txn["epoch"]

            # If sender has tainted balance > 0, propagate taint
            src_taint = taint_balances.get(src, 0.0)
            if src_taint > 0.01:
                # Total balance of sender prior to transfer
                src_total_bal = txn.get("source_balance_after", 0.0) + amt
                if src_total_bal <= 0:
                    src_total_bal = amt

                # Haircut proportional taint ratio
                ratio = min(1.0, src_taint / src_total_bal)
                taint_moved = round(min(amt * ratio, src_taint), 2)

                if taint_moved > 0.01:
                    # Deduct from sender
                    taint_balances[src] = max(0.0, round(src_taint - taint_moved, 2))
                    is_exit = dst in known_exits or "EXIT" in dst or "CRYPTO" in dst or "ATM" in dst
                    if is_exit:
                        cumulative_cashed_out = round(cumulative_cashed_out + taint_moved, 2)
                        # Exits are terminal cash-out points; funds have escaped recoverable banking circulation
                        taint_balances[dst] = 0.0
                    else:
                        # Add to active receiver
                        taint_balances[dst] = round(taint_balances.get(dst, 0.0) + taint_moved, 2)

                    record = {
                        "txn_id": txn["txn_id"],
                        "timestamp": txn["timestamp"],
                        "epoch": epoch,
                        "source": src,
                        "dest": dst,
                        "total_amount": amt,
                        "tainted_amount": taint_moved,
                        "is_exit_transfer": is_exit,
                    }
                    tainted_transfers.append(record)

                    # Snapshot active taint balances (filter zero balances)
                    active_snapshot = {k: v for k, v in taint_balances.items() if v > 0.01}

                    replay_frames.append({
                        "frame_index": frame_idx,
                        "timestamp": txn["timestamp"],
                        "epoch": epoch,
                        "txn_id": txn["txn_id"],
                        "source": src,
                        "dest": dst,
                        "amount": amt,
                        "tainted_amount": taint_moved,
                        "cumulative_cashed_out": cumulative_cashed_out,
                        "active_taint": active_snapshot,
                    })
                    frame_idx += 1

        # Final active holders
        final_active = {k: v for k, v in taint_balances.items() if v > 0.01}

        return {
            "seed_txn_id": seed_txn_id,
            "origin_victim": origin_victim,
            "initial_theft_amount": initial_theft,
            "seed_timestamp": seed_txn["timestamp"],
            "seed_epoch": seed_epoch,
            "total_cashed_out": cumulative_cashed_out,
            "total_unrecovered_in_circulation": round(sum(final_active.values()), 2),
            "tainted_transfers": tainted_transfers,
            "replay_frames": replay_frames,
            "final_taint_distribution": final_active,
        }
