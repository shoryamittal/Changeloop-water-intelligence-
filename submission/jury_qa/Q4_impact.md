# ChangeLoop — Question 4

## The question

**How much water is saved per unit per year, and who benefits?**

## My answer

Everything below is a **modelled projection, not a measured result.** I would
rather hand you a small number I can defend than a large one I cannot.

**On one machine, one shift, five lots**, with both human decisions approved, the
model credits 1,044 litres of fresh water avoided, 62.7 kg of salt kept out of
the effluent, 196 kWh of evaporator heat not burned, and about ₹10,171 of cost
avoided — with every delivery still on time.

That comes from two separate decisions: choosing a better plan at the start of
the shift, and ending wash-off when the sensors show the cloth is actually clean
rather than when a fixed timer expires.

**Annualised for one machine**, assuming two shifts a day and 300 working days —
600 comparable shifts — that is roughly 627,000 litres of fresh water, 37.6
tonnes of salt and 118 MWh of evaporator heat per year.

**At cluster scale**, the repository carries a separate projection on a per-lot
basis: 400 units, 900 lots per unit per year, 360,000 lots in total. That comes
to about 75 million litres of fresh water, 4,500 tonnes of salt, 14,106 MWh of
evaporator steam and 6,376 tonnes of CO₂e a year. Those two scalings use
different throughput assumptions, so I present them as two separate projections
rather than pretending one derives from the other. Both are labelled PROJECTED in
the interface and neither should ever be quoted as achieved impact.

**There is one more thing I want to say about these numbers, because a careful
reader will find it anyway.**

The 1,044 litres comes from the plan the system recommends under normal operating
economics. That plan improves water, salt and energy by about 6 percent. There is
a much better plan available — switching to low-electrolyte dye chemistry cuts
salt by around 46 percent, is feasible, and misses no deadline — and the
optimiser does **not** recommend it under normal economics, because the one-off
chemistry premium of roughly ₹9,000 on this batch outweighs a single shift's
savings. Price water scarcity or carbon higher, as happens in a drought
restriction, and the same engine starts recommending it. So the honest statement
is that the daily scheduling decision delivers the modest number, and the large
number is a procurement decision the system can justify but cannot execute on its
own.

**Who benefits.** The dyeing unit, through lower treatment charges and less salt
purchased. The common effluent treatment plant, through less steam bought and
less salt it has nowhere to store. And the basin, through lower freshwater
abstraction.

I deliberately do not claim a number of people served or hectares protected. I do
not have evidence strong enough to defend such a figure, and inventing one would
undermine everything else I have said.

The first real impact measurement would come from a pilot, starting with four
weeks of baseline metering before any recommendation is allowed to influence
operations.

---

## Supporting notes

### Why I answered it this way

Impact questions invite inflation, and inflated numbers are the easiest thing for
a jury to puncture. So the answer opens by labelling everything a projection and
closes by refusing to estimate people served.

The 6 percent versus 46 percent paragraph is in there on purpose. A judge who
reads the repository will find that the recommended plan under normal operation
saves 6 percent while a far better plan exists. If they find that themselves, it
reads as an overclaim being caught. If I say it first, it reads as understanding
my own system's economics. It also happens to be a genuinely interesting result:
the model is showing where the payback threshold sits.

### Every figure, and how to verify it

| Figure | Value | Source |
|---|---|---|
| Freshwater avoided, one shift | 1,044.2 L | `figures.json` → `impact.fresh_av` |
| Salt avoided, one shift | 62.65 kg | `impact.salt_av` |
| Evaporator heat avoided, one shift | 196.4 kWh | `impact.mee_av` |
| Cost avoided, one shift | ₹10,171 | `impact.cost_av` |
| Deliveries late in recommended plan | 0 | `options.OPTION_B.late` |
| Annualisation assumption | 2 shifts/day × 300 days = 600 | stated assumption, not measured |
| Annual per machine | ~627,000 L, 37.6 t, 118 MWh | 600 × the per-shift figures |
| Cluster projection | 75.0 M L, 4,500 t, 14,106 MWh, 6,376 t CO₂e | `figures.json` → `cluster` |
| Cluster assumptions | 400 units × 900 lots/unit/yr, 12.5 kg salt/lot | `core/economics.py` → `cluster_projection()` |
| Recommended plan improvement | 6.0% on water, salt and energy | `options.OPTION_A` vs `OPTION_B` |
| Low-salt plan, best feasible | 382.1 kg salt vs 714.4 baseline (−46%), 0 h late | exhaustive search over all 480 candidates |
| Chemistry premium on this batch | ~₹9,042 | `low_salt_chemistry_cost_inr_per_kg_fabric` × fabric weight |

### A correction I made while preparing this

The cluster projection used to report 398.9 million litres. That figure was
wrong. It took freshwater as an independent input of 1,108 litres per lot while
deriving reject volume from salt, and the two then disagreed by 5.3× inside the
same block — 398,880 m³ of freshwater against 75,000 m³ of reject.

In a closed loop those are the same water: makeup equals evaporative loss equals
reject volume. The engine enforces that identity everywhere else and reports both
as exactly 1,044.2 L on the reference shift. The cluster projection was the one
place that did not, and it was the place carrying the headline number.

Freshwater is now derived from reject, so they cannot diverge again, and three
tests lock it. The corrected figure is 75.0 million litres. The salt, steam and
CO₂e figures were already derived from salt and are unchanged.

I am including this because the correction reduced my own headline number by more
than 5×, and I would rather show the jury that I audit my own figures than have
them find it.

### What I deliberately did not claim

- No people served, no hectares protected, no lives improved.
- No claim that cluster-scale figures are achievable. Every unit resembling the
  modelled one, and every recommendation being approved, are both untested.
- No merging of the two scaling bases into one impressive total.

### The hardest follow-up, and my answer

**"Six percent is not very much."**

It is not, and that is the honest figure for a single scheduling decision under
normal economics. Two things make it matter anyway. It costs almost nothing —
there is no new equipment, only a different running order. And the same engine
shows exactly when the larger 46 percent move becomes worth buying, which is the
decision a unit actually needs help with. A tool that tells you a lever is not
worth pulling today is more useful than one that always says yes.
