"""Test Active Learning Loop and Day-Zero Early Warning Engine."""
from pathlib import Path
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph
from backend.learning import AnalystFeedbackLearner, DayZeroEarlyWarning


def test_analyst_feedback_learning_loop():
    """Verify learning layer activation rules (>=10 labels, >=2 confirmed, >=2 cleared) and training."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    learner = AnalystFeedbackLearner()

    # 1. Below threshold: Should refuse to train
    learner.add_verdict("ACC_MULE_FAN01", "confirmed_mule")
    learner.add_verdict("ACC_RET_0001", "cleared_legit")
    status = learner.get_status()
    assert status["can_train"] is False
    assert status["is_active"] is False

    train_res = learner.train(fg)
    assert train_res["success"] is False
    assert "Cannot train model yet" in train_res["error"]

    # 2. Add enough verdicts to meet threshold (>=10 total, >=2 of each)
    confirmed_pool = ["ACC_MULE_FAN01", "ACC_CHAIN_01", "ACC_CHAIN_02", "ACC_LOOP_01", "ACC_SYBIL_01"]
    cleared_pool = [f"ACC_RET_{i:04d}" for i in range(1, 7)]

    for c in confirmed_pool:
        learner.add_verdict(c, "confirmed_mule")
    for cl in cleared_pool:
        learner.add_verdict(cl, "cleared_legit")

    status = learner.get_status()
    assert status["can_train"] is True
    assert status["total_verdicts"] >= 10
    assert status["confirmed_mules"] >= 2
    assert status["cleared_legit"] >= 2

    # 3. Train model
    train_res = learner.train(fg)
    assert train_res["success"] is True
    assert train_res["is_active"] is True
    assert len(train_res["feature_importance"]) == len(learner.feature_names)

    # 4. Predict probability
    pred_mule = learner.predict_account(fg, "ACC_CHAIN_03")
    assert pred_mule is not None
    assert 0.0 <= pred_mule["ml_threat_probability"] <= 1.0
    assert "recommendation" in pred_mule


def test_day_zero_early_warning():
    """Verify pre-transaction detection of synthetic identity farms from accounts metadata."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    df_accs = load_accounts(demo_dir / "accounts.csv")
    warning_engine = DayZeroEarlyWarning(max_account_age_days=15, min_group_size=3)

    # Scan accounts without any transactions
    warnings = warning_engine.scan(df_accs)

    assert len(warnings) >= 1
    
    # R4 emulator farm must be detected as Day-Zero threat
    dev_warnings = [w for w in warnings if "DEV_EMU_9901" in w["shared_identifier"]]
    assert len(dev_warnings) >= 1
    w = dev_warnings[0]
    assert w["severity"] == "CRITICAL_DAY_ZERO"
    assert w["cluster_size"] == 4
    for s in range(1, 5):
        assert f"ACC_SYBIL_{s:02d}" in w["accounts"]

    # Family accounts (L5) must NOT trigger Day-Zero (they are aged > 600 days)
    for w in warnings:
        assert "ACC_FAMILY_01" not in w["accounts"]
