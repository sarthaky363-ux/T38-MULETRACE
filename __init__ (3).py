"""
MuleTrace Quantum-Inspired Simulation Layer (Omega)
Classical simulation of continuous-time quantum graph walks, QUBO-inspired
network interdiction, and Ring DNA quantum state fidelity.
Simulated on a classical computer. Synthetic demonstration data. Not a real case.
"""

from backend.quantum.qwalk import QuantumWalkSimulator, simulate_quantum_and_classical_walk
from backend.quantum.interdiction import NetworkInterdictionOptimizer
from backend.quantum.ringstate import compute_ring_fidelities

__all__ = [
    "QuantumWalkSimulator",
    "simulate_quantum_and_classical_walk",
    "NetworkInterdictionOptimizer",
    "compute_ring_fidelities",
]
