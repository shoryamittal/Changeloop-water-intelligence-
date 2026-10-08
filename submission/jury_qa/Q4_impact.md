# ChangeLoop — Question 4

## The question

**How much water is saved per unit per year, and who benefits?**

## My answer

Everything below is modelled, not measured. A small number I can defend is worth
more to me than a large one I cannot.

On one machine, one shift, five lots, with both human decisions approved, the
model credits 1,044 litres of fresh water avoided, 62.7 kg of salt kept out of
the effluent, 196 kWh of evaporator heat not burned, and about ₹10,171 of cost
avoided. Every delivery still goes out on time.

That comes from two separate decisions. One is choosing a better plan at the
start of the shift. The other is ending wash-off when the sensors show the cloth
is clean, instead of when a fixed timer runs out.

Annualised for a single machine, assuming two shifts a day across 300 working
days, which is 600 comparable shifts, that works out to roughly 627,000 litres
of fresh water, 37.6 tonnes of salt and 118 MWh of evaporator heat in a year.

At cluster scale the repository carries a separate projection on a per-lot
basis: 400 units, 900 lots per unit per year, 360,000 lots in total. That gives
about 75 million litres of fresh water, 4,500 tonnes of salt, 14,106 MWh of
evaporator steam and 6,376 tonnes of CO₂e annually. Those two scalings rest on
different throughput assumptions, so I keep them as two separate projections
rather than implying one follows from the other. Both are labelled PROJECTED in
the interface, and neither should be quoted as achieved impact.

There is something else I want to put on the record, because a careful reader
will find it anyway.

The 1,044 litres comes from the plan the system recommends under normal
operating economics, and that plan improves water, salt and energy by about 6
percent. A much better plan exists. Switching to low-electrolyte dye chemistry
cuts salt by around 46 percent, is feasible, and misses no deadline. The
optimiser does not recommend it under normal economics, because the one-off
chemistry premium of roughly ₹9,000 on this batch outweighs a single shift's
savings. Price water scarcity or carbon higher, which is what happens under a
drought restriction, and the same engine starts choosing it.

> The daily scheduling decision delivers the modest number. The large number is
> a procurement decision the system can justify but cannot make on its own.

Who benefits. The dyeing unit, through a lower treatment charge and less salt
bought. The common effluent treatment plant, through less steam purchased and
less salt it has nowhere to put. And the basin, through lower freshwater
abstraction.

I am not claiming a number of people served or hectares protected. I do not have
evidence strong enough to defend a figure like that, and making one up would
undermine everything else here.

The first real impact measurement comes from a pilot, starting with four weeks
of baseline metering before any recommendation is allowed to change what the
plant does.

---

## Supporting notes

### Why the answer is shaped this way

Impact questions invite inflation, and an inflated number is the easiest thing
for a panel to puncture. So the answer opens by labelling everything a
projection and closes by refusing to estimate people served.

The 6 percent against 46 percent paragraph is deliberate. A judge who reads the
repository will discover that the recommended plan under normal operation saves
6 percent while a far better plan sits unused. Found by them, it reads as an
overclaim being caught. Said first, it reads as understanding your own
economics. It is also a genuinely interesting output: the model is showing where
the payback threshold for the chemistry switch actually sits.

### Every figure, and how to check it

| Figure | Value | Source |
|---|---|---|
| Freshwater avoided, one shift | 1,044.2 L | `figures.json` → `impact.fresh_av` |
| Salt avoided, one shift | 62.65 kg | `impact.salt_av` |
| Evaporator heat avoided, one shift | 196.4 kWh | `impact.mee_av` |
| Cost avoided, one shift | ₹10,171 | `impact.cost_av` |
| Deliveries late in recommended plan | 0 | `options.OPTION_B.late` |
| Annualisation assumption | 2 shifts/day × 300 days = 600 | stated assumption, not measured |
| Annual, one machine | ~627,000 L, 37.6 t, 118 MWh | 600 × the per-shift figures |
| Cluster projection | 75.0 M L, 4,500 t, 14,106 MWh, 6,376 t CO₂e | `figures.json` → `cluster` |
| Cluster assumptions | 400 units × 900 lots/unit/yr, 12.5 kg salt/lot | `core/economics.py` → `cluster_projection()` |
| Recommended plan improvement | 6.0% on water, salt and energy | `options.OPTION_A` against `OPTION_B` |
| Best feasible low-salt plan | 382.1 kg salt against 714.4 baseline, −46%, 0 h late | exhaustive search across all 480 candidates |
| Chemistry premium on this batch | ~₹9,042 | `low_salt_chemistry_cost_inr_per_kg_fabric` × fabric weight |

### A correction made while preparing this answer

The cluster projection used to report 398.9 million litres. That figure was
wrong.

It treated freshwater as an independent input of 1,108 litres per lot, while
deriving reject volume from salt. The two then disagreed by 5.3× inside the same
block of output: 398,880 m³ of freshwater against 75,000 m³ of reject.

In a closed loop those are the same water. Makeup equals evaporative loss equals
reject volume. The engine enforces that identity everywhere else and reports
both as exactly 1,044.2 L on the reference shift. The cluster projection was the
one place that did not, and it happened to be the place carrying the headline
number.

Freshwater is now derived from reject so the two cannot drift apart again, and
three tests lock it. The corrected figure is 75.0 million litres. Salt, steam
and CO₂e were already derived from salt and did not change.

This is in the answer because the correction cut my own headline number by more
than five times. Better that the panel sees me audit my own figures than that
they find it themselves.

### What the answer deliberately avoids claiming

- No people served, no hectares protected, no lives improved.
- No suggestion the cluster figure is achievable. Every unit resembling the
  modelled one, and every recommendation being approved, are both untested.
- No merging of the two scaling bases into a single larger total.

### The hardest follow-up

**"Six percent isn't very much."**

It is not, and that is the honest figure for one scheduling decision under
normal economics. Two things still make it worth having. It costs almost
nothing, because there is no new equipment involved, only a different running
order. And the same engine shows exactly when the larger 46 percent move becomes
worth buying, which is the decision a unit actually needs help with. Something
that tells you a lever is not worth pulling today is more useful than something
that always says yes.
