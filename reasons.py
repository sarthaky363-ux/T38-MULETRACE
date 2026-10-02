"""
MuleTrace Compliance Explanations & Counterfactual Engine
Produces analyst-first, plain-language justifications and counterfactual mitigation scenarios.
"""

from typing import Any, Dict, List, Optional
from backend.detectors.fan_in_out import FanInOutDetector, format_inr
from backend.detectors.passthrough import PassthroughDetector
from backend.detectors.cycles import CycleDetector
from backend.detectors.sybil import SybilDetector

DETECTOR_REGISTRY = {
    "fan_in_out": FanInOutDetector(),
    "passthrough": PassthroughDetector(),
    "cycle": CycleDetector(),
    "sybil": SybilDetector(),
}


def build_explanation_dossier(
    account_id: str,
    signals: Dict[str, Any],
    hits: List[Dict[str, Any]],
    score_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Constructs comprehensive plain-language and technical reasons plus counterfactual scenarios.
    Adheres strictly to Rule 3 (explainability) and Rule 6 (pure banking terminology).
    """
    if score_data.get("role") == "victim":
        return {
            "plain_reason": "This account is identified as an innocent victim that originated transfers into a fraudulent layering network.",
            "technical_reason": "Victim entity classification. Zero risk assessed. Qualified as transfer origin to suspicious destination.",
            "counterfactual": "No mitigation required; this entity is an external victim, not a participant in the laundering structure.",
            "evidence_bullets": [
                f"Total outbound victim transfer: {format_inr(signals.get('total_outflow', 0.0))}",
                f"Account tenure: {signals.get('age_days', 0)} days with verified KYC credentials",
            ]
        }

    if not hits:
        return {
            "plain_reason": "This account demonstrates regular financial patterns with no suspicious structural linkages.",
            "technical_reason": "Baseline profile. No layering, fan-in funnel, cycle, or synthetic identity patterns detected.",
            "counterfactual": "Account is already clear of suspicious activity.",
            "evidence_bullets": [
                f"Total transaction volume: {format_inr(signals.get('total_volume', 0.0))}",
                f"Tenure: {signals.get('age_days', 0)} days (KYC: {'Verified' if signals.get('kyc_verified') else 'Unverified'})",
            ]
        }

    # Primary hit explanation
    primary_hit = hits[0]
    pattern_type = primary_hit["pattern"]
    detector = DETECTOR_REGISTRY.get(pattern_type)
    
    if detector:
        base_exp = detector.explain(primary_hit)
    else:
        base_exp = {
            "plain_reason": "Suspicious structural activity detected across connected accounts.",
            "technical_reason": f"Pattern {pattern_type} flagged.",
            "counterfactual": "Discontinuing correlated rapid transfers would clear this account.",
        }

    # Generate Evidence Bullets
    bullets = []
    bullets.append(f"Risk Score: {score_data['risk_score']}/100 ({score_data['risk_band'].upper()}) | Confidence: {score_data['confidence'].upper()}")
    bullets.append(f"Total Inflow: {format_inr(signals.get('total_inflow', 0.0))} | Total Outflow: {format_inr(signals.get('total_outflow', 0.0))}")
    bullets.append(f"Account Turnover Ratio: {signals.get('turnover_ratio', 0.0)}x normal account balance")
    
    if signals.get("shared_device_accounts", 0) > 1:
        bullets.append(f"Hardware Fingerprint: Shared with {signals['shared_device_accounts']} other accounts")

    if signals.get("min_forward_gap_minutes") is not None:
        bullets.append(f"Fastest Inflow-to-Outflow Transfer Gap: {signals['min_forward_gap_minutes']} minutes")

    # Counterfactual computation ('What would clear this account?')
    counterfactual = base_exp["counterfactual"]

    return {
        "plain_reason": base_exp["plain_reason"],
        "technical_reason": base_exp["technical_reason"],
        "counterfactual": counterfactual,
        "evidence_bullets": bullets,
    }
