# MuleTrace: Forensic Architecture & Algorithmic Methodology

MuleTrace is an autonomous financial crime investigation platform engineered specifically for detecting money-mule accounts, rapid pass-through layering chains, circular wash rings, and synthetic identity clusters in banking transfer networks.

This document details the underlying forensic algorithms, mathematical formulations, graph models, and scoring logic that power MuleTrace.

---

## 1. Network Representation & Graph Ingestion

MuleTrace represents financial transfer networks using a directed multigraph $G = (V, E)$ implemented over NetworkX `MultiDiGraph`:
- **Vertices ($V$)**: Bank accounts $u \in V$ enriched with KYC verification flags, synthetic tax identity hashes (PAN), hardware device fingerprints, IP locations, account creation age ($t_{\text{age}}$), declared monthly income, total historical inflow, total outflow, and computed turnover ratios.
- **Edges ($E$)**: Discrete financial transfers $e = (u, v, k) \in E$, where $u$ is the source account, $v$ is the destination account, $k$ is the unique transaction identifier (`txn_id`), carrying transfer amount $A_e \in \mathbb{R}^+$, transfer channel (e.g. UPI, NEFT, IMPS, RTGS), and integer Unix epoch seconds $t_e \in \mathbb{Z}^+$.

To guarantee sub-second algorithmic lookups, `FinancialGraph` maintains in-memory chronological indexes:
1. `in_txns[v]`: Transfers where $v = \text{dest}$, sorted by $t_e$.
2. `out_txns[u]`: Transfers where $u = \text{source}$, sorted by $t_e$.
3. Entity linkage inverted maps: `device_accounts[device_id]`, `pan_accounts[pan_hash]`, and `ip_accounts[ip_address]`.

---

## 2. Multi-Pattern Detection Engine

MuleTrace deploys four complementary analytical detectors operating concurrently. All thresholds are dynamic and externalized in `backend/config/thresholds.yaml`.

### 2.1 Funnel Aggregation & Dispersal (Fan-In / Fan-Out)
Money-mule hubs aggregate funds from multiple compromised sources or victims and rapidly disperse them toward cash-out endpoints or cryptocurrency OTC brokers.

- **Window Slicing**: Evaluates an aggregation window $\Delta t_{\text{in}} \le W_{\text{max}}$ (e.g. 15–30 minutes) and a subsequent dispersal window $\Delta t_{\text{out}} \le W_{\text{max}}$.
- **Forward-Ratio Formulation**:
  $$\text{Ratio}_{\text{forward}} = \frac{\sum_{e \in E_{\text{out}}} A_e}{\sum_{e \in E_{\text{in}}} A_e}$$
- **Threshold Criteria**:
  $$|S_{\text{senders}}| \ge N_{\text{min\_senders}} \quad \land \quad |S_{\text{receivers}}| \ge N_{\text{min\_receivers}} \quad \land \quad \text{Ratio}_{\text{forward}} \ge R_{\text{min\_forward}}$$
- **Hard Negative Safeguards**:
  - *Merchants & Payment Gateways*: Accumulate hundreds of retail credits during operating hours and settle in a single batch at night ($\Delta t > 8$ hours). Filtered out by the sliding velocity window.
  - *Corporate Payroll*: Executes massive fan-out from retained corporate revenue with negligible prior fan-in. Filtered out by zero antecedent fan-in ratio.
  - *Wedding Registries & Landlords*: Receive funds from multiple parties but retain balances rather than rapidly forwarding them ($\text{Ratio}_{\text{forward}} \ll 0.85$).

### 2.2 Temporal Pass-Through Layering Chains
Layering involves routing stolen funds through a sequence of intermediate relay accounts to obscure the money trail.

- **Single-Hop Relay Formulation**:
  For an account $u$, a transfer pair $(e_{\text{in}}, e_{\text{out}})$ qualifies as an illicit pass-through relay if:
  $$0 \le t_{e_{\text{out}}} - t_{e_{\text{in}}} \le \Delta t_{\text{gap\_max}} \quad (\le 8 \text{ minutes})$$
  $$\frac{A_{e_{\text{out}}}}{A_{e_{\text{in}}}} \ge R_{\text{pass\_min}} \quad (\ge 85\%)$$
  $$\text{Balance}_{\text{after}}(u) \le B_{\text{max\_residual}} \quad (\le \text{₹}2,000)$$
- **DFS Chain Stitching**:
  A depth-first search traverses consecutive relay pairs, assembling chains $\mathcal{C} = (u_1, u_2, \dots, u_k)$ where $k \ge 3$. Accounts are tagged by exact operational role: $u_1$ is Entry, $u_2 \dots u_{k-1}$ are Relays, and $u_k$ is Exit.
- **Hard Negative Safeguard**:
  - *Resellers & E-Commerce Merchants*: Legitimate peer resellers purchase goods and forward payments with hours or days of inspection delay ($t_{\text{gap}} \gg 8\text{m}$) and maintain substantial residual working capital.

### 2.3 Circular Wash Loops (Wash Trading)
Criminal networks route funds in closed loops to artificially fabricate transaction histories, defeat balance checks, or wash proceeds back to the ringleader.

- **Bounded Chronological DFS**:
  Identifies directed simple cycles $u_1 \to u_2 \to \dots \to u_k \to u_1$ subject to:
  $$3 \le k \le 5 \quad (\text{Cycle length bounded between 3 and 5 accounts})$$
  $$t_{\text{final}} - t_{\text{initial}} \le T_{\text{cycle\_max}} \quad (\le 45 \text{ minutes})$$
  $$\frac{\max_i(A_i) - \min_i(A_i)}{\max_i(A_i)} \le \epsilon_{\text{variance}} \quad (\le 20\%)$$
- **Hard Negative Safeguard**:
  - *Peer Reimbursements & Friend Expense Splits*: Legitimate two-party reimbursements (Alice pays Bob for dinner, Bob pays Alice next week) have $k = 2$. Enforcing $k \ge 3$ strictly prevents false positives on benign social transfers by design.

### 2.4 Multi-Signal Sybil Identity Linkage
Fraud syndicates create batches of mule accounts using mobile device emulators or synthetic identities.

- **Weighted Identity Match Score**:
  $$S(u, v) = w_{\text{dev}} \cdot \mathbb{I}(\text{dev}_u = \text{dev}_v) + w_{\text{pan}} \cdot \mathbb{I}(\text{pan}_u = \text{pan}_v) + w_{\text{phone}} \cdot \mathbb{I}(\text{phone}_u = \text{phone}_v) + w_{\text{ip}} \cdot \mathbb{I}(\text{ip}_u = \text{ip}_v)$$
  Where $w_{\text{dev}} = 1.0$, $w_{\text{pan}} = 1.0$, $w_{\text{phone}} = 0.9$, $w_{\text{ip}} = 0.4$.
- **Safeguards Against Over-Clustering**:
  - *Campus Wi-Fi & Corporate Proxies*: Setting `require_second_signal_for_ip: true` prevents clustering accounts based solely on a shared public IP address.
  - *Family Shared Tablets*: Shared devices must be combined with recent account creation ($\text{age} \le 30$ days). Long-tenured accounts sharing a household tablet are never grouped into synthetic fraud rings.

---

## 3. Explainable Risk Scoring & Counterfactuals

MuleTrace rejects uninterpretable black-box ML scoring in favor of an additive, auditable point-based scoring architecture.

### 3.1 Composite Threat Score Formula
For any account $u$:
$$\text{Score}(u) = \text{BasePoints}(u) + 0.5 \sum_{p \in \mathcal{P}_{\text{secondary}}} \text{BasePoints}(p) + \sum b_i - \sum d_j$$
Where:
- $\text{BasePoints} \in [35, 50]$ from the primary triggered detector.
- Secondary patterns contribute $50\%$ of their base points.
- Bonuses $b_i$: Drain velocity ($+15$), rapid dispersion ($+10$), dual device/PAN match ($+15$), turnover $> 50$ ($+10$), new account age $< 30$d ($+5$), multi-pattern synergy ($+20$).
- Dampeners $d_j$: Merchant turnover profiles, regular payroll signatures, long tenure ($>1$ year) with verified KYC.
- Clamped strictly: $\text{Score}(u) \in [0, 100]$.
- Categorized into bands: Critical ($\ge 70$), Medium ($40–69$), Low ($< 40$), Safe ($0$).

### 3.2 Victim Protection Invariant
When an account is classified as a source victim of fraud (e.g. fraudulent debit without subsequent laundering participation), its threat score is zeroed out:
$$\text{Score}_{\text{victim}} = 0.0, \quad \text{Band} = \text{'safe'}, \quad \text{Role} = \text{'victim'}$$
Victims are displayed with a protective calm-blue badge and excluded from punitive action lists.

### 3.3 Confidence Meter
Confidence is computed independently of the score magnitude based on empirical corroboration:
- **High**: $\ge 3$ distinct evidence categories (e.g. topological graph pattern + hardware fingerprint match + rapid drain ratio).
- **Medium**: 2 corroborating evidence categories.
- **Low**: 1 isolated trigger.

### 3.4 Automated Counterfactual Scenarios (Rule 3)
For every flagged account, the engine computes a mathematical delta describing the exact behavioral shift required to clear the alert:
> *"If the account retained at least 35% of incoming funds for over 4 hours instead of draining 96% within 3 minutes, its risk score would drop by 35 points into the Safe band."*

---

## 4. Taint Tracing & Freeze Intervention Simulation

### 4.1 Chronological Proportional Haircut Propagation
When an illicit transaction injects dirty capital into the network, funds mix with existing balances. MuleTrace tracks taint propagation chronologically:
$$\tau_{\text{out}} = A_e \cdot \min\left(1.0, \frac{\text{TaintedBalance}(u)}{\text{TotalBalance}(u)}\right)$$
- If the receiving account is an exit endpoint (ATM, crypto exchange), the flow is classified as escaped:
  $$\text{CashedOut} \mathrel{+}= \tau_{\text{out}}$$
- Conservation Invariant:
  $$\sum_{v \in V} \text{TaintedBalance}(v) + \text{CashedOut} \le \text{InitialTheft}$$

### 4.2 Freeze Intervention Curve (Rule 8)
Simulates capital preservation across delay horizons $t_{\text{freeze}} \in \{0, 5, 10, 15, 30, 60\}$ minutes:
$$\text{PreservedCapital}(t) = \text{InitialTheft} - \text{CashedOut}(t)$$
All freeze metrics carry the mandatory compliance notice:
> *"Estimated amount saved: ₹X. Synthetic demonstration data. Not a real case."*

---

## 5. Ring DNA & Typology Classification

MuleTrace extracts a normalized 6-dimensional forensic fingerprint vector $\vec{v} \in [0, 1]^6$ for every detected fraud ring:
1. **$v_1$ (Topology Structure)**: Fan-Out ($0.25$), Fan-In ($0.50$), Cycle ($0.75$), Layering Chain ($1.00$).
2. **$v_2$ (Syndicate Size)**: $\min(1.0, |V_{\text{ring}}| / 10)$.
3. **$v_3$ (Duration Velocity)**: $\max(0.0, 1.0 - \text{DurationMinutes} / 60.0)$.
4. **$v_4$ (Hop Gap Speed)**: $\max(0.0, 1.0 - \text{AvgGapMinutes} / 15.0)$.
5. **$v_5$ (Retained Ratio)**: $\text{VolumeRetained} / \text{VolumeInflow}$.
6. **$v_6$ (Drain Velocity)**: Speed of capital dispersion to terminal exits.

### Typology Cosine Matching
Matches $\vec{v}$ against known AML criminal typologies (e.g. Telegram Crypto Funnel, Metro ATM Mule Chain, Circular Wash Ring, Synthetic Mule Network) using cosine similarity:
$$\text{Similarity}(\vec{v}, \vec{w}) = \frac{\vec{v} \cdot \vec{w}}{\|\vec{v}\| \|\vec{w}\|}$$
Matches exceeding $70\%$ are classified with recommended operational interventions.

---

## 6. Active Learning Feedback & Day-Zero Warnings

### 6.1 Gated Active Learning Loop
Human analyst decisions (`confirmed_mule` vs. `cleared_benign`) feed an active learning loop:
- **Safety Gate**: Training is locked until $\ge 10$ verified labels are recorded, with $\ge 2$ positive and $\ge 2$ negative verdicts.
- **Model**: Regularized Logistic Regression trained on normalized velocity, turnover, and counterparty features.
- **Transparent Weights**: Feature coefficients are displayed to investigators, showing how human decisions adjust model sensitivity over time.

### 6.2 Day-Zero Pre-Transaction Early Warning
Monitors account opening metadata independently of transactions:
- Identifies newly created accounts ($\le 15$ days old) sharing device fingerprints or duplicate tax identifiers before any money moves.
- Issues preventative holds to intercept mule accounts before the first fraudulent transfer occurs.

---

## 7. MuleTrace Ω: Quantum-Inspired Classical Simulation

> **Honesty Notice**: *Simulated on a classical computer. Synthetic demonstration data. Not a real case.*
> All metrics and performance scores are computed live from data without hardcoded results or artificial speedup claims.

MuleTrace Ω is an exploratory physics-inspired analytical layer exploring how continuous-time quantum walks, binary quadratic network interdiction (QUBO), and quantum state fidelity can forecast and intercept fast-moving laundering networks.

### 7.1 Continuous-Time Quantum Walk (CTQW)
Continuous-time quantum walks model the coherent wave propagation of probability amplitudes across graph topologies:
- **Hamiltonian**: $H = A$, where $A$ is the symmetric weighted adjacency matrix of the ring subgraph (up to 150 accounts). Edge weights represent logarithmic financial capacity:
  $$A_{ij} = A_{ji} = \log(1 + \text{TotalTransferAmount}(i, j)) \quad (i \ne j), \quad A_{ii} = 0$$
- **Unitary Evolution**: The time-evolution operator $U(t)$ is computed via exact Hermitian spectral decomposition:
  $$H = V \Lambda V^\dagger \implies U(t) = \exp(-i H t) = V \exp(-i \Lambda t) V^\dagger$$
  where $\Lambda = \text{diag}(\lambda_1, \dots, \lambda_N)$ are the real eigenvalues and $V$ are the orthonormal eigenvectors computed via `numpy.linalg.eigh`.
- **Wavefunction & Probability**: Starting with localized amplitude $1$ on the initial theft entry account $s$ ($\psi(0) = e_s$):
  $$\psi(t) = U(t) \psi(0) = V (\exp(-i \Lambda t) \odot V[s, :]^T)$$
  The probability distribution over accounts at time $t$ is:
  $$p_i(t) = |\psi_i(t)|^2$$
  *Mathematical Invariant*: Unitary evolution strictly preserves norm, ensuring $\sum_{i=1}^N p_i(t) = 1.0 \pm 10^{-9}$ for all $t$.

### 7.2 Classical Laplacian Diffusion Baseline
For genuine, honest benchmarking, the quantum walk is directly compared against classical heat diffusion on the identical graph structure:
$$p(t) = \exp(-L \cdot t) \cdot p_0$$
where $L = D - A$ is the positive-semidefinite graph Laplacian ($D_{ii} = \sum_j A_{ij}$). Spectral solution:
$$L = V_L \Lambda_L V_L^T \implies p(t) = V_L (\exp(-\Lambda_L t) \odot V_L[s, :]^T)$$
*Mathematical Invariant*: Because $L \mathbf{1} = 0$, classical diffusion conserves total probability mass ($\sum_{i=1}^N p_i(t) = 1.0 \pm 10^{-9}$).

### 7.3 QUBO Network Interdiction & Victim Protection Invariant
Preemptive freezing of $K$ accounts is formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem:
$$\min_{x \in \{0, 1\}^N} E(x) = \lambda_1 \sum_{i=1}^N (1 - x_i) \cdot \text{flow}_i + \lambda_2 \sum_{i=1}^N x_i \cdot \text{innocence\_cost}_i + \mu \cdot \left(\sum_{i=1}^N x_i - K\right)^2$$
Where:
- $x_i = 1$ indicates freezing account $i$.
- $\text{flow}_i = \frac{1}{T} \sum_{t=0}^T p_i(t)$ is the time-integrated quantum walk probability.
- $\text{innocence\_cost}_i = \max(0.0, 1.0 - \text{RiskScore}_i / 100.0)$ penalizes false-positive disruption on low-risk customer accounts.
- **Victim Protection Invariant**: $x_{\text{victim}} \equiv 0$. Victim accounts are structurally constrained and can never be selected for freezing under any parameter configuration.
- **Deterministic Solver**: Solved using simulated annealing with a fixed seed (`seed = 42`) for 100% deterministic reproducibility.
- **Comparative Simulation**: Evaluated against the greedy Chase List using the chronological taint simulator, measuring:
  - *Estimated amount saved: ₹X* (Rule 8)
  - *Accounts frozen*
  - *Low-risk accounts frozen* (collateral damage)

### 7.4 Ring DNA Quantum State Fidelity
Comparing syndicate behavioral vectors using pure state transition fidelity:
$$F(|a\rangle, |b\rangle) = |\langle a | b \rangle|^2$$
Taking normalized unit states $\hat{a} = a / \|a\|_2$ from the 6D Ring DNA feature vectors:
$$\langle a | b \rangle = \hat{a} \cdot \hat{b} = \cos(\theta)$$
Since all Ring DNA feature dimensions (structure type, size, duration, hop gap, retained ratio, drain ratio) are strictly non-negative real numbers ($a_i \ge 0$), the inner product is non-negative and state fidelity simplifies to:
$$F(|a\rangle, |b\rangle) = (\cos \theta)^2$$
This provides quadratic contrast against weak correlations, separating true structural typologies from incidental look-alikes.

### 7.5 Theoretical Quantum Advantage & Physical Limitations
- **Theoretical Formulation**: On an ideal fault-tolerant quantum computer, continuous-time quantum walks can explore certain graph topologies with quadratic or exponential speedup over classical random walks (Childs et al., Farhi & Gutmann).
- **Physical Reality & Simulation Invariant**: The algorithms in MuleTrace Ω run entirely on a classical CPU using linear algebra (`numpy`). No actual quantum computer is accessed. In real-world physical architectures, loading classical transaction matrices into quantum registers via Quantum RAM (QRAM) remains an unsolved hardware engineering problem.

