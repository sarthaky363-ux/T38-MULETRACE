"""
MuleTrace Fan-In / Fan-Out (Funnel Hub) Detector
Detects rapid aggregation from multiple counterparties followed by swift outbound dispersal.
"""

from typing import Any, Dict, List, Optional
from backend.graph import FinancialGraph


def format_inr(amount: float) -> str:
    """Formats a numeric amount into Indian Rupee representation (e.g. ₹4,05,000)."""
    amt_int = int(round(amount))
    s = str(amt_int)
    if len(s) <= 3:
        return f"₹{s}"
    last_three = s[-3:]
    remaining = s[:-3]
    parts = []
    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        parts.insert(0, remaining)
    return f"₹{','.join(parts)},{last_three}"


class FanInOutDetector:
    """Detects rapid money-mule aggregation and dispersal structures."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        # Default balanced thresholds
        self.window_sec = (thresholds.get("window_min", 45) if thresholds else 45) * 60
        self.min_senders = thresholds.get("min_senders", 4) if thresholds else 4
        self.min_inflow = thresholds.get("min_inflow", 50000.0) if thresholds else 50000.0
        self.min_receivers = thresholds.get("min_receivers", 1) if thresholds else 1
        self.forward_ratio = thresholds.get("forward_ratio", 0.80) if thresholds else 0.80

    def detect(self, fg: FinancialGraph) -> List[Dict[str, Any]]:
        """
        Scans all accounts in fg for fan-in/fan-out funnel patterns.
        Returns list of structured hit dictionaries.
        """
        hits: List[Dict[str, Any]] = []

        for acc_id, in_txns in fg.in_txns.items():
            if len(in_txns) < self.min_senders:
                continue

            # Slide window over incoming transactions
            n_in = len(in_txns)
            for i in range(n_in):
                w_start_epoch = in_txns[i]["epoch"]
                w_end_epoch = w_start_epoch + self.window_sec

                window_in_txns = []
                distinct_senders = set()
                total_inflow = 0.0

                for j in range(i, n_in):
                    t = in_txns[j]
                    if t["epoch"] > w_end_epoch:
                        break
                    src = t["source"]
                    if src != acc_id:
                        window_in_txns.append(t)
                        distinct_senders.add(src)
                        total_inflow += t["amount"]

                if len(distinct_senders) < self.min_senders or total_inflow < self.min_inflow:
                    continue

                # Inflow qualification met. Now evaluate outflows within window from first inflow
                # Outflow window extends up to window_sec after the last inflow in the cluster
                last_in_epoch = window_in_txns[-1]["epoch"]
                out_window_end = last_in_epoch + self.window_sec

                out_txns_acc = fg.out_txns.get(acc_id, [])
                matching_out_txns = [
                    t for t in out_txns_acc
                    if w_start_epoch <= t["epoch"] <= out_window_end
                ]

                total_outflow = sum(t["amount"] for t in matching_out_txns)
                distinct_receivers = {t["dest"] for t in matching_out_txns if t["dest"] != acc_id}

                forwarded_ratio = (total_outflow / total_inflow) if total_inflow > 0 else 0.0

                if len(distinct_receivers) >= self.min_receivers and forwarded_ratio >= self.forward_ratio:
                    involved_txn_ids = [t["txn_id"] for t in window_in_txns] + [t["txn_id"] for t in matching_out_txns]
                    first_ts = window_in_txns[0]["timestamp"]
                    last_ts = matching_out_txns[-1]["timestamp"] if matching_out_txns else window_in_txns[-1]["timestamp"]
                    window_duration_min = round((matching_out_txns[-1]["epoch"] - window_in_txns[0]["epoch"]) / 60.0, 1) if matching_out_txns else round((window_in_txns[-1]["epoch"] - window_in_txns[0]["epoch"]) / 60.0, 1)

                    hit = {
                        "account": acc_id,
                        "pattern": "fan_in_out",
                        "ring_key": f"RING_FIO_{acc_id}_{w_start_epoch}",
                        "role": "hub",
                        "evidence": {
                            "window_minutes": window_duration_min,
                            "senders_count": len(distinct_senders),
                            "total_inflow": round(total_inflow, 2),
                            "receivers_count": len(distinct_receivers),
                            "total_outflow": round(total_outflow, 2),
                            "forward_ratio": round(forwarded_ratio, 3),
                            "senders": list(distinct_senders),
                            "receivers": list(distinct_receivers),
                        },
                        "txn_ids": involved_txn_ids,
                        "first_ts": first_ts,
                        "last_ts": last_ts,
                    }
                    hits.append(hit)
                    # Skip ahead to avoid duplicate sliding-window hits for same account cluster
                    break

        return hits

    def explain(self, hit: Dict[str, Any]) -> Dict[str, str]:
        """
        Produces compliance-grade, plain-language and technical explanations.
        Follows Rule 3 (explainability) & Rule 6 (banking vocabulary, never graph jargon).
        """
        ev = hit["evidence"]
        inflow_fmt = format_inr(ev["total_inflow"])
        outflow_fmt = format_inr(ev["total_outflow"])
        pct_fmt = f"{ev['forward_ratio'] * 100:.1f}%"
        win_min = ev["window_minutes"]
        senders = ev["senders_count"]
        receivers = ev["receivers_count"]

        plain_reason = (
            f"This account acted as an aggregation hub, receiving {inflow_fmt} from {senders} different accounts "
            f"within {win_min} minutes and rapidly forwarding {outflow_fmt} ({pct_fmt}) to "
            f"{receivers} connected account{'s' if receivers > 1 else ''}."
        )

        technical_reason = (
            f"Fan-in/fan-out funnel pattern detected. Window: {win_min}m. Inflow: {inflow_fmt} across {senders} "
            f"senders (threshold: >={self.min_senders}). Forwarded: {pct_fmt} to {receivers} receivers "
            f"(threshold: >={self.forward_ratio * 100:.0f}%)."
        )

        counterfactual = (
            f"If the forwarded ratio were below {self.forward_ratio * 100:.0f}% or if incoming transfers "
            f"were dispersed over more than {self.window_sec // 60} minutes, this account would not be flagged."
        )

        return {
            "plain_reason": plain_reason,
            "technical_reason": technical_reason,
            "counterfactual": counterfactual,
        }
