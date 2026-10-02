"""
MuleTrace Circular Transfer (Wash Trading / Loop) Detector
Detects closed circular money-flow loops across 3 to 5 accounts within a tight time window.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import format_inr


class CycleDetector:
    """Detects rapid closed-loop circular transfer rings."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.min_len = thresholds.get("min_len", 3) if thresholds else 3
        self.max_len = thresholds.get("max_len", 5) if thresholds else 5
        self.max_duration_sec = (thresholds.get("max_duration_min", 45) if thresholds else 45) * 60
        self.amount_tolerance = thresholds.get("amount_tolerance", 0.20) if thresholds else 0.20

    def detect(self, fg: FinancialGraph) -> List[Dict[str, Any]]:
        """
        Scans fg for temporal circular loops of length min_len..max_len.
        Returns list of structured hit dictionaries.
        """
        detected_cycles: List[Dict[str, Any]] = []
        seen_cycle_fingerprints: Set[frozenset] = set()

        # Bounded temporal DFS to find cycles starting from each account
        for start_node in fg.graph.nodes():
            out_txns = fg.out_txns.get(start_node, [])
            if not out_txns:
                continue

            for initial_txn in out_txns:
                t0_epoch = initial_txn["epoch"]
                t0_amt = initial_txn["amount"]
                target1 = initial_txn["dest"]

                if target1 == start_node:
                    continue  # Ignore self-transfers

                # DFS state: (current_node, current_epoch, path_nodes, path_txns)
                stack: List[Tuple[str, int, List[str], List[Dict[str, Any]]]] = [
                    (target1, t0_epoch, [start_node, target1], [initial_txn])
                ]

                while stack:
                    curr_node, curr_epoch, curr_path_nodes, curr_path_txns = stack.pop()
                    hop_count = len(curr_path_nodes) - 1

                    # Look at outbound transfers from curr_node
                    for next_txn in fg.out_txns.get(curr_node, []):
                        next_epoch = next_txn["epoch"]
                        
                        # Temporal condition: must occur after previous hop
                        if next_epoch < curr_epoch:
                            continue
                        
                        # Total duration constraint
                        if next_epoch - t0_epoch > self.max_duration_sec:
                            break  # out_txns are sorted by epoch; future txns will exceed window

                        # Amount tolerance constraint relative to starting amount
                        amt = next_txn["amount"]
                        if abs(amt - t0_amt) / t0_amt > self.amount_tolerance:
                            continue

                        next_dest = next_txn["dest"]

                        # Check if cycle closes back to start_node
                        if next_dest == start_node:
                            cycle_length = hop_count + 1
                            if self.min_len <= cycle_length <= self.max_len:
                                full_nodes = curr_path_nodes + [start_node]
                                full_txns = curr_path_txns + [next_txn]

                                # Canonical representation for deduplication
                                cycle_members = frozenset(curr_path_nodes)
                                if cycle_members not in seen_cycle_fingerprints:
                                    seen_cycle_fingerprints.add(cycle_members)
                                    detected_cycles.append({
                                        "path_nodes": full_nodes,
                                        "path_txns": full_txns,
                                        "start_epoch": t0_epoch,
                                        "end_epoch": next_epoch,
                                        "initial_amount": t0_amt,
                                        "final_amount": amt,
                                        "cycle_length": cycle_length,
                                    })
                        elif next_dest not in curr_path_nodes and (hop_count + 1) < self.max_len:
                            # Continue DFS path expansion
                            stack.append((
                                next_dest,
                                next_epoch,
                                curr_path_nodes + [next_dest],
                                curr_path_txns + [next_txn]
                            ))

        # Format hits for each participating account
        hits: List[Dict[str, Any]] = []
        for cyc in detected_cycles:
            accounts_in_cycle = cyc["path_nodes"][:-1]
            duration_min = round((cyc["end_epoch"] - cyc["start_epoch"]) / 60.0, 1)
            txn_ids = [t["txn_id"] for t in cyc["path_txns"]]
            first_ts = cyc["path_txns"][0]["timestamp"]
            last_ts = cyc["path_txns"][-1]["timestamp"]
            
            amounts = [t["amount"] for t in cyc["path_txns"]]
            max_dev_pct = max(abs(a - cyc["initial_amount"]) / cyc["initial_amount"] for a in amounts)
            ring_key = f"RING_CYCLE_{accounts_in_cycle[0]}_{cyc['start_epoch']}"

            for acc in accounts_in_cycle:
                hit = {
                    "account": acc,
                    "pattern": "cycle",
                    "ring_key": ring_key,
                    "role": "cycle",
                    "evidence": {
                        "cycle_length": cyc["cycle_length"],
                        "cycle_path": cyc["path_nodes"],
                        "cycle_duration_minutes": duration_min,
                        "initial_amount": round(cyc["initial_amount"], 2),
                        "final_amount": round(cyc["final_amount"], 2),
                        "max_amount_deviation": round(max_dev_pct, 3),
                        "accounts_in_cycle": accounts_in_cycle,
                    },
                    "txn_ids": txn_ids,
                    "first_ts": first_ts,
                    "last_ts": last_ts,
                }
                hits.append(hit)

        return hits

    def explain(self, hit: Dict[str, Any]) -> Dict[str, str]:
        """
        Produces compliance-grade, plain-language and technical explanations.
        Adheres to Rule 3 (explainability) & Rule 6 (banking vocabulary, never graph jargon).
        """
        ev = hit["evidence"]
        c_len = ev["cycle_length"]
        dur = ev["cycle_duration_minutes"]
        init_fmt = format_inr(ev["initial_amount"])
        dev_pct = f"{ev['max_amount_deviation'] * 100:.1f}%"

        plain_reason = (
            f"This account participated in a {c_len}-account circular transfer loop, where approximately {init_fmt} "
            f"was routed across {c_len} connected accounts in a closed circle and returned to the starting account "
            f"within {dur} minutes."
        )

        technical_reason = (
            f"Circular transfer loop detected. Accounts involved: {c_len} (limit: {self.min_len}-{self.max_len}). "
            f"Cycle completed in {dur}m (threshold: <={self.max_duration_sec // 60}m). "
            f"Max amount deviation: {dev_pct} (threshold: <={self.amount_tolerance * 100:.0f}%)."
        )

        counterfactual = (
            f"If the circular transfer took longer than {self.max_duration_sec // 60} minutes to return to the starting account, "
            f"or if transfer amounts fluctuated by more than {self.amount_tolerance * 100:.0f}%, this cycle would not be flagged."
        )

        return {
            "plain_reason": plain_reason,
            "technical_reason": technical_reason,
            "counterfactual": counterfactual,
        }
