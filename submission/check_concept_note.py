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


def safe(line):
    """Print on a console that may not speak Unicode (Windows cp1252)."""
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))


def main():
    if not os.path.exists(NOTE):
        raise SystemExit("missing: " + NOTE)
    note = io.open(NOTE, encoding="utf-8").read()
    # the note is written with en-dashes and non-breaking context; compare on
    # a whitespace-normalised copy so a line wrap cannot fail a real match
    flat = flatten(note)

    expectations = build_expectations()
    missing = []
    for label, text in expectations:
        if flatten(text) not in flat:
            missing.append((label, text))

    print("CONCEPT NOTE FIGURE CHECK")
    print("=" * 66)
    for label, text in expectations:
        hit = flatten(text) in flat
        line = "  %s  %-24s %s" % ("ok  " if hit else "FAIL", label,
                                     text if not hit else "")
        safe(line)
    print("=" * 66)
    if missing:
        print("\n%d of %d figures in the note no longer match the engine."
              % (len(missing), len(expectations)))
        print("Fix the note - or if the engine changed on purpose, fix both.")
        return 1
    print("\nAll %d engine figures in the concept note still check out."
          % len(expectations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
