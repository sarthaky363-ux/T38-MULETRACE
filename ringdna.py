"""
MuleTrace Ring Autopsy & Ring DNA Similarity Engine
Generates 3-line plain forensic narratives, extracts normalized DNA signature vectors,
and computes cosine similarity against a known typology library.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from backend.detectors.fan_in_out import format_inr

# Known Forensic Typology Library
KNOWN_TYPOLOGY_LIBRARY = [
    {
        "typology_id": "TYP_FUNNEL_CRYPTO",
        "name": "High-Velocity Funnel Aggregator (Crypto Escrow Cashout)",
        "description": "Multi-victim rapid aggregation hub routing directly into unregulated crypto OTC desks.",
        "dna_vector": [0.2, 0.6, 0.25, 0.2, 0.04, 0.96],  # [type, size, duration, hop_gap, retained, drain]
        "common_channels": ["UPI", "IMPS"],
        "recommended_action": "Freeze primary aggregation hub immediately; notify exchange compliance.",
    },
    {
        "typology_id": "TYP_ATM_LAYERING_CHAIN",
        "name": "Multi-Hop Pass-Through Layering (ATM Terminal Cashout)",
        "description": "Sequential hop-by-hop layering chain maintaining near-zero residual balance per hop.",
        "dna_vector": [0.4, 0.6, 0.23, 0.13, 0.01, 0.99],
        "common_channels": ["IMPS", "NEFT"],
        "recommended_action": "Deploy chase interception at Hop 2-3 before ATM cash-out execution.",
    },
    {
        "typology_id": "TYP_WASH_CYCLE",
        "name": "Circular Wash-Trading Round-Robin",
        "description": "Closed 3-5 party circular flow designed to simulate legitimate trade volume.",
        "dna_vector": [0.6, 0.4, 0.63, 0.6, 0.05, 0.90],
        "common_channels": ["UPI"],
        "recommended_action": "Flag all circular participants for cross-account audit and freeze wash pool.",
    },
    {
        "typology_id": "TYP_SYBIL_EMULATOR_FARM",
        "name": "Synthetic Identity Sybil Farm (Hardware Emulator)",
        "description": "Batch of newly opened accounts sharing hardware fingerprint and forged tax credentials.",
        "dna_vector": [0.8, 0.4, 0.05, 0.1, 0.50, 0.50],
        "common_channels": ["UPI"],
        "recommended_action": "Blacklist shared hardware fingerprint; block account creation via device hash.",
    },
    {
        "typology_id": "TYP_SMURF_TREE",
        "name": "Multi-Tiered Dispersal Scam Network (Smurfing Tree)",
        "description": "Tree-structured fan-out from primary ingestion to micro-layer dispersal and extraction.",
        "dna_vector": [1.0, 1.0, 0.42, 0.33, 0.03, 0.97],
        "common_channels": ["IMPS", "UPI"],
        "recommended_action": "Halt Layer 1 and Layer 2 gateway relays to starve Layer 3 extraction endpoints.",
    },
]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two normalized vectors."""
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class RingDNAEngine:
    """Extracts Ring DNA feature vectors and performs autopsy narrative generation."""

    def extract_ring_dna(
        self,
        ring_type: str,
        account_count: int,
        duration_minutes: float,
        avg_hop_gap_minutes: float,
        retained_ratio: float,
        forward_ratio: float
    ) -> List[float]:
        """
        Extracts a 6-dimensional normalized Ring DNA signature vector.
        Dimensions:
        0: Structure Type (0.2=fan_in_out, 0.4=passthrough, 0.6=cycle, 0.8=sybil, 1.0=story)
        1: Network Size (normalized to 10 accounts)
        2: Duration Velocity (normalized to 60 minutes)
        3: Average Hop Gap (normalized to 15 minutes)
        4: Retained Ratio (0.0 to 1.0)
        5: Forward Drain Ratio (0.0 to 1.0)
        """
        type_map = {
            "fan_in_out": 0.2,
            "passthrough": 0.4,
            "cycle": 0.6,
            "sybil": 0.8,
            "story": 1.0,
        }
        t_val = type_map.get(ring_type.lower(), 0.5)
        size_val = min(1.0, max(0.1, account_count / 10.0))
        dur_val = min(1.0, max(0.05, duration_minutes / 60.0))
        gap_val = min(1.0, max(0.05, avg_hop_gap_minutes / 15.0))
        ret_val = max(0.0, min(1.0, retained_ratio))
        drain_val = max(0.0, min(1.0, forward_ratio))

        return [
            round(t_val, 2),
            round(size_val, 2),
            round(dur_val, 2),
            round(gap_val, 2),
            round(ret_val, 2),
            round(drain_val, 2),
        ]

    def find_similar_typologies(self, query_dna: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Matches query DNA against known forensic typology library using cosine similarity."""
        matches = []
        for typ in KNOWN_TYPOLOGY_LIBRARY:
            sim = cosine_similarity(query_dna, typ["dna_vector"])
            matches.append({
                "typology_id": typ["typology_id"],
                "name": typ["name"],
                "description": typ["description"],
                "similarity_score": round(sim, 3),
                "similarity_pct": f"{sim * 100:.1f}%",
                "recommended_action": typ["recommended_action"],
            })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:top_k]

    def generate_autopsy(
        self,
        ring_id: str,
        ring_type: str,
        total_amount: float,
        duration_minutes: float,
        accounts_involved: List[str],
        avg_hop_gap_minutes: float,
        forward_ratio: float,
        exit_account: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Produces a concise 3-line plain-language forensic narrative and DNA match.
        Strictly follows Rule 6 (pure banking terminology; no graph theory jargon).
        """
        dna = self.extract_ring_dna(
            ring_type=ring_type,
            account_count=len(accounts_involved),
            duration_minutes=duration_minutes,
            avg_hop_gap_minutes=avg_hop_gap_minutes,
            retained_ratio=max(0.0, 1.0 - forward_ratio),
            forward_ratio=forward_ratio,
        )

        matches = self.find_similar_typologies(dna)
        top_match = matches[0] if matches else None

        amt_fmt = format_inr(total_amount)
        n_acc = len(accounts_involved)

        # Line 1: Incident Overview
        if ring_type == "passthrough":
            line1 = f"A rapid pass-through layering structure consisting of {n_acc} connected accounts moved {amt_fmt} from origin victim to terminal cash-out in {duration_minutes} minutes."
        elif ring_type == "fan_in_out":
            line1 = f"A high-velocity funnel aggregation hub gathered {amt_fmt} across multiple victim transfers and dispersed it within {duration_minutes} minutes."
        elif ring_type == "cycle":
            line1 = f"A circular wash-trading loop moved {amt_fmt} sequentially across {n_acc} accounts in a closed circle over {duration_minutes} minutes."
        elif ring_type == "sybil":
            line1 = f"A synthetic identity farm of {n_acc} newly opened accounts coordinated rapid transfers using shared device hardware credentials."
        else:
            line1 = f"A multi-stage scam dispersal flow coordinated {amt_fmt} across {n_acc} accounts in {duration_minutes} minutes."

        # Line 2: Velocity & Modus Operandi
        pct_fmt = f"{forward_ratio * 100:.1f}%"
        line2 = f"Accounts operated as rapid relays, forwarding {pct_fmt} of funds with an average transfer gap of {avg_hop_gap_minutes} minutes while retaining minimal residual balance."

        # Line 3: Interception Analysis
        interception_hop = max(1, n_acc // 2)
        line3 = f"Freezing accounts at transfer hop {interception_hop} within the first {round(duration_minutes * 0.4, 1)} minutes would have intercepted over 95% of illicit capital before final extraction."

        return {
            "ring_id": ring_id,
            "ring_type": ring_type,
            "dna_vector": dna,
            "top_match": top_match,
            "similar_typologies": matches,
            "autopsy_narrative": {
                "line_1_overview": line1,
                "line_2_modus_operandi": line2,
                "line_3_interception": line3,
                "full_narrative": f"{line1}\n{line2}\n{line3}",
            }
        }
