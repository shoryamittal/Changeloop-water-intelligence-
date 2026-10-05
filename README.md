# ChangeLoop

**Resource Decision Intelligence for water-stressed industry.**
SANKALP 2026 — Students Track. Climate / Water / Circular Economy.

> **A scheduling decision taken in the dyehouse this morning determines how
> much coal the zero-liquid-discharge evaporator burns tonight. No existing
> system connects those two facts. ChangeLoop does.**

---

## 1. The problem, in one paragraph

Indian textile clusters like Tirupur operate under a court-mandated **Zero
Liquid Discharge** regime, because the Noyyal is a seasonal river with no
dry-weather flow to dilute treated effluent. ZLD worked: the cluster now
treats and recycles on the order of **130 million litres a day**, recovering
most of its water. But it is expensive — reported to have raised unit
operating costs by **25–30%**, and the cost of dyed fabric by **12–15%**,
reducible to around **5% with salt and water recovery**. Recycled water is
reported at **₹120–150/kL against ₹30–60/kL** for fresh abstraction.

So water *recovery* is largely solved. What is not solved is the **energy and
salt burden of achieving it** — and that burden is decided upstream, by a
planner who never sees the evaporator.

## 2. The insight the product is built on

Salt is conserved. Reverse osmosis, biology and evaporation do not destroy
it, and the final RO stage can only concentrate up to a ceiling before
scaling stops it. By salt mass conservation:

```
V_reject  =  M_salt / C_reject_max
```

Reject volume — and therefore evaporator steam, boiler fuel and CO₂e — is set
by **salt mass**, not by water volume.

**Cutting water without cutting salt does not cut evaporator energy.**

The engine proves this live at `/api/insight/salt-is-water`: cut water 20% at
constant salt and evaporator energy moves **0.0%**; cut salt 20% at constant
water and it falls **20.0%**.

And because the loop is closed, freshwater makeup exactly equals what was
evaporated. In a ZLD plant, **freshwater intake, evaporator load and carbon
are the same number.** Salt *is* water.

## 3. What ChangeLoop actually does

It puts the downstream consequence inside the upstream decision, and refuses
to recommend anything that breaks a commitment.

```
dyehouse decision (lot order + process strategy)
  -> effluent volume + salt mass
  -> RO split: permeate reused / reject to evaporator
  -> evaporator steam -> boiler fuel -> CO2e
  -> freshwater makeup, weighted by basin stress
  -> cost
```

Two decisions, each gated by a named human:

1. **Lot sequence and process strategy** — which order the dye lots run in,
   and whether to run counter-current rinsing, low-electrolyte chemistry,
   both, or neither.
2. **Wash-off release** — whether to end a fixed-time wash-off early when the
   telemetry says the fabric has cleared.

## 4. Why a joint objective is required

The two available process levers pull in *different directions* through the
ZLD chain. This is the whole reason a water dashboard cannot do this job:

| Lever | Cuts water | Cuts salt | Cuts evaporator energy |
|---|---|---|---|
| Counter-current rinse cascade | **yes, ~35%** | no | barely |
| Low-electrolyte dye chemistry | no | **yes, ~45%** | **yes, proportionally** |

A water-only optimiser always picks counter-current and believes it has
solved the energy problem. It has not.

## 5. The decision, as the product renders it

Modelled on the five-lot reference order book, Tirupur site, normal
economics. The optimiser enumerates **480 candidates** (120 lot orders × 4
process strategies) — the optimum is *proven*, not approximated.

| | Plan | Freshwater | Salt | Evaporator | CO₂e | Cost | Late |
|---|---|---|---|---|---|---|---|
| **A** | No intervention (ERP arrival order) | 11,907 L | 714 kg | 2,133 kWh | 3,015 kg | ₹33,206 | 0 h |
| **B** | **Recommended** — resequenced + counter-current | 11,187 L | 671 kg | 2,004 kWh | 2,260 kg | ₹25,908 | 0 h |
| **C** | Freshwater minimum — **refused** | 5,889 L | 353 kg | 1,055 kWh | 2,171 kg | ₹31,823 | 2.6 h |

**Option C saves the most freshwater and ChangeLoop refuses it**, because it
breaches a firm buyer ship date. That refusal is the product working, and it
is why a planner might actually use it.

After the wash-off release is also granted, the full golden path gives
(all **MODELLED**, never measured):

- freshwater **−1,044 L** per shift (−8.8%), **11,570 L-eq** stress-weighted
- salt **−62.7 kg** (−8.8%)
- evaporator steam **−187 kWh** thermal
- CO₂e **−922 kg** (−30.6%)
- cost **−₹9,514** (−28.7%)

Notice freshwater falls only 8.8% while *process* water falls far more —
because basin draw tracks salt, not water. That is the thesis visible in the
ledger.

## 6. Does the architecture earn its complexity?

We ablate our own system and publish the result. Under a carbon price
(`/api/ablation?mode=CARBON_PRIORITY`):

| Variant | Freshwater reported | vs full | Firm breach |
|---|---|---|---|
| Full ChangeLoop | 5,538 L | 100% | 0 |
| Without downstream ZLD coupling | 720 L | **13%** | 0 |
| Without the salt-mass model | 2,342 L | 42% (over-reports) | 0 |
| Without basin stress weighting | 5,538 L | 100% | 0 |
| Without hard-constraint enforcement | 6,018 L | 109% (over-reports) | **1** |

A scheduler that optimises dyehouse water alone captures **13%** of the
available benefit. Two variants *over-report* savings — over-reporting is
their defect, not an advantage, and the product says so in the table.

Honestly: basin stress weighting does **not** change the answer at a single
site. It earns its place only for multi-site prioritisation, and the ablation
reports that rather than pretending otherwise. Under normal economics the ZLD
coupling is also inert, because counter-current rinsing is cheapest either
way — it becomes decisive the moment carbon or scarcity is priced. The
product tells you *when* each layer binds.

## 7. It changes its mind, for a readable reason

`/api/modes/compare` runs the same engine under different binding
constraints:

| Binding constraint | Recommended strategy |
|---|---|
| Normal operation | Counter-current rinse |
| Shipment crunch | Counter-current rinse |
| **Drought / abstraction restriction** | **Combined (buys the salt lever)** |
| **Carbon priority** | **Combined (buys the salt lever)** |

Under normal economics the site rationally skips low-salt chemistry — the dye
premium costs more than the steam it saves. Price water scarcity or carbon
and the same engine starts recommending it. That is this product's argument in
one table.

## 8. Honesty rules, enforced in code

- **Nothing here is measured.** The coefficient registry holds 5 PUBLISHED,
  2 DERIVED and 13 ASSUMED values and **zero MEASURED**. A test asserts that
  no value may claim MEASURED status while this is a prototype.
- **No number may be used unless it is registered** in `core/factors.py` with
  a unit, a derivation or source, and an evidence class. `factors.get()`
  raises on an unregistered key.
- **Basin stress weighting is a disclosed placeholder**, not an AWARE
  characterisation factor and not a WRI Aqueduct value. We do not ship or
  claim either dataset. See the Evidence screen.
- **The ledger is a hash chain, not a blockchain, and not a signature.** It
  proves no record was altered; it does not prove who authored one. The demo
  MAC key is a published constant and the interface says so.
- **No trained machine-learning model exists in this system** and none is
  claimed. At this problem size a deterministic optimiser is correct,
  auditable, and cannot hallucinate.
- **Established practice is not claimed as invention.** Ascending shade
  sequencing is standard dyehouse practice; counter-current rinsing is best
  available technique; low-electrolyte dyes are a commercial product. The
  addition is the ZLD consequence inside the objective, plus hard-constraint
  feasibility that a water saving cannot override.
- **A rejected recommendation credits exactly zero**, and the rejection is
  recorded. Tests assert this for every decision combination.

## 9. Safety

The wash-off release gate is **fail-closed and never automatic**.
`automatic_release` is hardcoded `False` with no code path that sets it true.

Ending wash-off early on unfixed dye causes bleeding and a failed fastness
test; the lot is then re-processed, consuming **more** water, steam and salt
than the baths that were skipped. So the gate is not bureaucracy — it is what
keeps the saving real.

Five injectable faults — probe dropout, frozen probe, calibration drift,
residual dye slug, bath under temperature — each force lockout. Tests assert
that under every one of them release is refused at the gate *and* at the API,
and that exactly zero saving is credited.

## 10. Run it

No dependencies, no build step. Python 3.9+ standard library only.

```bash
python backend/server.py
# http://localhost:8000
```

Tests:

```bash
python -m unittest discover -s tests -p "test_engine.py"   # 81 engine tests
python tests/verify_system.py                              # golden path, safety,
                                                           # determinism, tamper
node tests/test_frontend_render.js                         # all 8 views
                                                           # (server must be up)
```

Keyboard: `1`–`8` jump between sections.

## 11. Architecture

```
core/factors.py     every coefficient, with unit, derivation, evidence class
core/basin.py       basin stress weighting + explicit honesty boundary
core/process.py     dye lot model, COMPUTED changeover burden, strategies
core/zld.py         salt -> reject -> steam -> carbon -> cost
core/optimizer.py   constrained multi-objective search over order x strategy
core/telemetry.py   wash-off telemetry + fail-closed release gate
core/ledger.py      resource decision event + mass-balance impact ledger
core/provenance.py  tamper-evident HMAC hash-chained ledger
core/economics.py   site business case (refuses invented inputs) + projection
core/scenarios.py   constraint modes, sensitivity sweep, ablation study
core/session.py     golden-path orchestrator, single source of truth
backend/server.py   stdlib HTTP server + REST API
frontend/           vanilla JS/CSS, no framework, no build
```

Every figure the interface shows comes from the server. Nothing is computed
in the browser and nothing is hardcoded. `/api/trace?metric=...` returns the
formula, upstream chain and coefficients behind any headline number.

## 12. Documents

- [`docs/strategy.md`](docs/strategy.md) — hero use-case decision, white
  space, moat, what we deliberately did not build
- [`docs/methodology.md`](docs/methodology.md) — equations, system boundary,
  accounting definitions, invariants
- [`docs/pitch.md`](docs/pitch.md) — 30s / 90s / 3-minute scripts, demo
  runbook, deck outline
- [`docs/jury_defence.md`](docs/jury_defence.md) — 30 hostile questions and
  answers
- [`docs/archive/loreal_edition.md`](docs/archive/loreal_edition.md) — the
  superseded cosmetics variant, how to restore it, and the defects it carries

## 13. Scale

A cluster projection — clearly labelled **PROJECTED**, not a result — for 400
units at 900 lots each: ~399 ML/yr freshwater, ~4,500 t/yr salt, ~13,400
MWh/yr of evaporator steam and ~6,073 t/yr CO₂e avoided. It assumes every
unit resembles the modelled one and that every recommendation is approved.
Neither assumption has been tested, and it must never be quoted as achieved
impact.

Units in a cluster share one common effluent plant, so the effluent model,
basin weighting and steam cost are shared — the second and third unit cost
far less to onboard than the first. The CETP is the natural channel: it
already has a commercial relationship with every unit, and it directly
benefits from a lower, steadier inlet salt load.

## 14. What would change our conclusions

Our own sensitivity sweep flags the coefficients that matter. The lot
**order** never changes across the whole sweep; what flips is the process
**strategy**, and it flips in exactly the cases that make evaporator energy
more expensive: a worse measured steam economy, a lower reject TDS ceiling, a
cheaper low-salt dye range, or a higher steam price.

That tells a site which two numbers to meter first: **steam per m³ of reject,
and the reject TDS ceiling**. Both are Phase 1 of the pilot.

---

**Status:** advisory decision-support prototype. Modelled throughout, on a
synthetic five-lot reference order book. Not connected to any plant, and no
figure here is a measured result.
