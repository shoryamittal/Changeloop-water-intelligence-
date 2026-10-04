# ClearLoop — Competition Pitch Deck & Narrative

**Target:** L'Oréal Sustainability Challenge / Brandstorm 2026  
**Core Thesis:** Upstream Decision-Support to Reduce Modeled Changeover Water Demand Before It Enters the Loop.

---

## 1. The 30-Second Elevator Pitch

> *"L'Oréal has set an industry-defining benchmark: 100% of industrial water recycled and reused in a circular loop by 2030 across all manufacturing sites. But today, circularity starts downstream—treating water only after it's polluted.*  
>  
> *ClearLoop moves the intervention **upstream**: using transparent sequence optimization and physics-informed Clean-In-Place telemetry to reduce modeled changeover water demand before it ever enters the loop. By preventing water demand and terminating rinse cycles dynamically, ClearLoop cuts modeled water demand by up to 29%, saves thermal boiler steam energy, and eliminates chemical stress on recycling membranes—without replacing validated CIP quality release."*

---

## 2. The 90-Second Presentation Pitch

> *"Good morning, jury members. Imagine a cosmetic packaging hall at L'Oréal's Burgos factory running 2,800 changeovers a year. Every time a line shifts from a waterproof mascara to a light hyaluronic serum, hundreds of litres of 72°C hot water are pumped through pipes and agitators on rigid, static timers.*  
>  
> *ClearLoop solves this through four rigorously bounded layers:*  
>  
> 1. **PREVENT:** We sequence the batch queue using 2-Opt local search to minimize physical transition penalties (dark-to-light pigments, high-to-low viscosity steps, and allergen clearances). This avoids over 300 Litres of demand per campaign before cleaning even begins.  
> 2. **ADAPT:** Rather than running blind 42-minute timers, our advisory CIP engine tracks multi-sensor asymptotic conductivity and turbidity, safely detecting the cleanliness plateau at minute 29. Crucially, if a sensor drops or drifts, our Safety Gate instantly locks out early release and reverts to standard procedural SOPs.  
> 3. **CASCADE:** Aligned with the Burgos Waterloop architecture, we segregate high-load pre-rinse effluent to biogas digestion, while screening clean final-rinse permeate for non-product cooling tower utility—never auto-approving reuse without plant quality release.  
> 4. **MEASURE:** Every litre saved is tracked from one common baseline without double counting. And because cleaning uses hot water, every avoided litre eliminates natural gas boiler combustion, directly reducing Scope 1 GHG emissions.  
>  
> *ClearLoop is non-invasive, retrofittable to existing skids, and ready for a controlled 6-week single-line pilot."*

---

## 3. The 3-Minute Grand Jury Walkthrough

| Step | Live UI Moment | Key Spoken Narrative | Proof Point Shown |
|---|---|---|---|
| **1. The Upstream Gap** | Command Center Overview | *"L'Oréal is leading the world in water circularity, with 56% industrial water recycled in 2025 toward the 2030 100% target. But downstream recycling plants consume electricity and chemicals. ClearLoop introduces the upstream multiplier."* | Metric tiles: Water Avoided + Thermal MWh Avoided + Scope 1 CO₂e. |
| **2. Cosmetic Formulation Physics** | Planning & Batches | *"Cleaning cosmetic vessels depends on physical chemistry. Shifting from dark iron oxides to pale creams or high-lipid balms requires deep washouts. We model these transitions with full transparency."* | Queue showing Revitalift, Elvive, Color Riche, and Infaillible formulations. |
| **3. 2-Opt Optimization** | Changeover Optimizer | *"Our 2-Opt local search algorithm untangles crossover transitions, outperforming greedy heuristics by an extra 11% while guaranteeing deadline compliance. If no improvement is found, our baseline safeguard retains the original plan."* | Algorithm comparison: Baseline vs Greedy vs 2-Opt. |
| **4. 4-Phase Dynamic CIP** | Adaptive Cleaning | *"During CIP, conductivity reaches an asymptote once residue is purged. ClearLoop identifies this at minute 29, avoiding 13 minutes and 130 Litres of fresh water per wash."* | Multi-sensor SVG curve (Conductivity, Turbidity, Temp, Flow, pH). |
| **5. Fail-Safe Safety Gate** | Fault Injection Trigger | *"Could an AI glitch cause product contamination? Never. Click 'Inject Sensor Dropout'—the Safety Gate instantly trips to 'INSUFFICIENT DATA' and forces the standard procedural SOP."* | Safety Gate checklist & automatic release lockout. |
| **6. Circular Waterloop Segregation** | Water Cascade | *"Modeled on Burgos, effluent is segregated: first-flush to anaerobic biogas, caustic wash to re-dosing tanks, and final rinse permeate screened for utility cooling."* | 3-Stream manifold table & site validation checks. |
| **7. Multi-Dimensional Ledger** | ESG Analytics | *"One common baseline. Demand Avoided = Baseline − Prevent − Adapt. Cascade is segregated. Zero double counting. Hot water reduction yields Scope 1 carbon savings."* | Waterfall bar chart & ESG mass balance ledger. |
| **8. Pilot & Economics** | Business Case & Pilot Plan | *"A non-invasive 6-week pilot on Packaging Line 04. Over €17,000 net annual savings on an 8-line factory with a 2.6-year payback. Let's make L'Oréal changeovers truly zero-waste."* | Sensitivity tornado & 4-phase pilot roadmap. |

---

## 4. Why ClearLoop Wins Against Competitors

| Competition Evaluation Criterion | Typical Competitor Approach | ClearLoop Winning Standard |
|---|---|---|
| **Industrial Feasibility** | Claims to replace PLCs or automate physical valves. | **Non-invasive advisory retrofit**: reads sensors via MQTT/OPC-UA, leaves validated quality release in human hands. |
| **Scientific & Accounting Rigor** | Double counts recycled water as "demand avoided." | **Strict mass balance ledger**: Demand Avoided = $B - P - A$. Cascade ($C$) reported separately as potential reuse. |
| **Domain Understanding** | Generic box-sorting or toy TSP scheduling. | **Authentic cosmetic chemistry**: emulsion phases, microcrystalline waxes, pigment dispersion indices, allergen clearances. |
| **Safety & Risk Governance** | Black-box neural network that can silently hallucinate cleanliness. | **3-point deterministic Safety Gate**: asymptotic stability, turbidity clearance, and thermal log-kill verification with fail-safe fallback. |
| **ESG Multi-Dimensionality** | Only reports raw water litres. | **Water + Thermal MWh + Scope 1 GHG + Chemical NaOH + Reclaimed OEE Capacity**. |
