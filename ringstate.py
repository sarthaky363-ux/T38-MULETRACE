"""
MuleTrace Ring DNA Quantum State Fidelity Engine
Calculates quantum state fidelity |<a|b>|^2 across detected fraud rings and the
typology library. For non-negative real vectors, state fidelity is mathematically
identical to cosine^2(theta).
Simulated on a classical computer. Synthetic demonstration data. Not a real case.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.ringdna import KNOWN_TYPOLOGY_LIBRARY


def normalize_unit_state(vec: List[float]) -> np.ndarray:
    """Normalizes a 6D Ring DNA feature vector to unit length ||v|| = 1.0."""
    arr = np.array(vec, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm < 1e-12:
        return np.zeros_like(arr)
    return arr / norm


def compute_quantum_fidelity(v1: List[float], v2: List[float]) -> float:
    """
    Computes quantum state fidelity F(|a>, |b>) = |<a|b>|^2.
    For non-negative real vectors, this equals (cos(theta))^2.
    Invariant: F(|a>, |a>) == 1.0
    """
    u1 = normalize_unit_state(v1)
    u2 = normalize_unit_state(v2)
    overlap = float(np.dot(u1, u2))
    fidelity = overlap ** 2
    return float(np.clip(fidelity, 0.0, 1.0))


def compute_ring_fidelities(
    rings: Dict[str, Dict[str, Any]],
    max_rings: int = 6
) -> Dict[str, Any]:
    """
    Computes pairwise fidelity heat matrices:
    1. Ring-to-Typology fidelity matrix (max 6x6)
    2. Ring-to-Ring fidelity matrix (max 6x6)
    Includes one-sentence plain language interpretation for each ring's top match.
    """
    typologies = list(KNOWN_TYPOLOGY_LIBRARY)[:6]
    ring_items = list(rings.items())[:max_rings]

    ring_list = []
    for r_id, r_data in ring_items:
        ring_list.append({
            "ring_id": r_id,
            "ring_name": r_data.get("ring_name", r_id),
            "ring_type": r_data.get("ring_type", "Fraud Ring"),
            "dna_vector": r_data.get("dna_vector", [0.0] * 6),
        })

    typology_list = []
    for t in typologies:
        typology_list.append({
            "typology_id": t["typology_id"],
            "name": t["name"],
            "description": t.get("description", ""),
            "dna_vector": t["dna_vector"],
        })

    num_rings = len(ring_list)
    num_types = len(typology_list)

    # 1. Ring-to-Typology Fidelity Matrix
    ring_typology_matrix = np.zeros((num_rings, num_types), dtype=np.float64)
    highest_matches = []

    for i, r in enumerate(ring_list):
        best_fid = -1.0
        best_type = None

        for j, t in enumerate(typology_list):
            fid = compute_quantum_fidelity(r["dna_vector"], t["dna_vector"])
            ring_typology_matrix[i, j] = fid
            if fid > best_fid:
                best_fid = fid
                best_type = t

        pct_str = f"{best_fid * 100.0:.1f}%"
        type_name = best_type["name"] if best_type else "Unknown Typology"
        
        # Plain language reading using banking terms
        plain_reading = (
            f"{r['ring_name']} exhibits {pct_str} behavioral fidelity with {type_name}, "
            f"indicating matching transaction speed, account group size, and fund drain dynamics."
        )

        highest_matches.append({
            "ring_id": r["ring_id"],
            "ring_name": r["ring_name"],
            "matched_typology_id": best_type["typology_id"] if best_type else "",
            "matched_typology_name": type_name,
            "fidelity": round(float(best_fid), 4),
            "fidelity_pct": pct_str,
            "plain_language_reading": plain_reading,
        })

    # 2. Ring-to-Ring Fidelity Matrix
    ring_ring_matrix = np.zeros((num_rings, num_rings), dtype=np.float64)
    for i in range(num_rings):
        for j in range(num_rings):
            if i == j:
                ring_ring_matrix[i, j] = 1.0
            else:
                ring_ring_matrix[i, j] = compute_quantum_fidelity(
                    ring_list[i]["dna_vector"],
                    ring_list[j]["dna_vector"]
                )

    return {
        "rings": [
            {
                "ring_id": r["ring_id"],
                "ring_name": r["ring_name"],
                "ring_type": r["ring_type"]
            }
            for r in ring_list
        ],
        "typologies": [
            {
                "typology_id": t["typology_id"],
                "name": t["name"],
                "description": t["description"]
            }
            for t in typology_list
        ],
        "ring_typology_matrix": [
            [round(float(val), 4) for val in row]
            for row in ring_typology_matrix
        ],
        "ring_ring_matrix": [
            [round(float(val), 4) for val in row]
            for row in ring_ring_matrix
        ],
        "highest_matches": highest_matches,
        "disclaimer": "Simulated on a classical computer. Synthetic demonstration data. Not a real case.",
    }
