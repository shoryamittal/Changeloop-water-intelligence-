# Pitch, demo runbook and deck

All figures below come from the running product. Before presenting, re-run
and re-read them — never quote from memory, and never quote a number the
product does not currently produce.

---

## 1. The one-liner

> **ChangeLoop prices tonight's evaporator bill into this morning's
> scheduling decision.**

Alternative, if the audience needs the climate frame first:

> **In a zero-liquid-discharge plant, salt is water. ChangeLoop is the
> decision layer that acts on it.**

## 2. The memory hook (closing line)

> **"Zero Liquid Discharge gave India back its water. Nobody costed the
> coal it takes to keep it. That cost is decided by a scheduling choice
> nobody connects to it — and that is the choice we change."**

## 3. The 30-second pitch

Tirupur recycles 130 million litres of water a day under a court-mandated
zero-discharge regime. It worked — and it raised unit costs 25 to 30 percent,
because evaporating the reject takes enormous steam.

Here is what nobody acts on: that reject volume is set by the **salt** in the
water, not the water itself. So cutting water without cutting salt saves no
energy at all.

ChangeLoop puts that downstream consequence inside the upstream scheduling
decision. A planner sees, before committing a lot order, what it will cost
the evaporator tonight — and the system refuses any plan that breaks a buyer
ship date.

## 4. The 90-second pitch

**The problem.** The Noyyal is a seasonal river. It had no flow to dilute
dyeing effluent, farmers downstream lost their land and their irrigation
reservoir, and the courts ordered zero liquid discharge. When the units could
not comply, around 700 units were closed in February 2011 — exports fell roughly ₹1,000 crore in a quarter,
by the industry's own account.

**What's solved and what isn't.** The cluster now recovers most of its water.
But recycled water costs ₹120–150 a kilolitre against ₹30–60 for fresh, and
the evaporator burns coal all night. Compliance is survivable but expensive,
and these are mostly MSMEs.

**The insight.** Salt is conserved. Reverse osmosis can only concentrate to a
ceiling, so reject volume equals salt mass divided by that ceiling — and
evaporator steam is proportional to reject volume. Our engine shows it live:
cut water 20 percent, evaporator energy moves **zero**. Cut salt 20 percent,
it falls **20 percent**. In a closed loop, salt *is* water.

**What we built.** A decision layer. It scores every lot order against every
process strategy — 480 candidates, exhaustively, so the optimum is proven —
on freshwater, salt, evaporator steam, carbon and cost together. Two levers
pull opposite ways: counter-current rinsing cuts water but not salt;
low-electrolyte chemistry cuts salt but not water. A water dashboard picks
the wrong one.

**Why a planner would use it.** It refuses to recommend anything that breaches
a firm ship date — even the plan that saves the most water. That refusal is
why it might survive contact with a real dyehouse.

## 5. The 3-minute demo

Run the server, open `http://localhost:8000`, press **Reset session**. Keys
`1`–`8` jump between sections. Rehearse once: every number must match what
you say.

| Time | Screen | What you do | What you say |
|---|---|---|---|
| **0:00–0:20** | **1 Brief** | Nothing — let the headline sit | "Tirupur recycles 130 million litres a day under a court-mandated zero-discharge regime. It worked. It also raised costs 25 to 30 percent, and nobody has costed the coal." |
| **0:20–0:50** | **1 Brief**, point at the insight panel | Point at the two metric tiles | "Reject volume equals salt mass over the RO ceiling. So watch: cut water 20 percent — evaporator energy moves **zero point zero**. Cut salt 20 percent — it falls **20 percent**. This is computed live from mass conservation, not asserted. In a closed loop, salt is water." |
| **0:50–1:05** | **1 Brief**, scroll to the systems table | Scroll | "Everything in this chain exists. The ERP plans lots. The treatment plant treats whatever arrives. The regulator monitors the outfall. None of them talk. The planner never sees the evaporator." |
| **1:05–1:50** | **2 Decision** | Let the three options render. Point at Option C | "480 candidates, exhaustively — the optimum is proven, not approximated. Option B is recommended. **Option C saves twice the freshwater and we refuse it**, because it breaks a firm buyer ship date. That is the product working. A water optimiser that misses a shipment gets switched off." |
| **1:50–2:05** | **2 Decision** | Click **Approve recommendation** | "Approve. Recorded against a named planner. If I reject it instead, it credits exactly zero and the rejection is on the record too." |
| **2:05–2:30** | **3 Wash-off gate** | Click **Calibration drift**, then **Attempt release** | "Second decision: fixed-time wash-off wastes the tail. But get it wrong and the lot is re-processed, which costs more water than you saved. So — inject a probe fault. Gate locks. I try to release anyway. **Refused**, at the gate and at the API, and the refusal is written to the ledger. It never releases automatically." |
| **2:30–2:45** | **3**, then **4 Consequence** | Click **No fault**, **Grant early release**, go to 4 | "Clean run, release granted. Now the chain: dyehouse, effluent, RO split, reject to the evaporator, coal, and freshwater back from the basin. Eight accounting invariants, all passing. Click any number and it tells you its formula and its coefficients." |
| **2:45–2:55** | **8 Scale & proof** | Scroll to the ablation table | "We ablate our own system. A scheduler that optimises dyehouse water alone captures **13 percent** of the benefit. And two variants over-report their savings — we label that, because over-reporting is the defect." |
| **2:55–3:00** | **5 Evidence** | Land on the registry | "Nothing here is measured. Five published values, two derived, thirteen assumed, zero measured — a test enforces that. Zero Liquid Discharge gave India back its water. Nobody costed the coal. That's the decision we change." |

### Demo runbook

**Before you start**

1. `python backend/server.py`, confirm `http://localhost:8000/api/health`
   returns 200.
2. Press **Reset session** — a fresh ledger chain, clean state.
3. Confirm the Brief shows a stress weight and the insight tiles show
   `0.0%` and `-20.0%`.
4. Set the mode selector to **Normal operation**.

**If something goes wrong**

| Symptom | Do this |
|---|---|
| Blank view | press `1`, then **Reset session** |
| "Cannot reach the engine" | the server died; restart it, reset, resume at section 1 |
| Numbers differ from this script | **say the number on screen**, not the one here. Then fix the script |
| Asked for a figure you do not have | "That is not measured, and I will not estimate it. Phase 1 of the pilot measures it." |

**Do not**

- Do not call anything a result. Everything is modelled.
- Do not say "AI" — there is no trained model in this system.
- Do not say "blockchain" — it is a hash chain and the screen says so.
- Do not quote the cluster projection as impact. It is a projection.

## 6. Deck outline — 10 slides, one message each

| # | Message | Content |
|---|---|---|
| 1 | A seasonal river, a court order, and a bill nobody costed | Noyyal, farmers' litigation, Orathupalayam, ZLD mandate, ₹11bn and 100k jobs when units closed |
| 2 | ZLD solved recovery and created an energy problem | 130 MLD recycled; +25–30% cost; ₹120–150/kL recycled vs ₹30–60 fresh |
| 3 | **Salt is water** | `V_reject = M_salt / C_reject_max`; the 0.0% vs −20% screenshot |
| 4 | The gap is between systems, not inside one | the five-system table from the Brief |
| 5 | ChangeLoop: the decision layer | the consequence-chain diagram |
| 6 | Two levers that pull opposite ways | counter-current vs low-salt table; why a water dashboard picks wrong |
| 7 | The decision, live | the three-option table, with Option C refused |
| 8 | We ablate our own system | 13% table; over-reporting flagged; basin weighting honestly inert at one site |
| 9 | Pilot, business model, cluster scale | 6 phases with exit and stop conditions; CETP as channel; the projection, labelled |
| 10 | What is modelled, and the hook | evidence mix 5/2/13/0; closing line |

**Slide discipline.** Every quantitative slide carries its evidence tag
(MODELLED / DERIVED / PUBLISHED / ASSUMED / PROJECTED). Every range stays a
range. No slide says "achieves", "delivers" or "proven impact".

## 7. Business model

| Question | Answer |
|---|---|
| **Who uses it** | the production planner (sequence) and the quality supervisor (release) |
| **Who buys it** | the dyeing unit owner — steam and salt are real cash to an MSME |
| **Who else benefits** | the common effluent plant: lower, steadier inlet salt load |
| **Who pulls demand** | the brand/buyer, for Scope 3 water and carbon evidence |
| **Pricing unit** | per dyeing machine per year, plus a one-off integration. Machines, not sites: it scales with the decisions the product actually touches |
| **Channel** | the CETP. One integration reaches hundreds of units, it already has a commercial relationship with each, and its own incentive is aligned |
| **Why the second unit is cheaper** | cluster units share one effluent plant, so the effluent model, basin weighting and steam cost are shared |
| **The honest objection** | an MSME will not pay for a modelled saving. Hence shadow mode: run it for four weeks, show what it would have advised against what was actually done, then charge |

The business-case screen **refuses** to compute an ROI until the site enters
its own tariffs and volumes, because a projection built on a vendor's
assumptions is not a business case.

## 8. Claim register

The product serves its own claim register at `/api/claims` and renders it on
the Evidence screen. Every external claim carries an evidence level L1–L6 and
a safe wording. The forbidden list is short and absolute:

- any sentence implying a deployment, a customer, or a measured result
- "AI-powered" — there is no trained model
- "blockchain" — it is a hash chain
- any named company's internal standard
- any single-point figure where the source gives a range

Check the register before the deck, the video script, and any answer you give
under pressure.
