# Archive — ClearLoop, L'Oréal Sustainability Challenge Edition

**Status: superseded.** Retained so this variant can be rebuilt if a
cosmetics / personal-care submission is ever needed again.

The current product (ChangeLoop, SANKALP edition) targets Indian textile
wet-processing under Zero Liquid Discharge. This document records what the
L'Oréal edition was, how to restore it, and which parts of it must be fixed
before it is ever submitted anywhere.

---

## 1. How to restore the full code

The complete working tree of this edition is preserved in git history. Nothing
was deleted permanently.

```bash
# Inspect it without disturbing the current branch
git show df37f7e --stat
git checkout df37f7e -- core/ backend/ frontend/ docs/ config/ tests/

# Or take the whole snapshot onto its own branch
git branch loreal-edition df37f7e
git switch loreal-edition
```

Reference commit: `df37f7e` — *"feat(benchmark): integrate global water
benchmark matrix, fleet scaling simulator, and decision continuity strips
across all views"*.

Earlier relevant commits:

| Commit | Content |
|---|---|
| `df37f7e` | Global water benchmark matrix, fleet scaling simulator |
| `5f46770` | Demo control dock layout, test-suite latency |
| `7b1bd39` | Fail-closed safety gate interlocks, deterministic session reset |
| `3cb39da` | 34-scenario destruction suite, invariant torture tests |
| `a76a7a3` | Gateway headline calibration, master solution audit |

---

## 2. What the edition was

**Name:** ClearLoop — Zero-Waste Changeover Engine
**Target:** L'Oréal Sustainability Challenge 2026
**Hook:** L'Oréal's public commitment to recycle and reuse 100% of industrial
process water in a closed loop by 2030 (56% reported in 2025).

**Four-layer thesis:**

1. **PREVENT** — optimise packaging/formulation changeover order with 2-opt
   local search to avoid cleaning demand before it is created.
2. **ADAPT** — read Clean-In-Place multi-sensor telemetry (conductivity,
   turbidity, temperature, flow, pH) and detect the cleanliness asymptote to
   end the final rinse early.
3. **CASCADE** — segregate CIP effluent into three streams (pre-rinse to
   biogas, caustic to recovery, final permeate to cooling towers), modelled
   on the Burgos "Waterloop" factory architecture.
4. **MEASURE** — one common baseline, anti-double-counting mass balance, hot
   water reduction converted to avoided boiler steam and Scope 1 GHG.

### Domain model

Cosmetic batches characterised by `family` (care / colour / styling),
`shade` (light / medium / dark), `viscosity`, `residue`, allergen flag,
priority and deadline. Pairwise changeover burden from
`config/changeover_rules.json`:

```json
{
  "base_litres_by_residue":  { "low": 120, "medium": 180, "high": 260 },
  "base_minutes_by_residue": { "low": 18,  "medium": 27,  "high": 40  },
  "transition_multipliers": {
    "same_family": 1.0, "dark_to_light": 1.55,
    "viscous_to_low": 1.3, "special_clean": 1.7
  }
}
```

Conversion factors used: `0.0697 kWh` per litre per 60 K rise,
`0.202 kg CO2e/kWh` natural-gas boiler, `0.015 kg NaOH` per litre,
EUR tariffs.

### Module map

| Module | Role |
|---|---|
| `core/domain.py` | Frozen dataclasses for every entity |
| `core/cleanability.py` | Transition burden rules, synthetic cosmetic products |
| `core/optimizer.py` | Greedy nearest-neighbour + 2-opt, baseline retention safeguard |
| `core/simulator.py` | 4-phase CIP telemetry with fault injection (missing / spike / drift / thermal) |
| `core/safety.py` | Deterministic safety state machine, 3-point clearance, never auto-releases |
| `core/cascade.py` | 3-stream segregation and quality screening |
| `core/impact.py` | Mass-balance ESG ledger |
| `core/economics.py` | Input-driven ROI, refuses to invent defaults |
| `core/audit.py` | SQLite audit trail with in-memory fallback |
| `core/demo.py` | Deterministic golden-path session orchestrator |
| `backend/server.py` | Dependency-free stdlib HTTP server + REST API |
| `frontend/` | Vanilla JS/CSS cockpit, ~7.3k JS and ~10.6k CSS |

### Frontend surfaces

Operator gateway (SSO / SmartBadge / FIDO2 mock), cockpit shell with
facility + line selectors, eight views (Overview, Planning, Optimizer,
Cleaning, Cascade, Impact/ESG, Scenarios, Pilot), 8-slide pitch deck
modal, guided 3-minute judge tour, UV-Vis spectroscopy inspection modal,
printable executive dossier. Keyboard shortcuts `P` deck, `T` tour,
`D` dossier, `M` audio, `1`–`0` view jumps.

---

## 3. Why it was superseded

SANKALP 2026 is an **India** student track, judged on innovation,
scalability, execution and vision, with a 2026-10-08 submission deadline.
Against that audience the L'Oréal framing was weak:

- A French cosmetics plant is remote from the water-stress reality an Indian
  climate jury assesses every day.
- The edition leaned on a single company's public target. SANKALP rewards a
  problem owned by a sector, not a brand.
- The replacement hero (textile ZLD) carries a verifiable Indian regulatory
  driver, a famous cluster, and a genuine energy–water coupling that yields a
  non-obvious insight. See `docs/strategy.md`.

---

## 4. Defects that MUST be fixed before resubmitting this edition

These were found during the forensic audit. They are listed because restoring
the branch restores the defects with it.

### Blocking

1. **The demo did not run the optimiser.** `core/demo.py` held a hardcoded
   `optimized_sequence = ["B-217","B-218","B-219","B-220","B-221"]`.
   `run_optimization()` only *evaluated* that fixed list; `score_order_two_opt`
   was imported and never called. The headline optimisation shown to judges
   was a constant.
2. **The changeover matrix was hand-authored.** `PLANNING_MATRIX_SPEC` was a
   lookup table with a planted 450 L bottleneck, not computed from the stated
   physics rules in `changeover_rules.json`.
3. **`core/decision_engine.py` was entirely hardcoded.** `2245.0`, `1284.0`,
   `1120.0` litres etc., ignoring the `from_batch` / `to_batch` arguments.
4. **Fake cryptographic claim.** `provenance_signature` was emitted as
   `"ECDSA-P256-SHA256:<first 16 hex of a SHA-256>"`. No key, no signature,
   no ECDSA. Either implement real signing or call it a hash chain.
5. **Cascade violated mass balance.** Stream volumes were `0.35·V`, `0.45·V`
   and `1.00·V`, summing to `1.8·V` from a `V` input.
6. **Client-supplied impact numbers.** `/api/cleaning/authorize` took
   `water_saved_l` (default 130) and `/api/water/authorize` took `volume_l`
   (default 145) from the request body and echoed them into the ledger.
7. **`calculate_impact_timespan_ledger` was hardcoded** (`3850.0`, `920.0`,
   `364.0`, `210.0` scaled by a range multiplier) and so could not agree with
   the engine. Dashboard, ledger and export were not the same number.
8. **`override_cascade_to_wwtp` set `volume_l = 0.0`**, destroying physical
   water instead of routing it to treatment.
9. **Fabricated standards.** "L'Oréal Hygiene Charter Q-502", "L'Oréal Clean
   Water Charter 2026" do not exist. Inventing a named company's internal
   standard is the fastest way to lose a technical jury.
10. **Unauthorised brand use.** Lancôme, YSL, Armani, Kérastase, Biotherm
    product names and a fictional named employee with a corporate email.

### Non-blocking but worth fixing

11. `simulator.py` derived avoided water as `minutes_avoided * 10.0 L/min`
    while the same simulation reported final-rinse flow near `8.5 L/min`.
12. Scope mixing: `common_baseline = 3850.0 L` per shift was reduced by
    savings computed from a five-batch, 862 L sequence.
13. `aware_factor` values (1.2 / 3.4 / 8.5) were labelled
    "WRI Aqueduct 4.0 / AWARE" without a source for those specific basins.
14. README asserted "4,021 Passing Tests" and "100.000% Safety Reliability"
    as badges; neither was reproduced during the audit.

---

## 5. Reusable assets

Worth lifting back out of this edition regardless of vertical:

- `core/safety.py` — the fail-closed state machine design is sound: it never
  auto-releases, and a missing or drifting sensor forces lockout rather than a
  pass. Carried forward into `core/telemetry.py`.
- `core/economics.py` — refusing to compute a business case until the user
  supplies site inputs, rather than shipping invented savings, is the right
  instinct. Carried forward.
- `core/audit.py` — SQLite with in-memory fallback. Carried forward and
  extended into a hash-chained ledger in `core/provenance.py`.
- The dependency-free stdlib server. No build step, nothing to install,
  runs anywhere Python 3 runs. Carried forward unchanged in spirit.
- The evidence-classification discipline (`REAL` / `SIMULATED` / `ASSUMED` /
  `ARCHITECTED`). Carried forward and tightened into `core/factors.py`.
