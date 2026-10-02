"""Test ingestion pipeline and financial graph construction."""
from pathlib import Path
import pytest
from backend.ingest import load_accounts, load_transactions, compute_account_summaries
from backend.graph import FinancialGraph


def test_ingest_and_graph_construction():
    """Verify loading demo data and building FinancialGraph."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    df_accs_raw = load_accounts(demo_dir / "accounts.csv")
    df_txns = load_transactions(demo_dir / "transactions.csv")
    df_accs = compute_account_summaries(df_accs_raw, df_txns)

    assert len(df_accs) == 810
    assert 7000 <= len(df_txns) <= 12000
    assert "epoch" in df_txns.columns
    assert "total_inflow" in df_accs.columns
    assert "turnover_ratio" in df_accs.columns

    # Build graph
    fg = FinancialGraph(df_accs, df_txns)
    assert fg.graph.number_of_nodes() == len(df_accs)
    assert fg.graph.number_of_edges() == len(df_txns)

    # Check indices
    assert len(fg.device_accounts["DEV_EMU_9901"]) == 4  # R4 Sybils share this device
    assert "ACC_MULE_FAN01" in fg.in_txns
    assert len(fg.in_txns["ACC_MULE_FAN01"]) >= 5


def test_subgraph_extraction():
    """Verify sub-graph queries produce valid Cytoscape schema and respect node caps."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    demo_dir = root_dir / "data" / "demo"

    df_accs = compute_account_summaries(
        load_accounts(demo_dir / "accounts.csv"),
        load_transactions(demo_dir / "transactions.csv")
    )
    df_txns = load_transactions(demo_dir / "transactions.csv")
    fg = FinancialGraph(df_accs, df_txns)

    # Egocentric query for R1 Hub
    res = fg.get_subgraph(center_id="ACC_MULE_FAN01", hops=1, max_nodes=50)
    assert "nodes" in res
    assert "edges" in res
    assert res["total_nodes"] <= 50
    assert res["center"] == "ACC_MULE_FAN01"

    # Verify node structure
    for node in res["nodes"]:
        data = node["data"]
        assert "id" in data
        assert "label" in data
        assert "risk_score" in data
        assert "role" in data

    # Verify edge structure
    for edge in res["edges"]:
        data = edge["data"]
        assert "id" in data
        assert "source" in data
        assert "target" in data
        assert "amount" in data
