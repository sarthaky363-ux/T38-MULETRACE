"""
MuleTrace Pass-Through Layering Detector
Detects multi-hop rapid relay chains designed to obfuscate audit trails.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from backend.graph import FinancialGraph
from backend.detectors.fan_in_out import format_inr


class PassthroughDetector:
    """Detects rapid pass-through money-laundering relay chains."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.max_gap_sec = (thresholds.get("max_gap_min", 8) if thresholds else 8) * 60
        self.min_amount_ratio = thresholds.get("min_amount_ratio", 0.85) if thresholds else 0.85
        self.max_post_balance = thresholds.get("max_post_balance", 2000.0) if thresholds else 2000.0
        self.min_chain_accounts = thresholds.get("min_chain_accounts", 3) if thresholds else 3

    def detect(self, fg: FinancialGraph) -> List[Dict[str, Any]]:
        """
        Scans for sequential multi-hop pass-through relay chains.
        Returns list of structured hits for all qualifying relay accounts.
        """
        # Step 1: Identify all candidate relay transitions (in_txn -> out_txn on account V)
        # account -> list of (in_txn, out_txn, gap_sec, ratio)
        relays_by_account: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {}

        for acc_id, in_list in fg.in_txns.items():
            out_list = fg.out_txns.get(acc_id, [])
            if not in_list or not out_list:
                continue

            valid_pairs = []
            for t_in in in_list:
                in_amt = t_in["amount"]
                in_epoch = t_in["epoch"]

                for t_out in out_list:
                    gap_sec = t_out["epoch"] - in_epoch
                    # Must occur after or simultaneously, but within max_gap_sec
                    if 0 <= gap_sec <= self.max_gap_sec:
                        ratio = (t_out["amount"] / in_amt) if in_amt > 0 else 0.0
                        post_bal = t_out.get("source_balance_after", 0.0)
                        
                        if self.min_amount_ratio <= ratio <= 1.15 and post_bal <= self.max_post_balance:
                            valid_pairs.append((t_in, t_out))
                    elif gap_sec > self.max_gap_sec:
                        # Out txns are sorted; no future out_txn will be within window for this in_txn
                        break

            if valid_pairs:
                relays_by_account[acc_id] = valid_pairs

        # Step 2: Stitch valid pairs into connected multi-hop chains
        # A chain link exists if pair1's out_txn is pair2's in_txn
        # out_txn of account A -> dest account B -> in_txn of account B
        chains: List[List[Tuple[str, Dict[str, Any]]]] = []

        def build_chains_from_pair(curr_acc: str, curr_in: Dict[str, Any], curr_out: Dict[str, Any], visited: Set[str], current_chain: List[Dict[str, Any]]):
            next_acc = curr_out["dest"]
            if next_acc in visited or next_acc not in relays_by_account:
                # End of chain
                return [current_chain]

            found_extension = False
            results = []
            for nxt_in, nxt_out in relays_by_account[next_acc]:
                # The incoming transfer to next_acc must be the outgoing transfer from curr_acc
                if nxt_in["txn_id"] == curr_out["txn_id"]:
                    found_extension = True
                    results.extend(build_chains_from_pair(
                        next_acc, nxt_in, nxt_out, visited | {next_acc}, current_chain + [(next_acc, nxt_in, nxt_out)]
                    ))

            if not found_extension:
                return [current_chain]
            return results

        all_chains = []
        for start_acc, pairs in relays_by_account.items():
            for t_in, t_out in pairs:
                initial_step = [(start_acc, t_in, t_out)]
                expanded = build_chains_from_pair(start_acc, t_in, t_out, {start_acc}, initial_step)
                for c in expanded:
                    if len(c) >= self.min_chain_accounts:
                        all_chains.append(c)

        if not all_chains:
            return []

        # Deduplicate chains (keep maximum length chains)
        # Sort by chain length descending
        all_chains.sort(key=lambda x: len(x), reverse=True)
        unique_chains = []
        seen_txns: Set[str] = set()

        for c in all_chains:
            c_txns = {step[2]["txn_id"] for step in c}
            if not c_txns.issubset(seen_txns):
                unique_chains.append(c)
                seen_txns.update(c_txns)

        # Step 3: Format hits for each intermediate relay account in the qualifying chains
        hits: List[Dict[str, Any]] = []
        for chain in unique_chains:
            chain_accounts = [step[0] for step in chain]
            origin_acc = chain[0][1]["source"]
            final_exit_acc = chain[-1][2]["dest"]
            full_path = [origin_acc] + chain_accounts + [final_exit_acc]
            
            all_chain_txns = [chain[0][1]["txn_id"]] + [step[2]["txn_id"] for step in chain]
            chain_start_epoch = chain[0][1]["epoch"]
            ring_key = f"RING_PASS_{origin_acc}_{final_exit_acc}_{chain_start_epoch}"

            for idx, (acc, t_in, t_out) in enumerate(chain, start=1):
                gap_min = round((t_out["epoch"] - t_in["epoch"]) / 60.0, 1)
                forward_pct = round(t_out["amount"] / t_in["amount"], 3) if t_in["amount"] > 0 else 0.0

                hit = {
                    "account": acc,
                    "pattern": "passthrough",
                    "ring_key": ring_key,
                    "role": "relay",
                    "evidence": {
                        "chain_length": len(chain_accounts),
                        "hop_position": idx,
                        "hop_gap_minutes": gap_min,
                        "forward_ratio": forward_pct,
                        "in_amount": round(t_in["amount"], 2),
                        "out_amount": round(t_out["amount"], 2),
                        "post_balance": round(t_out.get("source_balance_after", 0.0), 2),
                        "chain_path": full_path,
                        "origin_account": origin_acc,
                        "exit_account": final_exit_acc,
                    },
                    "txn_ids": all_chain_txns,
                    "first_ts": chain[0][1]["timestamp"],
                    "last_ts": chain[-1][2]["timestamp"],
                }
                hits.append(hit)

        return hits

    def explain(self, hit: Dict[str, Any]) -> Dict[str, str]:
        """
        Produces compliance-grade, plain-language and technical explanations.
        Adheres to Rule 3 (explainability) & Rule 6 (banking vocabulary, never graph jargon).
        """
        ev = hit["evidence"]
        in_amt = format_inr(ev["in_amount"])
        out_amt = format_inr(ev["out_amount"])
        post_bal = format_inr(ev["post_balance"])
        pct_fmt = f"{ev['forward_ratio'] * 100:.1f}%"
        pos = ev["hop_position"]
        total_hops = ev["chain_length"]
        gap = ev["hop_gap_minutes"]

        plain_reason = (
            f"This account served as a rapid pass-through relay (transfer hop {pos} of {total_hops}), "
            f"receiving {in_amt} and forwarding {out_amt} ({pct_fmt}) within {gap} minutes, "
            f"leaving a minimal residual balance of {post_bal}."
        )

        technical_reason = (
            f"Pass-through layering chain detected. Hop {pos}/{total_hops}. Forwarded: {pct_fmt} "
            f"(threshold: >={self.min_amount_ratio * 100:.0f}%). Time gap: {gap}m (threshold: <={self.max_gap_sec // 60}m). "
            f"Post-transfer balance: {post_bal} (threshold: <={format_inr(self.max_post_balance)})."
        )

        counterfactual = (
            f"If funds were retained for more than {self.max_gap_sec // 60} minutes before forwarding, "
            f"or if more than {format_inr(self.max_post_balance)} remained in the account after the transfer, "
            f"this account would not be flagged as a rapid pass-through relay."
        )

        return {
            "plain_reason": plain_reason,
            "technical_reason": technical_reason,
            "counterfactual": counterfactual,
        }
