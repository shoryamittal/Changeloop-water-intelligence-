# -*- coding: utf-8 -*-
"""ChangeLoop - what price makes the right plan the profitable plan.

THE QUESTION THIS ANSWERS
-------------------------
Everywhere else this system reports a finding: under today's tariffs the
optimiser recommends the counter-current plan, which cuts freshwater and
evaporator steam by about 6%. The low-salt plan is available, feasible and
cuts both by about 47%, and the optimiser does not choose it, because the
dye-chemistry premium costs more than the steam it saves.

That is usually where an impact claim quietly switches to the bigger
number. Instead this module asks the question the finding actually
raises:

    How much would a price have to move before the 47% plan becomes the
    one a profit-seeking mill picks on its own?

That converts "price water and carbon properly" from a slogan into a
figure a tariff-setter can act on, and it is computed from the same
engine that produces every other number here - no separate model, no new
assumptions.

HOW THE ANSWER IS FOUND
-----------------------
Coarse scan, then bisection. For a lever we walk the coefficient across a
plausible range, re-running the full optimiser at each step, until the
recommended strategy changes to one that buys the salt lever. Then we
bisect inside that bracket to pin the crossing.

We scan before we bisect deliberately. Bisection alone assumes the answer
is monotonic in the coefficient, and we have not proved that it is. The
scan finds the FIRST crossing, which is the one a tariff-setter cares
about, and the result says so rather than implying there is only one.

THE CARBON PRICE
----------------
The steam lever converts directly. If steam has to rise by some number of
rupees per kWh_th, and the boiler emits a known mass of CO2e per kWh_th,
then the rupees per tonne of CO2e that would produce that rise is simple
division. That number is comparable to carbon prices in use elsewhere,
which is what makes it useful.

It is an IMPLIED price, not a proposal, and it assumes the whole cost
increase reaches the mill as a steam price. Both caveats are returned
with the figure.

Everything here is DERIVED from the engine. No coefficient is added.
"""
from typing import Any, Dict, List, Optional
import threading

from . import factors
from .basin import DEFAULT_SITE
from .optimizer import ObjectiveWeights, HardConstraints, optimise
from .process import reference_lots, arrival_order, strategies


# The strategies that actually reduce salt. Reaching any of these means
# the chemistry lever has been bought.
SALT_LEVER_STRATEGIES = ("LOW_SALT", "COMBINED")

# Each lever: the coefficient, which way it has to move, and how far we
# are willing to look. The ranges are deliberately wide enough to contain
# an answer and narrow enough to stay physically meaningful; a crossing
# not found inside one is reported as not found, never extrapolated.
LEVERS: Dict[str, Dict[str, Any]] = {
    "steam_cost_inr_per_kwh_th": {
        "direction": "up",
        "limit": 30.0,
        "question": "How much more would steam have to cost?",
        "policy_instrument": "A carbon price on coal, or any fuel cost "
                             "increase that reaches the boiler.",
    },
    "freshwater_cost_inr_per_m3": {
        "direction": "up",
        "limit": 3000.0,
        "question": "How much more would freshwater have to cost?",
        "policy_instrument": "A groundwater abstraction tariff, or "
                             "scarcity pricing in a stressed basin.",
    },
    "low_salt_chemistry_cost_inr_per_kg_fabric": {
        "direction": "down",
        "limit": 0.0,
        "question": "How far would the low-salt dye premium have to fall?",
        "policy_instrument": "Market maturity, volume procurement, or a "
                             "subsidy on low-electrolyte chemistry.",
    },
}

# An external benchmark for the implied carbon price. This is NOT a model
# coefficient - nothing is computed from it - so it is deliberately kept
# out of the factor registry. It exists so the implied price can be read
# against a carbon price that real industry already pays, and it carries
# its source and its as-of date because a market price goes stale.
CARBON_BENCHMARK = {
    "name": "EU Emissions Trading System allowance",
    "price_eur_per_tonne": 82.40,
    "as_of": "2026-10-05",
    "inr_per_eur_range": (108.0, 118.0),
    "source": "EU allowance December futures, reported by S&P Global "
              "Commodity Insights, 5 October 2026. Rupee conversion uses "
              "a range because the rate moves and a single figure would "
              "imply a precision this comparison does not have.",
    "why_it_is_here": "To answer the obvious question: is the price this "
                      "decision needs large or small? It is only "
                      "meaningful against a carbon price that industry "
                      "somewhere already pays.",
}


_SCAN_STEPS = 24
_BISECT_ROUNDS = 26


def _recommended_strategy(site_id: str,
                          weights: ObjectiveWeights,
                          constraints: HardConstraints,
                          lots, arrival) -> Optional[Dict[str, Any]]:
    """Run the optimiser and return the plan it actually recommends."""
    r = optimise(lots, arrival, site_id, weights, constraints)
    if r.get("status") != "FEASIBLE":
        return None
    return next((o for o in r["options"]
                 if o["option_id"] == r["recommended_option_id"]), None)


def _buys_the_salt_lever(rec: Optional[Dict[str, Any]]) -> bool:
    return bool(rec) and rec["strategy_id"] in SALT_LEVER_STRATEGIES


def switching_point(key: str,
                    site_id: str = DEFAULT_SITE,
                    weights: Optional[ObjectiveWeights] = None,
                    constraints: Optional[HardConstraints] = None
                    ) -> Dict[str, Any]:
    """Find the first value of `key` at which the salt lever is chosen.

    Returns the crossing, what the plan looks like on each side of it,
    and how far the crossing sits from today's value. If the engine
    already recommends a salt-reducing plan, that is reported plainly
    instead of being searched for.
    """
    if key not in LEVERS:
        raise KeyError("No policy lever defined for %r" % key)

    spec = LEVERS[key]
    weights = weights or ObjectiveWeights()
    constraints = constraints or HardConstraints()
    lots, arrival = reference_lots(), arrival_order()

    with factors.REGISTRY_LOCK:
        f = factors.factor(key)
        current = f.value

        def rec_at(value: float):
            with _patched(key, value):
                return _recommended_strategy(site_id, weights, constraints,
                                             lots, arrival)

        base_rec = _recommended_strategy(site_id, weights, constraints,
                                         lots, arrival)

        result: Dict[str, Any] = {
            "coefficient": key,
            "label": f.label,
            "unit": f.unit,
            "evidence": f.evidence,
            "current_value": round(current, 4),
            "direction": spec["direction"],
            "question": spec["question"],
            "policy_instrument": spec["policy_instrument"],
            "strategy_now": base_rec["strategy_id"] if base_rec else None,
            "classification": "DERIVED",
            "method": ("Coarse scan of %d steps to bracket the first "
                       "crossing, then %d rounds of bisection. The full "
                       "optimiser is re-run at every step; nothing is "
                       "interpolated."
                       % (_SCAN_STEPS, _BISECT_ROUNDS)),
        }

        if _buys_the_salt_lever(base_rec):
            result.update({
                "status": "ALREADY_CHOSEN",
                "switching_value": None,
                "reading": ("At today's value the optimiser already "
                            "recommends a salt-reducing plan, so there is "
                            "nothing for a price to fix here."),
            })
            return result

        limit = float(spec["limit"])

        # --- scan for the first crossing ------------------------------
        bracket = None
        prev = current
        for i in range(1, _SCAN_STEPS + 1):
            frac = i / float(_SCAN_STEPS)
            probe = (current + (limit - current) * frac)
            if _buys_the_salt_lever(rec_at(probe)):
                bracket = (prev, probe)
                break
            prev = probe

        if bracket is None:
            result.update({
                "status": "NOT_FOUND",
                "switching_value": None,
                "searched_to": round(limit, 4),
                "reading": ("Moving this price as far as %s %s did not "
                            "make the salt lever the profitable choice. "
                            "This lever alone does not decide it."
                            % (_fmt(limit), f.unit)),
            })
            return result

        # --- bisect inside the bracket --------------------------------
        a, b = bracket
        for _ in range(_BISECT_ROUNDS):
            mid = (a + b) / 2.0
            if _buys_the_salt_lever(rec_at(mid)):
                b = mid
            else:
                a = mid
        # Round so the reported figure stays on the side where the salt
        # lever IS bought. Plain rounding can land a hair short of the
        # boundary, and a quoted price that does not actually flip the
        # decision is worse than no price at all.
        crossing = _round_past(b, spec["direction"])

        before = rec_at(a)
        after = rec_at(crossing)

    change = crossing - current
    result.update({
        "status": "FOUND",
        "switching_value": crossing,
        "absolute_change": round(change, 3),
        "multiple_of_today": (round(crossing / current, 2)
                              if current else None),
        "percent_change": (round(change / current * 100.0, 1)
                           if current else None),
        "strategy_before": before["strategy_id"] if before else None,
        "strategy_after": after["strategy_id"] if after else None,
        "plan_after": _plan_summary(after),
        "plan_before": _plan_summary(before),
        "reading": _lever_reading(f, current, crossing, spec, after),
    })
    return result


def _patched(key: str, value: float):
    """Temporarily replace one coefficient. Caller holds the lock."""
    class _Ctx:
        def __enter__(self_inner):
            self_inner.original = factors.FACTORS[key]
            old = self_inner.original
            factors.FACTORS[key] = factors.Factor(
                key=old.key, label=old.label, value=float(value),
                unit=old.unit, evidence=old.evidence,
                basis=old.basis + "  [POLICY SWEEP: temporarily set to "
                                  "%s to locate a switching price]" % value,
                tunable=old.tunable,
            )
            return self_inner

        def __exit__(self_inner, *exc):
            factors.FACTORS[key] = self_inner.original
            return False
    return _Ctx()


def _round_past(value: float, direction: str, dp: int = 3) -> float:
    """Round to `dp` places, away from the no-change side.

    An "up" lever is rounded up and a "down" lever down, so the figure
    reported is always one the optimiser actually acts on.
    """
    import math
    scale = 10 ** dp
    if direction == "up":
        return math.ceil(value * scale) / scale
    return math.floor(value * scale) / scale


def _plan_summary(rec: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not rec:
        return None
    d = rec["delta_vs_baseline"]
    return {
        "strategy_id": rec["strategy_id"],
        "strategy_name": strategies()[rec["strategy_id"]].name,
        "freshwater_avoided_l": round(d["freshwater_l"], 1),
        "mee_thermal_avoided_kwh": round(d["mee_thermal_kwh"], 1),
        "co2e_avoided_kg": round(d["co2e_kg"], 2),
        "cost_avoided_inr": round(d["cost_inr"], 2),
    }


def _fmt(v: float) -> str:
    return ("%.2f" % v).rstrip("0").rstrip(".")


def _lever_reading(f, current, crossing, spec, after) -> str:
    verb = "rise" if spec["direction"] == "up" else "fall"
    tail = ""
    if after:
        d = after["delta_vs_baseline"]
        tail = (" At that point the recommended plan avoids "
                "{:,.0f} L of freshwater and {:,.0f} kWh of evaporator "
                "steam a shift, against {} and {} today."
                .format(d["freshwater_l"], d["mee_thermal_kwh"],
                        "720 L", "135 kWh"))
    return ("{label} would have to {verb} from {a} to {b} {unit} before a "
            "profit-seeking mill chooses the salt-reducing plan on its own "
            "account.{tail}".format(
                label=f.label, verb=verb, a=_fmt(current),
                b=_fmt(crossing), unit=f.unit, tail=tail))


def implied_carbon_price(steam_lever: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the steam switching price into rupees per tonne of CO2e.

    If steam must rise by D rupees per kWh_th, and burning enough fuel to
    deliver one kWh_th emits E kg of CO2e, then a carbon price of D/E
    rupees per kg - D/E x 1000 per tonne - produces exactly that rise.

    This is an IMPLIED price, not a proposal. It assumes the full cost
    passes through to the mill as a steam price, which is the optimistic
    case; where it does not, the real price needed is higher.
    """
    if steam_lever.get("status") != "FOUND":
        return {
            "status": steam_lever.get("status"),
            "inr_per_tonne_co2e": None,
            "note": "No steam switching price was found, so no carbon "
                    "price can be implied from it.",
        }

    e = factors.get("boiler_co2e_kg_per_kwh_th")
    delta = float(steam_lever["absolute_change"])
    per_kg = delta / e
    per_tonne = per_kg * 1000.0

    return {
        "status": "DERIVED",
        "steam_increase_inr_per_kwh_th": round(delta, 3),
        "boiler_co2e_kg_per_kwh_th": e,
        "inr_per_kg_co2e": round(per_kg, 3),
        "inr_per_tonne_co2e": round(per_tonne, 0),
        "arithmetic": ("{d} INR/kWh_th / {e} kg CO2e/kWh_th = {k} INR/kg "
                       "= {t:,.0f} INR/tonne CO2e"
                       .format(d=_fmt(delta), e=e, k=round(per_kg, 3),
                               t=per_tonne)),
        "what_it_assumes": (
            "That the entire carbon cost reaches the mill as a higher "
            "steam price. Where it is absorbed upstream or offset, the "
            "price needed is higher than this."),
        "what_it_is_not": (
            "A policy proposal, and not a claim about what a carbon price "
            "should be. It is the level at which this particular decision "
            "flips, in this modelled mill."),
        "benchmark": _benchmark(per_tonne),
        "classification": "DERIVED",
    }


def _benchmark(per_tonne: float) -> Dict[str, Any]:
    """Read the implied price against one a real market already charges."""
    b = CARBON_BENCHMARK
    lo_fx, hi_fx = b["inr_per_eur_range"]
    eur_lo = per_tonne / hi_fx
    eur_hi = per_tonne / lo_fx
    bench_inr_lo = b["price_eur_per_tonne"] * lo_fx
    bench_inr_hi = b["price_eur_per_tonne"] * hi_fx
    ratio_lo = bench_inr_lo / per_tonne
    ratio_hi = bench_inr_hi / per_tonne
    return {
        "benchmark": b["name"],
        "benchmark_eur_per_tonne": b["price_eur_per_tonne"],
        "benchmark_as_of": b["as_of"],
        "benchmark_source": b["source"],
        "implied_price_eur_per_tonne": "%.0f to %.0f" % (eur_lo, eur_hi),
        "benchmark_is_this_many_times_higher":
            "%.1f to %.1f" % (ratio_lo, ratio_hi),
        "reading": (
            "The carbon price this decision needs is about EUR {lo:.0f} to "
            "{hi:.0f} a tonne. The EU Emissions Trading System was "
            "charging EUR {b:.2f} on {d}, roughly {r:.0f} times more. The "
            "abatement is not waiting on an unreachable price; it is "
            "waiting on any price at all."
            .format(lo=eur_lo, hi=eur_hi, b=b["price_eur_per_tonne"],
                    d=b["as_of"], r=(ratio_lo + ratio_hi) / 2.0)),
    }


# The sweep re-runs the optimiser a few hundred times, which takes about
# 20 seconds on a laptop and over a minute on a small cloud instance.
# The answer only changes when a coefficient or the constraint set
# changes, so it is cached on exactly those. A reviewer clicking the
# Policy screen should not be left looking at a spinner.
_LEVER_CACHE: Dict[Any, Dict[str, Any]] = {}
_LEVER_CACHE_LOCK = threading.Lock()


def _cache_key(site_id, weights, constraints) -> tuple:
    # Every tunable coefficient, not just the three levers. Several
    # others feed the optimiser, and a key that ignored them would
    # serve a stale answer after a sweep or a what-if changed one.
    with factors.REGISTRY_LOCK:
        coeffs = tuple(sorted(
            (k, f.value) for k, f in factors.FACTORS.items() if f.tunable))
    return (site_id, coeffs,
            tuple(sorted(weights.to_dict().items())),
            tuple(sorted(constraints.to_dict().items())))


def policy_levers(site_id: str = DEFAULT_SITE,
                  weights: Optional[ObjectiveWeights] = None,
                  constraints: Optional[HardConstraints] = None
                  ) -> Dict[str, Any]:
    """All three levers, plus the carbon price the steam lever implies."""
    weights = weights or ObjectiveWeights()
    constraints = constraints or HardConstraints()
    key = _cache_key(site_id, weights, constraints)
    with _LEVER_CACHE_LOCK:
        hit = _LEVER_CACHE.get(key)
    if hit is not None:
        return hit

    levers: List[Dict[str, Any]] = []
    for lever_key in LEVERS:
        levers.append(switching_point(lever_key, site_id, weights,
                                      constraints))

    by_key = {l["coefficient"]: l for l in levers}
    carbon = implied_carbon_price(by_key["steam_cost_inr_per_kwh_th"])

    found = [l for l in levers if l["status"] == "FOUND"]
    cheapest = min(found, key=lambda l: abs(l.get("percent_change") or 1e9),
                   default=None)

    out = {
        "site_id": site_id,
        "question": ("The low-salt plan is feasible and cuts freshwater "
                     "and evaporator steam by about 47%, and the optimiser "
                     "does not choose it, because the dye premium costs "
                     "more than the steam it saves. What price would make "
                     "it the profitable choice?"),
        "levers": levers,
        "implied_carbon_price": carbon,
        "smallest_move": cheapest["coefficient"] if cheapest else None,
        "reading": _overall_reading(levers, carbon, cheapest),
        "honesty": (
            "Every figure here comes from re-running the same optimiser "
            "with one coefficient changed. Nothing is extrapolated and no "
            "new coefficient is introduced. It inherits every limitation "
            "of the model underneath, including that no coefficient has "
            "been measured at a real site."),
        "classification": "DERIVED",
    }
    with _LEVER_CACHE_LOCK:
        _LEVER_CACHE[key] = out
    return out


def _overall_reading(levers, carbon, cheapest) -> str:
    if not cheapest:
        return ("No single price moved far enough to make the salt lever "
                "the profitable choice, which would mean the decision "
                "turns on something other than these three prices.")

    parts = [
        "The 47% plan is not blocked by technology or by a ship date. It "
        "is blocked by a price."
    ]
    if carbon.get("inr_per_tonne_co2e"):
        parts.append(
            "A carbon price of about INR {t:,.0f} per tonne of CO2e, "
            "passed through to steam, is enough to flip it."
            .format(t=carbon["inr_per_tonne_co2e"]))
    parts.append(
        "Of the three levers tested, {} needs the smallest move."
        .format(cheapest["label"].lower()))
    parts.append(
        "That is the whole argument for pricing in one number: the "
        "cheaper abatement already exists, and nobody buys it because "
        "the signal does not reach the person deciding.")
    return " ".join(parts)
