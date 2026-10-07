# ChangeLoop — Data Sources and Evidence Register

**Purpose.** Every number that drives this system, where it came from, and
what we are entitled to claim about it. A reviewer should be able to pick
any figure shown in the interface and trace it to a line in this file.

**Status at the time of writing.** 25 registered coefficients:

| Evidence class | Count | What it means |
|---|---|---|
| PUBLISHED | 17 | Reported in public literature, regulation or an official database. Source named below. |
| DERIVED | 4 | Computed from published values by arithmetic stated in the coefficient's `basis` string and re-checked by a test. |
| ASSUMED | 4 | Our engineering or commercial assumption. Openly labelled, exposed as a tunable input. |
| **MEASURED** | **0** | **Nothing in this prototype is measured.** Enforced by `tests/test_published_validation.py::EvidenceHonesty::test_no_coefficient_claims_to_be_measured`. |

84% of coefficients are published or derived from published values.

We did **not** relabel what we could not source. Four coefficients remain
ASSUMED, and a test pins that exact set so a future change cannot quietly
promote one without coming back to this file.

---

## 1. The claim this file has to support

> In a zero-discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath — not by how much water comes out.

Formally, `V_reject = M_salt / C_reject_max`. The volume the evaporator
must boil is the dissolved salt mass divided by the highest concentration
the membranes can safely reach. Effluent volume does not appear.

Three published facts are load-bearing for that claim, and each is sourced
below: the **concentration ceiling** (what fixes `C_reject_max`), the
**specific steam consumption** (what turns volume into coal), and the
**electrolyte dose** (what sets `M_salt`).

---

## 2. Thermodynamics

| Coefficient | Value | Class | Source |
|---|---|---|---|
| `h_vap_kwh_per_kg` | 0.62694 kWh_th/kg | PUBLISHED | Latent heat of vaporisation of water, 2257 kJ/kg at 100 °C and 1 atm — standard steam tables. 2257 / 3600. |
| `mee_steam_economy` | 3.333 kg/kg | PUBLISHED | Specific steam consumption of MEE trains on textile RO reject reported at **0.25–0.35 kg steam per kg water evaporated**. Steam economy is the reciprocal; we take the midpoint 0.30 → 3.333. CPCB Tirupur ZLD assessment; Indian ZLD vendor design data. |
| `mee_specific_thermal_kwh_per_m3` | 188.08 kWh_th/m³ | DERIVED | 0.62694 × 1000 / 3.333. |
| `water_heating_kwh_per_l_per_k` | 0.00116278 | PUBLISHED | Specific heat capacity of water, 4.186 kJ/(kg·K). 4.186 / 3600. |

**Why we did not assume a worse evaporator.** Optimised trains with
thermocompression and condensate flashing reach 5–6 kg/kg. A *worse*
evaporator would make the steam saved per kg of salt avoided look
*larger*, so assuming one would inflate our claim. 3.333 is the published
middle of the reported range, not the flattering end.

**Independent triangulation.** Latent heat (steam tables) and steam
economy (Indian plant data) come from unrelated sources that do not cite
each other. Their product, 188.08 kWh_th/m³, lands inside a third
separately published band — the **150–250 kWh_th/m³** quoted for the
evaporator section of textile ZLD plants. Checked by
`test_mee_specific_thermal_energy_matches_published_band`.

---

## 3. Reverse osmosis — where the core claim lives

| Coefficient | Value | Class | Source |
|---|---|---|---|
| `ro_max_reject_tds_mg_l` | 60,000 mg/L | PUBLISHED | RO reject entering thermal evaporation reported at **15,000–80,000 mg/L**; multi-stage RO concentrates TDS 3–5×. We take the upper-middle of that band. CPCB Tirupur ZLD assessment; Indian ZLD process design data. |
| `ro_max_recovery_frac` | 0.90 | PUBLISHED | Reject reported at 20–30% of inlet for a single pass (70–80% recovery), rising to ~90% on multi-stage trains with interstage boosting — consistent with the 95–98% water reuse Tirupur CETPs report. **In this model recovery is a ceiling that is normally not binding; the salt balance binds first.** |
| `ro_specific_electrical_kwh_per_m3` | 1.2 kWh_e/m³ | ASSUMED | Specific energy of brackish-water RO on high-TDS textile effluent at elevated feed pressure. Site-specific; tunable. |

This is the single most important pair of numbers in the project. The
concentration ceiling is set by osmotic pressure and sparingly-soluble
salt scaling in the final stage — chemistry, not operator choice. Combined
with salt mass conservation it fixes reject volume, and therefore
evaporator duty, independent of how much water carried the salt.

---

## 4. External validation — the strongest evidence we have

Our engine's **outputs** are checked against operating envelopes published
by other people, using inputs the engine never reads back. If the
salt-mass formulation were wrong, these would fail.

### 4.1 Reject fraction, validated at CPCB's own measured inlet

CPCB measured **18,340 mg/L TDS entering the evaporation stage** at an
assessed Tirupur textile unit. Separately, Indian ZLD operators report **RO
reject at 20–30% of inlet volume**. Two facts, different sources, neither
an input to our model.

Feed the model the first, and it predicts the second:

| Inlet TDS fed to the model | What that TDS is | Model predicts |
|---|---|---|
| 12,000 mg/L | lower end of observed CETP inlet strength | **20.0%** reject — band floor, exact |
| 15,000 mg/L | midpoint of observed CETP inlet strength | **25.0%** reject — band midpoint, exact |
| 18,340 mg/L | **TDS CPCB measured at a real Tirupur unit** | **30.6%** reject — band ceiling |

The published 20–30% band is reproduced end to end. Nothing is tuned to
make this work: the only inputs are salt mass conservation and the 60,000
mg/L ceiling. Enforced by
`test_model_reproduces_published_reject_band_at_observed_inlet_tds`.

**This is cross-validation, not measurement.** It says the physics is
right. It does not say anything about any specific site.

### 4.2 Honesty about the gap

Our own reference load is **one dyehouse shift**, which comes out at about
10,400 mg/L — more dilute than a CETP's combined inlet, so its reject
fraction (~17%) sits just *below* the published band. That is expected: a
CETP aggregates many units and concentrates through secondary treatment
before the RO. We assert that direction explicitly in
`test_single_dyehouse_effluent_is_more_dilute_than_cetp_inlet` rather than
widening a band to make our headline number fit inside it.

### 4.3 Validation-only coefficients

These are registered so tests can use them and are **never read by the
optimiser** — a test (`test_validation_only_factors_are_not_read_by_the_engine`)
greps the engine source to prove it. Feeding them back in would make the
validation circular.

| Coefficient | Value | Source |
|---|---|---|
| `cetp_reject_volume_frac_published` | 0.25 | Indian ZLD operators: reject at 20–30% of inlet. |
| `tds_after_evaporation_mg_l_published` | 212,384 mg/L | CPCB-assessed unit: 18,340 mg/L in, 212,384 mg/L out of the MEE — an 11.6× concentration, approaching the solubility wall where the crystalliser takes over. The clearest published demonstration that the evaporator's job is to concentrate *salt*. |
| `cetp_charge_inr_per_m3_distressed` | 412.5 INR/m³ | TNPCB plant data: CETPs at 15% and 24% of capacity charged ₹450 and ₹375/kL. |
| `mee_specific_electrical_kwh_per_m3` | 3.5 kWh_e/m³ | MEE parasitic load reported at 2–5 kWh per kL evaporated. |
| `reactive_dye_fixation_frac` | 0.675 | Only 65–70% of reactive dye exhausts onto the fibre; 25–30% leaves as coloured effluent. |

---

## 5. Emissions

| Coefficient | Value | Class | Source |
|---|---|---|---|
| `grid_co2e_kg_per_kwh_e` | 0.705 kg CO₂e/kWh | PUBLISHED | **Combined margin of the Indian grid, FY 2025-26.** CO₂ Baseline Database for the Indian Power Sector, **User Guide Version 22.0, August 2026**, Central Electricity Authority, Ministry of Power, Government of India — Table S. Same table: weighted-average 0.675, simple operating margin 0.963, build margin 0.446. CM is the 50:50 weighting of OM and BM. |
| `boiler_co2e_kg_per_kwh_th` | 0.452 kg CO₂e/kWh_th | DERIVED | Coal combustion ≈ 0.353 kg CO₂e per kWh of fuel energy, at 78% boiler efficiency: 0.353 / 0.78. |

**Why combined margin and not the average.** Avoided dyehouse load
displaces marginal generation, not average generation. CM is the
conservative and methodologically correct choice; using the 0.675 average
would understate avoided emissions, using the 0.963 operating margin alone
would overstate them.

This is the freshest official figure available — v22.0 was published in
August 2026 and covers FY 2025-26.

---

## 6. Economics

| Coefficient | Value | Class | Source |
|---|---|---|---|
| `freshwater_cost_inr_per_m3` | ₹45/m³ | PUBLISHED | Bhavani river water supplied to Tirupur dyeing units reported at ₹45/kL. Tanker water ₹10–20/kL for small dyers in monsoon, ~₹90/kL at summer rates (₹1,000 per 11 kL load). Tirupur wet-processing units spend ~₹115 crore/year on groundwater. Down To Earth; India Environment Portal. |
| `recycled_water_cost_inr_per_m3` | ₹185/m³ | PUBLISHED | ZLD charges levied on member units by Tirupur CETPs, from TNPCB plant-level data: **₹150–220/kL at plants running at or above 30% of design capacity**; we take the midpoint. |
| `steam_cost_inr_per_kwh_th` | ₹2.03/kWh_th | DERIVED | Imported sub-bituminous thermal coal landed ≈ ₹9,180/t = ₹9.18/kg. At 5,000 kcal/kg: 5,000 × 4.184 = 20,920 kJ/kg = 5.811 kWh/kg fuel. ₹9.18 / 5.811 = ₹1.580/kWh_fuel. At 78% boiler efficiency: ₹2.03/kWh_th. |
| `electricity_cost_inr_per_kwh` | ₹9.04/kWh | DERIVED | TNERC tariff order 27 March 2025, effective 1 July 2025 (FY 2026): HT industrial energy charge **₹7.50/kWh** (up 3.4% from ₹7.25) and demand charge **₹608/kVA/month** (up from ₹589). At 0.90 power factor and 60% load factor, one kVA delivers 394 kWh/month, so demand adds ₹1.54/kWh. 7.50 + 1.54 = ₹9.04. |
| `salt_cost_inr_per_kg` | ₹9/kg | PUBLISHED | Textile/detergent grade Glauber salt quoted ≈ ₹9/kg in bulk at 10 t MOQ on Indian industrial marketplaces. Higher-purity grades ₹22–58/kg; Indian sodium sulphate prices rose 7–8% in Q2 2026. |
| `mee_opex_inr_per_m3_reject` | ₹180/m³ | PUBLISHED | Antiscalant, cleaning, crystalliser and salt handling, maintenance — **excluding steam**, which is costed separately so energy is never double counted. Indian ZLD operating cost reported at ₹180–350/kL treated; we take the bottom of that band for the non-energy share. |

### 6.1 The economic asymmetry the product rests on

**Recycled water costs ~4× the freshwater it replaces** (₹185/kL against
₹45/kL), because adding the evaporator and crystalliser roughly doubles
the cost of a plant that stops at reverse osmosis.

Once a site is closed-loop, the marginal litre comes from the recycle
train, not the borewell. So **avoiding a litre of demand is worth far more
than recovering a litre of effluent** — which is why ChangeLoop intervenes
upstream of the demand rather than downstream of the waste.

`test_recycled_water_costs_more_than_freshwater` fails if this inverts. If
real site data ever inverts it, the product thesis needs restating, not
the test loosening.

### 6.2 The utilisation trap

TNPCB plant-level data shows CETPs charging **₹450 and ₹375/kL at 15% and
24% of design capacity**, against ₹150–220/kL at 30% and above. The
mechanism is self-reinforcing: charges rise on an underused plant, members
default or withdraw, throughput falls, charges rise again, until the plant
drops below the load it needs to hold its own standards.

This matters twice. It sets the upper bound on what the downstream
consequence can cost. And a cluster in the trap is exactly the cluster
where upstream demand reduction is worth the most per litre.

### 6.3 Where we are conservative on purpose

- Boiler non-fuel operating cost (DM water, ash handling, labour,
  maintenance — typically +8–12%) is **excluded** from steam cost, which
  understates the steam price and therefore understates the energy saving
  we report.
- `mee_opex` takes the **bottom** of the published ₹180–350/kL band, so our
  two cost components together stay inside the published envelope rather
  than exceeding it.
- Domestic coal is cheaper at source (₹5,200–6,600/t for 4,500–5,000 GCV,
  April 2026), but Tamil Nadu is far from the coalfields and the delivered
  price converges on the imported figure. We use the imported landed price
  because it needs no freight assumption.

### 6.4 Denominators — stated because they are easy to conflate

The published **₹180–350/kL is all-in per kL *treated***: biological
stage, membranes, thermal stage, labour, consumables, capital recovery.

What ChangeLoop models is narrower on purpose — the **marginal cost of the
thermal consequence that an upstream scheduling decision actually moves**:
evaporator steam, evaporator non-energy opex, RO pumping power. On the
reference load that is **≈ ₹108 per m³ treated**, which must sit below the
all-in figure; if it ever exceeded it, something would be double counted.
Checked by `test_marginal_zld_cost_sits_below_the_published_all_in_charge`.

---

## 7. Process levers — and why we under-claim both

The two levers are the reason this needs an optimiser rather than a
checklist: **one saves water without saving salt, the other saves salt
without saving water.**

| Coefficient | Value | Class | Published range | Source |
|---|---|---|---|---|
| `counter_current_water_multiplier` | 0.65 (35% saving) | PUBLISHED | **50–80% saving** (2 to 5 wash tanks); ~30% whole-mill from BAT packages | EU IPPC BAT Reference Document for the Textiles Industry |
| `low_salt_chemistry_salt_multiplier` | 0.55 (45% saving) | PUBLISHED | conventional **50–80 g/L** → low-salt **5–40 g/L**; midpoint-to-midpoint implies **0.35** | Reactive dyeing practice and low-electrolyte range literature |
| `counter_current_cost_inr_per_kg_fabric` | ₹0.35/kg | ASSUMED | — | Transfer pumping, holding-tank turnover, cycle-time cost. Commercial; tunable. |
| `low_salt_chemistry_cost_inr_per_kg_fabric` | ₹6.50/kg | ASSUMED | — | Range premium. Sized against dye cost: deep shade at 6% owf with dye ≈ ₹600/kg is ≈ ₹36/kg fabric of dye, so an 18% premium ≈ ₹6.5/kg. **The single most decision-relevant uncertainty in the model** — see the sensitivity sweep. |

**We deliberately claim less than the literature supports, on both
levers.** Counter-current at 35% is below the published 50–80%
single-technique range. Low-salt at 0.55 under-claims the 0.35 the
published ranges support at their midpoints. Two tests
(`test_we_underclaim_against_the_published_low_salt_benefit`,
`test_we_underclaim_against_the_published_countercurrent_benefit`) fail if
anyone ever tunes either lever toward the flattering end.

**Neither lever is our invention.** Counter-current rinsing has been Best
Available Technique for decades. Low-electrolyte reactive chemistry is
commercially available from several suppliers. What is ours is the
coupling: that they pull in opposite directions through the ZLD chain,
that the trade-off is therefore a constrained optimisation rather than a
best practice, and that it has to be solved at scheduling time to be worth
anything.

### 7.1 Our salt curve, validated

Our depth-of-shade electrolyte curve is a model. Published dyeing practice
gives **5–120 g/L** across shade depths, with **50–80 g/L** customary for
conventional ranges. Our reference lots come out at:

| Lot | Depth (% owf) | Our dose |
|---|---|---|
| L-4416 | 0.18 | 27.3 g/L |
| L-4413 | 0.35 | 29.6 g/L |
| L-4414 | 1.60 | 45.8 g/L |
| L-4412 | 4.60 | 84.8 g/L |
| L-4415 | 6.00 | 103.0 g/L |

Inside the published envelope at every point, and in the customary band
for mid-to-deep shades. Checked by
`test_salt_dose_curve_reproduces_published_envelope` and
`test_mid_to_deep_shades_sit_in_the_customary_band`. Under the low-salt
multiplier the same lots land inside the published 5–40 g/L low-salt band.

---

## 8. Process conditions

| Coefficient | Value | Class | Basis |
|---|---|---|---|
| `rinse_delta_t_k` | 55 K | ASSUMED | Soaping and hot-wash stages in reactive dyeing run near 80 °C against a ~25 °C ambient intake in Tamil Nadu. |

---

## 9. What remains ASSUMED, and why

Four coefficients. All four are **commercial prices or premiums that
public literature cannot settle**, because they are set by contract and
vary by site:

1. `low_salt_chemistry_cost_inr_per_kg_fabric` — dye range premium
2. `counter_current_cost_inr_per_kg_fabric` — cascade operating cost
3. `ro_specific_electrical_kwh_per_m3` — RO specific energy at site feed pressure
4. `rinse_delta_t_k` — site ambient and hot-wash setpoint

`test_assumptions_that_remain_are_genuinely_commercial` pins this exact
set. A future change that promotes one has to come to this file and say
why; one that *adds* to the set has to justify that public literature
cannot settle it.

---

## 10. What would promote this work to MEASURED

**One site visit. Two instruments.**

| Reading | Promotes | Why it carries the most weight |
|---|---|---|
| Steam flow to the evaporator | `mee_steam_economy`, `steam_cost_inr_per_kwh_th` | Converts reject volume into rupees and CO₂. Every headline figure passes through it. |
| RO reject conductivity | `ro_max_reject_tds_mg_l` | Sets `C_reject_max`, and therefore reject volume, and therefore everything downstream. |

Those two readings, with the site named and the date recorded, would move
the two load-bearing coefficients from PUBLISHED to MEASURED. The evidence
screen would say so without a line of code changing — the registry is the
single source of truth and the UI renders it.

Until then, this system is an honestly-labelled model that reproduces
published operating data. That is what it claims to be, and no more.

---

## 11. Source list

**Official / regulatory**

- Central Electricity Authority, Ministry of Power, Government of India —
  *CO₂ Baseline Database for the Indian Power Sector, User Guide Version
  22.0*, August 2026. Table S (combined margin FY 2025-26).
  `https://cea.nic.in/wp-content/uploads/baseline/2026/09/User_Guide__Version_22.0.pdf`
- Central Pollution Control Board — *Report on Assessment of Pollution
  from Textile Dyeing Units in Tirupur, Tamil Nadu, and Measures Taken to
  Achieve Zero Liquid Discharge*.
  `https://cpcb.nic.in/openpdffile.php?id=UmVwb3J0RmlsZXMvNDEwXzE0OTU3MTQzMzZfbWVkaWFwaG90bzQ1MjIucGRm`
- Tamil Nadu Electricity Regulatory Commission — Tariff Order,
  27 March 2025 (effective 1 July 2025).
  `https://tnerc.tn.gov.in/Orders/files/TO-Order%20No%20270320251635.pdf`
- European Commission IPPC — *Reference Document on Best Available
  Techniques for the Textiles Industry* (counter-current washing).

**Cluster economics and ZLD cost incidence**

- *Who Pays When Shared Infrastructure Fails? Zero Liquid Discharge, the
  Utilisation Trap, and the Incidence of Compliance Cost in India's Textile
  and Tannery Clusters* — TNPCB plant-level charge data.
  `https://arxiv.org/html/2609.32377v1`
- *ZLD Uptake and Socio-Technical Transitions in Tirupur*, Water
  Alternatives 10(2).
  `https://www.water-alternatives.org/index.php/alldoc/articles/vol10/v10issue2/372-a10-2-22/file`
- IL&FS — Tirupur ZLD Effluent Management Project.
- Down To Earth / India Environment Portal — Tirupur cluster water costs,
  tanker pricing, groundwater expenditure.
  `https://www.downtoearth.org.in/coverage/towards-zero-discharge-33489`

**Commodity and chemical pricing**

- Coal India press release, 10 April 2026; BigMint domestic thermal coal
  price assessments, April–May 2026.
- Indian industrial marketplace quotations for textile/detergent grade
  sodium sulphate (Glauber salt), 10 t MOQ; Q2 2026 price movement.

**Process chemistry**

- Reactive dyeing electrolyte practice for cellulose (5–120 g/L envelope;
  50–80 g/L customary) and low-electrolyte range literature (5–40 g/L),
  including salt-free and low-salt dyeing studies that cite conventional
  exhaustion (65–70% fixation) as their baseline.

---

## 12. How to re-check any of this

```bash
# the full validation harness
python -m pytest tests/test_published_validation.py -v

# the whole suite
python -m pytest tests/ -q

# the registry as the UI renders it
python -c "from core import factors; [print(f.evidence, f.key, f.value, f.unit) for f in factors.FACTORS.values()]"

# the live narrative, with numbers computed at request time
curl -s localhost:8000/api/validation | python -m json.tool
```

Every figure in this document is either in `core/factors.py` with its
`basis` string, or computed by the engine and asserted by a named test.
Nothing is transcribed by hand into a slide.
