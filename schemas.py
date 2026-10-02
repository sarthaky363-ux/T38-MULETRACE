"""Pydantic data schemas for MuleTrace backend."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TransactionRecord(BaseModel):
    txn_id: str
    timestamp: str
    source_account: str
    dest_account: str
    amount: float
    channel: str
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    source_balance_after: Optional[float] = None
    dest_balance_after: Optional[float] = None


class AccountRecord(BaseModel):
    account_id: str
    display_name: str
    account_type: str = "SAVINGS"
    opened_at: str
    kyc_verified: bool = False
    kyc_pan_hash: Optional[str] = None
    kyc_phone_hash: Optional[str] = None
    kyc_address_hash: Optional[str] = None
    declared_monthly_income: float = 0.0
    shared_network_tag: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class CytoscapeNodeData(BaseModel):
    id: str
    label: str
    account_type: str
    risk_score: float = 0.0
    risk_band: str = "safe"  # safe, low, medium, critical, victim
    role: str = "member"     # hub, relay, exit, member, victim
    kyc_verified: bool = False
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    turnover_ratio: float = 0.0
    flagged: bool = False


class CytoscapeNode(BaseModel):
    data: CytoscapeNodeData


class CytoscapeEdgeData(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    channel: str
    timestamp: str
    tainted: bool = False


class CytoscapeEdge(BaseModel):
    data: CytoscapeEdgeData


class GraphResponse(BaseModel):
    nodes: List[CytoscapeNode]
    edges: List[CytoscapeEdge]
    center: Optional[str] = None
    total_nodes: int
    total_edges: int


class QuantumWalkResponse(BaseModel):
    ring_id: str
    ring_name: str
    entry_account: str
    nodes: List[str]
    metadata: Dict[str, Any]
    time_steps: List[float]
    quantum_probabilities: Dict[str, List[float]]
    classical_probabilities: Dict[str, List[float]]
    flow_quantum: Dict[str, float]
    flow_classical: Dict[str, float]
    t_90_quantum: Optional[float] = None
    t_90_classical: Optional[float] = None
    top_predictions_quantum: List[str]
    top_predictions_classical: List[str]
    real_exit_accounts: List[str]
    overlap_score_quantum: float
    overlap_score_classical: float
    disclaimer: str


class QuantumInterdictionSet(BaseModel):
    accounts: List[str]
    count_frozen: int
    count_low_risk_frozen: int
    estimated_saved: float
    estimated_saved_formatted: str


class QuantumInterdictionResponse(BaseModel):
    budget_K: int
    greedy_list: QuantumInterdictionSet
    optimized_set: QuantumInterdictionSet
    winner: str
    comparison_summary: str
    solver_diagnostics: Dict[str, Any]
    disclaimer: str


class QuantumRingFidelityResponse(BaseModel):
    rings: List[Dict[str, Any]]
    typologies: List[Dict[str, Any]]
    ring_typology_matrix: List[List[float]]
    ring_ring_matrix: List[List[float]]
    highest_matches: List[Dict[str, Any]]
    disclaimer: str

