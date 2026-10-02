"""
MuleTrace Quantum-Inspired Network Interdiction Optimizer
Formulates early account freezing as a binary quadratic minimization problem (QUBO),
solved via deterministic simulated annealing, and compared against the greedy Chase List.
Simulated on a classical computer. Synthetic demonstration data. Not a real case.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import yaml
import os

from backend.graph import FinancialGraph
from backend.taint import TaintTracker
from backend.detectors.fan_in_out import format_inr


def load_interdiction_config() -> Dict[str, Any]:
    """Loads interdiction hyperparameters from thresholds.yaml."""
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config", "thresholds.yaml"
    )
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("quantum", {}).get("interdiction", {})
        except Exception:
            pass
    return {}


class NetworkInterdictionOptimizer:
    """
    Minimizes:
        E(x) = λ1 * Σ (1 - x_i) * flow_i
             + λ2 * Σ x_i * innocence_cost_i
             + μ * (Σ x_i - K)^2

    Subject to:
        Victim Protection Invariant: x_victim = 0 (victims are NEVER frozen).
    """

    def __init__(self, fg: FinancialGraph, config: Optional[Dict[str, Any]] = None):
        self.fg = fg
        self.config = config or load_interdiction_config()
        self.lambda1 = float(self.config.get("lambda1_flow", 1.0))
        self.lambda2 = float(self.config.get("lambda2_innocence", 1.5))
        self.mu = float(self.config.get("mu_budget", 2.0))
        
        anneal_cfg = self.config.get("annealing", {})
        self.initial_temp = float(anneal_cfg.get("initial_temp", 10.0))
        self.cooling_rate = float(anneal_cfg.get("cooling_rate", 0.95))
        self.iterations = int(anneal_cfg.get("iterations", 500))
        self.seed = int(anneal_cfg.get("seed", 42))

    def compute_energy(
        self,
        x: np.ndarray,
        flow: np.ndarray,
        innocence: np.ndarray,
        budget_K: int
    ) -> float:
        """Evaluates the objective energy function E(x)."""
        term1 = self.lambda1 * np.sum((1.0 - x) * flow)
        term2 = self.lambda2 * np.sum(x * innocence)
        term3 = self.mu * ((np.sum(x) - budget_K) ** 2)
        return float(term1 + term2 + term3)

    def solve(
        self,
        nodes: List[str],
        flow: np.ndarray,
        budget_K: int,
        seed: Optional[int] = None
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Solves the interdiction QUBO using deterministic simulated annealing.
        Guarantees:
            1. Victim Protection Invariant: no victim account is ever frozen.
            2. Fixed seed ensures 100% deterministic reproducibility.
        """
        n = len(nodes)
        if n == 0 or budget_K <= 0:
            return [], {"initial_energy": 0.0, "final_energy": 0.0, "iterations": 0}

        effective_seed = self.seed if seed is None else seed
        rng = np.random.default_rng(effective_seed)

        # Build innocence costs and identify victims
        innocence = np.zeros(n, dtype=np.float64)
        is_victim = np.zeros(n, dtype=bool)

        for i, acc in enumerate(nodes):
            acc_d = self.fg.account_lookup.get(acc, {})
            role = acc_d.get("role", "member")
            risk_score = float(acc_d.get("risk_score", 0.0))

            if role == "victim" or "VICTIM" in acc:
                is_victim[i] = True
                innocence[i] = 1e6  # Infinite cost barrier
            else:
                # Low risk score -> High innocence cost (0 to 1)
                innocence[i] = max(0.0, 1.0 - (risk_score / 100.0))

        non_victim_indices = [i for i in range(n) if not is_victim[i]]
        if not non_victim_indices:
            return [], {"initial_energy": 0.0, "final_energy": 0.0, "iterations": 0}

        k_target = min(budget_K, len(non_victim_indices))

        # Initial solution: Top K accounts by flow / (innocence + 0.1)
        score_init = [
            (flow[i] / (innocence[i] + 0.1), i) for i in non_victim_indices
        ]
        score_init.sort(reverse=True)
        top_k_indices = {idx for _, idx in score_init[:k_target]}

        x = np.zeros(n, dtype=np.float64)
        for idx in top_k_indices:
            x[idx] = 1.0

        current_energy = self.compute_energy(x, flow, innocence, k_target)
        initial_energy = current_energy

        best_x = x.copy()
        best_energy = current_energy

        temp = self.initial_temp

        for step in range(self.iterations):
            # Select a random non-victim account to flip
            pick_idx = rng.choice(non_victim_indices)
            new_val = 1.0 - x[pick_idx]

            # Compute delta energy efficiently
            old_val = x[pick_idx]
            old_sum = np.sum(x)
            new_sum = old_sum - old_val + new_val

            delta_term1 = self.lambda1 * (-(new_val - old_val) * flow[pick_idx])
            delta_term2 = self.lambda2 * ((new_val - old_val) * innocence[pick_idx])
            delta_term3 = self.mu * (((new_sum - k_target) ** 2) - ((old_sum - k_target) ** 2))
            delta_E = delta_term1 + delta_term2 + delta_term3

            # Metropolis acceptance criterion
            accept = False
            if delta_E < 0:
                accept = True
            else:
                prob = np.exp(-delta_E / max(1e-6, temp))
                if rng.random() < prob:
                    accept = True

            if accept:
                x[pick_idx] = new_val
                current_energy += delta_E
                if current_energy < best_energy:
                    best_energy = current_energy
                    best_x = x.copy()

            temp *= self.cooling_rate

        # Enforce Victim Protection Invariant strictly on best_x
        for i in range(n):
            if is_victim[i]:
                best_x[i] = 0.0

        chosen_accounts = [nodes[i] for i in range(n) if best_x[i] > 0.5]
        return chosen_accounts, {
            "initial_energy": round(float(initial_energy), 4),
            "final_energy": round(float(best_energy), 4),
            "iterations": self.iterations,
            "seed": effective_seed,
        }

    def simulate_freeze_set(
        self,
        seed_txn_id: str,
        frozen_set: Set[str]
    ) -> Dict[str, Any]:
        """
        Simulates the financial impact of preemptively freezing a specific set of accounts.
        If an account is frozen, all subsequent outgoing transfers from it are blocked.
        Tainted funds trapped in frozen accounts cannot cash out.
        """
        # Find seed transaction
        seed_txn = None
        for u, v, key, data in self.fg.graph.edges(keys=True, data=True):
            if data["txn_id"] == seed_txn_id:
                seed_txn = data
                break

        if not seed_txn:
            return {
                "initial_theft": 0.0,
                "cashed_out": 0.0,
                "estimated_saved": 0.0,
                "estimated_saved_formatted": "Estimated amount saved: ₹0",
            }

        initial_theft = float(seed_txn["amount"])
        origin_victim = seed_txn["source"]
        first_mule = seed_txn["dest"]
        seed_epoch = seed_txn["epoch"]

        # If the first mule is frozen immediately, entire theft is saved
        if first_mule in frozen_set:
            return {
                "initial_theft": initial_theft,
                "cashed_out": 0.0,
                "estimated_saved": initial_theft,
                "estimated_saved_formatted": f"Estimated amount saved: {format_inr(initial_theft)}",
            }

        relevant_txns = [
            d for u, v, k, d in self.fg.graph.edges(keys=True, data=True)
            if d["epoch"] >= seed_epoch
        ]
        relevant_txns.sort(key=lambda x: (x["epoch"], x["txn_id"]))

        taint_balances: Dict[str, float] = {first_mule: initial_theft}
        cumulative_cashed_out = 0.0

        for txn in relevant_txns:
            if txn["txn_id"] == seed_txn_id:
                continue

            src = txn["source"]
            dst = txn["dest"]
            amt = float(txn["amount"])

            # If sender is frozen, outgoing transfer is BLOCKED!
            if src in frozen_set:
                continue

            src_taint = taint_balances.get(src, 0.0)
            if src_taint > 0.01:
                src_total_bal = float(txn.get("source_balance_after", 0.0)) + amt
                if src_total_bal <= 0:
                    src_total_bal = amt
                ratio = min(1.0, src_taint / src_total_bal)
                taint_moved = min(amt * ratio, src_taint)

                if taint_moved > 0.01:
                    taint_balances[src] = max(0.0, src_taint - taint_moved)
                    is_exit = "EXIT" in dst or "CRYPTO" in dst or "ATM" in dst or self.fg.account_lookup.get(dst, {}).get("role") == "exit"
                    
                    if is_exit:
                        cumulative_cashed_out += taint_moved
                        taint_balances[dst] = 0.0
                    else:
                        # If destination is frozen, funds land and get TRAPPED (cannot move further)
                        taint_balances[dst] = taint_balances.get(dst, 0.0) + taint_moved

        estimated_saved = max(0.0, round(initial_theft - cumulative_cashed_out, 2))
        return {
            "initial_theft": initial_theft,
            "cashed_out": round(cumulative_cashed_out, 2),
            "estimated_saved": estimated_saved,
            "estimated_saved_formatted": f"Estimated amount saved: {format_inr(estimated_saved)}",
        }

    def compare_greedy_vs_optimized(
        self,
        nodes: List[str],
        flow: np.ndarray,
        budget_K: int,
        seed_txn_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compares the existing greedy Chase List against the quantum-inspired
        simulated annealing optimized freeze set.
        """
        # 1. Solve optimization
        optimized_accounts, solver_stats = self.solve(nodes, flow, budget_K)
        opt_set = set(optimized_accounts)

        # 2. Build Greedy Chase List set
        # Filter out victims per Victim Protection Invariant
        eligible_nodes = [
            acc for acc in nodes
            if self.fg.account_lookup.get(acc, {}).get("role") != "victim" and "VICTIM" not in acc
        ]
        # Rank by current risk score descending, then by flow
        node_scores = [
            (
                float(self.fg.account_lookup.get(acc, {}).get("risk_score", 0.0)),
                float(flow[nodes.index(acc)]),
                acc
            )
            for acc in eligible_nodes
        ]
        node_scores.sort(reverse=True)
        greedy_accounts = [acc for _, _, acc in node_scores[:budget_K]]
        greedy_set = set(greedy_accounts)

        # 3. Find seed transaction if not provided
        target_seed = seed_txn_id
        if not target_seed and nodes:
            entry_acc = nodes[0]
            out_txs = self.fg.out_txns.get(entry_acc, [])
            if out_txs:
                target_seed = out_txs[0]["txn_id"]
            else:
                for acc in nodes:
                    in_txs = self.fg.in_txns.get(acc, [])
                    if in_txs:
                        target_seed = in_txs[0]["txn_id"]
                        break

        # 4. Simulate financial recovery for both sets
        greedy_sim = self.simulate_freeze_set(target_seed, greedy_set) if target_seed else {
            "estimated_saved": 0.0,
            "estimated_saved_formatted": "Estimated amount saved: ₹0",
        }
        opt_sim = self.simulate_freeze_set(target_seed, opt_set) if target_seed else {
            "estimated_saved": 0.0,
            "estimated_saved_formatted": "Estimated amount saved: ₹0",
        }

        # Count low-risk accounts frozen (collateral false positives, risk_score < 40)
        def count_low_risk(acc_list: List[str]) -> int:
            cnt = 0
            for a in acc_list:
                score = float(self.fg.account_lookup.get(a, {}).get("risk_score", 0.0))
                band = self.fg.account_lookup.get(a, {}).get("risk_band", "safe")
                if score < 40.0 or band in ["safe", "low"]:
                    cnt += 1
            return cnt

        greedy_low_risk = count_low_risk(greedy_accounts)
        opt_low_risk = count_low_risk(optimized_accounts)

        # Honest comparison evaluation (Rule 4: Never invent results)
        saved_opt = opt_sim["estimated_saved"]
        saved_greedy = greedy_sim["estimated_saved"]
        if saved_opt > saved_greedy:
            advantage = "Optimized set saves more funds"
            winner = "optimized"
        elif saved_opt < saved_greedy:
            advantage = "Greedy list saves more funds"
            winner = "greedy"
        else:
            if opt_low_risk < greedy_low_risk:
                advantage = "Equal savings with fewer low-risk freezes"
                winner = "optimized"
            elif opt_low_risk > greedy_low_risk:
                advantage = "Equal savings; greedy froze fewer low-risk"
                winner = "greedy"
            else:
                advantage = "Methods tied on this configuration"
                winner = "tie"

        return {
            "budget_K": budget_K,
            "greedy_list": {
                "accounts": greedy_accounts,
                "count_frozen": len(greedy_accounts),
                "count_low_risk_frozen": greedy_low_risk,
                "estimated_saved": saved_greedy,
                "estimated_saved_formatted": greedy_sim["estimated_saved_formatted"],
            },
            "optimized_set": {
                "accounts": optimized_accounts,
                "count_frozen": len(optimized_accounts),
                "count_low_risk_frozen": opt_low_risk,
                "estimated_saved": saved_opt,
                "estimated_saved_formatted": opt_sim["estimated_saved_formatted"],
            },
            "winner": winner,
            "comparison_summary": advantage,
            "solver_diagnostics": solver_stats,
            "disclaimer": "Simulated on a classical computer. Synthetic demonstration data. Not a real case.",
        }
