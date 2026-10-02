"""
MuleTrace Active Learning Loop & Day-Zero Early Warning Engine
Learns from human analyst verdicts using calibrated Logistic Regression,
and detects synthetic identity clusters before transaction execution occurs.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from backend.graph import FinancialGraph
from backend.signals import compute_account_signals


class AnalystFeedbackLearner:
    """
    Active learning layer using scikit-learn Logistic Regression.
    Strictly activates ONLY when >= 10 human analyst labels exist (with >= 2 confirmed and >= 2 cleared).
    """

    def __init__(self):
        self.verdicts: Dict[str, str] = {}  # account_id -> 'confirmed_mule' | 'cleared_legit'
        self.model: Optional[LogisticRegression] = None
        self.is_active: bool = False
        self.feature_names = [
            "turnover_ratio",
            "retained_ratio",
            "age_days",
            "is_new_account",
            "unique_counterparties",
            "shared_device_accounts",
            "shared_pan_accounts",
        ]

    def add_verdict(self, account_id: str, verdict: str) -> Dict[str, Any]:
        """Records an analyst verdict: 'confirmed_mule' or 'cleared_legit'."""
        if verdict not in ["confirmed_mule", "cleared_legit"]:
            raise ValueError(f"Invalid verdict '{verdict}'. Must be 'confirmed_mule' or 'cleared_legit'.")
        self.verdicts[account_id] = verdict
        return self.get_status()

    def remove_verdict(self, account_id: str) -> Dict[str, Any]:
        """Removes an analyst verdict (undo operation)."""
        self.verdicts.pop(account_id, None)
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """Returns training eligibility, current label counts, and active status."""
        confirmed_count = sum(1 for v in self.verdicts.values() if v == "confirmed_mule")
        cleared_count = sum(1 for v in self.verdicts.values() if v == "cleared_legit")
        total_count = len(self.verdicts)

        can_train = total_count >= 10 and confirmed_count >= 2 and cleared_count >= 2

        return {
            "is_active": self.is_active,
            "can_train": can_train,
            "total_verdicts": total_count,
            "confirmed_mules": confirmed_count,
            "cleared_legit": cleared_count,
            "activation_requirements": "Requires >= 10 labels with >= 2 confirmed and >= 2 cleared.",
        }

    def train(self, fg: FinancialGraph) -> Dict[str, Any]:
        """
        Trains Logistic Regression on accounts labeled by the analyst.
        Extracts explainable feature weights.
        """
        status = self.get_status()
        if not status["can_train"]:
            self.is_active = False
            return {
                "success": False,
                "error": f"Cannot train model yet. {status['activation_requirements']} Current: {status['total_verdicts']} total ({status['confirmed_mules']} confirmed, {status['cleared_legit']} cleared).",
                "status": status,
            }

        X = []
        y = []
        for acc_id, verdict in self.verdicts.items():
            if acc_id not in fg.account_lookup:
                continue
            sig = compute_account_signals(fg, acc_id)
            feats = [
                float(sig.get("turnover_ratio", 0.0)),
                float(sig.get("retained_ratio", 0.0)),
                float(sig.get("age_days", 0.0)),
                1.0 if sig.get("is_new_account") else 0.0,
                float(sig.get("unique_counterparties", 0.0)),
                float(sig.get("shared_device_accounts", 0.0)),
                float(sig.get("shared_pan_accounts", 0.0)),
            ]
            X.append(feats)
            y.append(1 if verdict == "confirmed_mule" else 0)

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=int)

        self.model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
        self.model.fit(X_arr, y_arr)
        self.is_active = True

        coefs = self.model.coef_[0]
        feature_importance = [
            {"feature": f_name, "weight": round(float(c), 3)}
            for f_name, c in zip(self.feature_names, coefs)
        ]
        feature_importance.sort(key=lambda x: abs(x["weight"]), reverse=True)

        return {
            "success": True,
            "is_active": True,
            "trained_samples": len(X),
            "feature_importance": feature_importance,
            "intercept": round(float(self.model.intercept_[0]), 3),
            "status": self.get_status(),
        }

    def predict_account(self, fg: FinancialGraph, acc_id: str) -> Optional[Dict[str, Any]]:
        """Predicts probability of being a mule using the trained model."""
        if not self.is_active or not self.model:
            return None

        sig = compute_account_signals(fg, acc_id)
        feats = np.array([[
            float(sig.get("turnover_ratio", 0.0)),
            float(sig.get("retained_ratio", 0.0)),
            float(sig.get("age_days", 0.0)),
            1.0 if sig.get("is_new_account") else 0.0,
            float(sig.get("unique_counterparties", 0.0)),
            float(sig.get("shared_device_accounts", 0.0)),
            float(sig.get("shared_pan_accounts", 0.0)),
        ]])

        prob = float(self.model.predict_proba(feats)[0][1])
        return {
            "ml_threat_probability": round(prob, 3),
            "ml_threat_score": round(prob * 100, 1),
            "recommendation": "Confirm Mule" if prob >= 0.65 else ("Monitor" if prob >= 0.40 else "Low Risk"),
        }


class DayZeroEarlyWarning:
    """
    Day-Zero Pre-Transaction Detection.
    Scans accounts and KYC metadata to identify synthetic account farms before transactions occur.
    """

    def __init__(self, max_account_age_days: int = 15, min_group_size: int = 3):
        self.max_account_age_days = max_account_age_days
        self.min_group_size = min_group_size

    def scan(self, df_accounts: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes account attributes completely independent of transaction data.
        Flags clusters sharing device fingerprints, phone hashes, or PAN hashes.
        """
        warnings = []
        df = df_accounts.copy()

        # Group by shared hardware device
        device_groups = df[df["device_id"].notna()].groupby("device_id")
        for dev_id, grp in device_groups:
            if len(grp) >= self.min_group_size:
                ages = grp["age_days"].tolist() if "age_days" in grp.columns else [0] * len(grp)
                # Check if group is newly created
                new_accounts = [a for a in ages if a <= self.max_account_age_days]
                if len(new_accounts) >= self.min_group_size:
                    acc_ids = grp["account_id"].tolist()
                    warnings.append({
                        "warning_id": f"WARN_ZERO_DEV_{dev_id}",
                        "signal_type": "SHARED_HARDWARE_EMULATOR",
                        "severity": "CRITICAL_DAY_ZERO",
                        "cluster_size": len(grp),
                        "accounts": acc_ids,
                        "shared_identifier": f"Device ID: {dev_id}",
                        "avg_age_days": round(float(np.mean(ages)), 1),
                        "description": f"{len(grp)} newly opened accounts share hardware fingerprint {dev_id} prior to transaction activity.",
                        "recommended_action": "Proactively block automated UPI provisioning; mandate physical or video KYC re-verification.",
                    })

        # Group by shared PAN hash
        pan_groups = df[df["kyc_pan_hash"].notna()].groupby("kyc_pan_hash")
        for pan_hash, grp in pan_groups:
            if len(grp) >= self.min_group_size:
                ages = grp["age_days"].tolist() if "age_days" in grp.columns else [0] * len(grp)
                new_accounts = [a for a in ages if a <= self.max_account_age_days]
                if len(new_accounts) >= self.min_group_size:
                    acc_ids = grp["account_id"].tolist()
                    warnings.append({
                        "warning_id": f"WARN_ZERO_PAN_{pan_hash}",
                        "signal_type": "SYNTHETIC_TAX_DUPLICATION",
                        "severity": "CRITICAL_DAY_ZERO",
                        "cluster_size": len(grp),
                        "accounts": acc_ids,
                        "shared_identifier": f"PAN Hash: {pan_hash}",
                        "avg_age_days": round(float(np.mean(ages)), 1),
                        "description": f"{len(grp)} new accounts registered using duplicate tax identification {pan_hash}.",
                        "recommended_action": "Freeze account creation and flag KYC identity for synthetic fraud investigation.",
                    })

        return warnings
