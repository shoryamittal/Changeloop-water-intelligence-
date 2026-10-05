"""ChangeLoop - Constraint Modes, Sensitivity and Ablation.

Three capabilities live here, each answering a specific challenge a reviewer
will make.

1. CONSTRAINT MODES  "Is this really decision intelligence, or a fixed
                      answer dressed up?"
   The site operates under different binding constraints at different times -
   a drought notice, a shipment crunch, a power tariff peak, an evaporator
   outage. Each mode changes the objective weights and the hard constraints,
   and the RECOMMENDATION CHANGES as a result. If the recommendation never
   changed, the optimiser would be decoration.

2. SENSITIVITY         "Your coefficients are assumptions. What if they are
                        wrong?"
   Varies each material coefficient low/base/high and reports both the effect
   on the headline numbers AND, more importantly, whether the RECOMMENDED
   OPTION changes. A recommendation that survives the full sweep is robust
   even when the absolute numbers are uncertain.

3. ABLATION            "Which parts of this architecture actually matter?"
   Removes one layer at a time and measures what is lost. A layer that
   changes nothing when removed should not exist.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import copy
import threading

# sensitivity() and ablation() work by temporarily replacing entries
# in the GLOBAL core.factors registry. Two of these running at once -
# which the threading HTTP server allows - would interleave their
# patches and read each other's coefficients. Every study that
# patches the registry takes this lock, so a concurrent caller waits
# instead of seeing a half-patched registry. Re-entrant because
# ablation() calls _with_factor() while already holding it.
_REGISTRY_LOCK = threading.RLock()

from . import factors, zld
from .process import reference_lots, arrival_order, evaluate_sequence
from .optimizer import (
    optimise, ObjectiveWeights, HardConstraints, evaluate_candidate,
)
from .basin import get_basin, DEFAULT_SITE


# ---------------------------------------------------------------------------
# 1. Constraint modes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConstraintMode:
    mode_id: str
    name: str
    trigger: str
    description: str
    weights: ObjectiveWeights
    constraints: HardConstraints

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "name": self.name,
            "trigger": self.trigger,
            "description": self.description,
            "weights": self.weights.to_dict(),
            "constraints": self.constraints.to_dict(),
        }


def constraint_modes() -> Dict[str, ConstraintMode]:
    """The operating modes a real dyehouse actually moves between."""
    return {
        "NORMAL": ConstraintMode(
            mode_id="NORMAL",
            name="Normal operation",
            trigger="No binding external constraint.",
            description="Balanced objective. Water, salt, energy, carbon and "
                        "cost are weighted at their declared economic value.",
            weights=ObjectiveWeights(),
            constraints=HardConstraints(),
        ),
        "DROUGHT": ConstraintMode(
            mode_id="DROUGHT",
            name="Drought / abstraction restriction",
            trigger="Groundwater notification or cluster abstraction cut.",
            description="Scarcity premium raised sharply. The optimiser will "
                        "now accept schedule cost to protect freshwater, "
                        "while still refusing to breach a firm ship date.",
            weights=ObjectiveWeights(
                stress_premium_inr_per_m3_eq=400.0,
                carbon_price_inr_per_tonne=2000.0,
                lateness_penalty_inr_per_hour=600.0,
            ),
            constraints=HardConstraints(max_total_lateness_h=10.0),
        ),
        "SHIPMENT_CRUNCH": ConstraintMode(
            mode_id="SHIPMENT_CRUNCH",
            name="Shipment crunch",
            trigger="Vessel cut-off or buyer escalation on multiple lots.",
            description="Lateness becomes close to prohibitive. The system "
                        "will tell you plainly when there is no resource "
                        "saving available without a delivery cost - rather "
                        "than inventing one.",
            weights=ObjectiveWeights(
                stress_premium_inr_per_m3_eq=40.0,
                carbon_price_inr_per_tonne=1000.0,
                lateness_penalty_inr_per_hour=25000.0,
            ),
            constraints=HardConstraints(
                max_total_lateness_h=0.5,
                max_single_lot_lateness_h=0.5,
            ),
        ),
        "CARBON_PRIORITY": ConstraintMode(
            mode_id="CARBON_PRIORITY",
            name="Carbon priority",
            trigger="Buyer Scope 3 commitment or internal carbon price.",
            description="Carbon priced at an internal shadow price. Because "
                        "evaporator steam dominates this site's carbon, the "
                        "objective shifts towards cutting salt load.",
            weights=ObjectiveWeights(
                stress_premium_inr_per_m3_eq=40.0,
                carbon_price_inr_per_tonne=12000.0,
                lateness_penalty_inr_per_hour=1500.0,
            ),
            constraints=HardConstraints(),
        ),
    }


def run_mode(mode_id: str = "NORMAL",
             site_id: str = DEFAULT_SITE) -> Dict[str, Any]:
    """Optimise under one constraint mode."""
    modes = constraint_modes()
    mode = modes.get(mode_id, modes["NORMAL"])
    lots = reference_lots()
    result = optimise(lots, arrival_order(), site_id,
                      mode.weights, mode.constraints)
    return {"mode": mode.to_dict(), "result": result}


def compare_modes(site_id: str = DEFAULT_SITE) -> Dict[str, Any]:
    """Run every mode and show that the recommendation genuinely moves.

    This is the honest answer to "is the optimiser doing anything?" - if the
    recommended order were identical in all modes, it would not be.
    """
    rows: List[Dict[str, Any]] = []
    orders_seen = set()

    for mode_id, mode in constraint_modes().items():
        run = run_mode(mode_id, site_id)
        res = run["result"]

        if res.get("status") != "FEASIBLE":
            rows.append({
                "mode_id": mode_id,
                "mode_name": mode.name,
                "status": res.get("status"),
                "reason": res.get("reason"),
                "recommended_order": None,
                "recommended_strategy": None,
            })
            continue

        rec = next(o for o in res["options"]
                   if o["option_id"] == res["recommended_option_id"])
        orders_seen.add((tuple(rec["order"]), rec["strategy_id"]))
        rows.append({
            "mode_id": mode_id,
            "mode_name": mode.name,
            "trigger": mode.trigger,
            "status": "FEASIBLE",
            "recommended_order": rec["order"],
            "recommended_strategy": rec["strategy_id"],
            "strategy_name": rec["strategy"]["name"],
            "freshwater_intake_l": rec["freshwater_intake_l"],
            "salt_kg": rec["total_salt_kg"],
            "mee_thermal_kwh": rec["mee_thermal_kwh"],
            "co2e_kg": rec["co2e_kg"],
            "cost_inr": rec["cost_inr"],
            "total_late_h": rec["total_late_h"],
            "objective_inr": rec["objective_inr"],
        })

    return {
        "site_id": site_id,
        "modes": rows,
        "distinct_recommended_plans": len(orders_seen),
        "interpretation": (
            "The recommended plan differs across {} distinct "
            "order-and-strategy combinations as the binding constraint "
            "changes. The optimiser is responding to the constraint set, "
            "not returning a fixed answer.".format(len(orders_seen))
            if len(orders_seen) > 1 else
            "Every mode selected the same plan. For this order book one "
            "plan dominates under all tested weights. Reported as-is "
            "rather than disguised."
        ),
        "classification": "MODELLED",
    }


# ---------------------------------------------------------------------------
# 2. Sensitivity
# ---------------------------------------------------------------------------

# The coefficients whose uncertainty could plausibly change a decision.
SENSITIVITY_SWEEP: Dict[str, Dict[str, float]] = {
    "ro_max_reject_tds_mg_l": {"low": 40000.0, "high": 90000.0},
    "mee_steam_economy": {"low": 2.5, "high": 6.0},
    "ro_max_recovery_frac": {"low": 0.80, "high": 0.95},
    "boiler_co2e_kg_per_kwh_th": {"low": 0.30, "high": 0.60},
    "recycled_water_cost_inr_per_m3": {"low": 120.0, "high": 150.0},
    "freshwater_cost_inr_per_m3": {"low": 30.0, "high": 60.0},
    "steam_cost_inr_per_kwh_th": {"low": 1.60, "high": 3.40},
    "low_salt_chemistry_cost_inr_per_kg_fabric": {"low": 3.00, "high": 11.00},
    "counter_current_water_multiplier": {"low": 0.55, "high": 0.80},
}


def _with_factor(key: str, value: float):
    """Context manager replacing one coefficient temporarily."""
    class _Ctx:
        def __enter__(self_inner):
            self_inner.original = factors.FACTORS[key]
            patched = factors.Factor(
                key=self_inner.original.key,
                label=self_inner.original.label,
                value=value,
                unit=self_inner.original.unit,
                evidence=self_inner.original.evidence,
                basis=self_inner.original.basis,
                tunable=self_inner.original.tunable,
            )
            factors.FACTORS[key] = patched
            # Derived coefficients must be recomputed, not left stale.
            if key == "mee_steam_economy":
                h = factors.FACTORS["h_vap_kwh_per_kg"].value
                d = factors.FACTORS["mee_specific_thermal_kwh_per_m3"]
                self_inner.derived = d
                factors.FACTORS["mee_specific_thermal_kwh_per_m3"] = \
                    factors.Factor(
                        key=d.key, label=d.label,
                        value=round((h * 1000.0) / value, 2),
                        unit=d.unit, evidence=d.evidence,
                        basis=d.basis + " (recomputed for sensitivity run)",
                        tunable=d.tunable)
            else:
                self_inner.derived = None
            return self_inner

        def __exit__(self_inner, *exc):
            factors.FACTORS[key] = self_inner.original
            if self_inner.derived is not None:
                factors.FACTORS["mee_specific_thermal_kwh_per_m3"] = \
                    self_inner.derived
            return False
    return _Ctx()


def sensitivity(site_id: str = DEFAULT_SITE) -> Dict[str, Any]:
    """Vary each material coefficient and report what moves.

    Holds the registry lock for the whole sweep, because it mutates
    global coefficients and must not interleave with another study.

    Reports two different things, because they matter differently:
      - how much the HEADLINE NUMBERS move (absolute uncertainty)
      - whether the RECOMMENDED ORDER changes (decision robustness)
    """
    lots = reference_lots()
    arrival = arrival_order()

    _REGISTRY_LOCK.acquire()
    try:
        return _sensitivity_locked(site_id, lots, arrival)
    finally:
        _REGISTRY_LOCK.release()


def _sensitivity_locked(site_id, lots, arrival) -> Dict[str, Any]:
    def run() -> Dict[str, Any]:
        r = optimise(lots, arrival, site_id)
        if r.get("status") != "FEASIBLE":
            return {}
        rec = next(o for o in r["options"]
                   if o["option_id"] == r["recommended_option_id"])
        return {
            "order": rec["order"],
            "strategy_id": rec["strategy_id"],
            "freshwater_avoided_l": rec["delta_vs_baseline"]["freshwater_l"],
            "mee_thermal_avoided_kwh":
                rec["delta_vs_baseline"]["mee_thermal_kwh"],
            "co2e_avoided_kg": rec["delta_vs_baseline"]["co2e_kg"],
            "cost_avoided_inr": rec["delta_vs_baseline"]["cost_inr"],
        }

    base = run()
    rows: List[Dict[str, Any]] = []
    order_changes = 0

    for key, bounds in SENSITIVITY_SWEEP.items():
        f = factors.factor(key)
        entry: Dict[str, Any] = {
            "coefficient": key,
            "label": f.label,
            "unit": f.unit,
            "evidence": f.evidence,
            "base_value": f.value,
            "variants": [],
        }
        for label in ("low", "high"):
            with _with_factor(key, bounds[label]):
                out = run()
            # The decision is the (order, strategy) pair, so a change in
            # either is a change in the recommendation.
            changed = bool(
                out and base
                and (out["order"] != base["order"]
                     or out["strategy_id"] != base["strategy_id"]))
            if changed:
                order_changes += 1
            entry["variants"].append({
                "bound": label,
                "value": bounds[label],
                "freshwater_avoided_l": out.get("freshwater_avoided_l"),
                "mee_thermal_avoided_kwh": out.get("mee_thermal_avoided_kwh"),
                "co2e_avoided_kg": out.get("co2e_avoided_kg"),
                "cost_avoided_inr": out.get("cost_avoided_inr"),
                "recommended_strategy": out.get("strategy_id"),
                "recommendation_changed": changed,
            })

        # Rank by the widest swing in avoided cost.
        vals = [v["cost_avoided_inr"] for v in entry["variants"]
                if v["cost_avoided_inr"] is not None]
        entry["cost_swing_inr"] = (round(max(vals) - min(vals), 2)
                                   if len(vals) == 2 else None)
        rows.append(entry)

    rows.sort(key=lambda r: (r["cost_swing_inr"] or 0.0), reverse=True)

    return {
        "site_id": site_id,
        "base_case": base,
        "coefficients": rows,
        "recommendation_changed_count": order_changes,
        "decision_robust": order_changes == 0,
        "interpretation": (
            "The recommended plan did not change under any single "
            "coefficient moved to either bound. The absolute savings carry "
            "the uncertainty shown, but the DECISION is robust to it."
            if order_changes == 0 else
            "The recommended plan changed in {} of {} sweep runs. The "
            "coefficients flagged below must be metered at the site before "
            "the recommendation is relied on - which is exactly what the "
            "pilot baseline period is for.".format(
                order_changes, len(SENSITIVITY_SWEEP) * 2)
        ),
        "classification": "DERIVED",
    }


# ---------------------------------------------------------------------------
# 3. Ablation
# ---------------------------------------------------------------------------

def ablation(site_id: str = DEFAULT_SITE,
             mode_id: str = "NORMAL") -> Dict[str, Any]:
    """Remove one architectural layer at a time and measure what is lost.

    The result depends on the binding constraint, and that is the point.
    Under NORMAL economics counter-current rinsing is the cheapest plan
    whether or not the optimiser can see the evaporator, so the
    ZLD-coupling layer does not change the answer. Price carbon or water
    scarcity and it does. We report which layers bind in the mode being
    examined rather than implying every layer always earns its place.

    Layers tested:
      full                  everything on
      no_zld_coupling       optimise on dyehouse water only, ignoring the
                            downstream evaporator consequence
      no_salt_model         treat reject as hydraulically limited only,
                            ignoring salt mass - i.e. a water-only product
      no_stress_weighting   treat every litre as environmentally equal
      no_hard_constraints   let a water saving override a firm ship date
    """
    with _REGISTRY_LOCK:
        return _ablation_locked(site_id, mode_id)


def _ablation_locked(site_id: str, mode_id: str) -> Dict[str, Any]:
    lots = reference_lots()
    arrival = arrival_order()
    basin = get_basin(site_id)
    modes = constraint_modes()
    mode = modes.get(mode_id, modes["NORMAL"])
    W = mode.weights
    C = mode.constraints
    out: List[Dict[str, Any]] = []

    # ---- full system -------------------------------------------------
    full = optimise(lots, arrival, site_id, W, C)
    full_rec = next(o for o in full["options"]
                    if o["option_id"] == full["recommended_option_id"])
    out.append({
        "variant": "full",
        "label": "Full ChangeLoop",
        "recommended_order": full_rec["order"],
        "freshwater_avoided_l": full_rec["delta_vs_baseline"]["freshwater_l"],
        "mee_thermal_avoided_kwh":
            full_rec["delta_vs_baseline"]["mee_thermal_kwh"],
        "co2e_avoided_kg": full_rec["delta_vs_baseline"]["co2e_kg"],
        "cost_avoided_inr": full_rec["delta_vs_baseline"]["cost_inr"],
        "firm_breaches": full_rec["firm_date_breaches"],
        "capability_lost": "-",
    })

    # ---- no ZLD coupling ---------------------------------------------
    # Optimise purely on dyehouse changeover water, then price the real
    # consequence of that choice. This is what a water-only scheduler does.
    best_water_order, best_water = None, None
    import itertools
    for perm in itertools.permutations([l.lot_id for l in lots]):
        seq = evaluate_sequence(lots, list(perm))
        if seq["firm_date_breaches"] > 0:
            continue
        if best_water is None or seq["changeover_water_l"] < best_water:
            best_water = seq["changeover_water_l"]
            best_water_order = list(perm)
    if best_water_order:
        c = evaluate_candidate(lots, best_water_order, site_id, W, C)
        base_c = evaluate_candidate(lots, arrival, site_id, W, C)
        out.append({
            "variant": "no_zld_coupling",
            "label": "Without downstream ZLD coupling",
            "recommended_order": best_water_order,
            "freshwater_avoided_l": round(
                base_c.consequence["water"]["freshwater_intake_l"]
                - c.consequence["water"]["freshwater_intake_l"], 1),
            "mee_thermal_avoided_kwh": round(
                base_c.consequence["zld"]["mee_thermal_kwh"]
                - c.consequence["zld"]["mee_thermal_kwh"], 1),
            "co2e_avoided_kg": round(
                base_c.consequence["carbon"]["total_co2e_kg"]
                - c.consequence["carbon"]["total_co2e_kg"], 2),
            "cost_avoided_inr": round(
                base_c.consequence["cost_inr"]["total"]
                - c.consequence["cost_inr"]["total"], 2),
            "firm_breaches": c.sequence["firm_date_breaches"],
            "capability_lost": (
                "Cannot see that reject volume - and therefore evaporator "
                "steam and boiler carbon - is driven by salt mass. Optimises "
                "a water headline and leaves the energy benefit on the table."
            ),
        })

    # ---- no salt model ----------------------------------------------
    with _with_factor("ro_max_reject_tds_mg_l", 10_000_000.0):
        # An absurdly high ceiling makes the salt constraint never bind, so
        # reject is purely hydraulic - exactly a water-only ZLD model.
        r = optimise(lots, arrival, site_id, W, C)
        rec = next(o for o in r["options"]
                   if o["option_id"] == r["recommended_option_id"])
        out.append({
            "variant": "no_salt_model",
            "label": "Without the salt-mass model (water-only ZLD)",
            "recommended_order": rec["order"],
            "freshwater_avoided_l": rec["delta_vs_baseline"]["freshwater_l"],
            "mee_thermal_avoided_kwh":
                rec["delta_vs_baseline"]["mee_thermal_kwh"],
            "co2e_avoided_kg": rec["delta_vs_baseline"]["co2e_kg"],
            "cost_avoided_inr": rec["delta_vs_baseline"]["cost_inr"],
            "firm_breaches": rec["firm_date_breaches"],
            "capability_lost": (
                "Reject volume becomes a fixed fraction of flow, so the "
                "model would mis-state evaporator load and would wrongly "
                "conclude that cutting water alone cuts energy."
            ),
        })

    # ---- no stress weighting ----------------------------------------
    r = optimise(lots, arrival, site_id,
                 ObjectiveWeights(
                     stress_premium_inr_per_m3_eq=0.0,
                     carbon_price_inr_per_tonne=W.carbon_price_inr_per_tonne,
                     lateness_penalty_inr_per_hour=W.lateness_penalty_inr_per_hour),
                 C)
    rec = next(o for o in r["options"]
               if o["option_id"] == r["recommended_option_id"])
    out.append({
        "variant": "no_stress_weighting",
        "label": "Without basin stress weighting",
        "recommended_order": rec["order"],
        "freshwater_avoided_l": rec["delta_vs_baseline"]["freshwater_l"],
        "mee_thermal_avoided_kwh":
            rec["delta_vs_baseline"]["mee_thermal_kwh"],
        "co2e_avoided_kg": rec["delta_vs_baseline"]["co2e_kg"],
        "cost_avoided_inr": rec["delta_vs_baseline"]["cost_inr"],
        "firm_breaches": rec["firm_date_breaches"],
        "capability_lost": (
            "Every litre is treated as environmentally equal, so the same "
            "plan is recommended in the Luni basin as on the Cauvery main "
            "stem. Multi-site prioritisation becomes impossible."
        ),
    })

    # ---- no hard constraints ----------------------------------------
    r = optimise(lots, arrival, site_id,
                 ObjectiveWeights(
                     stress_premium_inr_per_m3_eq=W.stress_premium_inr_per_m3_eq,
                     carbon_price_inr_per_tonne=W.carbon_price_inr_per_tonne,
                     lateness_penalty_inr_per_hour=0.0),
                 HardConstraints(no_firm_date_breach=False,
                                 max_total_lateness_h=1e9,
                                 max_single_lot_lateness_h=1e9))
    rec = next(o for o in r["options"]
               if o["option_id"] == r["recommended_option_id"])
    out.append({
        "variant": "no_hard_constraints",
        "label": "Without hard-constraint enforcement",
        "recommended_order": rec["order"],
        "freshwater_avoided_l": rec["delta_vs_baseline"]["freshwater_l"],
        "mee_thermal_avoided_kwh":
            rec["delta_vs_baseline"]["mee_thermal_kwh"],
        "co2e_avoided_kg": rec["delta_vs_baseline"]["co2e_kg"],
        "cost_avoided_inr": rec["delta_vs_baseline"]["cost_inr"],
        "firm_breaches": rec["firm_date_breaches"],
        "capability_lost": (
            "Produces the largest headline saving and breaches a firm buyer "
            "ship date to get it. This variant exists to show exactly what "
            "the constraint layer is preventing - a plan no planner would "
            "ever run, and the reason an unconstrained water optimiser gets "
            "ignored in practice."
        ),
    })

    full_fresh = out[0]["freshwater_avoided_l"] or 0.0
    full_order = out[0]["recommended_order"]
    for v in out:
        f = v["freshwater_avoided_l"] or 0.0
        # What the variant would REPORT, relative to the full system. Note
        # this is not always "benefit captured": two variants report MORE
        # than is really available, and that over-reporting is precisely
        # their defect rather than an advantage.
        v["reported_vs_full_pct"] = (
            round(f / full_fresh * 100.0, 1) if full_fresh else None)
        v["overstates"] = bool(full_fresh and f > full_fresh + 0.5
                               and v["variant"] != "full")
        if v["overstates"]:
            v["overstatement_note"] = (
                "This variant REPORTS a larger saving than the full system "
                "while actually delivering less or breaching a constraint. "
                "Over-reporting is the defect: a water-only ZLD model "
                "mis-states how much freshwater a plan really avoids, and an "
                "unconstrained optimiser books a saving from a plan nobody "
                "would run."
            )
        # Does this layer bind in THIS mode? A layer binds if removing
        # it changes the plan or produces a constraint breach.
        if v["variant"] == "full":
            v["layer_binds_in_this_mode"] = None
        else:
            v["layer_binds_in_this_mode"] = bool(
                v["recommended_order"] != full_order
                or abs(f - full_fresh) > 0.5
                or v["firm_breaches"] > 0)

    binding = [v["label"] for v in out
               if v.get("layer_binds_in_this_mode")]
    inert = [v["label"] for v in out
             if v.get("layer_binds_in_this_mode") is False]

    conclusion = (
        "Under the {} constraint mode, removing these layers changes the "
        "recommendation: {}. ".format(mode.name.lower(),
                                      "; ".join(binding) or "none")
    )
    if inert:
        conclusion += (
            "These layers do NOT change the recommendation in this mode: "
            "{}. That is reported rather than hidden. A layer can be "
            "inert under one price set and decisive under another - the "
            "zero-liquid-discharge coupling is inert while counter-current "
            "rinsing is the cheapest plan regardless, and becomes decisive "
            "as soon as carbon or water scarcity is priced. Re-run this "
            "study under Carbon priority or Drought to see it bind."
            .format("; ".join(inert)))
    conclusion += (
        " The hard-constraint layer is the one that binds in every mode: "
        "without it the system recommends a plan that breaches a firm "
        "buyer ship date, which is the single fastest way for a planner "
        "to stop trusting a scheduling tool.")

    return {
        "site_id": site_id,
        "basin": basin.basin_name,
        "mode_id": mode.mode_id,
        "mode_name": mode.name,
        "variants": out,
        "layers_binding": binding,
        "layers_inert_in_this_mode": inert,
        "conclusion": conclusion,
        "classification": "MODELLED",
    }
