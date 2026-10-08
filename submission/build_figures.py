# -*- coding: utf-8 -*-
"""Generate submission/figures.json from the engine.

WHY THIS EXISTS
---------------
figures.json feeds every number in the pitch deck. It used to be
maintained by hand, which meant the deck could drift away from the
product without anyone noticing - and it had. After the coefficient
registry was re-sourced from published data, the deck was still quoting
an evidence mix of 5 published / 13 assumed and a specific thermal energy
of 179.13 kWh/m3, neither of which had been true for some time.

A deck that quotes numbers the software does not produce is the single
easiest thing for a reviewer to catch and the hardest to recover from. So
the figures are generated, not typed:

    python submission/build_figures.py          # regenerate
    python submission/build_figures.py --check  # fail if stale (CI)
    node   submission/build_deck.js             # rebuild the deck

Run the generator before the deck, always. `--check` exits non-zero if
the committed figures.json no longer matches the engine, so staleness
becomes a test failure rather than a slide nobody re-read.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import economics, factors, forecast as fc_mod       # noqa: E402
from core import narrative, process, scenarios, zld            # noqa: E402
from core import session as session_mod                      # noqa: E402

OUT = os.path.join(HERE, "figures.json")


def _r(x, n=1):
    return round(float(x), n) if x is not None else None


def _counts() -> dict:
    """Test and endpoint counts, counted rather than typed.

    The deck used to state "95 engine tests" and "25 API endpoints" as
    literals. Both drifted the moment a test or route was added, and a
    reviewer who counts is entitled to hold that against everything else
    on the slide.
    """
    import re

    tests = 0
    tdir = os.path.join(ROOT, "tests")
    for name in sorted(os.listdir(tdir)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        with open(os.path.join(tdir, name), encoding="utf-8") as fh:
            tests += len(re.findall(r"^\s+def test_", fh.read(), re.M))

    with open(os.path.join(ROOT, "backend", "server.py"),
              encoding="utf-8") as fh:
        body = fh.read()
    endpoints = len(set(re.findall(r'route == "(/api/[^"]*)"', body)))

    return {"tests": tests, "endpoints": endpoints,
            "test_files": len([n for n in os.listdir(tdir)
                               if n.startswith("test_")])}


def build() -> dict:
    # Walk the full golden path, exactly as the demo does. Stopping at the
    # optimisation would leave impact at zero, because nothing has been
    # APPROVED yet - the system attributes a saving only to a decision a
    # named human actually took. That is the point of the design, and it
    # is also the trap: a figures file built from an un-walked session
    # reports every avoided litre as zero.
    s = session_mod.Session()
    s.run_optimisation()
    s.decide_sequence(approve=True, actor="Shift planner",
                      note="Figures generation: approve the recommendation.")
    s.run_washoff()
    s.release_washoff(approve=True, actor="Quality supervisor",
                      note="Figures generation: release on sensor evidence.")
    st = s.state()
    imp_check = st["impact"]
    if not imp_check["freshwater_avoided_l"] > 0:
        raise SystemExit(
            "Golden path did not produce a saving - figures would be zero. "
            "Sequencing status: {}, wash-off status: {}".format(
                st["sequencing_status"], st["washoff_status"]))
    opt = st["optimisation"]
    imp = st["impact"]
    ach = imp["achieved_scenario"]

    # ---- the three options, keyed the way the deck expects ------------
    options = {}
    for o in opt["options"]:
        options[o["option_id"]] = {
            "strategy": o["strategy_id"],
            "fresh": _r(o["freshwater_intake_l"]),
            "salt": _r(o["total_salt_kg"], 2),
            "mee": _r(o["mee_thermal_kwh"], 3),
            "co2": _r(o["co2e_kg"], 2),
            "cost": _r(o["cost_inr"], 2),
            "late": _r(o["total_late_h"]),
            "feasible": bool(o["feasible"]),
            "breaches": int(o["firm_date_breaches"]),
            "title": o["title"],
        }

    # ---- forecast envelopes under each lever -------------------------
    # ---- the three-lever envelope comparison -------------------------
    # All three projections use the SAME queue in the SAME order from the
    # SAME pre-decision state, so the only thing that differs is the
    # process strategy. That isolation is the whole point: mixing in a
    # post-decision state (as a hand-maintained figures file once did)
    # produces three numbers that cannot be attributed to the lever.
    #
    # The result is the core thesis, visible in the abstraction envelope:
    # the WATER lever moves it by nothing at all, because in a closed loop
    # freshwater makeup equals evaporative loss, which equals reject
    # volume, which is set by salt. Only the SALT lever moves the
    # envelope. tests/test_published_validation.py asserts this.
    envelopes, series = {}, {}
    lots = s.lots
    order = s.arrival
    for key, strategy in (("baseline", "CONVENTIONAL"),
                          ("water_lever", "COUNTER_CURRENT"),
                          ("salt_lever", "LOW_SALT")):
        f = fc_mod.project(lots, order, s.site_id, strategy)
        env = f["envelope"]
        envelopes[key] = {
            "draw": _r(env["projected_draw_l"]),
            "alloc": _r(env["allocation_l"]),
            "util": _r(env["utilisation_pct"]),
            "risk": env["risk"],
            "breach": env.get("breach_clock"),
            "basis": env.get("allocation_basis", ""),
        }
        # one point per hour: the cumulative freshwater trajectory
        seen, pts = set(), []
        for step in f["steps"]:
            if step["clock"] in seen:
                pts[-1]["cum"] = _r(step["cumulative_freshwater_l"])
                continue
            seen.add(step["clock"])
            pts.append({"clock": step["clock"],
                        "cum": _r(step["cumulative_freshwater_l"])})
        series[key] = pts

    ev = factors.evidence_summary()

    # ---- the external validation: our strongest evidence -------------
    val = narrative.validation()

    fig = {
        "candidates": opt["candidates_evaluated"],
        "optimality": opt["optimality"],
        "options": options,
        "impact": {
            "fresh_base": _r(imp["baseline_freshwater_intake_l"]),
            "fresh_ach": _r(imp["achieved_freshwater_intake_l"]),
            "fresh_av": _r(imp["freshwater_avoided_l"]),
            "leq": _r(imp["stress_equivalent_avoided_l_eq"]),
            "salt_av": _r(imp["salt_avoided_kg"], 2),
            "mee_av": _r(imp["mee_thermal_avoided_kwh"]),
            "co2_base": _r(imp["baseline_co2e_kg"], 2),
            "co2_av": _r(imp["co2e_avoided_kg"], 2),
            "cost_base": _r(imp["baseline_cost_inr"], 2),
            "cost_av": _r(imp["cost_avoided_inr"], 2),
            "invariants": len(imp["validation"]["checks"]),
            "all_pass": bool(imp["validation"]["all_pass"]),
        },
        "envelopes": envelopes,
        "envelope_note": (
            "All three projections are the same queue, same order, same "
            "pre-decision state; only the process strategy differs. The "
            "water lever (counter-current rinsing) moves the abstraction "
            "envelope by exactly nothing, because in a closed loop "
            "freshwater makeup equals evaporative loss, which equals RO "
            "reject volume, which is set by salt mass. Only the salt lever "
            "moves it. This is the same finding as the salt-vs-water "
            "sensitivity, arriving independently through the forecast."
        ),
        "insight": zld.sensitivity_salt_vs_water(),
        "ablation": [
            {"v": a["variant"], "label": a["label"],
             "fresh": _r(a.get("freshwater_avoided_l")),
             "share": _r(a.get("reported_vs_full_pct"))}
            for a in scenarios.ablation()["variants"]
        ],
        "cluster": economics.cluster_projection(
            units=400, lots_per_unit_per_year=900,
            salt_avoided_per_lot_kg=12.5),
        "evidence": ev,
        "mee_specific": factors.get("mee_specific_thermal_kwh_per_m3"),
        "counts": _counts(),
        "forecast_series": series,
        "flow": {
            "demand": _r(ach["water"]["process_demand_l"]),
            "reuse": _r(ach["water"]["permeate_reuse_l"]),
            "fresh": _r(ach["water"]["freshwater_intake_l"]),
            "reject": _r(ach["zld"]["reject_l"], 3),
            "permeate": _r(ach["zld"]["permeate_l"], 3),
            "recovery": _r(ach["zld"]["ro_recovery_frac"] * 100.0),
            "mee": _r(ach["zld"]["mee_thermal_kwh"], 3),
            "co2": _r(ach["zld"]["total_co2e_kg"], 2),
            "salt": _r(ach["zld"]["salt_mass_kg"], 2),
            "tds": _r(ach["zld"]["effluent_tds_mg_l"], 3),
        },

        # ---- new: the narrative and the external validation ----------
        "narrative": {
            "hook": narrative.HOOK,
            "hook_short": narrative.HOOK_SHORT,
            "consequence": narrative.CONSEQUENCE,
            "analogy": narrative.ANALOGY,
            "mechanism": narrative.MECHANISM,
            "equation": narrative.EQUATION,
            "so_what": narrative.SO_WHAT,
            "not_claimed": narrative.NOT_CLAIMED,
        },
        "validation": {
            "headline": val["headline"],
            "band_pct": val["published_band_pct"],
            "band_source": val["published_band_source"],
            "points": [
                {"tds": _r(p["inlet_tds_mg_l"], 0),
                 "note": p["note"],
                 "pct": p["predicted_reject_frac_pct"]}
                for p in val["points"]
            ],
            "is": val["what_this_is"],
            "is_not": val["what_this_is_not"],
            "enforced_by": val["enforced_by"],
        },
        "posture": narrative.evidence_posture(),

        # provenance of this file itself
        "_generated_by": "submission/build_figures.py",
        "_do_not_edit": (
            "Generated from the engine. Edit core/, not this file. "
            "Regenerate with: python submission/build_figures.py"
        ),
    }
    return fig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if figures.json is stale")
    args = ap.parse_args()

    fresh = build()
    text = json.dumps(fresh, indent=2, sort_keys=True, default=str) + "\n"

    if args.check:
        if not os.path.exists(OUT):
            print("FAIL figures.json does not exist. Run: "
                  "python submission/build_figures.py")
            return 1
        with open(OUT, encoding="utf-8") as fh:
            have = fh.read()
        if have != text:
            print("FAIL submission/figures.json is STALE - the deck would "
                  "quote numbers the engine no longer produces.")
            print("     Regenerate: python submission/build_figures.py")
            print("     Then rebuild: node submission/build_deck.js")
            # show what moved, so the failure is actionable
            try:
                old = json.loads(have)
                for k in sorted(set(old) | set(fresh)):
                    if old.get(k) != fresh.get(k):
                        print("     changed: {}".format(k))
            except ValueError:
                pass
            return 1
        print("ok   figures.json matches the engine")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    ps = fresh["posture"]
    print("wrote {}".format(OUT))
    print("  evidence   {}".format(fresh["evidence"]))
    print("  sourced    {}%".format(ps["sourced_frac_pct"]))
    print("  mee kWh/m3 {}".format(fresh["mee_specific"]))
    print("  validation {}".format(fresh["validation"]["headline"]))
    print()
    print("Now rebuild the deck:  node submission/build_deck.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
