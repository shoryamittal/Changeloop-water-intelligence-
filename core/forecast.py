"""ChangeLoop - Resource Forecast and Abstraction Envelope.

What this is, stated precisely
------------------------------
This is NOT a statistical forecast of unknown future demand, and it does not
claim to be. There is no trained model and no time-series fitting here.

The order book is already committed. Tomorrow's water and salt draw is
therefore a DETERMINISTIC CONSEQUENCE of a decision that has not been taken
yet. So what this module produces is:

  a causal projection of the committed queue under the plan currently
  selected, plus a declared uncertainty band, compared against the site's
  freshwater abstraction envelope.

That framing is the point. Change the plan and the trajectory moves, because
the trajectory was never an external forecast - it was always the shadow of a
decision. A statistical forecast would tell you what is probably coming. This
tells you what you are about to cause.

Why the envelope matters
------------------------
A demand curve on its own is not actionable. A demand curve against a daily
abstraction allowance is: it answers "if we run the shift like this, when do
we breach, and by how much?" before the breach happens rather than after.

Uncertainty
-----------
The band is NOT a confidence interval in the statistical sense, because there
is no sample. It is a declared coefficient-uncertainty envelope that widens
with horizon, and it is labelled ASSUMED. Saying "95% confidence" here would
be a fabrication.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import math

from . import factors, zld
from .basin import get_basin
from .process import (
    DyeLot, evaluate_sequence, changeover_burden, get_strategy,
    DEFAULT_STRATEGY,
)


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------

# Ambient temperature shapes how much thermal energy a hot rinse needs. A
# diurnal profile is modelled rather than measured: coldest before dawn,
# peak mid-afternoon. Tamil Nadu dry-season shape.
_AMBIENT_MIN_C = 24.0
_AMBIENT_MAX_C = 36.0
_AMBIENT_PEAK_HOUR = 15.0

# Declared uncertainty on the projection. Not a confidence interval.
_BAND_BASE_FRAC = 0.06          # coefficient uncertainty at hour zero
_BAND_GROWTH_PER_H = 0.009      # widens with horizon


def ambient_temp_c(hour_of_day: float) -> float:
    """Modelled diurnal ambient temperature."""
    mid = (_AMBIENT_MAX_C + _AMBIENT_MIN_C) / 2.0
    amp = (_AMBIENT_MAX_C - _AMBIENT_MIN_C) / 2.0
    phase = (hour_of_day - _AMBIENT_PEAK_HOUR) / 24.0 * 2.0 * math.pi
    return round(mid + amp * math.cos(phase), 1)


def band_fraction(hours_ahead: float) -> float:
    """Declared uncertainty fraction at a given horizon."""
    return round(_BAND_BASE_FRAC + _BAND_GROWTH_PER_H * max(0.0, hours_ahead), 4)


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """One hour of the projection."""
    hour: int
    clock: str
    lot_id: Optional[str]
    activity: str                 # DYEING | CHANGEOVER | IDLE
    water_l: float                # process + changeover water drawn this hour
    salt_kg: float
    freshwater_l: float           # basin draw attributable to this hour
    cumulative_freshwater_l: float
    band_low_l: float
    band_high_l: float
    ambient_c: float
    thermal_kwh: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: (round(v, 1) if isinstance(v, float) else v)
                for k, v in d.items()}


def project(lots: List[DyeLot],
            order: List[str],
            site_id: str,
            strategy_id: str = DEFAULT_STRATEGY,
            shift_start_hour: int = 6,
            horizon_h: int = 24) -> Dict[str, Any]:
    """Project the committed queue hour by hour against the envelope.

    Water is distributed across the hours a lot actually occupies, so the
    trajectory has the shape of the schedule rather than being a flat average.
    """
    basin = get_basin(site_id)
    strategy = get_strategy(strategy_id)
    index = {l.lot_id: l for l in lots}

    missing = [lid for lid in order if lid not in index]
    if missing:
        raise KeyError("Unknown lot id(s): {}".format(missing))

    seq = [index[lid] for lid in order]

    # ---- lay the schedule onto a timeline, in minutes ------------------
    # Each lot contributes its process demand; each junction contributes a
    # changeover burden. Both are spread evenly across their own duration,
    # which is what gives the curve its steps.
    segments: List[Dict[str, Any]] = []
    t = 0.0
    for i, lot in enumerate(seq):
        if i > 0:
            co = changeover_burden(seq[i - 1], lot)
            if co.minutes > 0:
                segments.append({
                    "kind": "CHANGEOVER",
                    "lot_id": lot.lot_id,
                    "start_min": t,
                    "minutes": co.minutes,
                    "water_l": co.water_l,
                    "salt_kg": co.salt_kg,
                })
                t += co.minutes

        pd = lot.process_demand()
        # The process strategy scales the rinse portion and the electrolyte.
        water = (pd["dye_water_l"]
                 + pd["rinse_water_l"] * strategy.water_multiplier)
        salt = pd["process_salt_kg"] * strategy.salt_multiplier
        segments.append({
            "kind": "DYEING",
            "lot_id": lot.lot_id,
            "start_min": t,
            "minutes": pd["process_minutes"],
            "water_l": water,
            "salt_kg": salt,
        })
        t += pd["process_minutes"]

    total_minutes = t

    # ---- bucket into hours --------------------------------------------
    hours: List[Dict[str, Any]] = []
    for h in range(horizon_h):
        hours.append({"water_l": 0.0, "salt_kg": 0.0,
                      "lot_id": None, "activity": "IDLE"})

    for seg in segments:
        start = seg["start_min"]
        end = start + seg["minutes"]
        if seg["minutes"] <= 0:
            continue
        h0 = int(start // 60)
        h1 = int(math.ceil(end / 60.0))
        for h in range(h0, min(h1, horizon_h)):
            lo = max(start, h * 60.0)
            hi = min(end, (h + 1) * 60.0)
            frac = max(0.0, hi - lo) / seg["minutes"]
            if frac <= 0:
                continue
            hours[h]["water_l"] += seg["water_l"] * frac
            hours[h]["salt_kg"] += seg["salt_kg"] * frac
            # Label the hour by whichever activity dominates it.
            if frac > 0.4 or hours[h]["lot_id"] is None:
                hours[h]["lot_id"] = seg["lot_id"]
                hours[h]["activity"] = seg["kind"]

    # ---- convert to basin draw through the ZLD chain ------------------
    # Freshwater makeup equals evaporative loss, which is set by salt mass.
    # So the basin draw attributable to an hour follows that hour's SALT,
    # not its water. This is the thesis showing up in the forecast.
    steps: List[Step] = []
    cumulative = 0.0
    h_per_l_per_k = factors.get("water_heating_kwh_per_l_per_k")

    for h in range(horizon_h):
        rec = hours[h]
        water = rec["water_l"]
        salt = rec["salt_kg"]

        if water > 0:
            res = zld.treat(water, salt, site_id)
            acct = zld.account_for_water(water, res)
            fresh = acct.freshwater_intake_l
        else:
            fresh = 0.0

        cumulative += fresh
        clock_h = (shift_start_hour + h) % 24
        amb = ambient_temp_c(clock_h)
        # Hot rinse has to close the gap from ambient to the wash temperature,
        # so a cooler hour costs slightly more thermal energy per litre.
        delta_t = max(0.0, 80.0 - amb)
        thermal = water * h_per_l_per_k * delta_t

        frac = band_fraction(h)
        steps.append(Step(
            hour=h,
            clock="{:02d}:00".format(clock_h),
            lot_id=rec["lot_id"],
            activity=rec["activity"],
            water_l=water,
            salt_kg=salt,
            freshwater_l=fresh,
            cumulative_freshwater_l=cumulative,
            band_low_l=cumulative * (1.0 - frac),
            band_high_l=cumulative * (1.0 + frac),
            ambient_c=amb,
            thermal_kwh=thermal,
        ))

    # ---- envelope -----------------------------------------------------
    # Judge the projection against the allocation for the scope actually
    # modelled - one machine, one shift - not the whole-site daily figure.
    allowance = basin.machine_shift_allocation_l
    breach_hour = None
    breach_clock = None
    for st in steps:
        if st.cumulative_freshwater_l > allowance:
            breach_hour = st.hour
            breach_clock = st.clock
            break

    # Earliest hour at which the UPPER band crosses, i.e. the earliest the
    # breach could plausibly arrive given declared uncertainty.
    band_breach_hour = None
    for st in steps:
        if st.band_high_l > allowance:
            band_breach_hour = st.hour
            break

    final = steps[-1].cumulative_freshwater_l if steps else 0.0
    headroom = allowance - final
    peak = max((st.freshwater_l for st in steps), default=0.0)
    peak_hour = next((st.clock for st in steps if st.freshwater_l >= peak - 1e-9),
                     None)

    if breach_hour is not None:
        risk = "BREACH_PROJECTED"
        risk_text = ("Projected to exceed the abstraction allowance at {} "
                     "under this plan.".format(breach_clock))
    elif band_breach_hour is not None:
        risk = "AT_RISK"
        risk_text = ("Central projection stays inside the allowance, but the "
                     "upper uncertainty band crosses it. Treat the headroom "
                     "as not assured.")
    elif headroom < allowance * 0.15:
        risk = "TIGHT"
        risk_text = ("Inside the allowance with less than 15% headroom. A "
                     "single added lot could change that.")
    else:
        risk = "WITHIN_ALLOWANCE"
        risk_text = "Projected to stay inside the abstraction allowance."

    return {
        "site_id": basin.site_id,
        "basin": basin.basin_name,
        "strategy_id": strategy.strategy_id,
        "strategy_name": strategy.name,
        "order": list(order),
        "shift_start_hour": shift_start_hour,
        "horizon_h": horizon_h,
        "schedule_minutes": round(total_minutes, 1),

        "steps": [st.to_dict() for st in steps],

        "envelope": {
            "allocation_l": allowance,
            "allocation_basis": (
                "{:,.0f} L/day site allowance / ({} machines x {} shifts) "
                "= {:,.0f} L per machine-shift".format(
                    basin.daily_abstraction_allowance_l,
                    basin.machines_in_scope, basin.shifts_per_day, allowance)),
            "daily_abstraction_allowance_l":
                basin.daily_abstraction_allowance_l,
            "projected_draw_l": round(final, 1),
            "headroom_l": round(headroom, 1),
            "utilisation_pct": round(final / allowance * 100.0, 1)
            if allowance > 0 else None,
            "risk": risk,
            "risk_text": risk_text,
            "breach_hour": breach_hour,
            "breach_clock": breach_clock,
            "earliest_band_breach_hour": band_breach_hour,
            "peak_hourly_draw_l": round(peak, 1),
            "peak_hour": peak_hour,
        },

        "drivers": [
            {
                "name": "Committed order book",
                "value": "{} lots".format(len(order)),
                "detail": "The dominant driver. Demand here is not forecast, "
                          "it is the consequence of a queue already accepted.",
                "evidence": "SIMULATED",
            },
            {
                "name": "Process strategy in force",
                "value": strategy.name,
                "detail": "Scales rinse water and electrolyte, and therefore "
                          "the basin draw.",
                "evidence": "MODELLED",
            },
            {
                "name": "Ambient temperature",
                "value": "{:.0f} to {:.0f} degC".format(_AMBIENT_MIN_C,
                                                        _AMBIENT_MAX_C),
                "detail": "Modelled diurnal profile. Affects hot-rinse "
                          "thermal load, not water volume.",
                "evidence": "ASSUMED",
            },
            {
                "name": "Abstraction allowance",
                "value": "{:,.0f} L per machine-shift".format(allowance),
                "detail": "Apportioned from the site daily allowance by the "
                          "number of machine-shifts run. The envelope the "
                          "trajectory is judged against.",
                "evidence": "ASSUMED",
            },
        ],

        "method": {
            "what_this_is": (
                "A causal projection of the committed queue under the plan "
                "currently selected, compared against the site abstraction "
                "allowance."
            ),
            "what_this_is_not": (
                "Not a statistical forecast. There is no trained model, no "
                "time-series fit and no sample, so there is no confidence "
                "interval. Demand is not being predicted - it is being "
                "derived from a decision."
            ),
            "band": (
                "The band is a declared coefficient-uncertainty envelope of "
                "+/-{:.0f}% at hour zero widening by {:.1f} percentage points "
                "per hour. It is ASSUMED, not fitted."
                .format(_BAND_BASE_FRAC * 100, _BAND_GROWTH_PER_H * 100)
            ),
            "why_it_moves": (
                "Freshwater draw per hour follows that hour's SALT load, not "
                "its water volume, because makeup equals evaporative loss. "
                "Approving a different plan therefore reshapes this curve."
            ),
            "classification": "MODELLED",
        },
    }


def compare_plans(lots: List[DyeLot],
                  baseline_order: List[str],
                  plan_order: List[str],
                  site_id: str,
                  plan_strategy_id: str,
                  shift_start_hour: int = 6) -> Dict[str, Any]:
    """Project the baseline and a candidate plan side by side.

    This is what makes the forecast a decision instrument rather than a
    chart: the two trajectories are the same queue under two different
    decisions, so the gap between them is the decision's consequence.
    """
    base = project(lots, baseline_order, site_id, DEFAULT_STRATEGY,
                   shift_start_hour)
    plan = project(lots, plan_order, site_id, plan_strategy_id,
                   shift_start_hour)

    b_env, p_env = base["envelope"], plan["envelope"]
    return {
        "baseline": base,
        "plan": plan,
        "delta": {
            "projected_draw_l": round(b_env["projected_draw_l"]
                                      - p_env["projected_draw_l"], 1),
            "headroom_gained_l": round(p_env["headroom_l"]
                                       - b_env["headroom_l"], 1),
            "peak_reduction_l": round(b_env["peak_hourly_draw_l"]
                                      - p_env["peak_hourly_draw_l"], 1),
            "baseline_risk": b_env["risk"],
            "plan_risk": p_env["risk"],
            "risk_improved": (b_env["risk"] != p_env["risk"]
                              and p_env["risk"] in
                              ("WITHIN_ALLOWANCE", "TIGHT")),
        },
        "classification": "MODELLED",
    }
