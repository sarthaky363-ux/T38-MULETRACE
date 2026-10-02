"""Test Ring Autopsy and Ring DNA signature similarity matching."""
import pytest
from backend.ringdna import RingDNAEngine, cosine_similarity


def test_ringdna_vector_extraction_and_matching():
    """Verify DNA extraction, cosine similarity, and 3-line plain-language autopsy narrative."""
    engine = RingDNAEngine()

    # 1. Test DNA Vector Extraction for R2 Pass-Through Layering
    dna_r2 = engine.extract_ring_dna(
        ring_type="passthrough",
        account_count=6,
        duration_minutes=14.0,
        avg_hop_gap_minutes=2.0,
        retained_ratio=0.01,
        forward_ratio=0.99,
    )
    assert len(dna_r2) == 6
    for val in dna_r2:
        assert 0.0 <= val <= 1.0

    # 2. Test Cosine Similarity Matching against Typology Library
    matches = engine.find_similar_typologies(dna_r2)
    assert len(matches) >= 3
    top_match = matches[0]
    
    # R2 should match the ATM Layering Chain typology with high similarity (>90%)
    assert top_match["typology_id"] == "TYP_ATM_LAYERING_CHAIN"
    assert top_match["similarity_score"] >= 0.90
    assert "recommended_action" in top_match

    # 3. Test Autopsy Narrative Generation
    autopsy = engine.generate_autopsy(
        ring_id="RING_R2_PASSTHROUGH",
        ring_type="passthrough",
        total_amount=350000.0,
        duration_minutes=14.0,
        accounts_involved=[f"ACC_CHAIN_{i:02d}" for i in range(1, 7)],
        avg_hop_gap_minutes=2.0,
        forward_ratio=0.99,
    )

    narrative = autopsy["autopsy_narrative"]
    assert "line_1_overview" in narrative
    assert "line_2_modus_operandi" in narrative
    assert "line_3_interception" in narrative

    # Rule 6 Verification: Strictly banking words, no graph jargon
    forbidden_terms = ["node", "edge", "graph", "vertex", "component"]
    full_text = narrative["full_narrative"].lower()
    for term in forbidden_terms:
        assert term not in full_text, f"Forbidden graph term '{term}' found in autopsy"

    assert "account" in full_text
    assert "₹" in full_text
