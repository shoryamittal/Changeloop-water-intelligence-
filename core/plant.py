# -*- coding: utf-8 -*-
"""ChangeLoop - Shared Treatment Plant Coordination.

THE GAP THIS CLOSES
-------------------
Everything else in this system optimises ONE machine's queue. A real mill
runs several machines into one membrane train and one evaporator, and a
common effluent plant serves hundreds of units into shared capacity. Up
to now that was named as the largest known gap and nothing more.

This module is the first step into it, and it exists because of a failure
mode that single-machine optimisation cannot see, let alone fix:

    Every machine can choose correctly, and the plant can still fail.

Each planner picks the plan that is best for their own machine. Each of
those choices is locally optimal and individually defensible. Their SUM
can still exceed what the shared evaporator can physically boil in a day.
Nobody did anything wrong, and the plant breaches anyway. It is a
coordination failure, not a competence failure, and it is invisible to
every tool that looks at one machine at a time.

WHERE THE CAPACITY NUMBER COMES FROM
------------------------------------
It is not invented. In a closed loop the freshwater makeup IS the
evaporative loss IS the reject volume - the identity this whole project
rests on. So the site's daily freshwater abstraction allowance, expressed
in cubic metres, is simultaneously the volume the shared evaporator has
to boil. One number, two readings, and they have to be the same number or
the loop is not closed.

That is why the plant capacity here is read from the basin's
`daily_abstraction_allowance_l` rather than being a new assumption.

WHAT IT DOES NOT DO
-------------------
It does not schedule machines against each other in time, model
queueing at the membrane train, or handle a CETP's hundreds of members.
It answers one question: when individually-optimal plans collectively
overload the shared plant, what is the cheapest way to pull back under
capacity, and who pays for it. That is a real question a CETP faces and
a single-machine optimiser cannot express.

Everything here is MODELLED. No plant has run it.
"""
from typing import Any, Dict, List, Optional
import itertools

from .basin import get_basin, DEFAULT_SITE
from .optimizer import (
    ObjectiveWeights, HardConstraints, evaluate_candidate,
)
from .process import DyeLot, reference_lots, strategies


MACHINE_PREFIX = "JET-"


def machine_queues(n_machines: int = 4) -> Dict[str, List[DyeLot]]:
    """Build one distinct order book per machine.

    SIMULATED. The four queues are derived from the single reference order
    book by rotating the shade assignment, so each machine runs a
    different colour mix on the same day while the fabric weights, due
    times and machine capability stay comparable. That is what makes the
    machines genuinely different without making one of them arbitrarily
    easy or hard.

    This is a modelled order book, not a real one. A pilot replaces it
    with the site's actual ERP extract.
    """
    base = reference_lots()
    n = len(base)
    queues: Dict[str, List[DyeLot]] = {}

    for m in range(max(1, int(n_machines))):
        machine_id = "%s%02d" % (MACHINE_PREFIX, m + 1)
        lots: List[DyeLot] = []
        for i, lot in enumerate(base):
            shade = base[(i + m) % n]
            lots.append(DyeLot(
                lot_id="%s-%s" % (machine_id, lot.lot_id.split("-")[-1]),
                buyer_ref=lot.buyer_ref,
                article=lot.article,
                shade_name=shade.shade_name,
                shade_hex=shade.shade_hex,
                depth_owf=shade.depth_owf,
                dye_class=lot.dye_class,
                fabric_kg=lot.fabric_kg,
                machine_id=machine_id,
                due_h=lot.due_h,
                priority=lot.priority,
            ))
        queues[machine_id] = lots
    return queues


def _machine_options(lots: List[DyeLot],
                     site_id: str,
                     weights: ObjectiveWeights,
                     constraints: HardConstraints) -> Dict[str, Any]:
    """For one machine: the best FEASIBLE plan under each strategy.

    The order is optimised separately within each strategy, so the four
    options are genuinely each strategy's best case rather than one order
    evaluated four ways. Infeasible strategies are dropped entirely - a
    plan that misses a ship date is not an option at any price.
    """
    ids = [lot.lot_id for lot in lots]
    out: Dict[str, Any] = {}

    for strategy_id in strategies().keys():
        best = None
        for order in itertools.permutations(ids):
            cand = evaluate_candidate(lots, list(order), site_id,
                                      weights, constraints, strategy_id)
            if not cand.feasible:
                continue
            if best is None or cand.objective_inr < best.objective_inr:
                best = cand
        if best is None:
            continue

        cons = best.consequence
        out[strategy_id] = {
            "strategy_id": strategy_id,
            "strategy_name": strategies()[strategy_id].name,
            "order": best.order,
            "objective_inr": round(best.objective_inr, 2),
            "reject_l": round(cons["zld"]["reject_l"], 1),
            "freshwater_l": round(cons["water"]["freshwater_intake_l"], 1),
            "salt_kg": round(cons["salt"]["total_salt_kg"], 2),
            "mee_thermal_kwh": round(cons["zld"]["mee_thermal_kwh"], 1),
            "co2e_kg": round(cons["carbon"]["total_co2e_kg"], 2),
            "cost_inr": round(cons["cost_inr"]["total"]
                              + best.sequence["strategy_cost_inr"], 2),
        }
    return out


def plant_plan(site_id: str = DEFAULT_SITE,
               n_machines: Optional[int] = None,
               shifts_per_day: Optional[int] = None,
               weights: Optional[ObjectiveWeights] = None,
               constraints: Optional[HardConstraints] = None
               ) -> Dict[str, Any]:
    """Compare what each machine wants with what the shared plant can take.

    Returns two plans over the same day:

      SELFISH     every machine picks its own lowest-objective plan. This
                  is what a per-machine tool recommends, and what each
                  planner would independently choose.

      COORDINATED the cheapest combination that fits under the shared
                  evaporator's capacity. Some machines take a locally
                  worse plan so the plant stays inside its limit.

    If the selfish plan already fits, the two are identical and the
    coordination premium is zero. That case is reported as plainly as the
    breach, because a system that only ever reports problems is not
    trustworthy either.
    """
    basin = get_basin(site_id)
    weights = weights or ObjectiveWeights()
    constraints = constraints or HardConstraints()

    machines = int(n_machines if n_machines is not None
                   else basin.machines_in_scope)
    shifts = int(shifts_per_day if shifts_per_day is not None
                 else basin.shifts_per_day)
    machines = max(1, machines)
    shifts = max(1, shifts)

    # The closed-loop identity: the day's freshwater allowance in m3 is
    # the same volume the shared evaporator has to boil.
    allowance_l = float(basin.daily_abstraction_allowance_l)
    capacity_m3 = allowance_l / 1000.0

    queues = machine_queues(machines)
    options = {mid: _machine_options(lots, site_id, weights, constraints)
               for mid, lots in queues.items()}

    usable = {mid: opts for mid, opts in options.items() if opts}
    if not usable:
        return {
            "status": "NO_FEASIBLE_PLAN",
            "site_id": site_id,
            "reason": ("No machine has a feasible plan under the current "
                       "constraints, so there is nothing to coordinate."),
            "classification": "MODELLED",
        }

    machine_ids = sorted(usable.keys())

    def totals(choice: Dict[str, str]) -> Dict[str, float]:
        """Day totals for one strategy choice per machine."""
        agg = {"objective_inr": 0.0, "reject_l": 0.0, "freshwater_l": 0.0,
               "salt_kg": 0.0, "mee_thermal_kwh": 0.0, "co2e_kg": 0.0,
               "cost_inr": 0.0}
        for mid, sid in choice.items():
            opt = usable[mid][sid]
            for key in agg:
                agg[key] += opt[key] * shifts
        return agg

    # --- selfish: each machine takes its own best ------------------------
    selfish_choice = {
        mid: min(opts.values(), key=lambda o: o["objective_inr"])["strategy_id"]
        for mid, opts in usable.items()
    }
    selfish = totals(selfish_choice)
    selfish_m3 = selfish["reject_l"] / 1000.0

    # --- coordinated: cheapest combination that fits ---------------------
    # Exhaustive over strategy choices. With four machines and four
    # strategies this is 256 combinations and the per-machine plans are
    # already computed, so the search is cheap and the optimum is proven
    # rather than approximated.
    best_fit = None
    for combo in itertools.product(*[sorted(usable[mid].keys())
                                     for mid in machine_ids]):
        choice = dict(zip(machine_ids, combo))
        agg = totals(choice)
        if agg["reject_l"] / 1000.0 > capacity_m3:
            continue
        if best_fit is None or agg["objective_inr"] < best_fit[1]["objective_inr"]:
            best_fit = (choice, agg)

    fits_without_coordination = selfish_m3 <= capacity_m3

    if fits_without_coordination:
        coordinated_choice, coordinated = selfish_choice, selfish
        status = "WITHIN_CAPACITY"
    elif best_fit is None:
        coordinated_choice, coordinated = None, None
        status = "CANNOT_FIT"
    else:
        coordinated_choice, coordinated = best_fit
        status = "COORDINATION_REQUIRED"

    result: Dict[str, Any] = {
        "status": status,
        "site_id": site_id,
        "basin_name": basin.basin_name,
        "machines": machines,
        "shifts_per_day": shifts,
        "machine_shifts_per_day": machines * shifts,
        "evaporator_capacity_m3_per_day": round(capacity_m3, 1),
        "capacity_basis": (
            "The site's daily freshwater abstraction allowance of "
            "{:,.0f} L. In a closed loop the makeup water is the "
            "evaporative loss is the reject volume, so the same figure is "
            "both the abstraction limit and the volume the shared "
            "evaporator must boil.".format(allowance_l)
        ),
        "machine_options": usable,
        "selfish": {
            "label": "Every machine optimises for itself",
            "choice": selfish_choice,
            "reject_m3_per_day": round(selfish_m3, 1),
            "utilisation_pct": round(selfish_m3 / capacity_m3 * 100.0, 1)
            if capacity_m3 else None,
            "totals": {k: round(v, 2) for k, v in selfish.items()},
        },
        "classification": "MODELLED",
    }

    if coordinated is not None:
        coord_m3 = coordinated["reject_l"] / 1000.0
        premium = coordinated["objective_inr"] - selfish["objective_inr"]
        result["coordinated"] = {
            "label": "Cheapest combination that fits the shared plant",
            "choice": coordinated_choice,
            "reject_m3_per_day": round(coord_m3, 1),
            "utilisation_pct": round(coord_m3 / capacity_m3 * 100.0, 1)
            if capacity_m3 else None,
            "totals": {k: round(v, 2) for k, v in coordinated.items()},
            "coordination_premium_inr_per_day": round(premium, 2),
            "machines_that_move": sorted(
                mid for mid in machine_ids
                if coordinated_choice.get(mid) != selfish_choice.get(mid)
            ),
        }

    result["reading"] = _reading(result)
    return result


def _reading(r: Dict[str, Any]) -> str:
    """One honest sentence a planner or CETP manager can act on."""
    status = r["status"]
    selfish = r["selfish"]

    if status == "WITHIN_CAPACITY":
        return (
            "Every machine can take its own best plan and the shared "
            "evaporator still fits, at {}% of capacity. No coordination is "
            "needed today.".format(selfish["utilisation_pct"])
        )

    if status == "CANNOT_FIT":
        return (
            "Even the lowest-load combination available exceeds the shared "
            "evaporator's capacity. Scheduling cannot solve this day; the "
            "plant is short of capacity or the order book is too heavy, "
            "and that is a different decision from the one this system "
            "makes."
        )

    coord = r["coordinated"]
    movers = coord["machines_that_move"]
    return (
        "Each machine choosing its own best plan puts the shared "
        "evaporator at {sel}% of capacity. Nobody chose badly; the sum "
        "does not fit. Moving {n} of {total} machines onto a locally "
        "worse plan brings the plant to {co}%, and costs "
        "INR {prem:,.0f} a day across the site. That cost is invisible to "
        "every machine individually, which is why no single planner can "
        "find it.".format(
            sel=selfish["utilisation_pct"],
            n=len(movers),
            total=r["machines"],
            co=coord["utilisation_pct"],
            prem=coord["coordination_premium_inr_per_day"],
        )
    )
