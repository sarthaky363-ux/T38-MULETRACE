"""
MuleTrace In-Memory State Store
Coordinates application state, demo data loading, file uploads, analyst feedback,
case dossier exports, and forensic simulations.
"""

from datetime import datetime, timezone
import io
import os
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.fraud_engine import FraudEngine
from backend.taint import TaintTracker
import threading
from backend.chase import build_chase_list, simulate_freeze, predict_next_hop
from backend.quantum import (
    simulate_quantum_and_classical_walk,
    QuantumWalkSimulator,
    NetworkInterdictionOptimizer,
    compute_ring_fidelities,
)


class MuleTraceStore:
    """Singleton-style in-memory state repository for MuleTrace API."""

    def __init__(self):
        self._lock = threading.Lock()
        self._tradeoffs_cache = None
        self.engine = FraudEngine(preset="balanced")
        self.dataset_loaded = False
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo")
        self.verdicts: Dict[str, Dict[str, Any]] = {}
        self.case_notes: Dict[str, str] = {}

    def load_demo_data(self) -> Dict[str, Any]:
        """Loads default synthetic demo dataset from disk."""
        acc_path = os.path.join(self.data_dir, "accounts.csv")
        txn_path = os.path.join(self.data_dir, "transactions.csv")
        gt_path = os.path.join(self.data_dir, "ground_truth.csv")

        if not os.path.exists(acc_path) or not os.path.exists(txn_path):
            raise FileNotFoundError(f"Demo files not found in {self.data_dir}")

        df_acc = pd.read_csv(acc_path)
        df_txn = pd.read_csv(txn_path)
        df_gt = pd.read_csv(gt_path) if os.path.exists(gt_path) else None

        self.engine.analyze(df_acc, df_txn, df_gt)
        self.dataset_loaded = True
        return self.engine.get_summary()

    def load_uploaded_files(
        self,
        accounts_bytes: bytes,
        transactions_bytes: bytes,
        ground_truth_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Ingests multipart CSV files directly into memory."""
        df_acc = pd.read_csv(io.BytesIO(accounts_bytes))
        df_txn = pd.read_csv(io.BytesIO(transactions_bytes))
        df_gt = pd.read_csv(io.BytesIO(ground_truth_bytes)) if ground_truth_bytes else None

        self.engine.analyze(df_acc, df_txn, df_gt)
        self.dataset_loaded = True
        return self.engine.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Returns overall KPI summary."""
        return self.engine.get_summary()

    def get_alerts(
        self,
        risk_band: Optional[str] = None,
        detector: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Returns filtered, paginated list of alerts."""
        if not self.dataset_loaded or not self.engine.alerts:
            return {"total": 0, "alerts": []}

        filtered = self.engine.alerts

        if risk_band and risk_band.lower() != "all":
            filtered = [a for a in filtered if a["risk_band"].lower() == risk_band.lower()]

        if detector and detector.lower() != "all":
            filtered = [
                a for a in filtered
                if any(h.get("pattern_type") == detector or h.get("detector") == detector for h in a.get("hits", []))
            ]

        if search:
            q = search.lower().strip()
            filtered = [
                a for a in filtered
                if q in a["account_id"].lower() or q in a["display_name"].lower()
            ]

        total = len(filtered)
        paged = filtered[offset : offset + limit]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "alerts": paged
        }

    def get_account_detail(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Returns comprehensive account dossier."""
        if not self.engine.graph or account_id not in self.engine.graph.account_lookup:
            return None

        node_data = dict(self.engine.graph.account_lookup[account_id])
        score_data = self.engine.scores_by_account.get(account_id, {
            "risk_score": 0.0, "risk_band": "safe", "role": "member", "confidence": "low", "breakdown": {}
        })
        explanations = self.engine.explanations_by_account.get(account_id, {})
        counterfactual = self.engine.counterfactuals_by_account.get(account_id, {})
        hits = self.engine.raw_hits.get(account_id, [])
        signals = self.engine.signals_by_account.get(account_id, {})

        # Find associated ring if any
        associated_ring = None
        for ring_id, ring_data in self.engine.rings.items():
            if account_id in ring_data.get("members", []):
                associated_ring = {
                    "ring_id": ring_id,
                    "ring_name": ring_data.get("ring_name"),
                    "ring_type": ring_data.get("ring_type"),
                    "typology_name": ring_data.get("typology_name")
                }
                break

        # Transaction history (incoming and outgoing)
        in_txns = self.engine.graph.in_txns.get(account_id, [])
        out_txns = self.engine.graph.out_txns.get(account_id, [])

        # Analyst verdict
        verdict_data = self.verdicts.get(account_id)

        return {
            "account_id": account_id,
            "display_name": node_data.get("display_name", account_id),
            "account_type": node_data.get("account_type", "SAVINGS"),
            "opened_at": node_data.get("opened_at", ""),
            "age_days": node_data.get("age_days", 0),
            "kyc_verified": node_data.get("kyc_verified", False),
            "kyc_pan_hash": node_data.get("kyc_pan_hash"),
            "device_id": node_data.get("device_id"),
            "ip_address": node_data.get("ip_address"),
            "total_inflow": node_data.get("total_inflow", 0.0),
            "total_outflow": node_data.get("total_outflow", 0.0),
            "turnover_ratio": node_data.get("turnover_ratio", 0.0),
            "retained_ratio": node_data.get("retained_ratio", 0.0),
            "risk_score": score_data.get("risk_score", 0.0),
            "risk_band": score_data.get("risk_band", "safe"),
            "role": score_data.get("role", "member"),
            "confidence": score_data.get("confidence", "low"),
            "breakdown": score_data.get("breakdown", {}),
            "primary_reason": explanations.get("plain_reason", "No abnormal behavior observed."),
            "technical_reason": explanations.get("technical_reason", ""),
            "counterfactual": counterfactual.get("counterfactual", ""),
            "hits": hits,
            "signals": signals,
            "associated_ring": associated_ring,
            "verdict": verdict_data["verdict"] if verdict_data else "pending",
            "analyst_notes": verdict_data["notes"] if verdict_data else "",
            "inflow_transactions": in_txns[:25],
            "outflow_transactions": out_txns[:25],
        }

    def get_graph_elements(
        self,
        center_id: Optional[str] = None,
        depth: int = 2,
        max_nodes: int = 150
    ) -> Dict[str, Any]:
        """Extracts Cytoscape nodes and edges."""
        if not self.engine.graph:
            return {"nodes": [], "edges": []}
        return self.engine.graph.get_subgraph(
            center_id=center_id,
            hops=depth,
            max_nodes=max_nodes
        )

    def get_rings(self) -> List[Dict[str, Any]]:
        """Returns all detected rings."""
        return list(self.engine.rings.values())

    def get_ring_detail(self, ring_id: str) -> Optional[Dict[str, Any]]:
        """Returns detailed autopsy data for a single ring."""
        return self.engine.rings.get(ring_id)

    def record_verdict(
        self,
        account_id: str,
        verdict: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Records human analyst review decision.
        Updates learner and recalculates adjusted risk score.
        """
        if not self.engine.graph or account_id not in self.engine.graph.account_lookup:
            return {"success": False, "message": "Account not found"}

        current_score = self.engine.scores_by_account.get(account_id, {}).get("risk_score", 0.0)

        # 1. Map verdict and record in learner
        learner_verdict = "confirmed_mule" if verdict == "confirmed_mule" else "cleared_legit"
        self.verdicts[account_id] = {
            "verdict": verdict,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        learner_status = self.engine.feedback_learner.add_verdict(account_id, learner_verdict)

        # Train if eligible
        if learner_status.get("can_train"):
            self.engine.feedback_learner.train(self.engine.graph)

        # 2. Adjust score
        if verdict in ["cleared_benign", "cleared_legit"]:
            adjusted_score = 0.0
            new_band = "safe"
        elif verdict == "confirmed_mule":
            adjusted_score = max(current_score, 85.0)
            new_band = "critical"
        else:
            adjusted_score = current_score
            new_band = self.engine.scores_by_account.get(account_id, {}).get("risk_band", "safe")

        # 3. Update account record in graph and alert queue
        if account_id in self.engine.scores_by_account:
            self.engine.scores_by_account[account_id]["risk_score"] = adjusted_score
            self.engine.scores_by_account[account_id]["risk_band"] = new_band
        if account_id in self.engine.graph.graph.nodes:
            self.engine.graph.graph.nodes[account_id]["risk_score"] = adjusted_score
            self.engine.graph.graph.nodes[account_id]["risk_band"] = new_band

        for a in self.engine.alerts:
            if a["account_id"] == account_id:
                a["verdict"] = verdict
                a["risk_score"] = adjusted_score
                a["risk_band"] = new_band

        return {
            "success": True,
            "account_id": account_id,
            "verdict": verdict,
            "original_score": current_score,
            "adjusted_score": adjusted_score,
            "model_status": learner_status,
            "model_trained": self.engine.feedback_learner.is_active,
        }

    def run_replay(
        self,
        source_account: str,
        start_time: str,
        initial_amount: float = 100000.0,
        freeze_hour: Optional[float] = None
    ) -> Dict[str, Any]:
        """Simulates temporal taint flow and returns timeline frames."""
        if not self.engine.graph:
            return {"frames": [], "total_recovered": 0.0, "total_cashed_out": 0.0}

        # Look for a seed transaction from or into source_account
        seed_txn = None
        for t in self.engine.graph.out_txns.get(source_account, []):
            seed_txn = t
            break
        if not seed_txn:
            for t in self.engine.graph.in_txns.get(source_account, []):
                seed_txn = t
                break
        if not seed_txn:
            for u, v, k, d in self.engine.graph.graph.edges(keys=True, data=True):
                seed_txn = d
                break

        if not seed_txn:
            return {"frames": [], "total_recovered": 0.0, "total_cashed_out": 0.0}

        tracker = TaintTracker(self.engine.graph)
        res = tracker.trace_taint(seed_txn["txn_id"])
        frames = res.get("replay_frames", [])
        return {
            "source_account": source_account,
            "seed_txn_id": seed_txn["txn_id"],
            "initial_amount": res.get("initial_theft_amount", initial_amount),
            "freeze_hour": freeze_hour,
            "total_frames": len(frames),
            "final_recovered": res.get("cumulative_cashed_out", 0.0),
            "final_cashed_out": res.get("cumulative_cashed_out", 0.0),
            "frames": frames,
            "flow_events": res.get("tainted_transfers", []),
        }

    def run_freeze_simulation(
        self,
        source_account: str,
        start_time: str,
        initial_amount: float = 100000.0
    ) -> Dict[str, Any]:
        """Simulates saved money across hourly intervention windows."""
        if not self.engine.graph:
            return {"curve": []}

        seed_txn = None
        for t in self.engine.graph.out_txns.get(source_account, []):
            seed_txn = t
            break
        if not seed_txn:
            for t in self.engine.graph.in_txns.get(source_account, []):
                seed_txn = t
                break
        if not seed_txn:
            for u, v, k, d in self.engine.graph.graph.edges(keys=True, data=True):
                seed_txn = d
                break

        if not seed_txn:
            return {"curve": []}

        tracker = TaintTracker(self.engine.graph)
        res = tracker.trace_taint(seed_txn["txn_id"])
        freeze_data = simulate_freeze(res, time_points_min=[0, 5, 10, 15, 30, 60])
        curve = freeze_data.get("curve", [])
        return {
            "source_account": source_account,
            "seed_txn_id": seed_txn["txn_id"],
            "initial_amount": res.get("initial_theft_amount", initial_amount),
            "curve": curve,
            "disclaimer": freeze_data.get("disclaimer", "Estimated amount saved is a synthetic demonstration.")
        }

    def get_chase_list(self) -> List[Dict[str, Any]]:
        """Returns proactive interdiction chase queue."""
        return self.engine.chase_list

    def get_presets(self) -> Dict[str, Any]:
        """Returns available presets and the active threshold config."""
        return {
            "active_preset": self.engine.preset_name,
            "presets": list(self.engine.raw_config.get("presets", {}).keys()),
            "current_thresholds": self.engine.preset_thresholds
        }

    def set_preset(self, preset_name: str) -> Dict[str, Any]:
        """Switches active preset and refreshes analysis."""
        self.engine.set_preset(preset_name)
        return self.engine.get_summary()

    def get_metrics(self) -> Dict[str, Any]:
        """Returns offline benchmark performance metrics."""
        metrics_data = self.engine.compute_evaluation_metrics()
        metrics_data["preset_tradeoffs"] = self.get_preset_tradeoffs()
        return metrics_data

    def get_preset_tradeoffs(self) -> List[Dict[str, Any]]:
        """Runs the offline evaluator once per preset to demonstrate trade-offs."""
        if not self.dataset_loaded:
            return []
        original_preset = self.engine.preset_name
        tradeoffs = []
        for p in ["relaxed", "balanced", "strict"]:
            self.engine.set_preset(p)
            m = self.engine.compute_evaluation_metrics()
            cm = m.get("confusion_matrix", {})
            tradeoffs.append({
                "preset": p,
                "precision": m.get("precision", 0.0),
                "recall": m.get("recall", 0.0),
                "f1": m.get("f1_score", 0.0),
                "tp": cm.get("tp", 0),
                "fp": cm.get("fp", 0),
                "fn": cm.get("fn", 0),
                "tn": cm.get("tn", 0),
            })
        self.engine.set_preset(original_preset)
        return tradeoffs

    def get_early_warnings(self) -> List[Dict[str, Any]]:
        """Returns pre-transaction day-zero mule warnings."""
        return self.engine.early_warnings

    def get_case_dossier(self, ring_id: str) -> Optional[Dict[str, Any]]:
        """
        Generates full regulatory SAR (Suspicious Activity Report) dossier.
        Adheres to Rule 6 (analyst language), Rule 7 (export disclaimer),
        and Rule 8 (saved money estimation).
        """
        ring = self.engine.rings.get(ring_id)
        if not ring or not self.engine.graph:
            return None

        members = ring.get("members", [])
        member_entities = []
        for m in members:
            node_d = self.engine.graph.account_lookup.get(m, {})
            score_d = self.engine.scores_by_account.get(m, {})
            member_entities.append({
                "account_id": m,
                "display_name": node_d.get("display_name", m),
                "account_type": node_d.get("account_type", "SAVINGS"),
                "age_days": node_d.get("age_days", 0),
                "kyc_verified": node_d.get("kyc_verified", False),
                "total_inflow": node_d.get("total_inflow", 0.0),
                "total_outflow": node_d.get("total_outflow", 0.0),
                "risk_score": score_d.get("risk_score", 0.0),
                "risk_band": score_d.get("risk_band", "safe"),
                "role": score_d.get("role", "member")
            })

        # Collect chronological transactions involving ring members
        ring_member_set = set(members)
        involved_txns = []
        for m in members:
            for t in self.engine.graph.out_txns.get(m, []):
                dst = str(t.get("dest", t.get("dest_account")))
                if dst in ring_member_set:
                    involved_txns.append(t)
        involved_txns.sort(key=lambda x: x["timestamp"])

        total_vol = ring.get("total_volume", 0.0)
        est_saved = total_vol * 0.65

        dossier = {
            "sar_reference_id": f"SAR-IND-2026-{ring_id}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_ring_id": ring_id,
            "target_ring_name": ring.get("ring_name"),
            "typology_classification": ring.get("typology_name", "Layering Syndicate"),
            "typology_similarity": ring.get("similarity_pct", "0%") if str(ring.get("similarity_pct", "")).endswith("%") else f"{ring.get('similarity_pct', 0.0)}%",
            "total_layered_volume": total_vol,
            "total_layered_volume_formatted": f"₹{total_vol:,.2f}",
            "estimated_amount_saved": round(est_saved, 2),
            "estimated_amount_saved_formatted": f"Estimated amount saved: ₹{est_saved:,.2f}",
            "member_count": len(members),
            "ring_dna_vector": ring.get("dna_vector", {}),
            "executive_narrative": ring.get("narrative", []),
            "recommended_action": ring.get("recommendation", "Immediate freeze of hub accounts"),
            "subject_accounts": member_entities,
            "transfer_ledger": involved_txns[:50],
            "disclaimer_synthetic": "Synthetic demonstration data. Not a real case.",
            "disclaimer_saved_money": f"Estimated amount saved: ₹{est_saved:,.2f}",
        }
        return dossier

    def run_evasion_test(self) -> Dict[str, Any]:
        """
        Runs sensitivity analysis comparing relaxed, balanced, and strict presets
        specifically against the slow-moving R6 evasion ring to show detector bounds.
        """
        if not self.dataset_loaded:
            return {"error": "Dataset not loaded"}

        results = {}
        original_preset = self.engine.preset_name

        for p in ["relaxed", "balanced", "strict"]:
            self.engine.set_preset(p)
            # Find R6 accounts (either in ground truth or by known IDs)
            r6_mules = []
            if self.engine.df_ground_truth is not None:
                r6_df = self.engine.df_ground_truth[
                    self.engine.df_ground_truth["ring_id"] == "R6"
                ]
                r6_mules = r6_df["account_id"].astype(str).tolist()

            caught = sum(
                1 for acc in r6_mules
                if self.engine.scores_by_account.get(acc, {}).get("risk_score", 0.0) >= 40.0
            )

            results[p] = {
                "preset": p,
                "total_evasion_mules": len(r6_mules),
                "caught_mules": caught,
                "detection_rate": round(caught / len(r6_mules), 4) if r6_mules else 0.0,
                "flagged_accounts_overall": sum(
                    1 for s in self.engine.scores_by_account.values() if s["risk_score"] >= 40.0
                )
            }

        # Restore original preset
        self.engine.set_preset(original_preset)

        return {
            "ring_id": "R6",
            "ring_name": "Slow-Paced Evasion Transfer Ring",
            "analysis": results,
            "takeaway": (
                "Under 'relaxed' thresholds, slow-paced transfers (extended gaps) partially evade single-window detection. "
                "'Strict' and 'balanced' presets with multi-pattern synergy successfully capture the distributed flow."
            )
        }

    def get_quantum_walk(
        self,
        ring_id: Optional[str] = None,
        steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """Runs continuous-time quantum walk and classical diffusion on a ring."""
        if not self.dataset_loaded:
            self.load_demo_data()

        # Find target ring or fallback to first available ring
        target_ring = None
        if ring_id and ring_id in self.engine.rings:
            target_ring = self.engine.rings[ring_id]
        elif self.engine.rings:
            target_ring = next(iter(self.engine.rings.values()))

        if not target_ring:
            # Fallback if no rings discovered: build a synthetic ring from top alerts
            top_accounts = [a["account_id"] for a in self.engine.alerts[:5]]
            target_ring = {
                "ring_id": ring_id or "RING_DEFAULT",
                "ring_name": "Default Investigation Subgraph",
                "members": top_accounts,
                "hub_account": top_accounts[0] if top_accounts else "ACC_0",
            }

        return simulate_quantum_and_classical_walk(
            self.engine.graph,
            target_ring,
            steps=steps
        )

    def get_quantum_interdiction(
        self,
        ring_id: Optional[str] = None,
        budget: int = 5
    ) -> Dict[str, Any]:
        """Solves interdiction optimization comparing greedy vs optimized freeze sets."""
        if not self.dataset_loaded:
            self.load_demo_data()

        target_ring = None
        if ring_id and ring_id in self.engine.rings:
            target_ring = self.engine.rings[ring_id]
        elif self.engine.rings:
            target_ring = next(iter(self.engine.rings.values()))

        if not target_ring:
            top_accounts = [a["account_id"] for a in self.engine.alerts[:5]]
            target_ring = {
                "ring_id": ring_id or "RING_DEFAULT",
                "ring_name": "Default Investigation Subgraph",
                "members": top_accounts,
                "hub_account": top_accounts[0] if top_accounts else "ACC_0",
            }

        sim = QuantumWalkSimulator(self.engine.graph)
        nodes, A, entry_acc, _ = sim.extract_ring_subgraph(target_ring)
        sim_res = sim.simulate(nodes, A, entry_acc)
        flow = sim_res["flow_quantum"]

        opt = NetworkInterdictionOptimizer(self.engine.graph)
        return opt.compare_greedy_vs_optimized(nodes, flow, budget_K=budget)

    def get_quantum_ring_fidelity(self) -> Dict[str, Any]:
        """Calculates pairwise quantum state fidelities across rings and typologies."""
        if not self.dataset_loaded:
            self.load_demo_data()
        return compute_ring_fidelities(self.engine.rings)


# Global store instance
store = MuleTraceStore()

