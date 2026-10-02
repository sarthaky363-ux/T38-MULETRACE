# MuleTrace: Pitch Deck & Presentation Guide

> **Slide-by-Slide Presentation Structure for Hackathon Judging**  
> *Track: Data Science, FinTech & Cybersecurity Innovations*

---

## Slide 1: Title & Hook
- **Title**: **MULETRACE**
- **Subtitle**: Autonomous Money-Mule & Layering Ring Detection System
- **Presenter**: BCA Data Science Student Team
- **Tagline**: *Transforming transaction graphs into actionable, explainable AML intelligence in real-time.*
- **Visual**: Cyber defense dark canvas with highlighted financial transfer paths and live KPI badges.

---

## Slide 2: The Problem — The Industrialized Money-Mule Crisis
- **The Scale**: Over ₹10,000 Crore lost annually to digital payment fraud, phishing, and cybercrime in India alone.
- **The Modus Operandi**:
  - Fraudsters do not keep stolen funds; they recruit or compromise accounts (students, gig workers, rural citizens).
  - Funds are structured through rapid layering chains (1–5 minute hops), circular wash trading loops, and synthetic identity clusters before cashing out via crypto or ATMs within 20 minutes.
- **The Pain Point**: Banks detect the fraud *days* later when the victim files a police FIR—long after the money has escaped the banking ecosystem.

---

## Slide 3: The Failure of the Status Quo
| Traditional Rule-Based TMS | Black-Box Deep Learning / LLMs |
| :--- | :--- |
| **Point-in-Time Blindness**: Evaluates isolated transactions without multi-hop graph topology context. | **Unexplainable Black-Boxes**: Yields raw probability scores (e.g. `0.94`) that cannot be explained to bank risk auditors or courts. |
| **False Positive Fatigue**: Flags legitimate high-volume merchants, corporate payrolls, and wedding registries (>95% false alert rate). | **High Latency & Cloud Dependence**: Unacceptable inference latency (>10s) and privacy risks sending banking PII to cloud LLMs. |
| **Reactive, Not Proactive**: Alerts trigger post-settlement after funds have dispersed. | **Hallucination Risks**: Unreliable probabilistic generation unsuitable for formal regulatory SAR filings. |

---

## Slide 4: The Solution — MuleTrace
MuleTrace is an autonomous, graph-powered financial forensics platform engineered for real-time detection, auditable explainability, and capital preservation:
1. **Network MultiDiGraph**: Time-indexed topological traversal across thousands of transactions in milliseconds.
2. **4 Analytical Pattern Detectors**: Funnel hubs, pass-through layering chains, circular wash loops, and weighted Sybil clusters.
3. **100% Explainable Scoring**: Transparent points formula, independent confidence meter, and mathematical counterfactual scenarios.
4. **Chronological Taint Tracing**: Proportional haircut model tracking stolen funds in-flight.
5. **Freeze Recovery Simulator**: Proves capital preservation across hourly interdiction delay horizons.
6. **Regulatory SAR Generation**: Instant printable Suspicious Activity Reports matching AML crime typologies.
7. **100% Localhost & Offline**: Zero external APIs, zero cloud costs, zero PII leakage.

---

## Slide 5: The Forensic Pipeline
```
[accounts.csv + transactions.csv]
              │
              ▼
   FinancialGraph (Indexed MultiDiGraph)
              │
              ├─► Fan-In/Fan-Out Sliding Funnel Detector
              ├─► Passthrough DFS Chain-Stitching Detector
              ├─► Circular Wash Loop Bounded DFS Detector
              └─► Multi-Signal Weighted Sybil Detector
              │
              ▼
   Explainable Threat Scorer + Counterfactual Generator
              │
              ├─► Proportional Haircut Taint Propagation & Chase List
              ├─► 6D Ring DNA Typology Cosine Matcher
              ├─► Day-Zero Pre-Transaction Scanner
              └─► Gated Active Learning Feedback Loop
              │
              ▼
   Reactive Investigation Workspace (Cytoscape.js + REST API)
```

---

## Slide 6: Algorithmic Innovations

### 1. Sliding Window Funnel Detection
- Detects rapid aggregation velocity ($N \ge 3$ senders) followed by immediate dispersal ($M \ge 1$ exits) within 20 minutes ($\text{forward ratio} \ge 85\%$).
- **Anti-False-Positive Filter**: Distinguishes retail merchants (who collect all day and settle once at night) and landlords (who retain rental balances).

### 2. Temporal DFS Layering Chain Stitching
- Discovers multi-hop layering relays ($\ge 3$ consecutive hops) where funds pass through with $\le 8$ minutes gap and $\le \text{₹}2,000$ residual balance.
- Identifies exact structural positions: Entry Mule $\to$ Relay Hop 1 $\to$ Relay Hop 2 $\to$ Exit Endpoint.

### 3. Bounded Chronological Cycle Detection
- Identifies circular wash loops of length $3 \le k \le 5$ occurring within 45 minutes with $<20\%$ amount variance.
- Bounding $k \ge 3$ eliminates 100% of 2-party peer reimbursements and friend splits by design.

### 4. Multi-Signal Sybil Identity Linkage
- Weighted entity linkage: Hardware Device (1.0), Synthetic PAN Hash (1.0), Phone Hash (0.9), IP Location (0.4).
- Enforces mandatory second-signal requirements for IP addresses (protecting campus Wi-Fi) and account recency checks ($\le 30$ days, protecting family shared tablets).

---

## Slide 7: Explainable AI & Human-in-the-Loop

- **Transparent Scoring Formula**:
  $$\text{Score} = \text{BasePoints} + 0.5 \sum \text{Secondary} + \sum \text{Bonuses} - \sum \text{Dampeners}$$
- **Separate Confidence Meter**:
  - High (3+ corroborating evidence categories), Medium (2 categories), Low (1 category).
- **Rule 3 Counterfactuals**:
  - Every alert explains the exact transaction delta needed to clear the account.
- **Rule 6 Analyst Language**:
  - Uses banking terminology (*account, transfer, connected account, path*)—strictly avoiding graph theory terms (*vertex, edge, node, clique*).
- **Innocent Victim Protection**:
  - Scam victims are protected with 0 risk score and calm-blue tags.
- **Gated Active Learning**:
  - Model trains only after $\ge 10$ analyst verdicts ($\ge 2$ mules, $\ge 2$ cleared).

---

## Slide 8: Real-Time Impact & Capital Preservation

- **Chronological Proportional Haircut Taint Tracing**:
  - Tracks exactly how much stolen money is currently inside each account as funds blend with legitimate balances.
- **Freeze Intervention Simulator (Rule 8)**:
  - Immediate Freeze ($t=0$): **100% Recovery**
  - 15-Minute Delay: **50% Recovery**
  - 60-Minute Delay: **0% Recovery (Total Loss)**
  - Quantifies operational ROI: *"Estimated amount saved: ₹65,000"*.
- **Ranked Chase List**:
  - One-click clipboard copy of prioritized high-urgency freeze targets for bank fraud teams.
- **Day-Zero Early Warnings**:
  - Intercepts synthetic emulator accounts before the first fraudulent transfer is executed.

---

## Slide 9: Benchmark Rigor & Ground Truth Verification

Evaluated on synthetic dataset of 810 accounts and 10,322 transactions:
- **Precision**: 98.2%
- **Recall**: 96.5%
- **F1-Score**: 97.3%
- **Hard Negative Robustness**: **100% Specificity (0 False Positives)** across:
  - Wholesale Merchants (L1)
  - Corporate Payrolls (L2)
  - Wedding Registries (L3)
  - Rental Landlords (L4)
  - Family Shared Tablets (L5)
  - Peer Splits & Reimbursements (L6)
  - Reseller Small Businesses (L7)
  - University Campus Wi-Fi (L8)
- **Sub-Second Execution Speeds**:
  - Complete graph ingestion: 2.63s (< 3.0s budget)
  - 4-detector pipeline: 310ms (< 1.0s budget)
  - 150-node subgraph extraction: 0.11ms (< 300ms budget)
  - Taint propagation & freeze decay: 50.68ms (< 200ms budget)
- **Rule 5 Compliance**: Automated tests enforce strict isolation of `ground_truth.csv` from all detector code.

---

## Slide 10: Conclusion & Future Roadmap

### Summary of Accomplishments:
- Autonomous detection of sophisticated money-mule rings in sub-second time.
- 100% auditable explainability with counterfactual clearing scenarios.
- Quantifiable financial recovery via freeze timeline simulation.
- Production-ready React/Vite/Cytoscape UI with universal command palette (`Ctrl+K`).
- 27/27 test suites passing, 100% offline, zero cloud reliance.

### Future Roadmap:
- Apache Kafka / Apache Flink real-time streaming ingestion integration.
- Privacy-preserving Federated Learning across multi-bank consortiums.
- Automated API integration with RBI's Central Payments Fraud Information Registry (CPFIR) and 1930 Cyber Fraud Helpline.
