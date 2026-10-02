import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend is in python path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir.parent))
sys.path.insert(0, str(backend_dir))

from ingest import load_accounts, load_transactions, compute_account_summaries
from graph import FinancialGraph
from detectors.fan_in_out import FanInOutDetector
from detectors.passthrough import PassthroughDetector
from detectors.cycles import CycleDetector
from detectors.sybil import SybilDetector
from signals import compute_account_signals
from scoring import RiskScorer
from reasons import build_explanation_dossier
from taint import TaintTracker
from chase import simulate_freeze
from ringdna import RingDNAEngine
import yaml


def run_benchmark() -> bool:
    project_root = backend_dir.parent
    data_dir = project_root / "data" / "demo"
    acc_path = data_dir / "accounts.csv"
    txn_path = data_dir / "transactions.csv"
    cfg_path = backend_dir / "config" / "thresholds.yaml"

    if not acc_path.exists() or not txn_path.exists():
        print(f"Error: Demo dataset missing in {data_dir}")
        return False

    with open(cfg_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    preset_thresholds = config.get("presets", {}).get("balanced", {})
    scoring_cfg = config.get("scoring", {})

    benchmarks = []

    print("=" * 65)
    print("        MULETRACE HIGH-PERFORMANCE BENCHMARK SUITE       ")
    print("=" * 65)

    # 1. Ingestion & Graph Construction
    t0 = time.perf_counter()
    raw_acc = load_accounts(str(acc_path))
    df_txn = load_transactions(str(txn_path))
    df_acc = compute_account_summaries(raw_acc, df_txn)
    graph = FinancialGraph(df_acc, df_txn)
    t1 = time.perf_counter()
    ingest_time_ms = (t1 - t0) * 1000
    target_ingest = 3000.0
    benchmarks.append({
        "Task": "Dataset Ingestion & MultiDiGraph Build",
        "Target": f"< {target_ingest:.0f} ms",
        "Actual": f"{ingest_time_ms:.1f} ms",
        "Passed": ingest_time_ms <= target_ingest
    })

    # 2. Complete Detection Pipeline
    t0 = time.perf_counter()
    d_fan = FanInOutDetector(preset_thresholds.get("fan_in_out", {}))
    d_pass = PassthroughDetector(preset_thresholds.get("passthrough", {}))
    d_cyc = CycleDetector(preset_thresholds.get("cycles", {}))
    d_syb = SybilDetector(preset_thresholds.get("sybil", {}))

    fan_hits = d_fan.detect(graph)
    pass_hits = d_pass.detect(graph)
    cyc_hits = d_cyc.detect(graph)
    syb_hits = d_syb.detect(graph)
    all_hits = fan_hits + pass_hits + cyc_hits + syb_hits
    t1 = time.perf_counter()
    detect_time_ms = (t1 - t0) * 1000
    target_detect = 1000.0
    benchmarks.append({
        "Task": "Multi-Pattern Detection Pipeline (4 Algorithms)",
        "Target": f"< {target_detect:.0f} ms",
        "Actual": f"{detect_time_ms:.1f} ms",
        "Passed": detect_time_ms <= target_detect
    })

    # 3. Behavioral Signals & Scoring
    t0 = time.perf_counter()
    from collections import defaultdict
    hits_by_acc = defaultdict(list)
    for h in all_hits:
        acc = h.get("account", h.get("account_id"))
        if acc:
            hits_by_acc[acc].append(h)

    signals = {acc: compute_account_signals(graph, acc) for acc in graph.account_lookup}
    scorer = RiskScorer(scoring_cfg)
    scores = {acc: scorer.score_account(signals[acc], hits_by_acc.get(acc, [])) for acc in graph.account_lookup}
    t1 = time.perf_counter()
    score_time_ms = (t1 - t0) * 1000
    target_score = 1000.0
    benchmarks.append({
        "Task": "Behavioral Signals & Explainable Scoring",
        "Target": f"< {target_score:.0f} ms",
        "Actual": f"{score_time_ms:.1f} ms",
        "Passed": score_time_ms <= target_score
    })

    # 4. Egocentric Subgraph Extraction (10 queries average)
    t0 = time.perf_counter()
    top_flagged = [acc for acc, s in scores.items() if s["risk_score"] >= 70.0][:10]
    for center in top_flagged:
        sub = graph.get_subgraph(center_id=center, hops=2, max_nodes=150)
    t1 = time.perf_counter()
    subgraph_avg_ms = ((t1 - t0) * 1000) / max(1, len(top_flagged))
    target_subgraph = 300.0
    benchmarks.append({
        "Task": "Subnetwork Extraction (2-hop, 150-node cap avg)",
        "Target": f"< {target_subgraph:.0f} ms",
        "Actual": f"{subgraph_avg_ms:.2f} ms",
        "Passed": subgraph_avg_ms <= target_subgraph
    })

    # 5. Taint Propagation & Freeze Curve Simulation
    t0 = time.perf_counter()
    tracker = TaintTracker(graph)
    sample_seed = "TXN_000001"
    for u, v, k, d in graph.graph.edges(keys=True, data=True):
        sample_seed = d["txn_id"]
        break
    taint_res = tracker.trace_taint(sample_seed)
    freeze_res = simulate_freeze(taint_res)
    t1 = time.perf_counter()
    taint_time_ms = (t1 - t0) * 1000
    target_taint = 200.0
    benchmarks.append({
        "Task": "Taint Propagation & Freeze Decay Simulation",
        "Target": f"< {target_taint:.0f} ms",
        "Actual": f"{taint_time_ms:.2f} ms",
        "Passed": taint_time_ms <= target_taint
    })

    # Print Table
    all_passed = True
    print(f"{'Task':<46} | {'Target':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 80)
    for b in benchmarks:
        status_str = "PASS" if b["Passed"] else "FAIL"
        if not b["Passed"]:
            all_passed = False
        print(f"{b['Task']:<46} | {b['Target']:<10} | {b['Actual']:<10} | {status_str}")

    print("=" * 65)
    if all_passed:
        print(">>> ALL PERFORMANCE TARGETS SATISFIED SUCCESSFULLY <<<")
    else:
        print(">>> PERFORMANCE TARGET VIOLATIONS DETECTED <<<")
    print("=" * 65)

    return all_passed


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
