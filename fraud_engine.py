"""
MuleTrace Core Fraud Orchestration Engine
Integrates graph ingestion, multi-pattern detectors, behavioral signals,
composite risk scoring, explainable reasons, ring autopsy, and active learning.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml
import numpy as np
import pandas as pd

from backend.graph import FinancialGraph
from backend.ingest import (
    load_accounts,
    load_transactions,
    compute_account_summaries
)
from backend.detectors.fan_in_out import FanInOutDetector
from backend.detectors.passthrough import PassthroughDetector
from backend.detectors.cycles import CycleDetector
from backend.detectors.sybil import SybilDetector
from backend.signals import compute_account_signals
from backend.scoring import RiskScorer
from backend.reasons import build_explanation_dossier
from backend.ringdna import RingDNAEngine
from backend.taint import TaintTracker
from backend.chase import build_chase_list, simulate_freeze, predict_next_hop
from backend.learning import AnalystFeedbackLearner, DayZeroEarlyWarning


class FraudEngine:
    """End-to-end detection, scoring, autopsy, and forensics engine."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        preset: str = "balanced"
    ):
        self.preset_name = preset
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config", "thresholds.yaml"
        )
        self.raw_config = self._load_raw_config()
        self.preset_thresholds = self._resolve_preset_thresholds(preset)
        self.scorer = RiskScorer(self.raw_config.get("scoring", {}))
        self.ring_engine = RingDNAEngine()
        self.feedback_learner = AnalystFeedbackLearner()

        # Engine State
        self.graph: Optional[FinancialGraph] = None
        self.df_accounts: Optional[pd.DataFrame] = None
        self.df_transactions: Optional[pd.DataFrame] = None
        self.df_ground_truth: Optional[pd.DataFrame] = None

        # Analysis Artifacts
        self.raw_hits: Dict[str, List[Dict[str, Any]]] = {}
        self.signals_by_account: Dict[str, Dict[str, Any]] = {}
        self.scores_by_account: Dict[str, Dict[str, Any]] = {}
        self.explanations_by_account: Dict[str, Dict[str, Any]] = {}
        self.counterfactuals_by_account: Dict[str, Dict[str, Any]] = {}
        self.rings: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.early_warnings: List[Dict[str, Any]] = []
        self.taint_tracker: Optional[TaintTracker] = None
        self.chase_list: List[Dict[str, Any]] = []

    def _load_raw_config(self) -> Dict[str, Any]:
        """Loads thresholds.yaml from disk."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _resolve_preset_thresholds(self, preset_name: str) -> Dict[str, Any]:
        """Extracts configuration dictionary for the specified preset."""
        presets = self.raw_config.get("presets", {})
        if preset_name in presets:
            return presets[preset_name]
        return presets.get("balanced", {})

    def set_preset(self, preset_name: str):
        """Updates the active threshold preset and re-runs detection if data loaded."""
        self.preset_name = preset_name
        self.preset_thresholds = self._resolve_preset_thresholds(preset_name)
        if self.df_accounts is not None and self.df_transactions is not None:
            self.analyze(
                self.df_accounts,
                self.df_transactions,
                self.df_ground_truth
            )

    def analyze(
        self,
        df_accounts: pd.DataFrame,
        df_transactions: pd.DataFrame,
        df_ground_truth: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Executes complete detection, scoring, explanation, and autopsy workflow.
        Strict ground truth isolation: df_ground_truth is only stored for offline
        evaluation and is NEVER passed to graph, detectors, or scoring.
        """
        self.df_accounts = df_accounts.copy()
        self.df_transactions = df_transactions.copy()
        self.df_ground_truth = df_ground_truth.copy() if df_ground_truth is not None else None

        # 1. Ingest and Construct Financial Graph
        df_acc_loaded = load_accounts(self.df_accounts)
        df_txn_loaded = load_transactions(self.df_transactions)
        df_acc_summarized = compute_account_summaries(df_acc_loaded, df_txn_loaded)
        self.graph = FinancialGraph(df_acc_summarized, df_txn_loaded)

        # 2. Run All 4 Detectors
        fio_thresh = self.preset_thresholds.get("fan_in_out", {})
        pass_thresh = self.preset_thresholds.get("passthrough", {})
        cyc_thresh = self.preset_thresholds.get("cycles", {})
        syb_thresh = self.preset_thresholds.get("sybil", {})

        fio_hits = FanInOutDetector(fio_thresh).detect(self.graph)
        pass_hits = PassthroughDetector(pass_thresh).detect(self.graph)
        cyc_hits = CycleDetector(cyc_thresh).detect(self.graph)
        syb_hits = SybilDetector(syb_thresh).detect(self.graph)

        # 3. Aggregate hits by account
        raw_hits: Dict[str, List[Dict[str, Any]]] = {
            acc_id: [] for acc_id in self.graph.account_lookup
        }
        for hit_list in [fio_hits, pass_hits, cyc_hits, syb_hits]:
            for h in hit_list:
                acc = str(h.get("account", h.get("account_id")))
                if acc in raw_hits:
                    raw_hits[acc].append(h)
        self.raw_hits = raw_hits

        # 4. Extract Behavioral Signals
        self.signals_by_account = {
            acc_id: compute_account_signals(self.graph, acc_id)
            for acc_id in self.graph.account_lookup
        }

        # 5. Composite Risk Scoring & Confidence
        self.scores_by_account = {}
        for acc_id, node_data in self.graph.account_lookup.items():
            sigs = self.signals_by_account.get(acc_id, {})
            hits = self.raw_hits.get(acc_id, [])
            role_hint = node_data.get("role")
            
            score_dict = self.scorer.score_account(
                signals=sigs,
                hits=hits,
                role_override=role_hint
            )
            self.scores_by_account[acc_id] = score_dict

            # Update FinancialGraph node attributes
            if acc_id in self.graph.graph.nodes:
                self.graph.graph.nodes[acc_id]["risk_score"] = score_dict["risk_score"]
                self.graph.graph.nodes[acc_id]["risk_band"] = score_dict["risk_band"]
                self.graph.graph.nodes[acc_id]["role"] = score_dict["role"]
                self.graph.graph.nodes[acc_id]["flagged"] = score_dict["risk_score"] >= 40.0

        # 6. Explanations & Counterfactuals
        self.explanations_by_account = {}
        self.counterfactuals_by_account = {}
        for acc_id, score_dict in list(self.scores_by_account.items()):
            node_d = self.graph.account_lookup.get(acc_id, {})
            sigs = self.signals_by_account.get(acc_id, {})
            hits = self.raw_hits.get(acc_id, [])
            
            dossier = build_explanation_dossier(
                account_id=acc_id,
                signals=sigs,
                hits=hits,
                score_data=score_dict
            )
            self.explanations_by_account[acc_id] = {
                "plain_reason": dossier["plain_reason"],
                "technical_reason": dossier["technical_reason"],
                "evidence_bullets": dossier["evidence_bullets"]
            }
            self.counterfactuals_by_account[acc_id] = {
                "counterfactual": dossier["counterfactual"]
            }

        # 7. Cluster Rings & Run Autopsies
        self._build_rings(fio_hits, pass_hits, cyc_hits, syb_hits)

        # 8. Run Day-Zero Early Warning Scanner
        early_scanner = DayZeroEarlyWarning(
            max_account_age_days=int(syb_thresh.get("max_age_days", 30)),
            min_group_size=int(syb_thresh.get("min_group", 3))
        )
        self.early_warnings = early_scanner.scan(self.graph.df_accounts)

        # 9. Initialize Taint Tracker & Chase List
        self._initialize_chase_and_taint()

        # 10. Assemble Alert Queue
        self._build_alerts_queue()

        return self.get_summary()

    def _build_rings(
        self,
        fio_hits: List[Dict[str, Any]],
        pass_hits: List[Dict[str, Any]],
        cyc_hits: List[Dict[str, Any]],
        syb_hits: List[Dict[str, Any]]
    ):
        """Discovers and structures financial fraud rings from detector outputs."""
        self.rings = {}
        ring_counter = 1

        # A. Fan-in / Fan-out hubs
        seen_fio: Set[str] = set()
        for h in fio_hits:
            r_key = h.get("ring_key", h.get("account"))
            if r_key in seen_fio:
                continue
            seen_fio.add(r_key)

            hub_id = str(h.get("account", h.get("account_id")))
            ev = h.get("evidence", {})
            senders = [str(s) for s in ev.get("senders", [])]
            receivers = [str(r) for r in ev.get("receivers", [])]
            members = list(set([hub_id] + senders + receivers))
            ring_id = f"RING-FIO-{ring_counter}"
            ring_counter += 1

            self.rings[ring_id] = {
                "ring_id": ring_id,
                "ring_name": f"Rapid Aggregation Hub ({hub_id})",
                "ring_type": "Fan-In/Fan-Out Aggregator",
                "primary_detector": "fan_in_out",
                "hub_account": hub_id,
                "members": members,
                "senders": senders,
                "receivers": receivers,
                "total_volume": float(ev.get("total_inflow", 0.0) + ev.get("total_outflow", 0.0)),
                "hit_data": {
                    "duration_minutes": float(ev.get("window_minutes", 45)),
                    "gap_min": 5.0,
                    "forward_ratio": float(ev.get("forward_ratio", 0.85))
                },
            }

        # B. Pass-Through Layering Chains
        seen_chains: Set[str] = set()
        for h in pass_hits:
            r_key = h.get("ring_key")
            if r_key in seen_chains:
                continue
            seen_chains.add(r_key)

            ev = h.get("evidence", {})
            chain = [str(x) for x in ev.get("chain_path", [])]
            if len(chain) < 3:
                continue

            ring_id = f"RING-LAY-{ring_counter}"
            ring_counter += 1
            gap = float(ev.get("hop_gap_minutes", 2.0))
            self.rings[ring_id] = {
                "ring_id": ring_id,
                "ring_name": f"Layering Relay Chain ({len(chain)} hops)",
                "ring_type": "Pass-Through Layering Chain",
                "primary_detector": "passthrough",
                "hub_account": chain[0],
                "members": chain,
                "chain": chain,
                "total_volume": float(ev.get("in_amount", 0.0)),
                "hit_data": {
                    "duration_minutes": gap * len(chain),
                    "gap_min": gap,
                    "forward_ratio": float(ev.get("forward_ratio", 0.95))
                },
            }

        # C. Circular Transfer Rings
        seen_cycles: Set[str] = set()
        for h in cyc_hits:
            r_key = h.get("ring_key")
            if r_key in seen_cycles:
                continue
            seen_cycles.add(r_key)

            ev = h.get("evidence", {})
            cycle = [str(x) for x in ev.get("accounts_in_cycle", ev.get("cycle_path", []))]
            if len(cycle) < 3:
                continue

            ring_id = f"RING-CYC-{ring_counter}"
            ring_counter += 1
            dur = float(ev.get("cycle_duration_minutes", 30.0))
            self.rings[ring_id] = {
                "ring_id": ring_id,
                "ring_name": f"Circular Wash Cycle ({len(cycle)} accounts)",
                "ring_type": "Circular Transfer Ring",
                "primary_detector": "cycles",
                "hub_account": cycle[0],
                "members": cycle,
                "cycle": cycle,
                "total_volume": float(ev.get("initial_amount", 0.0)),
                "hit_data": {
                    "duration_minutes": dur,
                    "gap_min": max(1.0, dur / len(cycle)),
                    "forward_ratio": 0.95
                },
            }

        # D. Sybil Identity Clusters
        seen_sybils: Set[str] = set()
        for h in syb_hits:
            r_key = h.get("ring_key")
            if r_key in seen_sybils:
                continue
            seen_sybils.add(r_key)

            ev = h.get("evidence", {})
            cluster = [str(x) for x in ev.get("cluster_accounts", [])]
            if len(cluster) < 2:
                continue
            ring_id = f"RING-SYB-{ring_counter}"
            ring_counter += 1
            tot_vol = sum(
                self.graph.account_lookup.get(acc, {}).get("total_inflow", 0.0)
                for acc in cluster
            )
            self.rings[ring_id] = {
                "ring_id": ring_id,
                "ring_name": f"Synthetic Sybil Cluster ({ev.get('shared_device', 'Device')})",
                "ring_type": "Sybil Identity Cluster",
                "primary_detector": "sybil",
                "hub_account": cluster[0],
                "members": cluster,
                "total_volume": float(tot_vol),
                "hit_data": {
                    "duration_minutes": 10.0,
                    "gap_min": 1.0,
                    "forward_ratio": 0.50
                },
            }

        # Run Ring DNA autopsy on each discovered ring
        for r_id, r_data in self.rings.items():
            primary_det = r_data.get("primary_detector", "passthrough")
            typ_map = {
                "fan_in_out": "fan_in_out",
                "passthrough": "passthrough",
                "cycles": "cycle",
                "sybil": "sybil",
            }
            mapped_type = typ_map.get(primary_det, "passthrough")
            hit_d = r_data.get("hit_data", {})
            dur = float(hit_d.get("window_min", hit_d.get("duration_minutes", 15.0)))
            gap = float(hit_d.get("gap_min", 2.0))
            fwd = float(hit_d.get("forward_ratio", 0.95))

            autopsy = self.ring_engine.generate_autopsy(
                ring_id=r_id,
                ring_type=mapped_type,
                total_amount=r_data.get("total_volume", 100000.0),
                duration_minutes=dur,
                accounts_involved=r_data["members"],
                avg_hop_gap_minutes=gap,
                forward_ratio=fwd
            )
            r_data["dna_vector"] = autopsy["dna_vector"]
            top_m = autopsy.get("top_match") or {}
            r_data["typology_match"] = top_m.get("typology_id", "TYP_UNKNOWN")
            r_data["typology_name"] = top_m.get("name", "Unknown Typology")
            r_data["similarity_score"] = top_m.get("similarity_score", 0.0)
            r_data["similarity_pct"] = top_m.get("similarity_pct", "0%")
            r_data["narrative"] = [
                autopsy["autopsy_narrative"]["line_1_overview"],
                autopsy["autopsy_narrative"]["line_2_modus_operandi"],
                autopsy["autopsy_narrative"]["line_3_interception"]
            ]
            r_data["recommendation"] = top_m.get("recommended_action", "Flag accounts for immediate review.")

    def _initialize_chase_and_taint(self):
        """Initializes TaintTracker and computes Chase List."""
        if not self.graph or (self.df_transactions is not None and self.df_transactions.empty):
            self.chase_list = []
            return

        self.taint_tracker = TaintTracker(self.graph)
        
        # Look for victim or top suspicious seed transaction
        seed_txn_id = None
        for victim_acc in ["ACC_VICTIM_CHAIN01", "ACC_VICTIM_01", "ACC_VICTIM_FAN01"]:
            out_txns = self.graph.out_txns.get(victim_acc, [])
            if out_txns:
                seed_txn_id = out_txns[0]["txn_id"]
                break

        if not seed_txn_id:
            for acc_id, d in self.scores_by_account.items():
                if d.get("role") in ["hub", "relay"] and d.get("risk_score", 0.0) >= 60.0:
                    in_txns = self.graph.in_txns.get(acc_id, [])
                    if in_txns:
                        seed_txn_id = in_txns[0]["txn_id"]
                        break

        if not seed_txn_id:
            for u, v, k, data in self.graph.graph.edges(keys=True, data=True):
                seed_txn_id = data["txn_id"]
                break

        if seed_txn_id:
            taint_res = self.taint_tracker.trace_taint(seed_txn_id)
            if "replay_frames" in taint_res:
                mid_frame = min(3, max(0, len(taint_res["replay_frames"]) - 1))
                chase_data = build_chase_list(taint_res, self.graph, at_frame_index=mid_frame)
                self.chase_list = chase_data.get("ranked_accounts", [])
            else:
                self.chase_list = []
        else:
            self.chase_list = []

    def _build_alerts_queue(self):
        """Constructs priority sorted list of actionable alerts."""
        self.alerts = []
        for acc_id, score_dict in self.scores_by_account.items():
            if score_dict["risk_score"] < 40.0 and score_dict["risk_band"] not in ["critical", "medium"]:
                continue

            node_d = self.graph.account_lookup.get(acc_id, {})
            explanations = self.explanations_by_account.get(acc_id, {})
            counterfactual = self.counterfactuals_by_account.get(acc_id, {})
            hits = self.raw_hits.get(acc_id, [])

            # Active feedback adjustment if trained
            status = self.feedback_learner.verdicts.get(acc_id, "pending")

            self.alerts.append({
                "account_id": acc_id,
                "display_name": node_d.get("display_name", acc_id),
                "account_type": node_d.get("account_type", "SAVINGS"),
                "risk_score": score_dict["risk_score"],
                "risk_band": score_dict["risk_band"],
                "role": score_dict["role"],
                "confidence": score_dict["confidence"],
                "breakdown": score_dict["breakdown"],
                "primary_reason": explanations.get("plain_reason", "Unusual activity pattern detected."),
                "technical_reason": explanations.get("technical_reason", ""),
                "counterfactual": counterfactual.get("counterfactual", ""),
                "total_inflow": node_d.get("total_inflow", 0.0),
                "total_outflow": node_d.get("total_outflow", 0.0),
                "turnover_ratio": node_d.get("turnover_ratio", 0.0),
                "hit_count": len(hits),
                "hits": hits,
                "verdict": status,
            })

        # Priority sort: Critical risk descending, then hit count descending
        self.alerts.sort(key=lambda a: (a["risk_score"], a["hit_count"]), reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        """Provides dashboard KPI statistics."""
        if not self.graph:
            return {
                "total_accounts": 0,
                "total_transactions": 0,
                "flagged_accounts": 0,
                "critical_accounts": 0,
                "rings_detected": 0,
                "estimated_amount_at_risk": 0.0,
                "estimated_amount_at_risk_formatted": "₹0",
                "estimated_amount_saved": 0.0,
                "estimated_amount_saved_formatted": "Estimated amount saved: ₹0",
                "preset": self.preset_name,
                "early_warnings_count": 0,
            }

        total_accounts = len(self.graph.account_lookup)
        total_transactions = len(self.df_transactions) if self.df_transactions is not None else 0
        flagged_count = sum(1 for s in self.scores_by_account.values() if s["risk_score"] >= 40.0)
        critical_count = sum(1 for s in self.scores_by_account.values() if s["risk_score"] >= 70.0)
        rings_count = len(self.rings)

        # Money at risk: sum of total_inflow for accounts in flagged status
        amount_at_risk = sum(
            self.graph.account_lookup.get(acc, {}).get("total_inflow", 0.0)
            for acc, s in self.scores_by_account.items()
            if s["risk_score"] >= 40.0
        )

        # Estimated saved: ~65% recovery if frozen rapidly
        amount_saved = amount_at_risk * 0.65

        def fmt_inr(v: float) -> str:
            if v >= 10_000_000:
                return f"₹{v / 10_000_000:.2f} Cr"
            elif v >= 100_000:
                return f"₹{v / 100_000:.2f} Lakh"
            return f"₹{v:,.0f}"

        return {
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "flagged_accounts": flagged_count,
            "critical_accounts": critical_count,
            "rings_detected": rings_count,
            "estimated_amount_at_risk": round(amount_at_risk, 2),
            "estimated_amount_at_risk_formatted": fmt_inr(amount_at_risk),
            "estimated_amount_saved": round(amount_saved, 2),
            "estimated_amount_saved_formatted": f"Estimated amount saved: {fmt_inr(amount_saved)}",
            "preset": self.preset_name,
            "early_warnings_count": len(self.early_warnings),
        }

    def compute_evaluation_metrics(self) -> Dict[str, Any]:
        """
        Computes benchmark metrics against isolated ground_truth.csv.
        Strict isolation: ground truth is NEVER accessed by detection or scoring pipelines.
        """
        if self.df_ground_truth is None or self.df_ground_truth.empty:
            return {
                "available": False,
                "message": "Ground truth dataset is not loaded in this session.",
                "isolation_disclaimer": "Ground truth isolation rule enforced: Ground truth is used strictly for offline post-detection evaluation and never accessed by detectors."
            }

        gt_map = dict(zip(
            self.df_ground_truth["account_id"].astype(str),
            self.df_ground_truth["label"].astype(str)
        ))

        tp = 0
        fp = 0
        tn = 0
        fn = 0
        hard_neg_fps: Dict[str, int] = {}
        hard_neg_totals: Dict[str, int] = {}

        for acc_id, gt_label in gt_map.items():
            is_positive_gt = gt_label in ["mule", "exit"]
            score_dict = self.scores_by_account.get(acc_id, {"risk_score": 0.0})
            is_positive_pred = score_dict["risk_score"] >= 40.0

            if is_positive_gt and is_positive_pred:
                tp += 1
            elif not is_positive_gt and is_positive_pred:
                fp += 1
            elif not is_positive_gt and not is_positive_pred:
                tn += 1
            elif is_positive_gt and not is_positive_pred:
                fn += 1

            if gt_label == "hard_negative":
                ring_type = self.df_ground_truth.loc[
                    self.df_ground_truth["account_id"].astype(str) == acc_id,
                    "ring_type"
                ].values
                type_name = str(ring_type[0]) if len(ring_type) > 0 else "other"
                hard_neg_totals[type_name] = hard_neg_totals.get(type_name, 0) + 1
                if is_positive_pred:
                    hard_neg_fps[type_name] = hard_neg_fps.get(type_name, 0) + 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        hard_neg_breakdown = {
            k: {
                "total": hard_neg_totals[k],
                "false_positives": hard_neg_fps.get(k, 0),
                "fp_rate": round(hard_neg_fps.get(k, 0) / hard_neg_totals[k], 4)
            }
            for k in hard_neg_totals
        }

        return {
            "available": True,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": {
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn
            },
            "hard_negative_breakdown": hard_neg_breakdown,
            "isolation_disclaimer": "Ground truth isolation rule enforced: Ground truth is used strictly for offline post-detection evaluation and never accessed by detectors."
        }
