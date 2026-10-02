"""Test dataset validation logic and failure detection."""
from pathlib import Path
import pandas as pd
import pytest
from data.validate_dataset import validate_dataset


def test_demo_dataset_is_valid():
    """Verify that generated demo dataset is strictly valid."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    is_valid, errors, stats = validate_dataset(demo_dir)
    assert is_valid, f"Demo dataset failed validation: {errors}"
    assert len(errors) == 0
    assert stats["account_count"] >= 750
    assert stats["transaction_count"] >= 7000


def test_validator_catches_negative_amount(tmp_path):
    """Test that validator flags negative transaction amount."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    # Copy files to tmp_path
    for fname in ["accounts.csv", "ground_truth.csv"]:
        content = (demo_dir / fname).read_text(encoding="utf-8")
        (tmp_path / fname).write_text(content, encoding="utf-8")

    df_txns = pd.read_csv(demo_dir / "transactions.csv")
    df_txns.loc[0, "amount"] = -500.0  # inject bad amount
    df_txns.to_csv(tmp_path / "transactions.csv", index=False)

    is_valid, errors, stats = validate_dataset(tmp_path)
    assert not is_valid
    assert any("amount <= 0" in e for e in errors)


def test_validator_catches_orphan_account(tmp_path):
    """Test that validator catches transaction referencing non-existent account."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    for fname in ["accounts.csv", "ground_truth.csv"]:
        content = (demo_dir / fname).read_text(encoding="utf-8")
        (tmp_path / fname).write_text(content, encoding="utf-8")

    df_txns = pd.read_csv(demo_dir / "transactions.csv")
    df_txns.loc[0, "source_account"] = "ACC_GHOST_9999"
    df_txns.to_csv(tmp_path / "transactions.csv", index=False)

    is_valid, errors, stats = validate_dataset(tmp_path)
    assert not is_valid
    assert any("Orphan source accounts" in e for e in errors)
