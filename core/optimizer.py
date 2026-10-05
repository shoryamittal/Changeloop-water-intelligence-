"""ChangeLoop - Constrained Multi-Objective Decision Optimiser.

What this is
------------
A transparent combinatorial optimiser over two decision dimensions:

    LOT ORDER         which sequence the dye lots run in
    PROCESS STRATEGY  how the wash-off is run (conventional, counter-current
                      rinse reuse, low-electrolyte chemistry, or both)

It is NOT a machine-learning model and the product does not claim one. The
decision space is small and discrete, the objective is a weighted sum of
physically computed consequences, and the constraints are hard. A
deterministic search is the correct tool: it is auditable line by line and it
cannot hallucinate.

Search strategy
---------------
  n <= 8   exhaustive enumeration over order x strategy. The optimum is
           PROVEN, and the system says so.
  n > 8    nearest-neighbour construction plus 2-opt local search, run for
           each strategy. The system then reports "local optimum, not proven".

Honesty about what is novel
---------------------------
Ascending shade sequencing is standard dyehouse practice. Counter-current
rinsing is established best available technique. Low-electrolyte reactive
dyes are a commercial product category. None is claimed here as an
invention, and the UI says so explicitly.

Two things are genuinely different:

  1. The objective includes the DOWNSTREAM zero-liquid-discharge consequence
     of each candidate - evaporator steam, boiler carbon and treatment cost.
     A planner optimising on shade practice or water volume alone cannot see
     that term, and the ablation study quantifies how much they miss.
  2. Hard constraints are enforced as FEASIBILITY, not as a penalty that a
     large enough water saving can buy its way out of. A plan that breaches
     a firm ship date is reported infeasible and cannot be recommended,
     whatever it saves.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
import itertools
import math

from .process import DyeLot, evaluate_sequence, strategies, DEFAULT_STRATEGY
from . import zld


EXHAUSTIVE_LIMIT = 8


@dataclass
class ObjectiveWeights:
    """Weights for the scalarised objective.

    Each weight converts a physical consequence onto a common comparable
    scale. The defaults make cost in rupees the common denominator, which
    keeps the objective interpretable: the optimiser minimises total rupees
    of environmental and operational consequence, with an explicit scarcity
    premium on stressed-basin freshwater and an explicit carbon price.

    These weights encode a value judgement, so they are shown to the user
    rather than buried.
    """
    stress_premium_inr_per_m3_eq: float = 40.0
    carbon_price_inr_per_tonne: float = 2000.0
    lateness_penalty_inr_per_hour: float = 1500.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HardConstraints:
    """Constraints a candidate must satisfy to be recommendable at all."""
    no_firm_date_breach: bool = True
    max_total_lateness_h: float = 6.0
    max_single_lot_lateness_h: float = 4.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Candidate:
    """One evaluated (lot order, process strategy) pair."""
    order: List[str]
    strategy_id: str
    feasible: bool
    violations: List[str]
    objective_inr: float
    sequence: Dict[str, Any]
    consequence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "strategy_id": self.strategy_id,
            "feasible": self.feasible,
            "violations": self.violations,
            "objective_inr": round(self.objective_inr, 2),
            "sequence": self.sequence,
            "consequence": self.consequence,
        }


def check_constraints(seq_eval: Dict[str, Any],
                      constraints: HardConstraints) -> List[str]:
    """Return the hard-constraint violations for a candidate."""
    v: List[str] = []
    if constraints.no_firm_date_breach and seq_eval["firm_date_breaches"] > 0:
        breached = [l["lot_id"] for l in seq_eval["lateness"]
                    if l["breaches_firm_date"]]
        v.append(
            "Firm ship date breached on {}. A confirmed buyer delivery date "
            "is a hard constraint and cannot be traded for water."
            .format(", ".join(breached))
        )
    if seq_eval["total_late_h"] > constraints.max_total_lateness_h:
        v.append(
            "Total schedule lateness {:.2f} h exceeds the {:.1f} h limit."
            .format(seq_eval["total_late_h"],
                    constraints.max_total_lateness_h)
        )
    worst = max((l["late_h"] for l in seq_eval["lateness"]), default=0.0)
    if worst > constraints.max_single_lot_lateness_h:
        v.append(
            "Single-lot lateness {:.2f} h exceeds the {:.1f} h limit."
            .format(worst, constraints.max_single_lot_lateness_h)
        )
    return v


def evaluate_candidate(lots: List[DyeLot],
                       order: List[str],
                       site_id: str,
                       weights: ObjectiveWeights,
                       constraints: HardConstraints,
                       strategy_id: str = DEFAULT_STRATEGY) -> Candidate:
    """Evaluate one candidate end to end: process -> ZLD -> objective."""
    seq = evaluate_sequence(lots, order, strategy_id)
    cons = zld.evaluate_scenario(
        process_water_l=seq["process_water_l"],
        process_salt_kg=seq["process_salt_kg"],
        changeover_water_l=seq["changeover_water_l"],
        changeover_salt_kg=seq["changeover_salt_kg"],
        site_id=site_id,
    )

    # Scalarised objective, in rupees of total consequence. The strategy's
    # own process cost is included, so a lever is only selected when the
    # consequence it avoids is worth more than the lever itself costs.
    cost = cons["cost_inr"]["total"] + seq["strategy_cost_inr"]
    stress_m3_eq = cons["stress_equivalent_l_eq"] / 1000.0
    stress_term = stress_m3_eq * weights.stress_premium_inr_per_m3_eq
    carbon_term = (cons["carbon"]["total_co2e_kg"] / 1000.0
                   * weights.carbon_price_inr_per_tonne)
    lateness_term = (seq["total_late_h"]
                     * weights.lateness_penalty_inr_per_hour)

    objective = cost + stress_term + carbon_term + lateness_term
    violations = check_constraints(seq, constraints)

    return Candidate(
        order=list(order),
        strategy_id=strategy_id,
        feasible=(len(violations) == 0),
        violations=violations,
        objective_inr=objective,
        sequence=seq,
        consequence=cons,
    )


def _nearest_neighbour(lots: List[DyeLot]) -> List[str]:
    """Greedy construction: repeatedly append the cheapest next lot."""
    from .process import changeover_burden
    index = {l.lot_id: l for l in lots}
    remaining = [l.lot_id for l in lots]
    start = min(remaining,
                key=lambda lid: (index[lid].due_h, index[lid].priority))
    order = [start]
    remaining.remove(start)
    while remaining:
        cur = index[order[-1]]

        def step_cost(lid: str) -> Tuple[float, float]:
            nxt = index[lid]
            co = changeover_burden(cur, nxt)
            return (co.water_l + co.salt_kg * 50.0, nxt.due_h)

        nxt_id = min(remaining, key=step_cost)
        order.append(nxt_id)
        remaining.remove(nxt_id)
    return order


def _two_opt(lots: List[DyeLot],
             order: List[str],
             site_id: str,
             weights: ObjectiveWeights,
             constraints: HardConstraints,
             strategy_id: str,
             max_passes: int = 40) -> List[str]:
    """2-opt local search on the scalarised objective.

    Infeasible candidates rank behind every feasible one, so the search will
    not walk into a constraint violation to chase a lower objective.
    """
    def key(o: List[str]) -> Tuple[int, float]:
        c = evaluate_candidate(lots, o, site_id, weights, constraints,
                               strategy_id)
        return (0 if c.feasible else 1, c.objective_inr)

    best = list(order)
    best_key = key(best)
    n = len(best)
    if n < 4:
        return best

    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(n - 1):
            for j in range(i + 1, n):
                cand = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                ck = key(cand)
                if ck < best_key:
                    best, best_key = cand, ck
                    improved = True
                    break
            if improved:
                break
    return best


def optimise(lots: List[DyeLot],
             arrival_order: List[str],
             site_id: str = "IN-TN-TIRUPUR-01",
             weights: Optional[ObjectiveWeights] = None,
             constraints: Optional[HardConstraints] = None) -> Dict[str, Any]:
    """Produce the baseline, the recommendation and the rejected extreme.

    Always returns comparable options so the user sees a trade-off rather
    than a single oracle answer:

      A  the arrival order under current practice - what happens with no
         intervention, and the baseline every saving is measured against.
      B  the best FEASIBLE plan under the hard constraints. Recommended.
      C  the plan that minimises freshwater regardless of constraints,
         included precisely so that its infeasibility is visible.
    """
    w = weights or ObjectiveWeights()
    c = constraints or HardConstraints()

    for lot in lots:
        err = lot.validate()
        if err:
            return {"status": "INFEASIBLE_INPUT", "reason": err,
                    "classification": "MODELLED"}

    ids = [l.lot_id for l in lots]
    if sorted(arrival_order) != sorted(ids):
        return {"status": "INFEASIBLE_INPUT",
                "reason": "Arrival order does not match the lot set.",
                "classification": "MODELLED"}

    n = len(ids)
    strat_ids = list(strategies().keys())

    baseline = evaluate_candidate(lots, arrival_order, site_id, w, c,
                                  DEFAULT_STRATEGY)

    # ---- search over (order x strategy) ------------------------------
    if n <= EXHAUSTIVE_LIMIT:
        all_c = [evaluate_candidate(lots, list(p), site_id, w, c, sid)
                 for p in itertools.permutations(ids)
                 for sid in strat_ids]
        method = ("Exhaustive enumeration of {} orders x {} process "
                  "strategies = {} candidates".format(
                      math.factorial(n), len(strat_ids), len(all_c)))
        optimality = "PROVEN_GLOBAL_OPTIMUM"
    else:
        seeds = [list(arrival_order), _nearest_neighbour(lots)]
        seen = set()
        all_c = []
        for sid in strat_ids:
            refined = [_two_opt(lots, sd, site_id, w, c, sid) for sd in seeds]
            for o in seeds + refined:
                tkey = (tuple(o), sid)
                if tkey not in seen:
                    seen.add(tkey)
                    all_c.append(evaluate_candidate(
                        lots, list(o), site_id, w, c, sid))
        method = ("Nearest-neighbour construction with 2-opt local search "
                  "over {} process strategies".format(len(strat_ids)))
        optimality = "LOCAL_OPTIMUM_NOT_PROVEN"

    searched = len(all_c)
    feasible = [x for x in all_c if x.feasible]

    if not feasible:
        return {
            "status": "NO_FEASIBLE_OPTION",
            "reason": ("No plan satisfies the hard constraints. The queue "
                       "itself has to change: a lot must move to another "
                       "machine or a delivery date must be renegotiated. "
                       "ChangeLoop does not recommend breaching a "
                       "constraint, so it returns nothing here rather than "
                       "the least-bad violation."),
            "baseline": baseline.to_dict(),
            "constraints": c.to_dict(),
            "classification": "MODELLED",
        }

    recommended = min(feasible, key=lambda x: x.objective_inr)

    # The unconstrained freshwater minimiser, kept visible on purpose.
    water_min = min(
        all_c,
        key=lambda x: (x.consequence["water"]["freshwater_intake_l"],
                       x.sequence["total_late_h"]),
    )

    def option(cand: Candidate, oid: str, title: str, desc: str,
               recommend: bool) -> Dict[str, Any]:
        cw = cand.consequence
        bw = baseline.consequence
        base_total = (bw["cost_inr"]["total"]
                      + baseline.sequence["strategy_cost_inr"])
        cand_total = (cw["cost_inr"]["total"]
                      + cand.sequence["strategy_cost_inr"])
        return {
            "option_id": oid,
            "title": title,
            "description": desc,
            "order": cand.order,
            "strategy_id": cand.strategy_id,
            "strategy": cand.sequence["strategy"],
            "strategy_cost_inr": cand.sequence["strategy_cost_inr"],
            "is_recommended": recommend,
            "feasible": cand.feasible,
            "violations": cand.violations,

            "changeover_water_l": cand.sequence["changeover_water_l"],
            "changeover_salt_kg": cand.sequence["changeover_salt_kg"],
            "freshwater_intake_l": cw["water"]["freshwater_intake_l"],
            "permeate_reuse_l": cw["water"]["permeate_reuse_l"],
            "stress_equivalent_l_eq": cw["stress_equivalent_l_eq"],
            "total_salt_kg": cw["salt"]["total_salt_kg"],
            "ro_reject_l": cw["zld"]["reject_l"],
            "mee_thermal_kwh": cw["zld"]["mee_thermal_kwh"],
            "site_energy_kwh": cw["energy"]["total_site_energy_kwh"],
            "co2e_kg": cw["carbon"]["total_co2e_kg"],
            "cost_inr": round(cand_total, 2),
            "total_late_h": cand.sequence["total_late_h"],
            "firm_date_breaches": cand.sequence["firm_date_breaches"],
            "objective_inr": round(cand.objective_inr, 2),

            "delta_vs_baseline": {
                "freshwater_l": round(
                    bw["water"]["freshwater_intake_l"]
                    - cw["water"]["freshwater_intake_l"], 1),
                "stress_l_eq": round(
                    bw["stress_equivalent_l_eq"]
                    - cw["stress_equivalent_l_eq"], 1),
                "salt_kg": round(bw["salt"]["total_salt_kg"]
                                 - cw["salt"]["total_salt_kg"], 2),
                "mee_thermal_kwh": round(bw["zld"]["mee_thermal_kwh"]
                                         - cw["zld"]["mee_thermal_kwh"], 1),
                "co2e_kg": round(bw["carbon"]["total_co2e_kg"]
                                 - cw["carbon"]["total_co2e_kg"], 2),
                "cost_inr": round(base_total - cand_total, 2),
                "lateness_h": round(cand.sequence["total_late_h"]
                                    - baseline.sequence["total_late_h"], 2),
            },
        }

    options = [
        option(baseline, "OPTION_A",
               "No intervention - ERP arrival order, current practice",
               "Lots run in order-entry sequence with conventional rinsing. "
               "This is the default behaviour today and the baseline every "
               "saving is measured against.",
               False),
        option(recommended, "OPTION_B",
               "ChangeLoop recommendation - constrained optimum",
               "Lowest total resource consequence among plans that satisfy "
               "every hard constraint, including all firm ship dates.",
               True),
    ]

    if (tuple(water_min.order), water_min.strategy_id) not in {
            (tuple(baseline.order), baseline.strategy_id),
            (tuple(recommended.order), recommended.strategy_id)}:
        options.append(option(
            water_min, "OPTION_C",
            "Freshwater minimum" + ("" if water_min.feasible
                                    else " - refused"),
            "The plan that minimises freshwater intake. It is shown whether "
            "or not it is feasible, so that the constraint logic is visible "
            "rather than merely asserted.",
            False))

    rationale = _build_rationale(
        baseline, recommended, options[1]["delta_vs_baseline"], site_id)

    return {
        "status": "FEASIBLE",
        "site_id": site_id,
        "method": method,
        "optimality": optimality,
        "candidates_evaluated": searched,
        "weights": w.to_dict(),
        "constraints": c.to_dict(),
        "options": options,
        "recommended_option_id": "OPTION_B",
        "rationale": rationale,
        "not_claimed": (
            "Ascending shade sequencing is established dyehouse practice. "
            "Counter-current rinsing is best available technique. "
            "Low-electrolyte reactive dyes are a commercial product. None of "
            "these is claimed as our invention. What is added is the "
            "downstream zero-liquid-discharge consequence inside the "
            "objective, and hard-constraint feasibility that a water saving "
            "cannot override."
        ),
        "classification": "MODELLED",
    }


def _build_rationale(baseline: Candidate,
                     rec: Candidate,
                     delta: Dict[str, Any],
                     site_id: str) -> Dict[str, Any]:
    """Explain the recommendation in the terms a reviewer will challenge."""
    from .basin import get_basin
    basin = get_basin(site_id)

    reasons: List[str] = []

    cw_base = baseline.sequence["changeover_water_l"]
    cw_rec = rec.sequence["changeover_water_l"]
    if cw_rec < cw_base:
        reasons.append(
            "Removes {:,.0f} L of machine-cleaning water by eliminating "
            "shade reversals the target shades cannot tolerate "
            "({:,.0f} L to {:,.0f} L)."
            .format(cw_base - cw_rec, cw_base, cw_rec))

    if rec.strategy_id != baseline.strategy_id:
        reasons.append(
            "Switches process strategy to {}. {}"
            .format(rec.sequence["strategy"]["name"],
                    rec.sequence["strategy"]["description"]))

    if delta["salt_kg"] > 0:
        reasons.append(
            "Removes {:.1f} kg of dissolved load. Because reject volume is "
            "set by salt mass, this is what actually reduces evaporator "
            "duty - a water saving alone would not."
            .format(delta["salt_kg"]))

    if delta["mee_thermal_kwh"] > 0:
        reasons.append(
            "Cuts {:,.0f} kWh of evaporator steam, avoiding {:,.0f} kg CO2e "
            "at the boiler."
            .format(delta["mee_thermal_kwh"], delta["co2e_kg"]))

    if delta["freshwater_l"] > 0:
        reasons.append(
            "Reduces freshwater intake by {:,.0f} L, which is {:,.0f} L-eq "
            "in the {} at a stress weight of {:.2f}."
            .format(delta["freshwater_l"], delta["stress_l_eq"],
                    basin.basin_name, basin.stress_weight))

    if abs(delta["lateness_h"]) < 0.01:
        reasons.append(
            "Adds no schedule lateness. Every firm ship date is preserved.")
    else:
        reasons.append(
            "Changes total lateness by {:+.2f} h, with no firm ship date "
            "breached.".format(delta["lateness_h"]))

    if delta["cost_inr"] > 0:
        reasons.append(
            "Net cost reduction of INR {:,.0f} for the shift, after paying "
            "for the process strategy itself.".format(delta["cost_inr"]))

    return {
        "recommendation": "Run {} using {}".format(
            " then ".join(rec.order), rec.sequence["strategy"]["name"]),
        "why": reasons,
        "constraints_satisfied": [
            "All firm ship dates met",
            "Total lateness within limit",
            "Per-lot lateness within limit",
            "Shade tolerance respected at every transition",
        ],
        "uncertainty": (
            "Coefficients are modelled or assumed, not metered. The RANKING "
            "of these plans is robust because every plan is scored with the "
            "same coefficients. The ABSOLUTE savings carry the uncertainty "
            "of those coefficients and must be confirmed against site "
            "sub-metering during a pilot."
        ),
        "what_would_change_this": [
            "A metered RO reject TDS ceiling different from the assumed "
            "60,000 mg/L would change evaporator load proportionally.",
            "A measured evaporator steam economy would move the energy "
            "term, and the sensitivity sweep shows this can flip the "
            "process strategy.",
            "A firm date moving on any lot can change which plans are "
            "feasible, and therefore which is recommended.",
            "A real electrolyte dosing schedule replacing the modelled "
            "depth-to-salt relationship would change the salt term.",
        ],
    }
