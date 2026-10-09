# -*- coding: utf-8 -*-
"""Re-check every engine figure quoted in the concept note.

    python submission/check_concept_note.py

WHY THIS EXISTS
---------------
The concept note is prose, so nothing stops it from quoting a number the
engine stopped producing three commits ago. That has already happened twice
in this project: figures.json drifted to a stale evidence mix, and the jury
answers carried a cluster water figure five times too large. Both were found
by hand, which is not a method.

So every figure in the note that comes from the engine is listed here with the
call that produces it. The check fails loudly and names the figure, rather than
quietly passing because a regex stopped matching.

Runs in-process - no server needed - so it can go in CI.
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import factors, basin, plant, policy, scenarios   # noqa: E402
from core import economics                                   # noqa: E402
from core import narrative, session as session_mod             # noqa: E402

NOTE = os.path.join(HERE, "concept_note", "CONCEPT_NOTE.md")
HABIT = os.path.join(HERE, "concept_note", "CONCEPT_NOTE_HABIT.md")

# The commercial terms quoted in the 12-section note. They are business
# decisions rather than engine outputs, so they live here and feed the
# business case, which keeps the note and the arithmetic in step.
# Plant-led pricing. The factory fee is per lot, so it does not move
# with the saving; the plant fee is anchored on the plant's own cost.
FEE_PER_LOT = 15.0
PLANT_PLATFORM_INR = 1200000.0
PLANT_ONBOARD_INR = 250000.0
PLANT_SHARE = 0.20
CETP_SALT_T_PER_YEAR = 7700.0
REJECT_FRACTION = 0.07
CLUSTER_MLD_ON_CETPS = 100.0
N_CETPS = 18
N_UNITS = 360
SETUP_INR = 75000.0
LOTS_PER_YEAR = 5000
LOTS_PER_SHIFT = 5

# The lots-per-year figure is anchored on audited fuel use, not on the
# model's own queue multiplied out. These are the three inputs to that
# cross-check, so the check can fail if they stop supporting 5,000.
AUDITED_FUEL_KG_PER_UNIT = 2_000_000      # Tiruppur MSME energy audits
SEASONED_WOOD_MJ_PER_KG = 15.5            # FAO, wood at 20% moisture
BOILER_EFFICIENCY = 0.78                  # the registry's own figure

# Per-lot avoidance for the two plans, from the modelled shift of five
# lots. The first is what the optimiser recommends under today's prices;
# the second is the low-salt plan it declines to pick.
TODAY_FW_PER_LOT = 144.0
TODAY_SALT_PER_LOT = 0.0
LOWSALT_FW_PER_LOT = 1107.6
LOWSALT_SALT_PER_LOT = 12.5


def lakh(v):
    """Indian digit grouping: 5204000 -> 52,04,000."""
    n = int(round(v))
    sign = "-" if n < 0 else ""
    d = str(abs(n))
    if len(d) <= 3:
        return sign + d
    head, tail = d[:-3], d[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts) + "," + tail


def thousands(v):
    return "{:,.0f}".format(v)


def flatten(text):
    """Whitespace- and dash-normalised, so a line wrap or a typographic
    minus cannot fail a match that is really correct."""
    text = text.replace("−", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text)


def build_expectations():
    """Each entry: (label, the exact string the note must contain).

    Everything on the right-hand side is computed, never typed.
    """
    exp = []

    def need(label, text):
        exp.append((label, text))

    # --- coefficients -------------------------------------------------
    need("MEE specific thermal",
         "takes about %.0f kWh of"
         % factors.get("mee_specific_thermal_kwh_per_m3"))
    need("latent heat",
         "Latent heat of %.3f kWh/kg" % factors.get("h_vap_kwh_per_kg"))
    need("steam economy",
         "Steam economy of %.2f kg per kg"
         % factors.get("mee_steam_economy"))


    # --- evidence posture ---------------------------------------------
    counts = factors.evidence_summary()
    need("evidence mix",
         "That makes %d published, %d derived, %d assumed"
         % (counts.get("PUBLISHED", 0), counts.get("DERIVED", 0),
            counts.get("ASSUMED", 0)))
    need("coefficient total",
         "runs on %d input numbers" % sum(counts.values()))
    if counts.get("MEASURED"):
        raise SystemExit(
            "A coefficient is now classed MEASURED. The note says zero are "
            "measured, in several places. Rewrite it before shipping.")

    # --- the salt-not-water proof -------------------------------------
    proof = narrative.proof()
    # The note now states these in words rather than as signed
    # percentages, so the check is that the engine still produces
    # exactly no change and exactly a matching cut - the two facts the
    # wording rests on.
    if abs(proof["cut_water_20pct_change_pct"]) > 1e-9:
        raise SystemExit(
            "Cutting water now moves evaporator energy by %.4f%%. The note "
            "says 'no change at all' in a table and 'Zero, not a small "
            "amount' under it. Both need rewriting."
            % proof["cut_water_20pct_change_pct"])
    if abs(proof["cut_salt_20pct_change_pct"] + 20.0) > 0.05:
        raise SystemExit(
            "Cutting salt 20%% now moves energy by %.2f%%, not -20%%. The "
            "note's '20% less energy' row is wrong."
            % proof["cut_salt_20pct_change_pct"])
    need("cut water row", "| Use 20% less water | **no change at all** |")
    need("cut salt row", "| Put in 20% less salt | **20% less energy** |")

    # --- external validation ------------------------------------------
    val = narrative.validation()
    cpcb = [p for p in val["points"] if abs(p["inlet_tds_mg_l"] - 18340) < 1]
    if not cpcb:
        raise SystemExit("The CPCB 18,340 mg/L validation point is gone.")
    need("CPCB inlet TDS", "18,340 mg/L")
    need("CPCB predicted reject",
         "said **%.1f%%** of the volume"
         % cpcb[0]["predicted_reject_frac_pct"])
    need("published band", "report %.0f to %.0f%% of inlet volume"
         % tuple(val["published_band_pct"]))

    # --- cluster projection -------------------------------------------
    cl = economics.cluster_projection()
    need("cluster units", "across %d factories" % cl["units"])
    need("cluster freshwater", "| Fresh water | %.0f million litres |"
         % cl["freshwater_avoided_million_litres_per_year"])
    need("cluster salt", "| Salt | %s tonnes |"
         % thousands(cl["salt_avoided_tonnes_per_year"]))
    need("cluster steam", "| Evaporator steam | %s MWh |"
         % thousands(cl["evaporator_steam_avoided_mwh_per_year"]))
    need("cluster co2e", "| CO2 | %s tonnes |"
         % thousands(cl["co2e_avoided_tonnes_per_year"]))

    # --- per-shift comparison -----------------------------------------
    s = session_mod.Session()
    s.run_optimisation()
    imp = s.state()["impact"]

    need("baseline row",
         "| Baseline | %s L | %s kWh | Rs %s |"
         % (thousands(imp["baseline_freshwater_intake_l"]),
            thousands(imp["baseline_mee_thermal_kwh"]),
            thousands(imp["baseline_cost_inr"])))
    need("basin stress weight",
         "stress weight of %.2f" % imp["stress_weight"])
    need("reject ceiling plain",
         "around %s mg/L for dyeing water"
         % thousands(factors.get("ro_max_reject_tds_mg_l")))

    cmp_modes = {m["mode_name"]: m
                 for m in scenarios.compare_modes(basin.DEFAULT_SITE)["modes"]}
    base_fw = imp["baseline_freshwater_intake_l"]
    base_st = imp["baseline_mee_thermal_kwh"]
    for name, label in (("Normal operation", "normal economics"),
                        ("Drought / abstraction restriction",
                         "priced scarcity")):
        m = cmp_modes[name]
        fw_cut = round((base_fw - m["freshwater_intake_l"]) / base_fw * 100)
        st_cut = round((base_st - m["mee_thermal_kwh"]) / base_st * 100)
        need("%s row" % label,
             "%s L (-%d%%) | %s kWh (-%d%%) | Rs %s |"
             % (thousands(m["freshwater_intake_l"]), fw_cut,
                thousands(m["mee_thermal_kwh"]), st_cut,
                thousands(m["cost_inr"])))
    # the headline tension, quoted four times in the note
    n = cmp_modes["Normal operation"]
    d = cmp_modes["Drought / abstraction restriction"]
    need("the 6-vs-47 gap",
         "%d%% against %d%% is the most important comparison"
         % (round((base_fw - n["freshwater_intake_l"]) / base_fw * 100),
            round((base_fw - d["freshwater_intake_l"]) / base_fw * 100)))

    # --- plant coordination -------------------------------------------
    modes = scenarios.constraint_modes()
    pn = plant.plant_plan(weights=modes["NORMAL"].weights,
                          constraints=modes["NORMAL"].constraints)
    pd = plant.plant_plan(weights=modes["DROUGHT"].weights,
                          constraints=modes["DROUGHT"].constraints)
    need("plant breach",
         "**%.1f%% of what it can handle**"
         % pn["selfish"]["utilisation_pct"])
    need("plant normal row",
         "| Today's prices | %.1f%% | Yes. Two of four machines take a "
         "worse plan, costing Rs %s a day |"
         % (pn["selfish"]["utilisation_pct"],
            thousands(
                pn["coordinated"]["coordination_premium_inr_per_day"])))
    need("plant drought row",
         "| Water priced for scarcity | %.1f%% | No. Everything fits |"
         % pd["selfish"]["utilisation_pct"])
    need("transfer payment",
         "Rs %s a day in the model" % thousands(
             pn["coordinated"]["coordination_premium_inr_per_day"]))
    if pd["status"] != "WITHIN_CAPACITY":
        raise SystemExit(
            "Priced scarcity no longer removes the breach. The note's "
            "central claim - that this is a pricing failure - is no longer "
            "true and must be rewritten, not patched.")
    from core.process import strategies as _strategies
    need("combination count",
         "all %d combinations" % (len(_strategies()) ** pn["machines"]))
    # --- counts -------------------------------------------------------
    import json
    fg = json.load(io.open(os.path.join(HERE, "figures.json"),
                           encoding="utf-8"))["counts"]
    need("test count", "| Tests | %d, covering" % fg["tests"])
    need("endpoint count", "| API | %d endpoints." % fg["endpoints"])
    need("closing test count", "with %d tests" % fg["tests"])
    need("summary counts",
         "%d API endpoints, %d tests" % (fg["endpoints"], fg["tests"]))

    # --- switching prices ---------------------------------------------
    pol = policy.policy_levers()
    lv = {l["coefficient"]: l for l in pol["levers"]}

    def money(key, fmt):
        l = lv[key]
        if l["status"] != "FOUND":
            raise SystemExit(
                "No switching price found for %s any more. The note quotes "
                "one in a table and in prose; both must be rewritten, not "
                "renumbered." % key)
        return l

    dye = money("low_salt_chemistry_cost_inr_per_kg_fabric", None)
    steam = money("steam_cost_inr_per_kwh_th", None)
    water = money("freshwater_cost_inr_per_m3", None)

    # Quote each threshold on the side where the lever is actually
    # bought - rounding a "rise to" figure down, or a "fall to" figure
    # up, prints a price that does not flip the decision. The engine
    # already rounds this way; the note has to agree with it.
    def quoted(lever, dp):
        scale = 10 ** dp
        v = lever["switching_value"]
        v = (math.ceil(v * scale) if lever["direction"] == "up"
             else math.floor(v * scale)) / scale
        return ("%%.%df" % dp) % v

    need("dye premium row",
         "| Low-salt dye premium | Rs %.2f/kg fabric | Rs %s/kg fabric | "
         "**%d%% cheaper** |"
         % (dye["current_value"], quoted(dye, 2),
            round(abs(dye["percent_change"]))))
    need("steam row",
         "| Boiler steam | Rs %.2f/kWh heat | Rs %s/kWh heat | %d%% dearer |"
         % (steam["current_value"], quoted(steam, 2),
            round(steam["percent_change"])))
    need("water row",
         "| Fresh water | Rs %.0f/m3 | Rs %s/m3 | %d%% dearer |"
         % (water["current_value"], quoted(water, 0),
            round(water["percent_change"])))
    need("dye premium in prose",
         "come down by about %d%%" % round(abs(dye["percent_change"])))

    if dye["coefficient"] != pol["smallest_move"]:
        raise SystemExit(
            "The dye premium is no longer the smallest move. The note says "
            "it is, twice, and builds the procurement argument on it.")

    carbon = pol["implied_carbon_price"]
    need("carbon price",
         "**Rs %s a tonne, about %.0f euro**"
         % (thousands(carbon["inr_per_tonne_co2e"]),
            round(float(
                carbon["benchmark"]["implied_price_eur_per_tonne"]
                .split(" to ")[0]))))
    need("steam increase",
         "go up Rs %.2f per kWh of heat"
         % carbon["steam_increase_inr_per_kwh_th"])
    need("boiler factor",
         "gives off %.3f kg of CO2" % carbon["boiler_co2e_kg_per_kwh_th"])
    bm = carbon["benchmark"]
    need("eu benchmark",
         "charging %.2f euro a tonne on 5 October 2026"
         % bm["benchmark_eur_per_tonne"])

    # --- pilot --------------------------------------------------------
    need("pilot length", "Thirty-two weeks, in six stages")

    return exp


def habit_expectations():
    """Figures quoted in the 12-section note that the shorter one omits."""
    exp = []

    def need(label, text):
        exp.append((label, text))

    sess = session_mod.Session()
    sess.run_optimisation()
    imp = sess.state()["impact"]
    base_cost = imp["baseline_cost_inr"]
    base_fw = imp["baseline_freshwater_intake_l"]
    base_st = imp["baseline_mee_thermal_kwh"]
    cmp_modes = {m["mode_name"]: m
                 for m in scenarios.compare_modes(basin.DEFAULT_SITE)["modes"]}
    nrm = cmp_modes["Normal operation"]
    low = cmp_modes["Drought / abstraction restriction"]

    per_lot_t = (base_cost - nrm["cost_inr"]) / LOTS_PER_SHIFT
    per_lot_l = (base_cost - low["cost_inr"]) / LOTS_PER_SHIFT
    per_shift_t, per_shift_l = per_lot_t, per_lot_l   # ranking guard below

    # Cross-check the annual scale against audited fuel use. If the
    # engine's energy per lot moves far enough that 5,000 lots stops
    # being what the audited fuel supports, every annual figure in
    # section 6 is wrong and must be re-derived.
    opts = sess.state()["optimisation"]["options"]
    conv = [o for o in opts if o["strategy_id"] == "CONVENTIONAL"][0]
    kwh_per_lot = conv["site_energy_kwh"] / LOTS_PER_SHIFT
    supported = (AUDITED_FUEL_KG_PER_UNIT * SEASONED_WOOD_MJ_PER_KG / 3.6
                 * BOILER_EFFICIENCY) / kwh_per_lot
    if not 0.85 * LOTS_PER_YEAR <= supported <= 1.15 * LOTS_PER_YEAR:
        raise SystemExit(
            "Audited fuel use now supports about %.0f lots a year, not %d. "
            "Section 6 annualises at %d and must be re-derived."
            % (supported, LOTS_PER_YEAR, LOTS_PER_YEAR))
    need("kwh per lot",
         "about %s kWh of energy per lot" % thousands(kwh_per_lot))
    need("lots supported", "roughly **%s lots a year**"
         % thousands(round(supported, -3)))

    need("per-lot row",
         "| Net saving per lot | Rs %s | Rs %s |"
         % (thousands(per_lot_t), thousands(per_lot_l)))
    need("lots row",
         "| Lots a year, mid-size unit | %s | %s |"
         % (thousands(LOTS_PER_YEAR), thousands(LOTS_PER_YEAR)))
    need("annual row",
         "| Net saving a year | **Rs %s** | **Rs %s** |"
         % (lakh(round(per_lot_t * LOTS_PER_YEAR, -3)),
            lakh(round(per_lot_l * LOTS_PER_YEAR, -3))))
    fee_year = FEE_PER_LOT * LOTS_PER_YEAR
    need("fee row",
         "| My fee at Rs %d a lot | Rs %s | Rs %s |"
         % (FEE_PER_LOT, lakh(fee_year), lakh(fee_year)))
    need("factory keeps row",
         "| Factory keeps | **Rs %s** | **Rs %s** |"
         % (lakh(round(per_lot_t * LOTS_PER_YEAR - fee_year, -3)),
            lakh(round(per_lot_l * LOTS_PER_YEAR - fee_year, -3))))
    # the fee must stay a small slice of the saving, or the pitch changes
    _slice = fee_year / (per_lot_t * LOTS_PER_YEAR) * 100
    if _slice > 3.0:
        raise SystemExit(
            "The per-lot fee is now %.1f%% of the modelled saving. Section 9 "
            "calls it roughly 1%%." % _slice)
    need("water steam row",
         "| Water and steam cut | %d%% | %d%% |"
         % (round((base_fw - nrm["freshwater_intake_l"]) / base_fw * 100),
            round((base_fw - low["freshwater_intake_l"]) / base_fw * 100)))

    # Split the recommended plan into re-ordering and the rinse change.
    # The note's honesty about counter-current units rests on this, so it
    # is recomputed here rather than trusted.
    import itertools
    from core.optimizer import (evaluate_candidate, ObjectiveWeights,
                                HardConstraints)
    from core.process import reference_lots, arrival_order
    _lots, _arr = reference_lots(), arrival_order()
    _w, _c = ObjectiveWeights(), HardConstraints()

    def _cost(r):
        return r.consequence["cost_inr"]["total"] + r.sequence["strategy_cost_inr"]

    def _best(strategy):
        b = None
        for o in itertools.permutations([x.lot_id for x in _lots]):
            r = evaluate_candidate(_lots, list(o), basin.DEFAULT_SITE,
                                   _w, _c, strategy)
            if r.feasible and (b is None or r.objective_inr < b.objective_inr):
                b = r
        return b

    _base = evaluate_candidate(_lots, _arr, basin.DEFAULT_SITE, _w, _c,
                               "CONVENTIONAL")
    _seq, _cc = _best("CONVENTIONAL"), _best("COUNTER_CURRENT")
    seq_lot = (_cost(_base) - _cost(_seq)) / LOTS_PER_SHIFT
    rinse_lot = (_cost(_seq) - _cost(_cc)) / LOTS_PER_SHIFT

    # The claim that counter-current changes fresh water and evaporator
    # steam by exactly nothing must stay true, or that paragraph is wrong.
    if (abs(_seq.consequence["water"]["freshwater_intake_l"]
            - _cc.consequence["water"]["freshwater_intake_l"]) > 0.5
            or abs(_seq.consequence["zld"]["mee_thermal_kwh"]
                   - _cc.consequence["zld"]["mee_thermal_kwh"]) > 0.5):
        raise SystemExit("Counter-current rinsing now changes fresh water or "
                         "evaporator steam. Section 6 says it does not.")

    need("split row reorder",
         "| Re-ordering the lots | Rs %s | Rs %s |"
         % (thousands(seq_lot), lakh(round(seq_lot * LOTS_PER_YEAR, -3))))
    need("split row rinse",
         "| Switching to counter-current rinsing | Rs %s | Rs %s |"
         % (thousands(rinse_lot), lakh(round(rinse_lot * LOTS_PER_YEAR, -3))))
    need("split row total",
         "| **Both together, the plan it recommends** | **Rs %s** | **Rs %s** |"
         % (thousands(per_lot_t), lakh(round(per_lot_t * LOTS_PER_YEAR, -3))))
    need("rinse lot in limits", "about Rs %s\n  a lot" % thousands(rinse_lot)
         if False else "about Rs %s" % thousands(rinse_lot))
    _proc_cut = 1 - (_cc.consequence["water"]["process_demand_l"]
                     / _seq.consequence["water"]["process_demand_l"])
    if not 0.20 <= _proc_cut <= 0.30:
        raise SystemExit("Counter-current now cuts circulated water by %.0f%%, "
                         "not 'about a quarter'." % (_proc_cut * 100))

    # Fuel sensitivity quoted in section 10: steam a quarter cheaper.
    with factors.REGISTRY_LOCK:
        with policy._patched("steam_cost_inr_per_kwh_th",
                             factors.get("steam_cost_inr_per_kwh_th") * 0.75):
            _sw = policy.switching_point(
                "low_salt_chemistry_cost_inr_per_kg_fabric")
    need("fuel sensitivity",
         "fall about %d%% instead of 12%%" % round(abs(_sw["percent_change"])))

    # --- what salt costs a treatment plant, from the registry ---------
    C = factors.get("ro_max_reject_tds_mg_l")
    m3_per_t = 1000.0 / (C / 1000.0)
    cost_per_t = m3_per_t * (
        factors.get("mee_specific_thermal_kwh_per_m3")
        * factors.get("steam_cost_inr_per_kwh_th")
        + factors.get("mee_opex_inr_per_m3_reject")
        + factors.get("mee_specific_electrical_kwh_per_m3")
        * factors.get("electricity_cost_inr_per_kwh"))
    need("salt m3", "about %d cubic\nmetres of reject" % round(m3_per_t))
    need("salt steam", "Rs %s of\nsteam" % thousands(
        m3_per_t * factors.get("mee_specific_thermal_kwh_per_m3")
        * factors.get("steam_cost_inr_per_kwh_th")))
    need("salt opex", "Rs %s of evaporator operating cost" % thousands(
        m3_per_t * factors.get("mee_opex_inr_per_m3_reject")))
    need("salt power", "Rs %s of power" % thousands(
        m3_per_t * factors.get("mee_specific_electrical_kwh_per_m3")
        * factors.get("electricity_cost_inr_per_kwh")))
    need("salt per tonne", "**Rs %s a tonne**" % thousands(cost_per_t))

    plant_cost = CETP_SALT_T_PER_YEAR * cost_per_t
    need("plant salt tonnes",
         "**%s tonnes of salt a year" % thousands(CETP_SALT_T_PER_YEAR))
    need("plant cost", "costing it around Rs %.2f crore**" % (plant_cost / 1e7))
    for pct, label in ((3, "3%"), (10, "10%")):
        need("plant saving %s" % label,
             "Rs %s" % lakh(round(CETP_SALT_T_PER_YEAR * pct / 100
                                  * cost_per_t, -4)))

    # The plant fee has to stay a small share of the plant's own cost,
    # or the "a manager can check this without trusting my model" claim
    # stops being true.
    _pf = PLANT_PLATFORM_INR / plant_cost * 100
    if _pf > 4.0:
        raise SystemExit(
            "The plant platform fee is now %.1f%% of the plant's salt-driven "
            "cost. Section 9 calls it about 1.6%%." % _pf)
    need("plant fee pct", "about %.1f%% of it" % _pf)

    need("platform fee", "| Treatment plant platform | Rs %s a year |"
         % lakh(PLANT_PLATFORM_INR))
    need("onboard fee", "| Treatment plant onboarding, once | Rs %s |"
         % lakh(PLANT_ONBOARD_INR))
    need("plant share", "| Share of the plant's verified reduction | %d%% |"
         % round(PLANT_SHARE * 100))
    need("factory fee", "| Member factory planner | Rs %d a lot, about Rs %s "
         "a year |" % (FEE_PER_LOT, lakh(fee_year)))

    need("tirupur market",
         "%d treatment plants at about Rs %s a year is Rs %.1f crore, and "
         "%d factories at Rs %s is Rs %.1f crore. Together of the order of "
         "**Rs %.1f crore a year**"
         % (N_CETPS, lakh(2000000), N_CETPS * 2000000 / 1e7,
            N_UNITS, lakh(fee_year), N_UNITS * fee_year / 1e7,
            (N_CETPS * 2000000 + N_UNITS * fee_year) / 1e7))

    # --- revenue projection -------------------------------------------
    plants = {1: 0, 2: 1, 3: 3}
    new_plants = {1: 0, 2: 1, 3: 2}
    facts = {1: 2, 2: 10, 3: 30}
    y2 = (plants[2] * PLANT_PLATFORM_INR + new_plants[2] * PLANT_ONBOARD_INR
          + facts[2] * fee_year)
    y3 = (plants[3] * PLANT_PLATFORM_INR + new_plants[3] * PLANT_ONBOARD_INR
          + facts[3] * fee_year)
    need("plants live row",
         "| Treatment plants live | 0, pilot only | %d | %d |"
         % (plants[2], plants[3]))
    need("factories live row",
         "| Member factories live | 2, pilot | %d | %d |"
         % (facts[2], facts[3]))
    need("platform fees row",
         "| Plant platform fees | none | Rs %s | Rs %s |"
         % (lakh(plants[2] * PLANT_PLATFORM_INR),
            lakh(plants[3] * PLANT_PLATFORM_INR)))
    need("onboarding row",
         "| Plant onboarding, new plants only | none | Rs %s | Rs %s |"
         % (lakh(new_plants[2] * PLANT_ONBOARD_INR),
            lakh(new_plants[3] * PLANT_ONBOARD_INR)))
    need("planner fees row",
         "| Factory planner fees | waived during pilot | Rs %s | Rs %s |"
         % (lakh(facts[2] * fee_year), lakh(facts[3] * fee_year)))
    need("revenue totals",
         "| **Total revenue** | **nil** | **Rs %s** | **Rs %s** |"
         % (lakh(y2), lakh(y3)))

    per_site = 60000 + 50000 + 35000 + 15000 + 15000
    need("per site", "| **Per site** | **Rs %s** | |" % lakh(per_site))
    sub = per_site * 2 + 50000 + 60000 + 20000
    need("pilot total", "| **Total** | **Rs %s** | |"
         % lakh(sub + round(sub * 0.10)))
    need("closing pilot cost", "costs about Rs %s"
         % lakh(sub + round(sub * 0.10)))

    need("MEE thermal",
         "takes about %.0f kWh of heat"
         % factors.get("mee_specific_thermal_kwh_per_m3"))
    need("reject ceiling",
         "The %s mg/L limit" % thousands(
             factors.get("ro_max_reject_tds_mg_l")))

    proof = narrative.proof()
    if abs(proof["cut_water_20pct_change_pct"]) > 1e-9:
        raise SystemExit("Cutting water now moves evaporator energy by "
                         "%.4f%%." % proof["cut_water_20pct_change_pct"])
    if abs(proof["cut_salt_20pct_change_pct"] + 20.0) > 0.05:
        raise SystemExit("Cutting salt 20%% now moves energy by %.2f%%."
                         % proof["cut_salt_20pct_change_pct"])
    need("cut water row", "| Uses 20% less water | **no change at all** |")
    need("cut salt row", "| Puts in 20% less salt | **20% less energy** |")

    val = narrative.validation()
    cpcb = [q for q in val["points"] if abs(q["inlet_tds_mg_l"] - 18340) < 1]
    if not cpcb:
        raise SystemExit("The CPCB 18,340 mg/L validation point is gone.")
    need("validation row",
         "18,340 mg/L, the model predicted %.1f%% leftover. Indian plants "
         "report %.0f to %.0f%%"
         % (cpcb[0]["predicted_reject_frac_pct"],
            val["published_band_pct"][0], val["published_band_pct"][1]))

    counts = factors.evidence_summary()
    if counts.get("MEASURED"):
        raise SystemExit("A coefficient is now MEASURED.")
    need("input numbers row",
         "| Input numbers | %d, each labelled with its source. %d "
         "published, %d derived, %d assumed, 0 measured |"
         % (sum(counts.values()), counts.get("PUBLISHED", 0),
            counts.get("DERIVED", 0), counts.get("ASSUMED", 0)))
    need("published row", "| Published | %d |" % counts.get("PUBLISHED", 0))

    import json as _json
    fg = _json.load(io.open(os.path.join(HERE, "figures.json"),
                            encoding="utf-8"))["counts"]
    need("api row", "| API | %d endpoints." % fg["endpoints"])
    need("tests row", "| Tests | %d, covering" % fg["tests"])

    need("baseline row",
         "| Baseline | %s L | %s kWh | Rs %s |"
         % (thousands(base_fw), thousands(base_st), thousands(base_cost)))
    for name, label in (("Normal operation", "Recommended today"),
                        ("Drought / abstraction restriction",
                         "Available with low-salt chemistry")):
        m = cmp_modes[name]
        need("%s row" % label.lower(),
             "| %s | %s L (-%d%%) | %s kWh (-%d%%) | Rs %s |"
             % (label, thousands(m["freshwater_intake_l"]),
                round((base_fw - m["freshwater_intake_l"]) / base_fw * 100),
                thousands(m["mee_thermal_kwh"]),
                round((base_st - m["mee_thermal_kwh"]) / base_st * 100),
                thousands(m["cost_inr"])))

    cl = economics.cluster_projection()
    need("cluster units", "across %d units at 900 lots" % cl["units"])
    need("cluster water", "| Fresh water | %.0f million litres |"
         % cl["freshwater_avoided_million_litres_per_year"])
    need("cluster salt", "| Salt | %s tonnes |"
         % thousands(cl["salt_avoided_tonnes_per_year"]))
    need("cluster steam", "| Evaporator steam | %s MWh |"
         % thousands(cl["evaporator_steam_avoided_mwh_per_year"]))
    need("cluster co2", "| CO2 | %s tonnes |"
         % thousands(cl["co2e_avoided_tonnes_per_year"]))

    modes = scenarios.constraint_modes()
    pn = plant.plant_plan(weights=modes["NORMAL"].weights,
                          constraints=modes["NORMAL"].constraints)
    need("plant breach",
         "**%.1f%% of what it can" % pn["selfish"]["utilisation_pct"])

    pol = policy.policy_levers()
    lv = {l["coefficient"]: l for l in pol["levers"]}
    dye = lv["low_salt_chemistry_cost_inr_per_kg_fabric"]
    steam_l = lv["steam_cost_inr_per_kwh_th"]
    water_l = lv["freshwater_cost_inr_per_m3"]

    def quoted(lever, dp):
        scale = 10 ** dp
        v = lever["switching_value"]
        v = (math.ceil(v * scale) if lever["direction"] == "up"
             else math.floor(v * scale)) / scale
        return ("%%.%df" % dp) % v

    need("dye row",
         "| Low-salt dye premium | Rs %.2f/kg fabric | Rs %s/kg fabric | "
         "**%d%% cheaper** |"
         % (dye["current_value"], quoted(dye, 2),
            round(abs(dye["percent_change"]))))
    need("steam lever row",
         "| Boiler steam | Rs %.2f/kWh heat | Rs %s/kWh heat | %d%% dearer |"
         % (steam_l["current_value"], quoted(steam_l, 2),
            round(steam_l["percent_change"])))
    need("water lever row",
         "| Fresh water | Rs %.0f/m3 | Rs %s/m3 | %d%% dearer |"
         % (water_l["current_value"], quoted(water_l, 0),
            round(water_l["percent_change"])))
    need("dye gap in business model",
         "Close the %d%% gap" % round(abs(dye["percent_change"])))

    carbon = pol["implied_carbon_price"]
    need("steam increase",
         "rise Rs %.2f" % carbon["steam_increase_inr_per_kwh_th"])
    need("boiler factor",
         "gives off %.3f kg of CO2" % carbon["boiler_co2e_kg_per_kwh_th"])
    need("carbon price",
         "**Rs %s a tonne, about %.0f euro**"
         % (thousands(carbon["inr_per_tonne_co2e"]),
            round(float(carbon["benchmark"]["implied_price_eur_per_tonne"]
                        .split(" to ")[0]))))
    need("eu benchmark",
         "charging %.2f euro a tonne on 5 October 2026"
         % carbon["benchmark"]["benchmark_eur_per_tonne"])

    return exp


def check_one(path, expectations, heading):
    if not os.path.exists(path):
        raise SystemExit("missing: " + path)
    flat = flatten(io.open(path, encoding="utf-8").read())
    safe("")
    safe(heading)
    safe("=" * 66)
    missing = []
    for label, text in expectations:
        hit = flatten(text) in flat
        if not hit:
            missing.append((label, text))
        safe("  %s  %-26s %s" % ("ok  " if hit else "FAIL", label,
                                 "" if hit else text))
    return missing


def safe(line):
    """Print on a console that may not speak Unicode (Windows cp1252)."""
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))


def main():
    expectations = build_expectations()
    missing = check_one(NOTE, expectations, "SHORT CONCEPT NOTE")

    # The 12-section note quotes the same engine plus the commercial
    # figures, so it gets the shared set and its own on top.
    hx = habit_expectations()
    missing += check_one(HABIT, hx,
                         "12-SECTION CONCEPT NOTE (HABIT TEMPLATE)")
    total = len(expectations) + len(hx)

    safe("=" * 66)
    if missing:
        safe("")
        safe("%d of %d figures no longer match the engine."
             % (len(missing), total))
        safe("Fix the note - or if the engine changed on purpose, fix both.")
        return 1
    safe("")
    safe("All %d engine figures across both concept notes check out." % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
