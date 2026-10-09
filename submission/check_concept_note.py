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
SHARE_OF_SAVING = 0.25
SETUP_INR = 75000.0
LOTS_PER_YEAR = 9000

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
    from core import economics
    exp = []

    def need(label, text):
        exp.append((label, text))

    def case(fw, salt):
        return economics.business_case({
            "lots_per_year": LOTS_PER_YEAR,
            "freshwater_avoided_per_lot_l": fw,
            "salt_avoided_per_lot_kg": salt,
            "freshwater_cost_inr_per_m3":
                factors.get("freshwater_cost_inr_per_m3"),
            "recycled_water_cost_inr_per_m3":
                factors.get("recycled_water_cost_inr_per_m3"),
            "steam_cost_inr_per_kwh_th":
                factors.get("steam_cost_inr_per_kwh_th"),
            "salt_cost_inr_per_kg": factors.get("salt_cost_inr_per_kg"),
            "implementation_cost_inr": SETUP_INR,
            # The fee is a share of the gross saving, so the gross is what
            # the note quotes; pass no subscription and derive the share.
            "annual_subscription_inr": 0.0,
        })

    today = case(TODAY_FW_PER_LOT, TODAY_SALT_PER_LOT)
    lowsalt = case(LOWSALT_FW_PER_LOT, LOWSALT_SALT_PER_LOT)
    for name, r in (("today", today), ("low-salt", lowsalt)):
        if r.get("status") != "CALCULATED":
            raise SystemExit(
                "The %s business case no longer computes (%s). Section 6 of "
                "the 12-section note quotes it." % (name, r.get("status")))

    def k(v):
        return lakh(round(v / 1000.0) * 1000)

    g_today = today["annual_gross_benefit_inr"]
    g_low = lowsalt["annual_gross_benefit_inr"]
    fee_today = g_today * SHARE_OF_SAVING
    fee_low = g_low * SHARE_OF_SAVING

    need("share", "| Share of verified saving | %d%% |"
         % round(SHARE_OF_SAVING * 100))
    need("setup cost", "| One-off setup | Rs %s per unit |" % lakh(SETUP_INR))
    need("saving row",
         "| Saving the system can verify | Rs %s | Rs %s |"
         % (k(g_today), k(g_low)))
    need("share row",
         "| My %d%% share | Rs %s | Rs %s |"
         % (round(SHARE_OF_SAVING * 100), k(fee_today), k(fee_low)))
    need("factory keeps row",
         "| **Factory keeps** | **Rs %s** | **Rs %s** |"
         % (k(g_today - fee_today), k(g_low - fee_low)))
    need("share per unit",
         "about Rs %s a year" % k(fee_today))

    # the flat-fee figure the note cites as the reason it was abandoned
    need("rejected flat fee share",
         "would have taken %d%% of the saving" % round(240000 / g_today * 100))

    # payback on setup, in months, against what the factory keeps
    months = SETUP_INR / (g_today - fee_today) * 12
    if not 2.0 <= months <= 4.0:
        raise SystemExit(
            "Payback on setup is now %.1f months. Section 6 says 'about 3 "
            "months'." % months)

    # revenue projections
    live = {1: 2, 2: 12, 3: 40}
    new_units = {1: 2, 2: 10, 3: 28}
    need("y2 setup", "| Setup revenue, new units only | Rs %s | Rs %s | Rs %s |"
         % (lakh(new_units[1] * SETUP_INR), lakh(new_units[2] * SETUP_INR),
            lakh(new_units[3] * SETUP_INR)))
    need("y2 share",
         "| Share of verified saving | waived during pilot | Rs %s | Rs %s |"
         % (lakh(round(live[2] * fee_today, -3)),
            lakh(round(live[3] * fee_today, -3))))
    y2 = new_units[2] * SETUP_INR + round(live[2] * fee_today, -3)
    y3 = new_units[3] * SETUP_INR + round(live[3] * fee_today, -3)
    need("revenue totals",
         "| **Total revenue** | **Rs %s** | **Rs %s** | **Rs %s** |"
         % (lakh(new_units[1] * SETUP_INR), lakh(y2), lakh(y3)))

    # pilot cost build-up
    per_site = 60000 + 50000 + 35000 + 15000 + 15000
    need("per site", "| **Per site** | **Rs %s** | |" % lakh(per_site))
    two = per_site * 2
    sub = two + 50000 + 60000 + 20000
    need("pilot total", "| **Total** | **Rs %s** | |"
         % lakh(sub + round(sub * 0.10)))
    need("closing pilot cost", "costs about Rs %s"
         % lakh(sub + round(sub * 0.10)))

    # market size follows from the share, so it has to move with it
    need("tirupur market",
         "roughly **Rs %.1f crore a year**" % (360 * fee_today / 1e7))

    # --- physics and validation ---------------------------------------
    need("MEE thermal",
         "takes about %.0f kWh of heat"
         % factors.get("mee_specific_thermal_kwh_per_m3"))
    need("reject ceiling",
         "The %s mg/L limit" % thousands(
             factors.get("ro_max_reject_tds_mg_l")))

    proof = narrative.proof()
    if abs(proof["cut_water_20pct_change_pct"]) > 1e-9:
        raise SystemExit(
            "Cutting water now moves evaporator energy by %.4f%%. The "
            "12-section note says 'no change at all'."
            % proof["cut_water_20pct_change_pct"])
    if abs(proof["cut_salt_20pct_change_pct"] + 20.0) > 0.05:
        raise SystemExit(
            "Cutting salt 20%% now moves energy by %.2f%%, not -20%%."
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

    # --- counts --------------------------------------------------------
    counts = factors.evidence_summary()
    if counts.get("MEASURED"):
        raise SystemExit("A coefficient is now MEASURED. Both notes say "
                         "zero, in several places.")
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

    # --- per-shift and cluster -----------------------------------------
    sess = session_mod.Session()
    sess.run_optimisation()
    imp = sess.state()["impact"]
    cmp_modes = {m["mode_name"]: m
                 for m in scenarios.compare_modes(basin.DEFAULT_SITE)["modes"]}
    base_fw = imp["baseline_freshwater_intake_l"]
    base_st = imp["baseline_mee_thermal_kwh"]
    need("baseline row",
         "| Baseline | %s L | %s kWh | Rs %s |"
         % (thousands(base_fw), thousands(base_st),
            thousands(imp["baseline_cost_inr"])))
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

    # --- plant and policy ----------------------------------------------
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
    need("steam row",
         "| Boiler steam | Rs %.2f/kWh heat | Rs %s/kWh heat | %d%% dearer |"
         % (steam_l["current_value"], quoted(steam_l, 2),
            round(steam_l["percent_change"])))
    need("water row",
         "| Fresh water | Rs %.0f/m3 | Rs %s/m3 | %d%% dearer |"
         % (water_l["current_value"], quoted(water_l, 0),
            round(water_l["percent_change"])))
    need("dye gap in business model",
         "premium falls about %d%%" % round(abs(dye["percent_change"])))

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
