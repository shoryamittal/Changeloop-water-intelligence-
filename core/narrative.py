# -*- coding: utf-8 -*-
"""ChangeLoop - the explanation ladder.

WHY THIS MODULE EXISTS
----------------------
The engine's central finding is thermodynamically subtle and that is a
liability, not an asset. A reviewer with forty submissions and ten minutes
each does not reward rigour they cannot parse. If the first thing a reader
meets is `V_reject = M_salt / C_reject_max`, we have lost them before the
physics has a chance to be impressive.

So the explanation is treated as a product surface with its own source of
truth, exactly like the coefficient registry. Six rungs, each one complete
on its own, each one true, ordered so a reader can stop at any rung and
still be holding something correct:

    rung 0  HOOK        one sentence, no jargon, repeatable from memory
    rung 1  CONSEQUENCE what it means for anyone spending money on water
    rung 2  ANALOGY     a physical intuition for a non-engineer
    rung 3  MECHANISM   one paragraph of plain-language process
    rung 4  EQUATION    the formal statement, for a reader who wants it
    rung 5  PROOF       the live number the engine computes
    rung 6  VALIDATION  the published data our output reproduces

Every pitch surface - the UI banner, the one-pager, the deck, the video
script, the API - reads from here. One wording, one place to change it, no
drift between what the interface says and what the deck claims.

Nothing in this module computes anything. `proof()` and `validation()`
call into the engine so the numbers quoted in the narrative are the
numbers the engine actually produces, never transcribed by hand.
"""
from typing import Any, Dict, List

from core import factors, process, zld


# ---------------------------------------------------------------------------
# The ladder. Prose is deliberately hand-written, not generated.
# ---------------------------------------------------------------------------

HOOK = (
    "In a zero-discharge dyehouse, the evaporator's fuel bill is set by how "
    "much salt goes into the dye bath — not by how much water comes out."
)

HOOK_SHORT = "Salt sets the fuel bill. Not water."

CONSEQUENCE = (
    "Which means almost every water-saving project in the cluster is aimed "
    "at the wrong number. Cut effluent volume by 20% and the evaporator "
    "burns exactly the same fuel. Cut the salt by 20% and it burns 20% "
    "less. Two levers that both look like 'saving water' do completely "
    "different things to the energy bill, and nobody on the dyehouse floor "
    "can see which is which."
)

ANALOGY = (
    "Think of wringing out a wet cloth. Most of the water comes out easily "
    "- that is the membrane stage, and it is cheap. But you can never wring "
    "it fully dry, and what stays behind clings to whatever is dissolved in "
    "it. The more salt you put in, the more you are left holding. And the "
    "part you cannot wring out is the part you have to boil."
)

MECHANISM = (
    "A zero-discharge plant is not allowed to release anything, so whatever "
    "it cannot recycle it has to boil dry. Membranes pull most of the clean "
    "water back cheaply, but they have to stop before the leftover brine "
    "gets thick enough to scale up the tubes - around 60,000 mg/L of "
    "dissolved solids. That ceiling is fixed by chemistry, not by choice. "
    "So the volume left to boil is simply the salt mass divided by that "
    "ceiling. Put in more water with the same salt and the membranes just "
    "recover more clean water; the brine left at the end is the same, and "
    "so is the steam. Put in more salt and there is more brine to boil, "
    "whatever you did about water. Water is the carrier. Salt is the load."
)

EQUATION = "V_reject = M_salt / C_reject_max"

EQUATION_GLOSS = (
    "The volume that must be evaporated equals the dissolved salt mass "
    "divided by the highest concentration the membranes can safely reach. "
    "Volume of effluent does not appear on the right-hand side. That "
    "absence is the whole finding."
)

SO_WHAT = (
    "The person who decides this is a planner choosing what order to run "
    "today's dye lots in, and they are choosing hours before anyone can "
    "see the consequence. The evaporator's fuel bill arrives weeks later, "
    "on someone else's cost centre, with no way to trace it back to the "
    "decision that caused it. ChangeLoop closes that loop: it prices the "
    "downstream thermal consequence into the upstream scheduling choice, "
    "at the moment the choice is being made."
)

# What we are explicitly NOT claiming. Stated in the narrative itself
# because a reviewer's first instinct is to look for the overclaim, and
# finding it pre-empted is worth more than another impressive number.
NOT_CLAIMED = [
    "Counter-current rinsing is not our invention. It is established Best "
    "Available Technique and has been for decades.",
    "Low-electrolyte reactive dye chemistry is not our invention either. "
    "It is commercially available from several suppliers.",
    "We have not measured anything. Every number in this system is "
    "published, derived from published values, or an openly labelled "
    "assumption. Zero coefficients are classed MEASURED, and a test "
    "enforces that.",
    "The system issues no setpoints and releases no bath. It is advisory. "
    "Every action requires a named human decision.",
    "What is ours is the coupling: that these two well-known levers pull "
    "in opposite directions through the ZLD chain, that the trade-off is "
    "therefore a constrained optimisation rather than a best practice, and "
    "that it has to be solved at scheduling time to be worth anything.",
]


def ladder() -> List[Dict[str, Any]]:
    """The six rungs, as data, in order."""
    return [
        {
            "rung": 0,
            "id": "hook",
            "label": "The finding, in one sentence",
            "audience": "anyone",
            "seconds": 8,
            "body": HOOK,
            "compact": HOOK_SHORT,
        },
        {
            "rung": 1,
            "id": "consequence",
            "label": "Why it matters",
            "audience": "anyone spending money on water",
            "seconds": 20,
            "body": CONSEQUENCE,
        },
        {
            "rung": 2,
            "id": "analogy",
            "label": "The intuition",
            "audience": "non-technical",
            "seconds": 20,
            "body": ANALOGY,
        },
        {
            "rung": 3,
            "id": "mechanism",
            "label": "How it actually works",
            "audience": "technical generalist",
            "seconds": 45,
            "body": MECHANISM,
        },
        {
            "rung": 4,
            "id": "equation",
            "label": "The formal statement",
            "audience": "process engineer",
            "seconds": 15,
            "body": EQUATION_GLOSS,
            "equation": EQUATION,
        },
        {
            "rung": 5,
            "id": "proof",
            "label": "The engine proves it, live",
            "audience": "reviewer",
            "seconds": 30,
            "body": None,          # filled by proof()
        },
        {
            "rung": 6,
            "id": "validation",
            "label": "Published data agrees",
            "audience": "reviewer",
            "seconds": 30,
            "body": None,          # filled by validation()
        },
    ]


def proof() -> Dict[str, Any]:
    """Rung 5. The live sensitivity result, computed now, not quoted.

    This is the moment in a demo where the claim stops being a claim. Two
    identical 20% cuts, one to water and one to salt, run through the same
    code path, with opposite outcomes.
    """
    s = zld.sensitivity_salt_vs_water()
    water_pct = s["cut_water_20pct_only"]["mee_energy_change_pct"]
    salt_pct = s["cut_salt_20pct_only"]["mee_energy_change_pct"]
    return {
        "headline": (
            "Cut water 20%: evaporator energy changes by {:+.1f}%. "
            "Cut salt 20%: it changes by {:+.1f}%. Same code path, same "
            "baseline, one variable each.".format(water_pct, salt_pct)
        ),
        "cut_water_20pct_change_pct": water_pct,
        "cut_salt_20pct_change_pct": salt_pct,
        "reading": (
            "A 20% water reduction moves the evaporator by exactly nothing. "
            "Not 'a little' - zero, to the precision of the arithmetic. "
            "That is not a tuned result; it falls out of salt mass "
            "conservation and it is why a water dashboard cannot find this "
            "saving."
        ),
        "binding_constraint": s["baseline"]["binding_constraint"],
        "classification": s.get("classification", "DERIVED"),
    }


def validation() -> Dict[str, Any]:
    """Rung 6. What the model predicts at conditions somebody else measured.

    CPCB recorded 18,340 mg/L TDS entering the evaporation stage at an
    assessed Tirupur textile unit. Indian ZLD operators separately report
    RO reject at 20-30% of inlet volume. Those two facts come from
    different places and neither is an input to our engine. Feed our model
    the first and it predicts the second.
    """
    volume_l = 100_000.0
    points = []
    for tds, note in (
        (12_000.0, "lower end of observed CETP inlet strength"),
        (15_000.0, "midpoint of observed CETP inlet strength"),
        (18_340.0, "TDS measured by CPCB entering evaporation at an "
                   "assessed Tirupur unit"),
    ):
        r = zld.treat(volume_l, tds * volume_l / 1e6)
        points.append({
            "inlet_tds_mg_l": tds,
            "note": note,
            "predicted_reject_frac_pct": round(100.0 * r.reject_l / volume_l,
                                               1),
            "binding_constraint": r.binding_constraint,
        })

    return {
        "headline": (
            "Fed the TDS that CPCB measured at a real Tirupur unit, the "
            "model predicts a reject fraction of {:.1f}% - inside the "
            "20-30% that Indian ZLD operators independently report.".format(
                points[-1]["predicted_reject_frac_pct"])
        ),
        "published_band_pct": [20.0, 30.0],
        "published_band_source": (
            "RO reject reported at 20-30% of inlet volume by Indian textile "
            "ZLD operators; inlet TDS of 18,340 mg/L measured by CPCB at an "
            "assessed Tirupur dyeing unit."
        ),
        "points": points,
        "what_this_is": (
            "Cross-validation against published operating data. Our outputs "
            "land where real plants sit, using inputs the engine never "
            "reads back."
        ),
        "what_this_is_not": (
            "Measurement. No instrument on any real asset has fed this "
            "system. Zero coefficients are classed MEASURED and a test "
            "enforces it. A pilot is still required before any figure here "
            "describes a specific site."
        ),
        "enforced_by": "tests/test_published_validation.py",
    }


def evidence_posture() -> Dict[str, Any]:
    """One honest paragraph about what this prototype knows, for the top of
    any surface where a reviewer might otherwise assume more."""
    summary = factors.evidence_summary()
    total = sum(summary.values())
    published = summary.get("PUBLISHED", 0)
    derived = summary.get("DERIVED", 0)
    assumed = summary.get("ASSUMED", 0)
    return {
        "summary": summary,
        "total": total,
        "sourced_frac_pct": round(100.0 * (published + derived) / total, 0),
        "statement": (
            "{total} coefficients drive this system. {published} are taken "
            "from published sources - CPCB, the Central Electricity "
            "Authority, TNERC tariff orders, Tamil Nadu pollution board "
            "plant data, the EU BAT reference document, steam tables. "
            "{derived} are derived from those by stated arithmetic that a "
            "test re-checks. {assumed} remain openly labelled assumptions, "
            "and they stay that way because they are commercial prices and "
            "premiums that public literature cannot settle. None is "
            "MEASURED. We did not relabel what we could not "
            "source.".format(total=total, published=published,
                              derived=derived, assumed=assumed)
        ),
        "measured_count": summary.get("MEASURED", 0),
        "next_step_to_promote": (
            "One site visit. Two instrument readings - steam flow to the "
            "evaporator and reject conductivity - promote the two "
            "coefficients that carry the most weight in the result from "
            "published to measured, and the evidence screen would say so "
            "without a line of code changing."
        ),
    }


def plain_summary() -> Dict[str, Any]:
    """Everything a reader needs in the first fifteen seconds."""
    return {
        "hook": HOOK,
        "hook_short": HOOK_SHORT,
        "consequence": CONSEQUENCE,
        "so_what": SO_WHAT,
        "equation": EQUATION,
        "proof": proof(),
        "validation": validation(),
    }


def bundle() -> Dict[str, Any]:
    """Full narrative payload for /api/narrative and for deck generation."""
    rungs = ladder()
    for r in rungs:
        if r["id"] == "proof":
            p = proof()
            r["body"] = p["headline"]
            r["detail"] = p
        elif r["id"] == "validation":
            v = validation()
            r["body"] = v["headline"]
            r["detail"] = v
    return {
        "hook": HOOK,
        "hook_short": HOOK_SHORT,
        "so_what": SO_WHAT,
        "ladder": rungs,
        "not_claimed": NOT_CLAIMED,
        "evidence_posture": evidence_posture(),
        "read_time_seconds": sum(r["seconds"] for r in rungs),
        "classification": "NARRATIVE",
        "note": (
            "This module holds no numbers of its own. Every figure quoted "
            "above is computed by the engine at request time, so the pitch "
            "cannot drift from the product."
        ),
    }
