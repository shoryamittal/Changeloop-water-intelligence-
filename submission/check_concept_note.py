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
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import factors, basin, plant, scenarios, economics   # noqa: E402
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
         "about %.0f kWh of thermal energy"
         % factors.get("mee_specific_thermal_kwh_per_m3"))
    need("latent heat",
         "Latent heat of %.3f kWh/kg" % factors.get("h_vap_kwh_per_kg"))
    need("steam economy",
         "steam economy of %.2f kg" % factors.get("mee_steam_economy"))
    need("reject TDS ceiling",
         "around %s mg/L" % thousands(factors.get("ro_max_reject_tds_mg_l")))

    # --- evidence posture ---------------------------------------------
    counts = factors.evidence_summary()
    need("evidence mix",
         "%d published, %d derived, %d assumed"
         % (counts.get("PUBLISHED", 0), counts.get("DERIVED", 0),
            counts.get("ASSUMED", 0)))
    need("coefficient total",
         "Each of the %d numbers" % sum(counts.values()))
    if counts.get("MEASURED"):
        raise SystemExit(
            "A coefficient is now classed MEASURED. The note says zero are "
            "measured, in several places. Rewrite it before shipping.")

    # --- the salt-not-water proof -------------------------------------
    proof = narrative.proof()
    need("cut water effect",
         "| Cut effluent water volume by 20%% | **%+.1f%%** |"
         % proof["cut_water_20pct_change_pct"])
    need("cut salt effect",
         "| Cut salt load by 20%% | **%.1f%%** |"
         % proof["cut_salt_20pct_change_pct"])

    # --- external validation ------------------------------------------
    val = narrative.validation()
    cpcb = [p for p in val["points"] if abs(p["inlet_tds_mg_l"] - 18340) < 1]
    if not cpcb:
        raise SystemExit("The CPCB 18,340 mg/L validation point is gone.")
    need("CPCB inlet TDS", "18,340 mg/L")
    need("CPCB predicted reject",
         "reject fraction of **%.1f%%**" % cpcb[0]["predicted_reject_frac_pct"])
    need("published band", "%.0f-%.0f%% of inlet volume"
         % tuple(val["published_band_pct"]))

    # --- cluster projection -------------------------------------------
    cl = economics.cluster_projection()
    need("cluster units", "across %d units" % cl["units"])
    need("cluster freshwater", "| %.0f million litres/year |"
         % cl["freshwater_avoided_million_litres_per_year"])
    need("cluster salt", "| %s tonnes/year |"
         % thousands(cl["salt_avoided_tonnes_per_year"]))
    need("cluster steam", "| %s MWh/year |"
         % thousands(cl["evaporator_steam_avoided_mwh_per_year"]))
    need("cluster co2e", "| %s tonnes/year |"
         % thousands(cl["co2e_avoided_tonnes_per_year"]))

    # --- per-shift comparison -----------------------------------------
    s = session_mod.Session()
    s.run_optimisation()
    imp = s.state()["impact"]
    need("baseline freshwater",
         "| Baseline | %s L |" % thousands(imp["baseline_freshwater_intake_l"]))
    need("baseline steam",
         "%s kWh | ₹%s |" % (thousands(imp["baseline_mee_thermal_kwh"]),
                                  thousands(imp["baseline_cost_inr"])))
    need("basin stress weight",
         "stress weight of %.2f" % imp["stress_weight"])

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
             "%s L (−%d%%) | %s kWh (−%d%%) | ₹%s |"
             % (thousands(m["freshwater_intake_l"]), fw_cut,
                thousands(m["mee_thermal_kwh"]), st_cut,
                thousands(m["cost_inr"])))
    # the headline tension, quoted four times in the note
    n = cmp_modes["Normal operation"]
    d = cmp_modes["Drought / abstraction restriction"]
    need("the 6-vs-47 gap",
         "That %d%% against %d%% gap"
         % (round((base_fw - n["freshwater_intake_l"]) / base_fw * 100),
            round((base_fw - d["freshwater_intake_l"]) / base_fw * 100)))

    # --- plant coordination -------------------------------------------
    modes = scenarios.constraint_modes()
    pn = plant.plant_plan(weights=modes["NORMAL"].weights,
                          constraints=modes["NORMAL"].constraints)
    pd = plant.plant_plan(weights=modes["DROUGHT"].weights,
                          constraints=modes["DROUGHT"].constraints)
    need("plant breach",
         "**%.1f%% of capacity**" % pn["selfish"]["utilisation_pct"])
    need("plant normal row",
         "| Normal operation | %.1f%% | Yes — %d of %d machines"
         % (pn["selfish"]["utilisation_pct"],
            len(pn["coordinated"]["machines_that_move"]), pn["machines"]))
    need("coordination premium",
         "₹%s/day" % thousands(
             pn["coordinated"]["coordination_premium_inr_per_day"]))
    need("plant drought row",
         "| Scarcity priced (drought) | %.1f%% | None | ₹0 |"
         % pd["selfish"]["utilisation_pct"])
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
    need("test count", "| Tests | %d," % fg["tests"])
    need("endpoint count", "| %d REST endpoints" % fg["endpoints"])
    need("closing test count", "with %d tests" % fg["tests"])

    # --- pilot --------------------------------------------------------
    need("pilot length", "32-week staged pilot")

    return exp


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
        print("  %s  %-24s %s" % ("ok  " if hit else "FAIL", label,
                                  text if not hit else ""))
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
