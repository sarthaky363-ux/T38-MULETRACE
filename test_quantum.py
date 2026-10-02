"""
Unit and benchmark tests for MuleTrace Quantum-Inspired Simulation Layer.
Tests:
1. Quantum walk probabilities sum to 1 (+-1e-9) at all time steps.
2. Classical diffusion conserves total probability mass (+-1e-9).
3. Simulated annealing solver is deterministic with a fixed seed.
4. Victims are never in the freeze set (Victim Protection Invariant).
5. Fidelity of a ring with itself is exactly 1.0.
6. Benchmark: Quantum walk on a 150-account subgraph completes in under 1 second.
7. Benchmark: Solver on a 150-account graph completes in under 2 seconds.
"""

import time
import pytest
import numpy as np

from backend.quantum.qwalk import QuantumWalkSimulator
from backend.quantum.interdiction import NetworkInterdictionOptimizer
from backend.quantum.ringstate import compute_quantum_fidelity, normalize_unit_state
from backend.graph import FinancialGraph


def create_mock_financial_graph(num_accounts: int = 150) -> FinancialGraph:
    """Constructs a deterministic synthetic FinancialGraph with num_accounts nodes."""
    import pandas as pd

    account_ids = [f"ACC_TEST_{i:04d}" for i in range(num_accounts)]
    # Designate first account as victim and last 5 as exit
    roles = ["victim"] + ["mule"] * (num_accounts - 6) + ["exit"] * 5

    df_acc = pd.DataFrame({
        "account_id": account_ids,
        "display_name": [f"Account {i}" for i in range(num_accounts)],
        "account_type": ["SAVINGS"] * num_accounts,
        "opened_at": ["2026-01-01"] * num_accounts,
        "kyc_verified": [True] * num_accounts,
        "kyc_pan_hash": ["PAN_MOCK"] * num_accounts,
        "kyc_phone_hash": ["PH_MOCK"] * num_accounts,
        "kyc_address_hash": ["ADDR_MOCK"] * num_accounts,
        "declared_monthly_income": [50000.0] * num_accounts,
        "shared_network_tag": [None] * num_accounts,
        "device_id": [f"DEV_{i % 10}" for i in range(num_accounts)],
        "ip_address": ["192.168.1.1"] * num_accounts,
        "total_inflow": [100000.0] * num_accounts,
        "total_outflow": [90000.0] * num_accounts,
        "turnover_ratio": [0.9] * num_accounts,
        "retained_ratio": [0.1] * num_accounts,
        "age_days": [100] * num_accounts,
        "role": roles,
    })

    # Create connected ring topology edges
    rng = np.random.default_rng(12345)
    txns = []
    base_epoch = 1789640000

    for i in range(num_accounts - 1):
        amt = float(rng.uniform(10000, 50000))
        txns.append({
            "txn_id": f"TXN_{i:05d}",
            "timestamp": "2026-09-17T12:00:00+05:30",
            "epoch": base_epoch + i * 60,
            "source_account": account_ids[i],
            "dest_account": account_ids[i + 1],
            "amount": amt,
            "channel": "UPI",
            "device_id": f"DEV_{i % 10}",
            "ip_address": "192.168.1.1",
            "source_balance_after": 1000.0,
            "dest_balance_after": amt + 500.0,
        })

    # Add cross-edges to create graph density
    for _ in range(num_accounts // 2):
        u_idx = int(rng.integers(0, num_accounts))
        v_idx = int(rng.integers(0, num_accounts))
        if u_idx != v_idx:
            amt = float(rng.uniform(5000, 20000))
            txns.append({
                "txn_id": f"TXN_X_{len(txns)}",
                "timestamp": "2026-09-17T12:30:00+05:30",
                "epoch": base_epoch + 1800,
                "source_account": account_ids[u_idx],
                "dest_account": account_ids[v_idx],
                "amount": amt,
                "channel": "IMPS",
                "device_id": "DEV_X",
                "ip_address": "192.168.1.1",
                "source_balance_after": 2000.0,
                "dest_balance_after": amt + 1000.0,
            })

    df_txn = pd.DataFrame(txns)
    return FinancialGraph(df_acc, df_txn)


def test_quantum_walk_probability_conservation():
    """Verify that continuous-time quantum walk probabilities sum to 1.0 (+-1e-9) at every step."""
    fg = create_mock_financial_graph(20)
    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "TEST-RING-01",
        "members": [f"ACC_TEST_{i:04d}" for i in range(20)],
        "hub_account": "ACC_TEST_0000",
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data)
    result = sim.simulate(nodes, A, entry_acc, steps=60, time_step=0.1)

    q_probs = result["quantum_probs"]
    assert q_probs.shape == (60, len(nodes))

    for step_idx in range(60):
        total_p = float(np.sum(q_probs[step_idx, :]))
        assert abs(total_p - 1.0) < 1e-9, f"Quantum probability at step {step_idx} was {total_p}"


def test_classical_walk_mass_conservation():
    """Verify that classical Laplacian diffusion conserves total probability mass (+-1e-9)."""
    fg = create_mock_financial_graph(20)
    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "TEST-RING-01",
        "members": [f"ACC_TEST_{i:04d}" for i in range(20)],
        "hub_account": "ACC_TEST_0000",
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data)
    result = sim.simulate(nodes, A, entry_acc, steps=60, time_step=0.1)

    c_probs = result["classical_probs"]
    assert c_probs.shape == (60, len(nodes))

    for step_idx in range(60):
        total_p = float(np.sum(c_probs[step_idx, :]))
        assert abs(total_p - 1.0) < 1e-9, f"Classical mass at step {step_idx} was {total_p}"


def test_simulated_annealing_determinism():
    """Verify that the simulated annealing solver with a fixed seed produces identical output."""
    fg = create_mock_financial_graph(30)
    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "TEST-RING-01",
        "members": [f"ACC_TEST_{i:04d}" for i in range(30)],
        "hub_account": "ACC_TEST_0000",
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data)
    sim_res = sim.simulate(nodes, A, entry_acc, steps=40)
    flow = sim_res["flow_quantum"]

    opt = NetworkInterdictionOptimizer(fg)

    # Run 1
    frozen_1, stats_1 = opt.solve(nodes, flow, budget_K=5, seed=42)
    # Run 2
    frozen_2, stats_2 = opt.solve(nodes, flow, budget_K=5, seed=42)

    assert frozen_1 == frozen_2, "Solver was not deterministic with fixed seed 42"
    assert stats_1["final_energy"] == stats_2["final_energy"], "Energies diverged across identical runs"


def test_victim_protection_invariant():
    """Verify that victim accounts are NEVER in the freeze set under any budget."""
    fg = create_mock_financial_graph(30)
    victim_acc = "ACC_TEST_0000"
    assert fg.account_lookup[victim_acc]["role"] == "victim"

    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "TEST-RING-01",
        "members": [f"ACC_TEST_{i:04d}" for i in range(30)],
        "hub_account": victim_acc,
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data)
    sim_res = sim.simulate(nodes, A, entry_acc, steps=30)
    flow = sim_res["flow_quantum"]

    opt = NetworkInterdictionOptimizer(fg)

    # Test across multiple budgets up to high coverage
    for budget in [1, 3, 5, 10, 20]:
        frozen_accounts, _ = opt.solve(nodes, flow, budget_K=budget, seed=42)
        assert victim_acc not in frozen_accounts, f"VICTIM {victim_acc} was frozen under budget {budget}!"


def test_quantum_fidelity_self_is_one():
    """Verify that the quantum fidelity of any Ring DNA state with itself is exactly 1.0."""
    test_vectors = [
        [0.2, 0.6, 0.25, 0.2, 0.04, 0.96],
        [0.4, 0.6, 0.23, 0.13, 0.01, 0.99],
        [0.6, 0.4, 0.63, 0.6, 0.05, 0.90],
        [0.8, 0.4, 0.05, 0.1, 0.50, 0.50],
        [1.0, 1.0, 0.42, 0.33, 0.03, 0.97],
    ]

    for vec in test_vectors:
        fid = compute_quantum_fidelity(vec, vec)
        assert abs(fid - 1.0) < 1e-12, f"Self-fidelity for {vec} was {fid}, expected 1.0"


def test_benchmark_quantum_walk_under_one_second():
    """Benchmark: Continuous-time quantum walk on a 150-account graph completes in under 1 second."""
    fg = create_mock_financial_graph(150)
    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "BENCH-RING-150",
        "members": [f"ACC_TEST_{i:04d}" for i in range(150)],
        "hub_account": "ACC_TEST_0000",
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data, max_nodes=150)
    assert len(nodes) == 150

    start_time = time.perf_counter()
    res = sim.simulate(nodes, A, entry_acc, steps=60)
    elapsed = time.perf_counter() - start_time

    assert elapsed < 1.0, f"Quantum walk on 150 nodes took {elapsed:.3f} s (threshold: < 1.0 s)"
    assert res["quantum_probs"].shape == (60, 150)


def test_benchmark_interdiction_solver_under_two_seconds():
    """Benchmark: Simulated annealing solver on a 150-account graph completes in under 2 seconds."""
    fg = create_mock_financial_graph(150)
    sim = QuantumWalkSimulator(fg)
    ring_data = {
        "ring_id": "BENCH-RING-150",
        "members": [f"ACC_TEST_{i:04d}" for i in range(150)],
        "hub_account": "ACC_TEST_0000",
    }
    nodes, A, entry_acc, _ = sim.extract_ring_subgraph(ring_data, max_nodes=150)
    sim_res = sim.simulate(nodes, A, entry_acc, steps=60)
    flow = sim_res["flow_quantum"]

    opt = NetworkInterdictionOptimizer(fg)

    start_time = time.perf_counter()
    frozen_accounts, stats = opt.solve(nodes, flow, budget_K=10, seed=42)
    elapsed = time.perf_counter() - start_time

    assert elapsed < 2.0, f"Solver on 150 nodes took {elapsed:.3f} s (threshold: < 2.0 s)"
    assert len(frozen_accounts) > 0
