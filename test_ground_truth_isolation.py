import os
import shutil
import pytest
from pathlib import Path
from backend.fraud_engine import FraudEngine


def test_no_ground_truth_in_detector_source_code():
    """
    Rule 5 Invariant:
    Detectors, scoring, signals, taint, and ringdna modules must NEVER import,
    reference, or read ground_truth.csv.
    """
    backend_dir = Path(__file__).resolve().parent.parent
    detector_dir = backend_dir / "detectors"

    files_to_check = list(detector_dir.glob("*.py")) + [
        backend_dir / "scoring.py",
        backend_dir / "signals.py",
        backend_dir / "taint.py",
        backend_dir / "chase.py",
        backend_dir / "ringdna.py",
        backend_dir / "graph.py",
        backend_dir / "ingest.py",
    ]

    for file_path in files_to_check:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
            # Assert "ground_truth" never appears in any core analytical detector file
            assert "ground_truth" not in content, (
                f"Rule 5 Violation: '{file_path.name}' contains a forbidden reference to 'ground_truth'!"
            )


def test_fraud_engine_runs_without_ground_truth(tmp_path):
    """
    Rule 5 Invariant:
    Detection and scoring must produce identical results even if ground_truth.csv
    is completely absent or removed.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    demo_dir = project_root / "data" / "demo"
    cfg_path = project_root / "backend" / "config" / "thresholds.yaml"

    # Copy accounts and transactions to a temp directory WITHOUT ground_truth.csv
    shutil.copy(demo_dir / "accounts.csv", tmp_path / "accounts.csv")
    shutil.copy(demo_dir / "transactions.csv", tmp_path / "transactions.csv")

    import pandas as pd
    df_acc = pd.read_csv(tmp_path / "accounts.csv")
    df_txn = pd.read_csv(tmp_path / "transactions.csv")

    engine = FraudEngine(config_path=str(cfg_path))
    summary = engine.analyze(
        df_accounts=df_acc,
        df_transactions=df_txn,
        df_ground_truth=None
    )

    # Core engine must execute fully and produce flagged accounts & rings
    assert summary["total_accounts"] > 0
    assert summary["flagged_accounts"] > 0
    assert summary["rings_detected"] > 0
    assert len(engine.alerts) > 0

    # Offline metrics must gracefully report ground truth is not loaded
    metrics = engine.compute_evaluation_metrics()
    assert metrics["available"] is False
    assert "isolation_disclaimer" in metrics
