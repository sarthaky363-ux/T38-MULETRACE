"""
MuleTrace Sybil / Device / IP / KYC Cluster Detector
Detects synthetic identity farms and multi-account clusters sharing hardware fingerprints, PANs, and IPs.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from backend.graph import FinancialGraph


class SybilDetector:
    """Detects multi-account identity clusters and synthetic account farms."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.min_group = thresholds.get("min_group", 3) if thresholds else 3
        self.max_age_days = thresholds.get("max_age_days", 30) if thresholds else 30
        self.require_second_signal_for_ip = thresholds.get("require_second_signal_for_ip", True) if thresholds else True

    def detect(self, fg: FinancialGraph) -> List[Dict[str, Any]]:
        """
        Scans all accounts in fg for shared identity attributes.
        Returns list of structured hit dictionaries for qualifying sybil cluster accounts.
        """
        # Step 1: Build identity linkage graph
        # Accounts share a link if they share device_id, pan_hash, phone_hash, or IP
        identity_graph = nx.Graph()

        # Add all accounts as nodes
        for acc_id, attrs in fg.account_lookup.items():
            identity_graph.add_node(acc_id, **attrs)

        # Attribute linkage weights
        # device: 1.0, pan: 1.0, phone: 0.9, address: 0.5, ip: 0.4
        attribute_groups = [
            ("device_id", fg.device_accounts, 1.0, "device"),
            ("kyc_pan_hash", fg.pan_accounts, 1.0, "pan"),
            ("ip_address", fg.ip_accounts, 0.4, "ip"),
        ]

        # Inverted index for phone & address
        phone_accounts = defaultdict(set)
        address_accounts = defaultdict(set)
        for acc_id, attrs in fg.account_lookup.items():
            if attrs.get("kyc_phone_hash"):
                phone_accounts[attrs["kyc_phone_hash"]].add(acc_id)
            if attrs.get("kyc_address_hash"):
                address_accounts[attrs["kyc_address_hash"]].add(acc_id)

        attribute_groups.append(("kyc_phone_hash", phone_accounts, 0.9, "phone"))
        attribute_groups.append(("kyc_address_hash", address_accounts, 0.5, "address"))

        # Build pairwise links
        for attr_name, acc_map, weight, signal_name in attribute_groups:
            for attr_val, members in acc_map.items():
                if not attr_val or len(members) < 2:
                    continue
                # Add edges between all members sharing this attribute
                mem_list = list(members)
                for i in range(len(mem_list)):
                    for j in range(i + 1, len(mem_list)):
                        u, v = mem_list[i], mem_list[j]
                        if identity_graph.has_edge(u, v):
                            identity_graph[u][v]["weight"] += weight
                            identity_graph[u][v]["signals"].add(signal_name)
                            identity_graph[u][v]["attributes"][attr_name] = attr_val
                        else:
                            identity_graph.add_edge(
                                u, v,
                                weight=weight,
                                signals={signal_name},
                                attributes={attr_name: attr_val}
                            )

        # Step 2: Evaluate connected components (identity clusters)
        hits: List[Dict[str, Any]] = []

        for component in nx.connected_components(identity_graph):
            if len(component) < self.min_group:
                continue

            # Subgraph induced by component
            sub_g = identity_graph.subgraph(component)

            # Filter 1: Check IP-alone rule
            # If all edges in component only have the "ip" signal and require_second_signal_for_ip is True, ignore!
            all_signals = set()
            for u, v, data in sub_g.edges(data=True):
                all_signals.update(data.get("signals", set()))

            if self.require_second_signal_for_ip and all_signals == {"ip"}:
                # Discard cluster: pure shared IP without any hardware or KYC corroboration (e.g. campus Wi-Fi)
                continue

            # Filter 2: Account age / recency check
            # Real sybil clusters consist of newly opened burner accounts
            member_attrs = [fg.account_lookup[acc] for acc in component]
            new_accounts = [acc for acc, d in zip(component, member_attrs) if d.get("age_days", 999) <= self.max_age_days]

            if len(new_accounts) < self.min_group:
                # Discard cluster: accounts are aged/established (e.g. family sharing an iPad for years)
                continue

            # Qualifying Sybil Cluster identified!
            cluster_list = sorted(list(component))
            avg_age = round(sum(d.get("age_days", 0) for d in member_attrs) / len(member_attrs), 1)
            shared_devices = {d.get("device_id") for d in member_attrs if d.get("device_id")}
            shared_pans = {d.get("kyc_pan_hash") for d in member_attrs if d.get("kyc_pan_hash")}
            shared_ips = {d.get("ip_address") for d in member_attrs if d.get("ip_address")}

            # Collect any transaction IDs between or involving these accounts
            cluster_txns = []
            for acc in cluster_list:
                for t in fg.in_txns.get(acc, []):
                    if t["source"] in component:
                        cluster_txns.append(t["txn_id"])

            first_opened = min(d.get("opened_at", "") for d in member_attrs)
            last_opened = max(d.get("opened_at", "") for d in member_attrs)
            ring_key = f"RING_SYBIL_{cluster_list[0]}"

            for acc in cluster_list:
                acc_data = fg.account_lookup[acc]
                hit = {
                    "account": acc,
                    "pattern": "sybil",
                    "ring_key": ring_key,
                    "role": "mule",
                    "evidence": {
                        "cluster_size": len(cluster_list),
                        "cluster_accounts": cluster_list,
                        "avg_age_days": avg_age,
                        "account_age_days": acc_data.get("age_days", 0),
                        "shared_signals": list(all_signals),
                        "shared_device": list(shared_devices)[0] if len(shared_devices) == 1 else "multiple",
                        "shared_pan": list(shared_pans)[0] if len(shared_pans) == 1 else "multiple",
                        "shared_ip": list(shared_ips)[0] if len(shared_ips) == 1 else "multiple",
                    },
                    "txn_ids": cluster_txns,
                    "first_ts": first_opened,
                    "last_ts": last_opened,
                }
                hits.append(hit)

        return hits

    def explain(self, hit: Dict[str, Any]) -> Dict[str, str]:
        """
        Produces compliance-grade, plain-language and technical explanations.
        Adheres to Rule 3 (explainability) & Rule 6 (banking vocabulary, never graph jargon).
        """
        ev = hit["evidence"]
        size = ev["cluster_size"]
        age = ev["account_age_days"]
        sig_list = ", ".join(ev["shared_signals"])

        signals_desc = []
        if ev.get("shared_device") and ev["shared_device"] != "multiple":
            signals_desc.append(f"hardware device {ev['shared_device']}")
        if ev.get("shared_pan") and ev["shared_pan"] != "multiple":
            signals_desc.append(f"PAN tax identifier {ev['shared_pan']}")
        if ev.get("shared_ip") and ev["shared_ip"] != "multiple":
            signals_desc.append(f"IP address {ev['shared_ip']}")

        shared_str = ", ".join(signals_desc) if signals_desc else sig_list

        plain_reason = (
            f"This account is part of a {size}-account synthetic identity cluster. "
            f"All connected accounts were opened within the last {self.max_age_days} days (this account is {age} days old) "
            f"and share the same {shared_str}."
        )

        technical_reason = (
            f"Sybil identity farm detected. Cluster size: {size} accounts (threshold: >={self.min_group}). "
            f"Account age: {age} days (threshold: <={self.max_age_days}d). "
            f"Corroborated identity signals: {sig_list}."
        )

        counterfactual = (
            f"If this account were older than {self.max_age_days} days or did not share hardware device fingerprints "
            f"and KYC tax identifiers with at least {self.min_group - 1} other accounts, this cluster would not be flagged."
        )

        return {
            "plain_reason": plain_reason,
            "technical_reason": technical_reason,
            "counterfactual": counterfactual,
        }
