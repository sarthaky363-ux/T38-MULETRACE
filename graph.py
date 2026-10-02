"""
MuleTrace Temporal Financial Graph Model
Constructs time-indexed NetworkX graph and provides sub-graph neighborhood queries for UI visualization.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
import pandas as pd


class FinancialGraph:
    """Time-aware MultiDiGraph modeling financial transactions and account entities."""

    def __init__(self, df_accounts: pd.DataFrame, df_transactions: pd.DataFrame):
        self.df_accounts = df_accounts.copy()
        self.df_transactions = df_transactions.copy()

        self.graph = nx.MultiDiGraph()
        self.account_lookup: Dict[str, Dict[str, Any]] = {}
        
        # Fast indexed lookup for detectors
        self.in_txns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.out_txns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Identity cluster indices
        self.device_accounts: Dict[str, Set[str]] = defaultdict(set)
        self.pan_accounts: Dict[str, Set[str]] = defaultdict(set)
        self.ip_accounts: Dict[str, Set[str]] = defaultdict(set)

        self._build_graph()

    def _build_graph(self):
        """Constructs the NetworkX MultiDiGraph and in-memory indexes."""
        # 1. Add Accounts (Nodes)
        for _, row in self.df_accounts.iterrows():
            acc_id = str(row["account_id"])
            node_data = {
                "account_id": acc_id,
                "display_name": str(row.get("display_name", acc_id)),
                "account_type": str(row.get("account_type", "SAVINGS")),
                "opened_at": str(row.get("opened_at", "")),
                "age_days": int(row.get("age_days", 0)),
                "kyc_verified": bool(row.get("kyc_verified", False)),
                "kyc_pan_hash": row.get("kyc_pan_hash"),
                "kyc_phone_hash": row.get("kyc_phone_hash"),
                "kyc_address_hash": row.get("kyc_address_hash"),
                "declared_monthly_income": float(row.get("declared_monthly_income", 0.0)),
                "device_id": row.get("device_id"),
                "ip_address": row.get("ip_address"),
                "total_inflow": float(row.get("total_inflow", 0.0)),
                "total_outflow": float(row.get("total_outflow", 0.0)),
                "inflow_count": int(row.get("inflow_count", 0)),
                "outflow_count": int(row.get("outflow_count", 0)),
                "turnover_ratio": float(row.get("turnover_ratio", 0.0)),
                "retained_ratio": float(row.get("retained_ratio", 0.0)),
                "risk_score": 0.0,
                "risk_band": "safe",
                "role": str(row.get("role", "member")),
                "flagged": False,
            }
            self.account_lookup[acc_id] = node_data
            self.graph.add_node(acc_id, **node_data)

            # Index shared identifiers
            if node_data["device_id"]:
                self.device_accounts[str(node_data["device_id"])].add(acc_id)
            if node_data["kyc_pan_hash"]:
                self.pan_accounts[str(node_data["kyc_pan_hash"])].add(acc_id)
            if node_data["ip_address"]:
                self.ip_accounts[str(node_data["ip_address"])].add(acc_id)

        # 2. Add Transactions (Edges)
        for _, row in self.df_transactions.iterrows():
            src = str(row["source_account"])
            dst = str(row["dest_account"])
            txn_id = str(row["txn_id"])
            amt = float(row["amount"])
            ts = str(row["timestamp"])
            epoch = int(row["epoch"])
            channel = str(row.get("channel", "UPI"))

            edge_data = {
                "txn_id": txn_id,
                "amount": amt,
                "timestamp": ts,
                "epoch": epoch,
                "channel": channel,
                "device_id": row.get("device_id"),
                "ip_address": row.get("ip_address"),
                "source_balance_after": float(row.get("source_balance_after", 0.0)),
                "dest_balance_after": float(row.get("dest_balance_after", 0.0)),
                "source": src,
                "dest": dst,
            }

            self.graph.add_edge(src, dst, key=txn_id, **edge_data)
            self.out_txns[src].append(edge_data)
            self.in_txns[dst].append(edge_data)

        # Ensure in/out txn lists are sorted chronologically
        for acc in self.in_txns:
            self.in_txns[acc].sort(key=lambda x: x["epoch"])
        for acc in self.out_txns:
            self.out_txns[acc].sort(key=lambda x: x["epoch"])

    def get_subgraph(
        self,
        center_id: Optional[str] = None,
        hops: int = 1,
        max_nodes: int = 150
    ) -> Dict[str, Any]:
        """
        Extracts egocentric or high-risk neighborhood sub-graph for Cytoscape.js canvas.
        Caps at max_nodes to ensure smooth 60fps rendering.
        """
        selected_nodes: Set[str] = set()

        if center_id and center_id in self.graph:
            # BFS neighborhood expansion up to `hops` hops
            current_layer = {center_id}
            selected_nodes.add(center_id)
            for _ in range(hops):
                next_layer = set()
                for n in current_layer:
                    successors = set(self.graph.successors(n))
                    predecessors = set(self.graph.predecessors(n))
                    next_layer.update(successors | predecessors)
                new_nodes = next_layer - selected_nodes
                if len(selected_nodes) + len(new_nodes) > max_nodes:
                    # Add top nodes by transfer volume
                    sorted_new = sorted(
                        new_nodes,
                        key=lambda x: self.graph.nodes[x].get("total_inflow", 0.0) + self.graph.nodes[x].get("total_outflow", 0.0),
                        reverse=True
                    )
                    remaining_slots = max_nodes - len(selected_nodes)
                    selected_nodes.update(sorted_new[:remaining_slots])
                    break
                else:
                    selected_nodes.update(new_nodes)
                    current_layer = new_nodes
                if len(selected_nodes) >= max_nodes:
                    break
        else:
            # Default view: pick top active / highest risk nodes up to max_nodes
            sorted_nodes = sorted(
                self.graph.nodes(),
                key=lambda x: (
                    self.graph.nodes[x].get("risk_score", 0.0),
                    self.graph.nodes[x].get("total_inflow", 0.0) + self.graph.nodes[x].get("total_outflow", 0.0)
                ),
                reverse=True
            )
            selected_nodes = set(sorted_nodes[:max_nodes])

        # Extract induced subgraph nodes and edges
        sub_nodes = []
        for n in selected_nodes:
            d = dict(self.graph.nodes[n])
            sub_nodes.append({
                "data": {
                    "id": n,
                    "label": d.get("display_name", n),
                    "account_type": d.get("account_type", "SAVINGS"),
                    "risk_score": round(d.get("risk_score", 0.0), 1),
                    "risk_band": d.get("risk_band", "safe"),
                    "role": d.get("role", "member"),
                    "kyc_verified": d.get("kyc_verified", False),
                    "total_inflow": d.get("total_inflow", 0.0),
                    "total_outflow": d.get("total_outflow", 0.0),
                    "turnover_ratio": d.get("turnover_ratio", 0.0),
                    "flagged": d.get("flagged", False),
                }
            })

        sub_edges = []
        # Find all edges between selected nodes
        for u in selected_nodes:
            for v in self.graph.successors(u):
                if v in selected_nodes:
                    for key, e_data in self.graph.get_edge_data(u, v).items():
                        sub_edges.append({
                            "data": {
                                "id": f"{e_data['txn_id']}",
                                "source": u,
                                "target": v,
                                "amount": e_data["amount"],
                                "channel": e_data["channel"],
                                "timestamp": e_data["timestamp"],
                                "tainted": e_data.get("tainted", False),
                            }
                        })

        return {
            "nodes": sub_nodes,
            "edges": sub_edges,
            "center": center_id,
            "total_nodes": len(sub_nodes),
            "total_edges": len(sub_edges),
        }
