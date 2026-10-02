"""
MuleTrace Composite Risk Scoring & Confidence Meter
Calculates explainable threat scores (0-100), risk bands, confidence levels, and evidence breakdown.
"""

from typing import Any, Dict, List, Optional, Tuple


class RiskScorer:
    """Computes explainable composite risk scores and confidence metrics."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.base_points = cfg.get("base_points", {
            "fan_in_out": 45,
            "passthrough": 50,
            "cycle": 45,
            "sybil": 35,
        })
        self.bonuses = cfg.get("bonuses", {
            "drain_ratio_90": 15,
            "velocity_20min": 10,
            "sybil_device_and_pan": 15,
            "turnover_gt_50": 10,
            "new_account_30d": 5,
            "multi_pattern_synergy": 20,
        })
        self.secondary_pattern_weight = cfg.get("secondary_pattern_weight", 0.5)
        self.dampeners = cfg.get("dampeners", {
            "merchant_like": 0.5,
            "payroll_like": 0.5,
            "long_tenure_kyc": 0.15,
        })
        self.bands = cfg.get("bands", {"critical": 70, "medium": 40})

    def score_account(
        self,
        signals: Dict[str, Any],
        hits: List[Dict[str, Any]],
        role_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates composite threat score, confidence, and transparent point breakdown.
        """
        # 1. Victim Role Protection
        if role_override == "victim":
            return {
                "risk_score": 0.0,
                "risk_band": "victim",
                "role": "victim",
                "confidence": "high",
                "breakdown": {"base": 0, "bonuses": {}, "dampeners": {}},
                "is_victim": True,
            }

        if not hits:
            return {
                "risk_score": 0.0,
                "risk_band": "safe",
                "role": "member",
                "confidence": "low",
                "breakdown": {"base": 0, "bonuses": {}, "dampeners": {}},
                "is_victim": False,
            }

        # 2. Base Points (Highest pattern + weighted secondary patterns)
        pattern_types = sorted(list({h["pattern"] for h in hits}))
        pattern_bases = [self.base_points.get(p, 30) for p in pattern_types]
        pattern_bases.sort(reverse=True)

        highest_base = pattern_bases[0]
        secondary_base = sum(b * self.secondary_pattern_weight for b in pattern_bases[1:])
        total_base = highest_base + secondary_base

        breakdown_bonuses = {}
        bonus_points = 0

        # Evidence Categories for Confidence Meter
        categories_detected = set()
        categories_detected.add("topology_pattern")

        # 3. Bonuses Evaluation
        # Bonus: Drain ratio >= 90%
        has_drain_90 = False
        for h in hits:
            ev = h.get("evidence", {})
            f_ratio = ev.get("forward_ratio", 0.0)
            if f_ratio >= 0.90:
                has_drain_90 = True
                break
        if has_drain_90:
            b_val = self.bonuses.get("drain_ratio_90", 15)
            bonus_points += b_val
            breakdown_bonuses["drain_ratio_90"] = b_val
            categories_detected.add("drain_velocity")

        # Bonus: Rapid velocity <= 20 min
        has_velocity_20 = False
        for h in hits:
            ev = h.get("evidence", {})
            w_min = ev.get("window_minutes") or ev.get("hop_gap_minutes") or ev.get("cycle_duration_minutes")
            if w_min is not None and w_min <= 20.0:
                has_velocity_20 = True
                break
        if has_velocity_20:
            b_val = self.bonuses.get("velocity_20min", 10)
            bonus_points += b_val
            breakdown_bonuses["velocity_20min"] = b_val
            categories_detected.add("rapid_speed")

        # Bonus: Sybil sharing both device and PAN
        has_sybil_device_pan = False
        for h in hits:
            if h["pattern"] == "sybil":
                ev = h.get("evidence", {})
                if ev.get("shared_device") and ev.get("shared_pan") and ev["shared_device"] != "multiple":
                    has_sybil_device_pan = True
                    break
        if has_sybil_device_pan:
            b_val = self.bonuses.get("sybil_device_and_pan", 15)
            bonus_points += b_val
            breakdown_bonuses["sybil_device_and_pan"] = b_val
            categories_detected.add("identity_hardware")

        # Bonus: Turnover ratio > 50
        if signals.get("turnover_ratio", 0.0) > 50.0:
            b_val = self.bonuses.get("turnover_gt_50", 10)
            bonus_points += b_val
            breakdown_bonuses["turnover_gt_50"] = b_val
            categories_detected.add("volume_anomaly")

        # Bonus: New account <= 30 days
        if signals.get("is_new_account", False):
            b_val = self.bonuses.get("new_account_30d", 5)
            bonus_points += b_val
            breakdown_bonuses["new_account_30d"] = b_val

        # Bonus: Multi-pattern synergy
        if len(pattern_types) >= 2:
            b_val = self.bonuses.get("multi_pattern_synergy", 20)
            bonus_points += b_val
            breakdown_bonuses["multi_pattern_synergy"] = b_val
            categories_detected.add("multi_pattern")

        # 4. Dampeners
        raw_score = total_base + bonus_points
        breakdown_dampeners = {}

        if signals.get("account_type") == "MERCHANT":
            factor = self.dampeners.get("merchant_like", 0.5)
            raw_score *= factor
            breakdown_dampeners["merchant_dampener"] = f"{factor * 100:.0f}%"

        elif signals.get("account_type") == "CORPORATE":
            factor = self.dampeners.get("payroll_like", 0.5)
            raw_score *= factor
            breakdown_dampeners["payroll_dampener"] = f"{factor * 100:.0f}%"

        if signals.get("tenure_kyc", False):
            reduction_factor = self.dampeners.get("long_tenure_kyc", 0.15)
            raw_score *= (1.0 - reduction_factor)
            breakdown_dampeners["tenure_kyc_dampener"] = f"-{reduction_factor * 100:.0f}%"

        # 5. Clamp and Band Assignment
        final_score = round(max(0.0, min(100.0, raw_score)), 1)

        if final_score >= self.bands.get("critical", 70):
            risk_band = "critical"
        elif final_score >= self.bands.get("medium", 40):
            risk_band = "medium"
        elif final_score > 0.0:
            risk_band = "low"
        else:
            risk_band = "safe"

        # 6. Confidence Meter
        # 1 category = low, 2 categories = medium, 3+ categories = high
        cat_count = len(categories_detected)
        if cat_count >= 3:
            confidence = "high"
        elif cat_count == 2:
            confidence = "medium"
        else:
            confidence = "low"

        # Assign role from primary hit
        primary_hit = hits[0]
        role = role_override or primary_hit.get("role", "member")

        return {
            "risk_score": final_score,
            "risk_band": risk_band,
            "role": role,
            "confidence": confidence,
            "confidence_factors": list(categories_detected),
            "breakdown": {
                "base_pattern_points": round(total_base, 1),
                "bonuses": breakdown_bonuses,
                "dampeners": breakdown_dampeners,
            },
            "is_victim": False,
        }
