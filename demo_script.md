# MuleTrace: 3-Minute Hackathon Demo Script

> **Target Audience**: Hackathon Judges, BCA Data Science Evaluators, Financial Crime / AML Domain Experts.  
> **Presenter Persona**: BCA Data Science Student presenting an autonomous financial crime investigation platform.  
> **Total Time Budget**: 3 minutes (180 seconds) + 1-2 minutes Q&A.

---

## Stage Setup Checklist Before Pitching

1. Start both servers: Run `.\run.ps1` or `start.bat`.
2. Open browser: Navigate to `http://localhost:5173`.
3. Press `P` on your keyboard to activate **Presenter Mode** (high contrast, clear fonts for projectors).
4. Verify offline indicator in header says: `● 100% LOCALHOST OFFLINE`.
5. Ensure keyboard shortcuts are active: `J`/`K` for alerts, `Space` for replay, `Ctrl+K` for command search.

---

## Second-by-Second Presentation Script

```
0:00 ── 0:30 │ 1. The Hook: The ₹10,000 Crore Money-Mule Crisis
0:30 ── 1:00 │ 2. Live Investigation & Explainable AI
1:00 ── 1:45 │ 3. Forensic Taint Replay & Real-Time Freeze Simulation
1:45 ── 2:15 │ 4. 6D Ring DNA Syndicate Autopsies & Regulatory SAR
2:15 ── 3:00 │ 5. Data Science Rigor, Benchmark Metrics & Conclusion
```

---

### Phase 1: The Hook — The High-Velocity Money-Mule Crisis (0:00 – 0:30)

**[Action]**: Stand with hands visible, showing the MuleTrace Command Center Ribbon on screen.

**[Speaker Dialogue]**:
> "Good morning, respected judges. In 2026, real-time digital payments like UPI and IMPS move money in seconds. But financial crime moves just as fast.
>
> When victims fall prey to phishing or cyber scams, the stolen money isn't kept in one place. It is routed through a web of compromised student and rural bank accounts called **money mules**—bouncing through rapid layering chains, circular wash trading loops, and synthetic identity clusters before escaping into cryptocurrency exchanges or ATM cash-outs within 15 minutes.
>
> Traditional bank rule engines fail because they look at isolated transactions. Machine learning black-boxes fail because compliance officers cannot explain a raw probability score to a regulator.
>
> That is why we built **MuleTrace**: an autonomous, real-time forensic investigation platform that combines graph topology, explainable threat scoring, chronological taint propagation, and syndication typology matching—running 100% offline on localhost with zero external dependencies."

---

### Phase 2: Live Investigation & Explainable AI (0:30 – 1:00)

**[Action]**: Press `J` on the keyboard to select the top Critical alert in the left Alert Queue. The Cytoscape graph immediately focuses on `ACC-101` in a 2-hop concentric view, and the right Inspector Drawer opens.

**[Speaker Dialogue]**:
> "Let’s dive into a live incident. On our screen, MuleTrace ingested over 10,000 transactions across 810 accounts in sub-second time.
>
> Notice our visual network canvas. Instead of confusing network hairballs, every account has a geometric role: **Hexagons** are aggregation hubs, **Rectangles** are pass-through relays, **Diamonds** are exit cash-out endpoints, and **Rhombuses** are innocent victims.
>
> Look at this highlighted account: `ACC-101`. MuleTrace assigned it a Threat Score of **88 out of 100 (Critical)** with High Confidence.
>
> But we don't just give a score. Look at our **Explainable Forensic Justification**: in pure banking terms—without any confusing graph jargon—it shows that this account aggregated ₹4,05,000 from 6 distinct senders within 18 minutes and drained 96% of the capital within 4 minutes.
>
> Even more powerful is our **Counterfactual Scenario**: MuleTrace computes mathematically what would clear the alert: *If this account retained at least 35% of incoming funds for over 4 hours, its score would drop into the Safe band.* That gives compliance officers instant evidentiary clarity."

---

### Phase 3: Temporal Taint Replay & Freeze Simulation (1:00 – 1:45)

**[Action]**: Click **"Replay Flows"** in the Inspector Drawer. The floating Timeline Scrubber appears at the bottom. Press `Spacebar` to start temporal playback.

**[Speaker Dialogue]**:
> "Now, how did the stolen money move? I’ll click **Replay Flows** and press `Space`.
>
> Watch our chronological timeline scrubber. MuleTrace performs a mathematical proportional haircut taint trace. As the scrubber steps through timestamps, you can see the red tainted capital flowing from victim to entry mule, bouncing across intermediate relays, and dispersing toward terminal cashout endpoints.
>
> But catching the crime after money is gone is useless. What matters is **Capital Preservation**.
>
> I’ll open our **Freeze Intervention Simulator**."

**[Action]**: Click **"Freeze Simulation"**. The Freeze Modal opens displaying the recovery decay curve.

**[Speaker Dialogue]**:
> "Here, our algorithms simulate what happens across intervention horizons. If our bank's automated fraud defense freezes the hub in real-time at $t=0$, **100% of the capital—₹1,00,000—is preserved**.
>
> If the team waits 15 minutes, recovery drops to 50%. After 60 minutes, the money is completely cashed out.
>
> As per Rule 8, our system explicitly computes the estimated money saved: **₹65,000 preserved**, providing quantifiable ROI for fraud operations."

---

### Phase 4: 6D Ring DNA & Regulatory SAR Generation (1:45 – 2:15)

**[Action]**: Press `Escape` to close modal. Click on **"RINGS"** in the top navigation bar (or press `Ctrl+K` and type `rings` + Enter).

**[Speaker Dialogue]**:
> "Next, let’s examine syndicate syndication. In our **Fraud Rings Screen**, MuleTrace clusters related mule accounts and extracts a **6-Dimensional Ring DNA vector** capturing structural topology, syndicate size, duration velocity, hop speed, retention ratio, and drain velocity.
>
> Using cosine similarity, it automatically matches the ring against known AML typologies: this ring is a **97.4% match to the Telegram Crypto Funnel typology**.
>
> And when it's time to report to law enforcement or the Financial Intelligence Unit, compliance officers don't spend hours writing reports.
>
> I’ll click **Regulatory SAR**."

**[Action]**: Click **"Regulatory SAR"** button. The formal Suspicious Activity Report dossier opens in printable paper format.

**[Speaker Dialogue]**:
> "With one click, MuleTrace generates a complete, printable **Suspicious Activity Report (SAR)**—with executive narrative, subject accounts, hardware IMEI fingerprints, and chronological transfer ledgers, complete with our synthetic demonstration disclaimer."

---

### Phase 5: Data Science Rigor & Benchmark Validation (2:15 – 3:00)

**[Action]**: Press `Escape`. Click on **"LAB"** in the top navigation bar. Show the Benchmark Confusion Matrix and Hard Negative Robustness table.

**[Speaker Dialogue]**:
> "Finally, let's address the most critical question in Data Science: **How do we know it works, and how does it handle false positives?**
>
> Here in our **Forensic Lab Screen**, we evaluate our detectors against isolated ground truth data. Notice our strict architectural guarantee: following Rule 5, ground truth is strictly isolated for offline post-detection evaluation and is never accessible to detectors during runtime.
>
> Look at our benchmark results:
> - **Precision**: 98.2%
> - **Recall**: 96.5%
> - **F1-Score**: 97.3%
>
> And look at our **Hard Negative Robustness Stress-Test**:
> We tested our algorithms against 8 real-world legitimate scenarios that fool standard systems—wholesale merchants, corporate payroll, wedding registries, rental landlords, family shared tablets, and university campus Wi-Fi.
>
> Result: **Zero false positives across all legitimate hard negatives. 100% specificity.**
>
> In our **Interdiction Chase List**, compliance officers can copy the ranked freeze target list to their clipboard with a single click, while our **Day-Zero Pre-Transaction Scanner** catches emulator clusters before money even moves.
>
> In conclusion: MuleTrace delivers high-velocity detection, 100% explainability, verified mathematical rigor, and real-time capital preservation—all running locally in under 3 seconds.
>
> Thank you, and we welcome your questions!"

---

## MuleTrace Ω: Dedicated 90-Second Stage Segment (Advanced Track)

> **Context**: Use this segment when presenting to technical evaluators, mathematics faculty, or innovation track judges to showcase physics-inspired simulation and future AML horizons.  
> **Target Duration**: Exactly 90 seconds.  
> **Key Shortcut**: Press `Ctrl+K` and select **"Go to MuleTrace Ω Simulation"** (or click the **"MuleTrace Ω"** tab).

```
0:00 ── 0:25 │ Step 1: Continuous-Time Quantum Walk vs. Classical Diffusion
0:25 ── 0:50 │ Step 2: Binary Quadratic Interdiction (QUBO) & Freeze Comparison
0:50 ── 1:10 │ Step 3: Ring DNA Quantum State Fidelity (cos²θ)
1:10 ── 1:30 │ Step 4: The 27-Qubit Horizon & Adversarial Arms Race
```

### 1. Where Will the Money Go? — CTQW vs. Classical Diffusion (0:00 – 0:25)

**[Action]**: Click the **MuleTrace Ω** tab in the header. Show the two Cytoscape panes side by side. Drag the shared time slider from $t=0$ to $t=3.0\text{s}$, or click **Play**.

**[Speaker Dialogue]**:
> "Now, respected judges, let’s look into the future with **MuleTrace Ω**: our quantum-inspired simulation layer.
>
> *First, an honesty disclaimer: this runs as a classical simulation on synthetic data. No real quantum computer is used.*
>
> Here we ask: *What if we could see where stolen money will go before it gets there?*
>
> On the left is classical heat diffusion. On the right is a **Continuous-Time Quantum Walk**, where the Hamiltonian equals the ring's logarithmic adjacency matrix, solved via Hermitian eigendecomposition.
>
> Watch as probability amplitudes interfere. The quantum walk forecasts exit cash-out accounts with **75% overlap against real exits** from our taint trace, while classical diffusion spreads uniformly and lags behind. Both strictly conserve total mass within $\pm 10^{-9}$."

---

### 2. Which Accounts Should We Freeze? — QUBO Interdiction (0:25 – 0:50)

**[Action]**: Press `Right Arrow` to advance to Step 2. Drag the budget slider to $K=5$. Click **"Show on map"**.

**[Speaker Dialogue]**:
> "Next: *Which accounts do we freeze?*
>
> Instead of simple greedy heuristics that cause massive customer friction, we formulate early freezing as a **Binary Quadratic Optimization (QUBO)** problem:
> We minimize escaping flow while heavily penalizing the freezing of innocent or low-risk accounts. Crucially, our **Victim Protection Invariant** mathematically guarantees that victims can never be frozen.
>
> Look at the live comparison computed from our data:
> At budget $K=5$, the greedy list freezes 2 low-risk accounts as collateral damage. Our simulated annealing optimizer achieves **₹1,00,000 in estimated funds saved** with **zero low-risk account freezes**.
>
> I click **Show on map**, and the exact interdiction perimeter lights up in orange."

---

### 3. Which Rings Behave Alike? — Quantum State Fidelity (0:50 – 1:10)

**[Action]**: Press `Right Arrow` to advance to Step 3. Point to the $6 \times 6$ fidelity heat table.

**[Speaker Dialogue]**:
> "In Step 3, we compare syndicate signatures using **Quantum State Fidelity**: $|\langle a | b \rangle|^2$.
>
> Because our 6D Ring DNA feature vectors are normalized non-negative real numbers, pure state transition fidelity is mathematically identical to $\cos^2(\theta)$.
>
> Notice this reading: our active ring exhibits **94.2% fidelity** with the High-Velocity Crypto Funnel typology, giving investigators instantaneous geometric pattern matching."

---

### 4. Where This Goes Next — The 27-Qubit Horizon (1:10 – 1:30)

**[Action]**: Press `Right Arrow` to advance to Step 4. Display the three future horizon cards.

**[Speaker Dialogue]**:
> "Finally, where does this go next?
>
> 1. **Why Quantum**: For $N$ accounts, quantum state space scales logarithmically. A national banking network of 100 million accounts requires only **27 ideal qubits**—though loading transaction ledgers via QRAM remains an unsolved hardware challenge.
> 2. **Un-gameable Detectors**: Syndicates beat static 30-minute rules today. Continuous wave interference creates dynamic probes that cannot be reverse-engineered.
> 3. **The Arms Race**: Criminal syndicates will eventually adopt quantum optimization tools to design evasive laundering paths. We must build quantum-resilient defense rails today.
>
> That is MuleTrace Ω: grounded in real math, fully transparent, and engineered for the next decade of financial intelligence."

---

## Emergency Troubleshooting & Presenter Tips

- **If you get lost in the UI**: Press `1` on your keyboard to switch to Balanced Preset and click "Reset View" on the graph.
- **To find any account or screen quickly**: Press `Ctrl+K` (or `Cmd+K`) to open the Command Palette.
- **To see keyboard shortcuts during presentation**: Press `?` to open the cheat sheet modal.
- **If projector colors are washed out**: Press `T` to switch from Dark Theme to High-Contrast Colorblind Theme.

