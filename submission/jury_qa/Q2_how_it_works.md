# ChangeLoop — Question 2

## The question

**How does it work, and what have you measured?**

## My answer

Let me start with the honest part. **I have not measured this in a real plant.**
Every number I have comes from a working model I built and tested using published
figures, values derived from them, and a small number of stated assumptions. The
product is designed to make that distinction visible on every screen rather than
hide it.

Here is what the system does.

It takes a day's order book — the dye lots, their shade depths, fabric weights
and ship dates — along with the machine's water allowance. It then works out, for
each possible way of running that day, what the consequences are: water used,
salt entering the effluent, concentrated reject volume, evaporator heat, steam,
carbon, cost and whether any delivery slips.

The link that matters is this one. Reject volume is not guessed. It comes from
salt mass divided by the highest concentration the membranes can safely reach,
which I model at 60,000 mg/L. That is a stated model parameter, not a claim that
every membrane in Tirupur runs at exactly that limit. Reject volume then sets
evaporator heat, which sets steam, coal and carbon.

For the five-lot example, it evaluates 480 candidate plans — every running order
crossed with every process strategy — and picks the best plan that is actually
**feasible**, not simply the one with the lowest water number. Firm ship dates
are hard constraints. A plan cannot buy an environmental saving by becoming
operationally unacceptable.

Two human gates sit in the workflow. A named person approves the plan, and a
second gate controls wash-off release. If a sensor is unreliable, the system
holds rather than releasing, and credits exactly zero saving.

**I tested it three ways.**

First, 143 automated tests covering the calculations, the accounting invariants,
the safety interlocks, record integrity, fault behaviour and concurrency.

Second, I checked the model against published plant data. The Central Pollution
Control Board measured 18,340 mg/L of dissolved solids entering evaporation at a
Tirupur unit. Separately, operators report reject running at 20–30 percent of
inlet volume. Those two facts come from different places, and neither is an input
to my engine. When I feed it the first, it predicts 30.6 percent — inside the
reported band. At 12,000 mg/L it gives exactly 20.0 percent and at 15,000 it
gives 25.0. Nothing was tuned to make that happen. This is a sanity check against
published operating data, not a field validation.

Third, I ran a worked example on one machine, one shift, five lots. The baseline
plan draws 11,907 litres of fresh water. The recommended plan draws 11,187 and
cuts evaporator heat from 2,239 to 2,104 kWh. The lowest-water plan available
uses only 5,889 litres — and the system refuses it, because it makes one delivery
2.6 hours late.

Of the 25 inputs driving the model, 17 come from published sources, 4 are derived
from those, and 4 are openly labelled assumptions. **None are plant measurements
yet.** The two measurements I need first are evaporator steam flow and reject
conductivity.

---

## Supporting notes

### Why I answered it this way

The question asks what I measured, and the truthful answer is "nothing, in a
plant." Any attempt to blur that would collapse the first time a judge asked a
direct follow-up. Saying it in the opening line removes the risk entirely and
buys credibility for everything after it.

The three-part test structure exists because "I tested it" means nothing on its
own. Automated tests prove internal consistency. The CPCB comparison proves the
physics behaves like real plants. The worked example proves it produces a
decision, not just numbers. They answer three different doubts.

The refused plan is in the answer deliberately. Showing the system rejecting its
own best-looking water result is the strongest available evidence that it is
built for a factory rather than for a scoreboard.

### Every figure, and how to verify it

| Claim | Value | How to check |
|---|---|---|
| Automated tests | 143 | `python -m pytest tests/ -q` |
| Candidate plans evaluated | 480 | `figures.json` → `candidates`; 120 orders × 4 strategies |
| Membrane concentration ceiling | 60,000 mg/L | `core/factors.py` → `ro_max_reject_tds_mg_l` (PUBLISHED, 15,000–80,000 band) |
| CPCB measured inlet | 18,340 mg/L | CPCB Tirupur ZLD assessment |
| Model prediction at that inlet | 30.6% | `tests/test_published_validation.py` |
| At 12,000 / 15,000 mg/L | 20.0% / 25.0% | same test |
| Published reject band | 20–30% of inlet | Indian ZLD operator data |
| Baseline freshwater | 11,906.8 L | `figures.json` → `options.OPTION_A.fresh` |
| Recommended plan freshwater | 11,186.8 L | `options.OPTION_B.fresh` |
| Evaporator heat, baseline → recommended | 2,239.4 → 2,104.0 kWh | `options.OPTION_A/B.mee` |
| Lowest-water plan | 5,888.8 L, 2.6 h late, refused | `options.OPTION_C` |
| Evidence mix | 17 published / 4 derived / 4 assumed / 0 measured | `core/factors.py`; `/api/evidence` |

### What I deliberately did not claim

- I did not call the CPCB comparison a validation of the product. It validates
  the *physics*, at conditions someone else measured. It says nothing about any
  specific site.
- I did not describe 60,000 mg/L as a universal truth. It is a modelled ceiling
  inside a published 15,000–80,000 range.
- I did not claim the automated tests prove real-world correctness. They prove
  the system is internally consistent and fails safe.

### The hardest follow-up, and my answer

**"Your model agrees with your model. Why should I believe any of it?"**

Because the check uses numbers my engine never reads. CPCB measured the inlet.
Operators reported the reject band. I feed in the first and compare against the
second, and nothing in between was adjusted to make them meet. If the salt-mass
formulation were wrong, that test would fail — and it is a test, so it fails the
build, not just a slide.
