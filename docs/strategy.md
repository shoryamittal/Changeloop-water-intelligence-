# Strategy — hero use case, white space, moat

**Written for:** the SANKALP jury and anyone auditing why this product is
shaped the way it is. This document records the decisions, including the ones
we rejected.

---

## 1. The hero use-case decision

We evaluated three directions and committed to one. The decision is frozen.

| Criterion | Cosmetics CIP (the previous direction) | **Indian textile ZLD** | AI data-centre cooling |
|---|---|---|---|
| Relevance to an Indian climate jury | low | **very high** | medium |
| Verifiable regulatory driver | none | **court-mandated ZLD, CPCB guidelines** | none yet |
| Is the data available in practice? | unknown | **yes — CPCB mandated OCEMS since 2014** | proprietary |
| Human stake | diffuse | **farmers, 100k jobs, MSME survival** | diffuse |
| Non-obvious technical insight | no | **yes — salt sets evaporator load** | partly |
| Demonstrable with this codebase | yes | **yes** | only superficially |
| Who would pay | a large brand | **the unit, and the shared CETP** | hyperscaler procurement |

**Chosen: Indian textile wet processing under a Zero Liquid Discharge
mandate, Tirupur-class cluster.**

The data-centre direction is deliberately *not* built. It would have been
feature theatre: we could not model a real cooling plant honestly, we have no
access to workload data, and claiming to be a cloud scheduler would have been
the kind of unsupported claim this project exists to avoid. The engine would
transfer — the consequence chain is the same shape — but we are not going to
assert that without building it.

## 2. Why the cosmetics direction was dropped

It is archived in full at [`archive/loreal_edition.md`](archive/loreal_edition.md),
with instructions to restore it. It was dropped because:

- A French cosmetics plant is remote from the water-stress reality an Indian
  jury assesses daily.
- It leaned on one company's published target. A problem owned by a sector is
  stronger than a problem owned by a brand.
- It used a named company's branding and *invented that company's internal
  standards* ("Hygiene Charter Q-502", "Clean Water Charter 2026"). Inventing
  a named company's internal standard is the fastest way to lose a technical
  jury.
- Its headline optimisation was a hardcoded constant. The demo did not run
  the optimiser.

## 3. The white space

Everything in this chain already exists. None of it is connected.

| What exists today | What it optimises | What it cannot see |
|---|---|---|
| Dyehouse ERP / PPC | delivery dates, machine loading | water, salt, the evaporator |
| CETP / ZLD plant SCADA | treating whatever arrives, reliably | that the inlet load was decided upstream, hours earlier |
| CPCB OCEMS | compliance reporting of effluent | causation — it measures outcomes, not decisions |
| ESG / sustainability software | disclosing last quarter accurately | tomorrow's schedule |
| Dye supplier technical service | recipe and chemistry for a shade | lot sequence, and the plant's own steam price |

The gap is **between** these systems. The planning decision and the treatment
consequence sit in different systems, different departments, and frequently
different companies — the dyeing unit and the common effluent plant are often
separate businesses. Nobody prices one into the other.

**ChangeLoop is the decision layer that does.**

## 4. What is genuinely novel, stated narrowly

We claim three things and no more:

1. **The downstream ZLD consequence inside the upstream objective.** Not
   "we optimise water" — we score each candidate plan on evaporator steam,
   boiler carbon and treatment cost, which is what the plant actually pays.
   Our ablation measures the difference: a water-only scheduler captures 13%
   of the available benefit once carbon is priced.
2. **Salt-mass accounting as the energy driver.** `V_reject = M_salt /
   C_reject_max` is just mass conservation, but acting on it inverts the
   normal advice. The model reports which constraint binds, so a user can see
   whether salt or water is the lever at their plant.
3. **Hard-constraint feasibility that a saving cannot buy its way out of.**
   A plan breaching a firm ship date is reported INFEASIBLE and cannot be
   recommended, whatever it saves. This is the single most common reason
   water-optimisation tools get ignored by planners, and we made it
   structural rather than a penalty weight.

**We explicitly do not claim:** shade sequencing (standard practice),
counter-current rinsing (best available technique), low-electrolyte dyes (a
commercial product), ZLD itself, RO, MEE, or online effluent monitoring.

## 5. The moat, assessed honestly

| Candidate moat | Real? | Assessment |
|---|---|---|
| AI / ML | **no** | there is no trained model here, by design |
| The optimiser | **no** | exhaustive search over 480 candidates; anyone can write it |
| The dashboard | **no** | copyable in a week |
| The salt-mass insight | **partly** | it is mass conservation — not ownable, but currently unexploited, and being first to productise it is worth something |
| The calibrated consequence model | **yes, eventually** | the value is a model calibrated to a specific cluster's steam economy, reject TDS ceiling, and shade-tolerance behaviour. That takes a pilot to build and does not transfer for free |
| The decision-and-outcome record | **yes, eventually** | every recommendation paired with what the human decided and what then happened. That dataset does not exist anywhere and cannot be bought |
| Cluster position via the CETP | **yes** | one integration with a common effluent plant reaches hundreds of units, and the CETP's own incentive is aligned |

**Honest conclusion: today the moat is weak.** It is a prototype with a good
insight. The defensible asset is the calibrated per-cluster model plus the
decision/outcome history, and neither exists until a pilot runs. We would
rather say that than claim a moat we do not have.

## 6. The human stake

This is not an abstract efficiency story.

- The litigation that produced the ZLD mandate was brought by the **Noyyal
  River Ayacutdars Protection Association** — a farmers' body. The
  Orathupalayam dam, built to irrigate about **20,000 ha**, became a
  repository of polluted water.
- When the units failed to comply, the court ordered closure. The industry
  association's representation reported around **₹11 billion in lost exports
  and about 100,000 jobs lost**.
- The cluster is **MSME-dominated**. These units cannot afford consultants or
  enterprise software, and they carry the compliance cost that threatens their
  survival.

So the stake runs in both directions: the downstream victims are farmers, and
the upstream actors are small businesses whose survival depends on making
compliance cheaper. A tool that cuts the energy cost of compliance serves
both. That is why the business case is priced in rupees per shift and the
software is dependency-free.

## 7. What we deliberately did not build

A long audit specification was applied to this project. We implemented the
parts that change the outcome and rejected the rest, because that same
specification says to keep a complexity budget and remove anything that does
not earn its place.

**Built:** constraint modes, sensitivity sweep, ablation study, data-quality
handling in the telemetry gate, claim register, model governance, pilot
design with exit and stop conditions, traceability on every headline metric,
idempotency on mutating endpoints, tamper-evident ledger.

**Rejected, with reasons:**

| Not built | Why not |
|---|---|
| Blockchain provenance | a hash chain answers the only question that matters ("was this edited?"). There is one accountable operator of record and no byzantine-fault problem for a chain to solve. Adding one would be a competition tick-box |
| Monte Carlo uncertainty | the sweep already shows the decision is robust on order and sensitive on strategy in four identifiable cases. A distribution would add computation and no decision value |
| Trained ML model | the decision space is 480 discrete candidates. A deterministic search is correct, auditable, and cannot hallucinate. An ML model here would be worse *and* less defensible |
| Multi-tenancy / RBAC implementation | the conceptual boundary exists (actor on every ledger record, site scoping) but building a SaaS permission system into a prototype is complexity without user value |
| A second vertical (data centres) | would require claims we cannot support. The engine would transfer; we are not asserting it without building it |
| Role-based dashboards per persona | the personas are documented in the business-case screen, but five dashboards would fragment a story that needs to be understood in 90 seconds |
| Chatbot / natural-language layer | nothing a planner needs here is easier to say than to click |

## 8. Known weaknesses

Stated plainly, because a jury will find them anyway.

1. **No measured data.** Every figure is modelled. The ranking of options is
   robust because all options are scored with the same coefficients, but the
   absolute savings carry the full uncertainty of those coefficients.
2. **The basin stress weighting is a placeholder.** It is a transparent
   ordering index, not an AWARE factor. It also does not change the answer at
   a single site — our own ablation says so.
3. **Single machine, five lots.** Real dyehouses run many machines with
   shared utilities. The optimiser would need to become a scheduler over
   machines, which is a materially harder problem.
4. **Pretreatment is excluded.** We model dyeing and wash-off only, so the
   litres-per-kilogram figure is lower than a whole-mill specific water
   consumption and must not be compared to one.
5. **The salt-to-shade-depth relationship is modelled, not metered.** A real
   dosing schedule would change the salt term.
6. **We have not spoken to a dyehouse.** This is modelled from public
   information. Phase 1 of the pilot exists to replace our assumptions with
   their measurements, and some of our conclusions will change when it does.
