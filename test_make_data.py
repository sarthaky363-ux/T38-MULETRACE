"""Test synthetic dataset generator reproducibility and contract adherence."""
from pathlib import Path
import pandas as pd
import pytest
from data.make_data import generate_dataset


def test_make_data_execution(tmp_path):
    """Test generating dataset in a temporary path."""
    df_txns, df_accounts, df_gt = generate_dataset(seed=42, output_dir=tmp_path)

    # 1. Accounts verification
    assert len(df_accounts) >= 750, f"Expected >= 750 accounts, got {len(df_accounts)}"
    assert "account_id" in df_accounts.columns
    assert "kyc_verified" in df_accounts.columns
    assert "kyc_pan_hash" in df_accounts.columns

    # 2. Transactions verification
    assert 7000 <= len(df_txns) <= 12000, f"Expected 7k-12k transactions, got {len(df_txns)}"
    assert (df_txns["amount"] > 0).all(), "All transaction amounts must be > 0"
    
    # Check channel breakdown
    channels = df_txns["channel"].value_counts(normalize=True)
    assert 0.65 <= channels.get("UPI", 0) <= 0.90, f"UPI proportion {channels.get('UPI')} out of range"
    assert 0.05 <= channels.get("IMPS", 0) <= 0.25, f"IMPS proportion {channels.get('IMPS')} out of range"
    assert 0.01 <= channels.get("NEFT", 0) <= 0.15, f"NEFT proportion {channels.get('NEFT')} out of range"

    # Verify chronological ordering
    ts_series = pd.to_datetime(df_txns["timestamp"])
    assert ts_series.is_monotonic_increasing, "Transactions must be sorted chronologically"

    # 3. Ground truth verification
    assert len(df_gt) == len(df_accounts), "Ground truth must match account count"
    labels = df_gt["label"].unique()
    assert "mule" in labels
    assert "victim" in labels
    assert "exit" in labels
    assert "hard_negative" in labels
    assert "legit" in labels

    # 4. Verify specific fraud rings are present
    ring_ids = df_gt["ring_id"].unique()
    assert "RING_R1_FAN_IN_OUT" in ring_ids
    assert "RING_R2_PASSTHROUGH" in ring_ids
    assert "RING_R3_CIRCULAR" in ring_ids
    assert "RING_R4_SYBIL" in ring_ids
    assert "RING_R5_SCAM_STORY" in ring_ids
    assert "RING_R6_EVASION" in ring_ids

    # 5. Verify hard negative rings
    assert "RING_L1_MERCHANTS" in ring_ids
    assert "RING_L2_PAYROLL" in ring_ids
    assert "RING_L3_WEDDING" in ring_ids
    assert "RING_L4_LANDLORD" in ring_ids
    assert "RING_L5_FAMILY" in ring_ids
