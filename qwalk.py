"""
MuleTrace Quantum Walk & Classical Diffusion Simulator
Continuous-time quantum random walk on financial ring subgraphs compared against
classical Laplacian diffusion.
Simulated on a classical computer. Synthetic demonstration data. Not a real case.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import yaml
import os

from backend.graph import FinancialGraph
from backend.taint import TaintTracker


def load_quantum_config() -> Dict[str, Any]:
    """Loads quantum-specific thresholds from config/thresholds.yaml."""
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config", "thresholds.yaml"
    )
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("quantum", {})
        except Exception:
            pass
    return {}


class QuantumWalkSimulator:
    """
    Executes continuous-time quantum walks (CTQW) and classical Laplacian diffusion
    on financial subgraphs to forecast the propagation velocity of illicit funds.
    """

    def __init__(self, fg: FinancialGraph, config: Optional[Dict[str, Any]] = None):
        self.fg = fg
        self.config = config or load_quantum_config()
        self.walk_cfg = self.config.get("walk", {})
        self.default_steps = int(self.walk_cfg.get("default_steps", 60))
        self.max_nodes = int(self.walk_cfg.get("max_nodes", 150))
        self.time_scale = float(self.walk_cfg.get("time_scale", 0.1))
        self.top_k_exits = int(self.walk_cfg.get("top_k_exits", 5))

    def extract_ring_subgraph(
        self,
        ring_data: Dict[str, Any],
        max_nodes: Optional[int] = None
    ) -> Tuple[List[str], np.ndarray, str, Dict[str, Any]]:
        """
        Builds a symmetric weighted adjacency matrix A from the ring's accounts and
        connected transaction partners, up to the safety cap (150 nodes).
        Edge weight = log(1 + total_transfer_amount).
        Returns:
            nodes: list of account IDs (indexed 0..N-1)
            A: symmetric NxN numpy array
            entry_account: root theft entry account ID
            metadata: account attributes dictionary
        """
        cap = max_nodes or self.max_nodes
        members = list(ring_data.get("members", []))
        if not members and "chain" in ring_data:
            members = list(ring_data["chain"])

        # Determine entry account
        # Priority: explicit victim sender > hub_account > chain[0] > first member
        entry_account = ring_data.get("hub_account")
        if not entry_account and members:
            entry_account = members[0]

        # Check if an external victim feeds into the ring
        for m in members:
            for in_tx in self.fg.in_txns.get(m, []):
                src = in_tx["source"]
                if "VICTIM" in src or self.fg.account_lookup.get(src, {}).get("role") == "victim":
                    entry_account = src
                    if src not in members:
                        members.insert(0, src)
                    break

        selected_set: Set[str] = set(members)

        # Expand neighborhood if under safety cap to capture terminal exit points
        if len(selected_set) < cap:
            candidate_neighbors: List[str] = []
            for acc in list(selected_set):
                for out_tx in self.fg.out_txns.get(acc, []):
                    dst = out_tx["dest"]
                    if dst not in selected_set:
                        candidate_neighbors.append(dst)
                for in_tx in self.fg.in_txns.get(acc, []):
                    src = in_tx["source"]
                    if src not in selected_set:
                        candidate_neighbors.append(src)

            # Prioritize exits and high-volume accounts
            def neighbor_priority(acc_id: str) -> float:
                score = 0.0
                if "EXIT" in acc_id or "CRYPTO" in acc_id or "ATM" in acc_id:
                    score += 1000.0
                node_d = self.fg.account_lookup.get(acc_id, {})
                score += node_d.get("total_inflow", 0.0) + node_d.get("total_outflow", 0.0)
                return score

            sorted_neighbors = sorted(set(candidate_neighbors), key=neighbor_priority, reverse=True)
            for n in sorted_neighbors:
                if len(selected_set) >= cap:
                    break
                selected_set.add(n)

        node_list = sorted(list(selected_set))
        if entry_account not in node_list:
            node_list.insert(0, entry_account)
            if len(node_list) > cap:
                node_list = node_list[:cap]

        n = len(node_list)
        idx_map = {acc: i for i, acc in enumerate(node_list)}
        A = np.zeros((n, n), dtype=np.float64)

        # Sum total transaction amounts between node pairs in either direction
        for i, u in enumerate(node_list):
            for out_tx in self.fg.out_txns.get(u, []):
                v = out_tx["dest"]
                if v in idx_map:
                    j = idx_map[v]
                    amt = float(out_tx.get("amount", 0.0))
                    # Symmetric accumulation
                    A[i, j] += amt
                    A[j, i] += amt

        # Apply logarithmic weighting: weight = log(1 + amount)
        for i in range(n):
            for j in range(n):
                if i != j and A[i, j] > 0.0:
                    A[i, j] = np.log1p(A[i, j])
                else:
                    A[i, j] = 0.0

        # Account metadata for UI rendering
        metadata = {}
        for acc in node_list:
            acc_d = self.fg.account_lookup.get(acc, {})
            metadata[acc] = {
                "account_id": acc,
                "display_name": acc_d.get("display_name", acc),
                "account_type": acc_d.get("account_type", "SAVINGS"),
                "role": acc_d.get("role", "exit" if "EXIT" in acc else "member"),
                "risk_score": float(acc_d.get("risk_score", 0.0)),
                "risk_band": acc_d.get("risk_band", "safe"),
            }

        return node_list, A, entry_account, metadata

    def simulate(
        self,
        nodes: List[str],
        A: np.ndarray,
        entry_account: str,
        steps: Optional[int] = None,
        time_step: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Runs both Continuous-Time Quantum Walk and Classical Laplacian Diffusion.
        Invariant:
            Quantum sum(p_i(t)) == 1.0 (+-1e-9)
            Classical sum(p_i(t)) == 1.0 (+-1e-9)
        """
        n = len(nodes)
        if n == 0:
            return {"error": "Empty node graph."}

        num_steps = steps or self.default_steps
        dt = time_step or self.time_scale
        entry_idx = nodes.index(entry_account) if entry_account in nodes else 0

        # --- 1. Continuous-Time Quantum Walk ---
        # Hamiltonian H = A (symmetric weighted adjacency matrix)
        # Spectral decomposition: H = V * Lambda * V.T
        eigvals_H, V_H = np.linalg.eigh(A)

        # Initial amplitude vector psi_0: amplitude 1 on the theft entry account
        # psi(t) = V * exp(-i * Lambda * t) * (V.T * psi_0)
        # Note: V.T * psi_0 is simply the entry_idx column of V.T, which is V[entry_idx, :]
        v_entry_H = V_H[entry_idx, :]  # shape: (n,)

        # --- 2. Classical Laplacian Diffusion ---
        # Graph Laplacian L = D - A
        degrees = np.sum(A, axis=1)
        L = np.diag(degrees) - A
        eigvals_L, V_L = np.linalg.eigh(L)
        # Numerical guard: clip any negative eigenvalues arising from numerical roundoff
        eigvals_L = np.maximum(eigvals_L, 0.0)
        v_entry_L = V_L[entry_idx, :]

        # Storage for probability time series
        times = [round(float(k * dt), 3) for k in range(num_steps)]
        quantum_probs = np.zeros((num_steps, n), dtype=np.float64)
        classical_probs = np.zeros((num_steps, n), dtype=np.float64)

        for k, t in enumerate(times):
            # Quantum: psi(t) = sum_j V[:, j] * exp(-i * lambda_j * t) * v_entry[j]
            phase = np.exp(-1j * eigvals_H * t)  # (n,)
            psi_t = V_H @ (phase * v_entry_H)     # (n,) complex
            p_q = np.abs(psi_t) ** 2
            # Re-normalize strictly within float tolerance
            q_sum = float(np.sum(p_q))
            if q_sum > 0:
                p_q = p_q / q_sum
            quantum_probs[k, :] = p_q

            # Classical: p(t) = exp(-L * t) * p0 = V_L @ (exp(-Lambda_L * t) * v_entry_L)
            decay = np.exp(-eigvals_L * t)
            p_c = V_L @ (decay * v_entry_L)
            p_c = np.maximum(p_c, 0.0)
            c_sum = float(np.sum(p_c))
            if c_sum > 0:
                p_c = p_c / c_sum
            classical_probs[k, :] = p_c

        # Time-integrated walk probability per account (flow_i)
        flow_quantum = np.mean(quantum_probs, axis=0)
        flow_classical = np.mean(classical_probs, axis=0)

        # Time to 90% probability mass dispersed away from the entry account
        t_90_quantum = None
        t_90_classical = None
        for k, t in enumerate(times):
            non_entry_mass_q = float(np.sum(quantum_probs[k, :])) - float(quantum_probs[k, entry_idx])
            non_entry_mass_c = float(np.sum(classical_probs[k, :])) - float(classical_probs[k, entry_idx])
            if t_90_quantum is None and non_entry_mass_q >= 0.90:
                t_90_quantum = t
            if t_90_classical is None and non_entry_mass_c >= 0.90:
                t_90_classical = t

        return {
            "nodes": nodes,
            "entry_account": entry_account,
            "entry_index": entry_idx,
            "times": times,
            "quantum_probs": quantum_probs,
            "classical_probs": classical_probs,
            "flow_quantum": flow_quantum,
            "flow_classical": flow_classical,
            "t_90_quantum": t_90_quantum,
            "t_90_classical": t_90_classical,
        }

    def evaluate_exit_predictions(
        self,
        sim_result: Dict[str, Any],
        seed_txn_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes top-5 exit predictions for both quantum and classical walks,
        and computes the overlap score against real exit accounts discovered by taint tracing.
        """
        nodes = sim_result["nodes"]
        entry_idx = sim_result["entry_index"]
        entry_acc = sim_result["entry_account"]
        q_probs = sim_result["quantum_probs"]
        c_probs = sim_result["classical_probs"]

        # Final time-step probability (or time-integrated flow)
        final_q = q_probs[-1, :]
        final_c = c_probs[-1, :]

        # Exclude the entry account from exit predictions
        candidate_indices = [i for i in range(len(nodes)) if i != entry_idx]
        if not candidate_indices:
            candidate_indices = list(range(len(nodes)))

        # Top 5 exit predictions per method
        top_k = min(self.top_k_exits, len(candidate_indices))
        sorted_q_idx = sorted(candidate_indices, key=lambda i: final_q[i], reverse=True)[:top_k]
        sorted_c_idx = sorted(candidate_indices, key=lambda i: final_c[i], reverse=True)[:top_k]

        q_pred = [nodes[i] for i in sorted_q_idx]
        c_pred = [nodes[i] for i in sorted_c_idx]

        # Determine real exit accounts using taint tracking
        real_exits: Set[str] = set()
        
        # 1. Check for real exit accounts via taint tracking if seed transaction exists
        if seed_txn_id:
            tracker = TaintTracker(self.fg)
            taint_res = tracker.trace_taint(seed_txn_id)
            for transfer in taint_res.get("tainted_transfers", []):
                if transfer.get("is_exit_transfer"):
                    real_exits.add(transfer["dest"])
        else:
            # Look for outbound transactions from entry_account
            out_txs = self.fg.out_txns.get(entry_acc, [])
            if out_txs:
                tracker = TaintTracker(self.fg)
                taint_res = tracker.trace_taint(out_txs[0]["txn_id"])
                for transfer in taint_res.get("tainted_transfers", []):
                    if transfer.get("is_exit_transfer"):
                        real_exits.add(transfer["dest"])

        # 2. Also check node attributes for terminal/exit markers
        for acc in nodes:
            acc_d = self.fg.account_lookup.get(acc, {})
            if "EXIT" in acc or "CRYPTO" in acc or "ATM" in acc or acc_d.get("role") == "exit":
                real_exits.add(acc)

        # Invariant: If real exits exist in the graph, compute overlap against real exits
        k_eval = max(1, len(real_exits))
        top_k_q = sorted(candidate_indices, key=lambda i: final_q[i], reverse=True)[:k_eval]
        top_k_c = sorted(candidate_indices, key=lambda i: final_c[i], reverse=True)[:k_eval]

        set_k_q = {nodes[i] for i in top_k_q}
        set_k_c = {nodes[i] for i in top_k_c}

        if real_exits:
            overlap_q = len(set_k_q.intersection(real_exits)) / float(len(real_exits))
            overlap_c = len(set_k_c.intersection(real_exits)) / float(len(real_exits))
        else:
            overlap_q = 0.0
            overlap_c = 0.0

        return {
            "top_predictions_quantum": q_pred,
            "top_predictions_classical": c_pred,
            "real_exit_accounts": sorted(list(real_exits)),
            "overlap_score_quantum": round(float(overlap_q), 3),
            "overlap_score_classical": round(float(overlap_c), 3),
            "k_evaluated": k_eval,
        }


def simulate_quantum_and_classical_walk(
    fg: FinancialGraph,
    ring_data: Dict[str, Any],
    steps: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience orchestrator for quantum & classical walk simulation on a ring.
    Returns complete UI payload for Screen Step 1.
    """
    sim = QuantumWalkSimulator(fg)
    nodes, A, entry_acc, metadata = sim.extract_ring_subgraph(ring_data)
    sim_res = sim.simulate(nodes, A, entry_acc, steps=steps)
    eval_res = sim.evaluate_exit_predictions(sim_res)

    # Format arrays for JSON transmission
    times = sim_res["times"]
    q_probs_by_acc: Dict[str, List[float]] = {}
    c_probs_by_acc: Dict[str, List[float]] = {}

    for i, acc in enumerate(nodes):
        q_probs_by_acc[acc] = [round(float(p), 5) for p in sim_res["quantum_probs"][:, i]]
        c_probs_by_acc[acc] = [round(float(p), 5) for p in sim_res["classical_probs"][:, i]]

    return {
        "ring_id": ring_data.get("ring_id", ""),
        "ring_name": ring_data.get("ring_name", ""),
        "entry_account": entry_acc,
        "nodes": nodes,
        "metadata": metadata,
        "time_steps": times,
        "quantum_probabilities": q_probs_by_acc,
        "classical_probabilities": c_probs_by_acc,
        "flow_quantum": {acc: round(float(sim_res["flow_quantum"][i]), 5) for i, acc in enumerate(nodes)},
        "flow_classical": {acc: round(float(sim_res["flow_classical"][i]), 5) for i, acc in enumerate(nodes)},
        "t_90_quantum": sim_res["t_90_quantum"],
        "t_90_classical": sim_res["t_90_classical"],
        "top_predictions_quantum": eval_res["top_predictions_quantum"],
        "top_predictions_classical": eval_res["top_predictions_classical"],
        "real_exit_accounts": eval_res["real_exit_accounts"],
        "overlap_score_quantum": eval_res["overlap_score_quantum"],
        "overlap_score_classical": eval_res["overlap_score_classical"],
        "disclaimer": "Simulated on a classical computer. Synthetic demonstration data. Not a real case.",
    }
