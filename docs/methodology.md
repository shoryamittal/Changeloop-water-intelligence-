# Methodology

Equations, system boundary, accounting definitions and the invariants the
code enforces. Every coefficient referenced here is registered in
`core/factors.py` with a unit, a derivation or source, and an evidence class,
and is rendered on the Evidence screen.

---

## 1. System boundary

**Inside the boundary**

- Dyeing and wash-off of reactive-dyed cotton on soft-flow jet machines
- Machine cleaning between lots (the changeover burden)
- The site's effluent stream as a single blended flow
- Common/in-house treatment: biological pretreatment, reverse osmosis,
  multiple-effect evaporation
- Permeate reuse back to process, and freshwater makeup from the basin
- Boiler steam for both dyehouse heating and evaporation
- Grid electricity for RO pumping

**Outside the boundary, and therefore excluded from every figure**

- Pretreatment: singeing, desizing, scouring, bleaching. This is why our
  litres-per-kilogram figure is lower than a whole-mill specific water
  consumption and **must not be compared to one**.
- Embodied impacts of dye, chemicals, membranes or plant construction
- Fabric transport, finishing, garmenting
- Sludge and salt disposal beyond the evaporator opex line
- Permeate salt passage, which we neglect (stated in the ZLD model's
  limitations)

Thermal and electrical energy are reported **separately** because they are not
interchangeable. Where a combined figure is shown it is labelled a
*site-energy* total, not a primary-energy total.

## 2. Water vocabulary

These six quantities are defined once in `core/zld.py` and are never used
interchangeably anywhere in the codebase. Conflating them is the most common
way water claims become dishonest.

| Term | Definition |
|---|---|
| **Process demand** | water the process must receive, from any source |
| **Permeate reuse** | recovered water actually fed back. Bounded by both what RO produced *and* what the process demands |
| **Freshwater intake** | demand that reuse could not cover. The only figure representing new abstraction from the basin |
| **Evaporative loss** | water destroyed in the evaporator. Leaves as vapour; not available for reuse |
| **Demand avoided** | reduction in process demand versus baseline, caused by a decision. **Not** a recovery figure |
| **Freshwater avoided** | reduction in freshwater intake versus baseline. The headline climate number, and always ≤ baseline freshwater intake |

The account must close exactly:

```
process_demand = permeate_reuse + freshwater_intake
```

`WaterAccount.check_closes()` asserts this.

## 3. The ZLD consequence chain

### 3.1 Reject volume

Salt is conserved: RO, biology and evaporation do not destroy it. The final
RO stage can only concentrate to a ceiling `C_reject_max` before osmotic
pressure and sparingly-soluble-salt scaling stop it. Therefore:

```
V_reject_salt      = M_salt / C_reject_max
V_reject_hydraulic = (1 - r_max) x V_effluent
V_reject           = max(V_reject_salt, V_reject_hydraulic)
V_permeate         = V_effluent - V_reject
```

Whichever constraint binds is **reported** (`binding_constraint`), so a
reviewer can see whether a stream is salt-limited or hydraulically limited —
and therefore whether salt reduction or water reduction is the real lever.

**The crossover matters and is tested.** Below
`M_salt = (1 - r_max) x V x C_reject_max`, the hydraulic floor takes over and
further salt reduction buys no evaporator saving. A product claiming "cut
salt, always win" would be wrong there. See
`test_hydraulic_floor_takes_over_below_the_crossover`.

### 3.2 Evaporator energy

Latent heat of vaporisation at 100 °C, 1 atm is 2257 kJ/kg (standard steam
tables) = 0.62694 kWh/kg. A 4-effect forced-circulation evaporator has a
steam economy — kg of water evaporated per kg of live steam. This is no
longer an assumption. Specific steam consumption for multiple-effect
evaporators on textile RO reject is reported at **0.25–0.35 kg steam per kg
of water evaporated** (CPCB's Tirupur ZLD assessment; Indian MEE vendor
design data). Steam economy is the reciprocal of that figure, so the
published band is 1/0.35 = 2.86 to 1/0.25 = 4.00. We take the **midpoint of
the published specific-steam range**, 0.30 kg/kg:

```
steam_economy    = 1 / 0.30
                 = 3.333 kg water evaporated per kg steam

specific_thermal = h_vap x 1000 / steam_economy
                 = 0.62694 x 1000 / 3.333
                 = 188.08 kWh_th per m3 evaporated
```

This sits inside the 150–250 kWh_th/m³ band quoted for the evaporator
section of textile ZLD plants — which is an independent check rather than a
restatement: latent heat comes from steam tables and steam economy from
Indian plant data, two unrelated sources that do not cite each other, and
their product lands inside a third separately published band.

We deliberately do **not** use the 5–6 kg/kg reachable by optimised trains
with thermocompression and condensate flashing. A better evaporator would
make the steam saved per kg of salt avoided look *smaller*, so assuming a
poor one would inflate our claim. 3.333 is the published middle, not a
flattering end.

```
MEE_thermal_kWh = (V_reject / 1000) x 188.08
```

### 3.3 Emissions

```
boiler:  0.353 kg CO2e per kWh_fuel / 0.78 boiler efficiency
       = 0.452 kg CO2e per kWh_th delivered
grid:    0.71 kg CO2e per kWh_e   (CEA Indian grid combined margin)
```

### 3.4 Dyehouse thermal

Specific heat of water 4.186 kJ/(kg·K); 1 L ≈ 1 kg:

```
0.00116278 kWh_th per litre per kelvin
x 55 K rise (80 degC soaping against a 25 degC Tamil Nadu intake)
```

### 3.5 Cost

Each line is priced **once**, so no term is double counted:

| Line | Rate | Evidence |
|---|---|---|
| Freshwater | ₹45/m³ (reported ₹30–60) | PUBLISHED |
| Recycled water | ₹135/m³ (reported ₹120–150) | PUBLISHED |
| Dyehouse steam | ₹2.40/kWh_th | ASSUMED |
| Evaporator steam | ₹2.40/kWh_th | ASSUMED |
| Evaporator non-energy opex | ₹180/m³ reject | ASSUMED |
| RO power | ₹8.50/kWh_e | ASSUMED |
| Electrolyte | ₹9/kg | ASSUMED |

**Recycled water is priced above freshwater, and this is deliberate and
load-bearing.** In a closed-loop plant the marginal litre comes from the
recycle train, not the borewell. Avoiding a litre of *demand* is therefore
worth more than recovering a litre of effluent — which is exactly why
ChangeLoop intervenes upstream of the demand rather than downstream of the
waste. Pricing the avoided litre at the freshwater rate would understate the
saving roughly threefold.

## 4. The process model

Everything is computed from lot attributes. There is no lookup table of
pre-baked answers and no planted bottleneck.

Two quantities are kept rigorously separate:

- **Process demand** — water and salt a lot needs regardless of sequence.
  Not optimisable by scheduling, and therefore **never claimed as a
  scheduling saving**.
- **Changeover burden** — additional water, salt and time caused purely by
  the ORDER in which lots run. This is the decision variable.

### 4.1 Electrolyte and wash-off from shade depth

```
salt_dose_g_per_L = 25 + 13 x depth_owf          (30 g/L pale -> ~100 g/L black)
washoff_baths     = clamp(round(2 + 0.95 x depth_owf), 2, 7)
shade_tolerance   = 0.04 + 0.11 x depth_owf
```

### 4.2 Changeover burden

Residual colour left after a deep shade contaminates the next shade — but
whether that matters depends entirely on the **target**:

- **Going darker or lateral:** the next shade masks the residue. No cleaning
  bath required beyond the normal drain. Burden is zero.
- **Going lighter:** residue must be reduced below the target's tolerance.
  Each cleaning bath removes ~70% of what remains, so the number of baths
  grows logarithmically with the ratio of carried-over depth to tolerance:

```
carryover = depth_from x 0.18
baths     = ceil( ln(carryover / tolerance_to) / ln(1 / 0.30) ),  clamped 1..6
```

A dye-class change adds one stripping bath regardless of direction. Each
cleaning bath carries 6 g/L of caustic/reducing agent into the effluent,
which is why cutting cleaning baths cuts **both** water and salt.

This arithmetic — not a hand-authored table — is what makes dark-to-light
transitions expensive, and therefore what the optimiser can reorder away.

### 4.3 Process strategies

| Strategy | Water × | Salt × | Cost (₹/kg fabric) |
|---|---|---|---|
| Conventional | 1.00 | 1.00 | 0 |
| Counter-current rinse cascade | 0.65 | 1.00 | 0.35 |
| Low-electrolyte chemistry | 1.00 | 0.55 | 6.50 |
| Combined | 0.65 | 0.55 | 6.85 |

Multipliers apply to the **rinse** portion and the electrolyte, not to the
dyebath fill — a cascade cannot reduce the bath the fabric has to be dyed in.

The low-salt premium is sized against dye cost: a deep shade at 6% owf with
dye near ₹600/kg is roughly ₹36/kg fabric of dye, so an 18% range premium is
about ₹6.50/kg fabric. **This premium is load-bearing**: it makes the choice a
genuine trade-off rather than a free win, and the sensitivity sweep identifies
it as one of the decision-flipping coefficients.

## 5. The objective

A scalarised sum, in rupees of total consequence:

```
objective = total_cost_INR
          + strategy_cost_INR
          + (stress_equivalent_L_eq / 1000) x stress_premium_INR_per_m3_eq
          + (CO2e_kg / 1000)             x carbon_price_INR_per_tonne
          + lateness_h                   x lateness_penalty_INR_per_hour
```

The weights encode a value judgement, so they are **shown to the user** in
the Decision view rather than buried. Changing the binding constraint changes
the weights and genuinely changes the recommendation.

**Hard constraints are feasibility, not penalty.** A candidate breaching a
firm ship date, the total lateness limit, or the per-lot lateness limit is
marked INFEASIBLE and cannot be recommended at any objective value.

## 6. Search

| Queue size | Method | Claim made |
|---|---|---|
| n ≤ 8 | exhaustive over orders × strategies | **PROVEN_GLOBAL_OPTIMUM** |
| n > 8 | nearest-neighbour + 2-opt per strategy | LOCAL_OPTIMUM_NOT_PROVEN |

At the reference size this is 120 × 4 = **480 candidates** and the optimum is
proven. The system states which regime it used; it never calls a local optimum
a global one.

## 7. Basin stress weighting — honesty boundary

**Read this before quoting any L-eq figure.**

We do **not** ship licensed AWARE characterisation factors or WRI Aqueduct
raster values, and we do not claim to. What we ship is an explicit,
arithmetically transparent placeholder occupying the slot a licensed factor
would occupy:

```
stress_weight = 1 + 4 x (1 - renewable_availability_index)
                      x seasonality_penalty
                      x abstraction_pressure
```

Normalised so a well-supplied perennial basin scores 1.00, where L-eq equals
physical litres. It is an **ordering device** for comparing sites inside this
prototype, not a published characterisation factor, and it must be replaced
with a licensed factor before any disclosed or audited external claim. The
interface is a single scalar per site, so that is a data swap, not a code
change.

Our own ablation reports that this layer does **not** change the answer at a
single site. It earns its place only for multi-site prioritisation.

## 8. Attribution rules

Every ledger line names the decision that produced it, and a line is zero
unless that decision was approved.

- **Sequencing + strategy** is attributed the whole difference that decision
  caused: changeover burden removed by resequencing, plus rinse water and
  electrolyte removed by the process strategy.
- **Wash-off release** is attributed separately, from the baths actually
  released.

These two are **disjoint and additive**: the sequence evaluation is the
chosen plan's demand *before* any release, so the release is a further,
separate reduction inside that plan. Subtracting it from both would remove the
same litres twice — which is exactly what the balance invariant caught during
development.

## 9. Invariants, enforced on every read of the ledger

`ImpactLedger.validate()` runs all eight on every read. If any fails, the
impact figure is not fit to display and the product says so rather than
rendering it anyway.

| Invariant | What it prevents |
|---|---|
| `water_balance_closes` | baseline − each approved avoidance = achieved, with no residual fudge term |
| `salt_balance_closes` | the same, for salt |
| `freshwater_avoided_bounded` | avoided freshwater can never exceed baseline freshwater intake |
| `no_negative_physical_quantities` | negative water, salt, reject or energy |
| `reuse_bounded_by_recovery_and_demand` | reusing more than was recovered, or more than is needed — the classic double count |
| `unapproved_decision_yields_zero` | crediting a saving from a decision nobody approved |
| `stress_equivalence_consistent` | L-eq that does not equal litres × the declared basin weight |
| `energy_tracks_reject` | evaporator energy that does not equal reject volume × the derived specific energy |

## 10. Provenance

An append-only hash chain in SQLite, with a keyed MAC over each link:

```
record_hash = HMAC_SHA256(key, seq | timestamp | actor | action
                             | detail | payload_hash | prev_hash)
```

`detail` is inside the MAC deliberately — it is the human-readable text an
auditor actually reads, so leaving it out would allow a record's *meaning* to
be rewritten while the chain still verified. An earlier revision made exactly
that mistake and the tamper test caught it.

**What it proves:** no record was altered or removed after it was written,
provided the key holder is trusted.

**What it does not prove:** which individual authored a record. An HMAC uses a
shared key; non-repudiable authorship needs asymmetric signing with the key in
an HSM or KMS. That is a deployment decision, not something a prototype should
pretend to have made.

**It is not a blockchain.** No distributed consensus, no peers, no token. A
single accountable plant operator of record means there is no byzantine-fault
problem for a chain to solve.

The demonstration key is a published constant unless
`CHANGELOOP_LEDGER_KEY` is set. Anything else would be security theatre.

## 11. Evidence classes

| Class | Meaning | Count |
|---|---|---|
| MEASURED | instrument reading from a real asset | **0** |
| DERIVED | computed from first principles in this repository | 2 |
| PUBLISHED | reported in public literature or regulation | 5 |
| ASSUMED | our engineering assumption, exposed as a tunable input | 13 |
| SIMULATED | produced by our own synthetic generators | — |

The MEASURED class exists so a pilot can promote values into it. A test
asserts the count stays at zero while this is a prototype.

## 12. Reproducibility

Deterministic throughout: the telemetry generator is seeded, the search is
exhaustive, and there is no wall-clock or random input to any calculation.
`tests/verify_system.py` runs the full golden path ten times and asserts a
single distinct outcome across all of them.
