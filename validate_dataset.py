#!/usr/bin/env python3
"""
MuleTrace Dataset Validation Tool
Validates strict schema integrity, referential integrity, temporal ordering, and data contracts.
Usage: python data/validate_dataset.py --data-dir data/demo
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

REQUIRED_TXN_COLUMNS = [
    "txn_id", "timestamp", "source_account", "dest_account", "amount",
    "channel", "device_id", "ip_address", "source_balance_after", "dest_balance_after"
]

REQUIRED_ACCOUNT_COLUMNS = [
    "account_id", "display_name", "account_type", "opened_at", "kyc_verified",
    "kyc_pan_hash", "kyc_phone_hash", "kyc_address_hash", "declared_monthly_income",
    "shared_network_tag", "device_id", "ip_address"
]

REQUIRED_GT_COLUMNS = [
    "account_id", "label", "ring_id", "ring_type", "note"
]

ALLOWED_CHANNELS = {"UPI", "IMPS", "NEFT"}
ALLOWED_LABELS = {"mule", "exit", "victim", "legit", "hard_negative"}


def validate_dataset(data_dir: Path) -> Tuple[bool, List[str], Dict[str, int]]:
    """
    Validates the dataset files in data_dir.
    Returns (is_valid, errors, stats).
    """
    errors: List[str] = []
    stats: Dict[str, int] = {}

    txns_path = data_dir / "transactions.csv"
    accs_path = data_dir / "accounts.csv"
    gt_path = data_dir / "ground_truth.csv"

    # 1. File existence
    for p in [txns_path, accs_path, gt_path]:
        if not p.exists():
            errors.append(f"Missing required file: {p}")

    if errors:
        return False, errors, stats

    # 2. Load CSVs
    try:
        df_txns = pd.read_csv(txns_path)
        df_accs = pd.read_csv(accs_path)
        df_gt = pd.read_csv(gt_path)
    except Exception as e:
        errors.append(f"Failed to parse CSV files: {e}")
        return False, errors, stats

    stats["account_count"] = len(df_accs)
    stats["transaction_count"] = len(df_txns)
    stats["ground_truth_count"] = len(df_gt)

    # 3. Check Columns
    txn_missing = set(REQUIRED_TXN_COLUMNS) - set(df_txns.columns)
    if txn_missing:
        errors.append(f"transactions.csv missing columns: {txn_missing}")

    acc_missing = set(REQUIRED_ACCOUNT_COLUMNS) - set(df_accs.columns)
    if acc_missing:
        errors.append(f"accounts.csv missing columns: {acc_missing}")

    gt_missing = set(REQUIRED_GT_COLUMNS) - set(df_gt.columns)
    if gt_missing:
        errors.append(f"ground_truth.csv missing columns: {gt_missing}")

    if errors:
        return False, errors, stats

    # 4. Primary Key Uniqueness
    if df_accs["account_id"].duplicated().any():
        dupes = df_accs["account_id"][df_accs["account_id"].duplicated()].tolist()
        errors.append(f"Duplicate account_id in accounts.csv: {dupes[:5]}")

    if df_txns["txn_id"].duplicated().any():
        dupes = df_txns["txn_id"][df_txns["txn_id"].duplicated()].tolist()
        errors.append(f"Duplicate txn_id in transactions.csv: {dupes[:5]}")

    if df_gt["account_id"].duplicated().any():
        dupes = df_gt["account_id"][df_gt["account_id"].duplicated()].tolist()
        errors.append(f"Duplicate account_id in ground_truth.csv: {dupes[:5]}")

    # 5. Referential Integrity
    acc_ids = set(df_accs["account_id"])
    gt_acc_ids = set(df_gt["account_id"])

    if acc_ids != gt_acc_ids:
        missing_in_gt = acc_ids - gt_acc_ids
        missing_in_acc = gt_acc_ids - acc_ids
        if missing_in_gt:
            errors.append(f"{len(missing_in_gt)} accounts present in accounts.csv but missing in ground_truth.csv")
        if missing_in_acc:
            errors.append(f"{len(missing_in_acc)} accounts present in ground_truth.csv but missing in accounts.csv")

    src_orphans = set(df_txns["source_account"]) - acc_ids
    if src_orphans:
        errors.append(f"Orphan source accounts in transactions.csv: {list(src_orphans)[:5]}")

    dst_orphans = set(df_txns["dest_account"]) - acc_ids
    if dst_orphans:
        errors.append(f"Orphan dest accounts in transactions.csv: {list(dst_orphans)[:5]}")

    # 6. Data Validity Checks
    # No self transfers
    self_txns = df_txns[df_txns["source_account"] == df_txns["dest_account"]]
    if len(self_txns) > 0:
        errors.append(f"Found {len(self_txns)} self-transfers where source_account == dest_account")

    # Positive amounts
    non_positive_amt = df_txns[df_txns["amount"] <= 0]
    if len(non_positive_amt) > 0:
        errors.append(f"Found {len(non_positive_amt)} transactions with amount <= 0")

    # Allowed channels
    invalid_channels = set(df_txns["channel"]) - ALLOWED_CHANNELS
    if invalid_channels:
        errors.append(f"Invalid transaction channels found: {invalid_channels}")

    # Allowed labels
    invalid_labels = set(df_gt["label"]) - ALLOWED_LABELS
    if invalid_labels:
        errors.append(f"Invalid ground truth labels found: {invalid_labels}")

    # 7. Temporal Monotonicity
    try:
        ts_series = pd.to_datetime(df_txns["timestamp"])
        if not ts_series.is_monotonic_increasing:
            errors.append("transactions.csv is not sorted chronologically ascending by timestamp")
    except Exception as e:
        errors.append(f"Error parsing transaction timestamps: {e}")

    # 8. Scale & Ring checks
    if len(df_accs) < 700:
        errors.append(f"Account count ({len(df_accs)}) is below minimum expected (700)")

    if len(df_txns) < 5000:
        errors.append(f"Transaction count ({len(df_txns)}) is below minimum expected (5000)")

    expected_rings = {
        "RING_R1_FAN_IN_OUT", "RING_R2_PASSTHROUGH", "RING_R3_CIRCULAR",
        "RING_R4_SYBIL", "RING_R5_SCAM_STORY", "RING_R6_EVASION"
    }
    found_rings = set(df_gt["ring_id"])
    missing_rings = expected_rings - found_rings
    if missing_rings:
        errors.append(f"Ground truth is missing planted fraud rings: {missing_rings}")

    is_valid = len(errors) == 0
    return is_valid, errors, stats


def main():
    parser = argparse.ArgumentParser(description="Validate MuleTrace dataset integrity")
    parser.add_argument("--data-dir", type=str, default="data/demo", help="Path to dataset directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    print(f"Validating dataset in: {data_dir.resolve()}")
    is_valid, errors, stats = validate_dataset(data_dir)

    if is_valid:
        print("[SUCCESS] Dataset passed all validation checks!")
        print(f" - Accounts:     {stats.get('account_count', 0)}")
        print(f" - Transactions: {stats.get('transaction_count', 0)}")
        print(f" - Ground Truth: {stats.get('ground_truth_count', 0)}")
        sys.exit(0)
    else:
        print(f"[FAILED] Dataset validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  * {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
