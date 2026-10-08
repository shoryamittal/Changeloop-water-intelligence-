# ChangeLoop — Question 1

## The question

**Which water challenge are you addressing, where, and why do current approaches fail?**

## My answer

I am working on wastewater reuse in the Tirupur textile cluster in Tamil Nadu,
on the Noyyal river. But the part I want to fix is not the reuse itself. It is
the energy and cost burden that reuse creates.

The Noyyal is a seasonal river. For most of the year there is almost no flow in
it, so there is nothing to dilute what gets discharged. After farmers took the
industry to court, the cluster was ordered to move to Zero Liquid Discharge:
treat and reuse the water, release nothing. Around 450 dyeing units built 18
shared treatment plants for this, at a cost of over ₹1,000 crore. Today they
recycle about 130 million litres a day.

It worked. The river is cleaner. But it made production 25 to 30 percent more
expensive, and it created a problem nobody has solved yet.

Here is why. Filters can pull clean water out of the effluent, but they cannot
remove salt. They only squeeze it into less and less water. What is left is a
small volume of very concentrated brine that cannot be released anywhere, so it
has to be boiled until only dry salt remains. Boiling needs steam, and steam
comes from a coal boiler. Then the salt is still there: the Dyers Association of
Tiruppur reported in 2025 that more than one lakh tonnes of it now sits in sheds
at the treatment plants, roughly double the 2022 figure, because no disposal
method has been found.

So the dyehouse pays for its salt twice. Once to buy it for the dye bath, and
again through the treatment charge to boil it back out. Treatment runs about
₹185 per kilolitre against ₹45 for river water.

There are two reasons the current approaches do not fix this.

The first is where the decision sits. The amount of salt entering the system is
decided upstream, by a production planner choosing what to run and how to dye it.
The bill arrives weeks later, at a shared treatment plant, split across hundreds
of factories. The planner never sees it. So the decision that creates the cost
and the person paying it are completely disconnected.

The second is what everyone is measuring. Almost every water project in this
industry targets water volume. But in a closed loop, the volume you have to boil
is set by the salt, not the water. In my model, cutting water by 20 percent while
holding salt constant changes evaporator energy by 0.0 percent. Cutting salt by
20 percent cuts it by 20. That means most water-saving effort here does not
reduce the energy burden at all.

What is missing is not another dashboard reporting water used last month. It is a
planning layer that shows the downstream consequence of a production decision
*before* that decision is made.

---

## Supporting notes

### Why I answered it this way

A jury hears "I am solving water pollution in textiles" constantly. That problem
is genuinely already addressed here — the court order worked, and saying
otherwise would be wrong and easy to disprove. So the answer deliberately
concedes that up front and then identifies the problem that actually remains
open: the cost and energy of compliance, and the salt that has nowhere to go.

I also put the two failure reasons in a specific order. The organisational one
(decision and cost are separated) is intuitive and anyone can follow it. The
technical one (water volume is the wrong lever) is counter-intuitive, so it
lands better once the reader is already engaged.

### Where each figure comes from

| Claim | Source |
|---|---|
| Noyyal has no dry-weather dilution flow | CPCB Tirupur ZLD assessment; this is the stated reason discharge was ruled out |
| ~700 units shut, February 2011, on a contempt petition | Down To Earth; Economic Times, June 2025 |
| 450 dyeing units, 18 CETPs, over ₹1,013 crore | Economic Times, June 2025 |
| 130 million litres a day recycled | Economic Times, June 2025; CETP operator data |
| Operating costs up 25–30% | Down To Earth |
| Over 1 lakh tonnes of salt stored, no disposal method | Dyers Association of Tiruppur, via Economic Times, June 2025 |
| ~50,000 tonnes in 2022, growing up to 70 tonnes/day | DT Next, October 2022 |
| ₹185/kL treatment charge vs ₹45/kL river water | TNPCB plant-level charge data (₹150–220/kL band); Down To Earth for Bhavani supply |
| 0.0% vs −20.0% energy response | Computed live by the engine, `/api/insight/salt-is-water` |

Full register: `docs/data_sources.md`.

### What I deliberately did not claim

- I did not say ZLD failed. It did not. Saying so would be false and would also
  insult the people who built it.
- I did not give a jobs-lost figure for 2011. Published estimates range from
  15,000 to 200,000 depending on the source, so quoting any single number would
  be indefensible. The unit count is consistent across sources, so I use that.
- I did not claim the salt mountain is *my* problem to solve. It is the
  consequence that makes the upstream decision matter, not something a
  scheduling tool removes on its own.

### The hardest follow-up, and my answer

**"If recycling already works, is this not a minor efficiency problem?"**

No, because the cost of compliance is what decides whether compliance survives.
These are mostly small and medium businesses. The treatment plants only work if
enough members can afford to stay connected, and the published charge data shows
plants below about 30 percent utilisation charging ₹375–450 per kilolitre
against ₹150–220 for well-used ones. Cost pressure is what pushes a cluster
toward that spiral.
