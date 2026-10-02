"""
MuleTrace Data Ingestion Engine
Loads and prepares transaction and account data for graph construction and detector pipelines.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def load_accounts(source: Union[str, Path, pd.DataFrame]) -> pd.DataFrame:
    """Loads and standardizes accounts data."""
    if isinstance(source, (str, Path)):
        df = pd.read_csv(source)
    else:
        df = source.copy()

    required_cols = [
        "account_id", "display_name", "account_type", "opened_at",
        "kyc_verified", "kyc_pan_hash", "kyc_phone_hash", "kyc_address_hash",
        "declared_monthly_income", "shared_network_tag", "device_id", "ip_address"
    ]
    for col in required_cols:
        if col not in df.columns:
            if col == "kyc_verified":
                df[col] = False
            elif col == "declared_monthly_income":
                df[col] = 0.0
            else:
                df[col] = None

    df["account_id"] = df["account_id"].astype(str).str.strip()
    df["kyc_verified"] = df["kyc_verified"].astype(bool)
    df["declared_monthly_income"] = pd.to_numeric(df["declared_monthly_income"], errors="coerce").fillna(0.0)

    # Compute account age in days relative to current analysis timestamp
    opened_dates = pd.to_datetime(df["opened_at"], errors="coerce")
    reference_date = opened_dates.max() if not opened_dates.empty else pd.Timestamp.now()
    df["age_days"] = (reference_date - opened_dates).dt.days.fillna(0).astype(int)

    return df


def load_transactions(source: Union[str, Path, pd.DataFrame]) -> pd.DataFrame:
    """Loads, standardizes, and pre-indexes transaction data."""
    if isinstance(source, (str, Path)):
        df = pd.read_csv(source)
    else:
        df = source.copy()

    required_cols = [
        "txn_id", "timestamp", "source_account", "dest_account", "amount",
        "channel", "device_id", "ip_address", "source_balance_after", "dest_balance_after"
    ]
    for col in required_cols:
        if col not in df.columns:
            if col in ["source_balance_after", "dest_balance_after"]:
                df[col] = 0.0
            else:
                df[col] = None

    df["txn_id"] = df["txn_id"].astype(str).str.strip()
    df["source_account"] = df["source_account"].astype(str).str.strip()
    df["dest_account"] = df["dest_account"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["channel"] = df["channel"].astype(str).str.upper().str.strip()

    # Parse ISO timestamp and compute epoch seconds for fast mathematical comparisons
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    epoch_ref = pd.Timestamp("1970-01-01T00:00:00Z")
    df["epoch"] = (df["timestamp_dt"] - epoch_ref).dt.total_seconds().astype("int64")

    # Ensure chronological order
    df = df.sort_values("epoch").reset_index(drop=True)

    return df


def compute_account_summaries(df_accs: pd.DataFrame, df_txns: pd.DataFrame) -> pd.DataFrame:
    """Enriches account dataframe with transaction volume, count, and velocity features."""
    acc_df = df_accs.copy().set_index("account_id", drop=False)

    # Inflows
    inflow_grp = df_txns.groupby("dest_account")
    inflow_sum = inflow_grp["amount"].sum()
    inflow_cnt = inflow_grp.size()

    # Outflows
    outflow_grp = df_txns.groupby("source_account")
    outflow_sum = outflow_grp["amount"].sum()
    outflow_cnt = outflow_grp.size()

    acc_df["total_inflow"] = acc_df["account_id"].map(inflow_sum).fillna(0.0)
    acc_df["total_outflow"] = acc_df["account_id"].map(outflow_sum).fillna(0.0)
    acc_df["inflow_count"] = acc_df["account_id"].map(inflow_cnt).fillna(0).astype(int)
    acc_df["outflow_count"] = acc_df["account_id"].map(outflow_cnt).fillna(0).astype(int)
    acc_df["txn_count"] = acc_df["inflow_count"] + acc_df["outflow_count"]

    # Net retained ratio: (inflow - outflow) / inflow (if inflow > 0)
    inflow_safe = acc_df["total_inflow"].replace(0, np.nan)
    acc_df["retained_ratio"] = ((acc_df["total_inflow"] - acc_df["total_outflow"]) / inflow_safe).fillna(0.0).clip(-1.0, 1.0)

    # Average balance proxy
    # If balances are present in transactions, use median dest_balance_after or declared income
    acc_df["avg_balance"] = acc_df["declared_monthly_income"] * 0.35 + 5000.0

    # Turnover ratio: total_volume / (avg_balance + 1000)
    total_volume = acc_df["total_inflow"] + acc_df["total_outflow"]
    acc_df["turnover_ratio"] = (total_volume / (acc_df["avg_balance"] + 1000.0)).round(2)

    return acc_df.reset_index(drop=True)
