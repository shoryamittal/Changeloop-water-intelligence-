# ChangeLoop — Question 1

## The question

**Which water challenge are you addressing, where, and why do current
approaches fail?**

## My answer

My project is about wastewater reuse in Tirupur, the textile cluster in Tamil
Nadu on the Noyyal river. But the specific thing I am trying to fix is not the
reuse itself. It is what reuse costs to run.

The Noyyal barely flows for most of the year, so there is nothing to dilute
whatever goes into it. Farmers downstream took the dyeing industry to court over
that, and the outcome was Zero Liquid Discharge: treat the water, reuse it,
release nothing. Around 450 dyeing units built 18 shared treatment plants to
comply, spending over ₹1,000 crore between them. The cluster now recycles about
130 million litres a day.

That part worked. The river is in better shape than it was.

What it also did was push production costs up by 25 to 30 percent, and leave
behind a problem that still has no answer.

The reason is salt. Filters can separate clean water out of the effluent, but
they cannot remove salt from it. All they do is squeeze the same salt into a
smaller and smaller volume of water. Eventually you are holding a brine that
cannot be discharged, cannot be reused, and has to go somewhere. So it gets
boiled until only dry salt is left, and the steam for that boiling comes off a
boiler that, in Tiruppur, mostly burns wood.

Then you still have the salt. The Dyers Association of Tiruppur said in 2025
that over one lakh tonnes of it is sitting in sheds at the treatment plants,
nearly double the 2022 figure, because nobody has worked out how to dispose of
it. Their own words were that the technology for it is yet to evolve.

So a dyehouse ends up paying for the same salt twice. Once when it buys it for
the dye bath, and again in the treatment charge to boil it back out. Treatment
costs about ₹185 per kilolitre. River water costs ₹45.

Two things stop the existing approaches from fixing this.

The first is organisational. The amount of salt going into the system is decided
by a production planner, in the morning, choosing what to run and how to dye it.
The bill turns up weeks later at a shared treatment plant and gets split across
hundreds of member units. The planner never sees it. The decision that creates
the cost and the person who pays it have no connection at all.

The second is that almost everyone is measuring the wrong variable. Water
projects in this industry count litres. But in a closed loop the volume you have
to boil is set by how much salt is in the water, not how much water there is. In
my model, cutting water by 20 percent while leaving salt alone changes evaporator
energy by 0.0 percent. Cutting salt by 20 percent cuts it by 20.

> Most of the water-saving effort in this cluster is aimed at a variable that
> does not move the energy bill.

What is missing is not another dashboard reporting last month's consumption. It
is something that shows a planner the downstream cost of a production decision
while they are still making it.

---

## Supporting notes

### Why the answer is shaped this way

Juries hear "I am solving water pollution in textiles" constantly, and in
Tirupur that problem has largely been addressed. The court order worked.
Pretending otherwise would be false and trivially disproved by anyone who knows
the cluster, so the answer concedes it early and then points at what is still
open: the cost of compliance, and a growing pile of salt with nowhere to go.

The two failure reasons are ordered deliberately. The organisational one is
intuitive and needs no technical background. The second one is counter-intuitive,
and lands better once the reader is already following.

### Where each figure comes from

| Claim | Source |
|---|---|
| Noyyal has no dry-weather dilution flow | CPCB Tirupur ZLD assessment, which gives this as the reason discharge was ruled out |
| ~700 units shut, February 2011, on a contempt petition | Down To Earth; Economic Times, June 2025 |
| 450 dyeing units, 18 CETPs, over ₹1,013 crore | Economic Times, June 2025 |
| 130 million litres a day recycled | Economic Times, June 2025; CETP operator data |
| Operating costs up 25–30% | Down To Earth |
| Over 1 lakh tonnes stored, no disposal method, "yet to evolve" | Dyers Association of Tiruppur, via Economic Times, June 2025 |
| ~50,000 tonnes in 2022, growing up to 70 tonnes/day | DT Next, October 2022 |
| ₹185/kL treatment vs ₹45/kL river water | TNPCB plant-level charge data (₹150–220/kL band); Down To Earth for Bhavani supply |
| 0.0% vs −20.0% energy response | Computed live by the engine at `/api/insight/salt-is-water` |

The full register is in `docs/data_sources.md`.

### What the answer deliberately avoids claiming

- It does not say ZLD failed. It did not, and saying so would insult the people
  who spent ₹1,013 crore making it work.
- It gives no jobs-lost figure for 2011. Published estimates run from 15,000 to
  200,000 depending on who counted, so any single number would be indefensible.
  The unit count is consistent across sources, so that is what gets quoted.
- It does not claim the salt mountain is mine to solve. That pile is why the
  upstream decision matters. A scheduling tool does not make it disappear.

### The hardest follow-up

**"If recycling already works, isn't this just an efficiency problem?"**

The cost of compliance decides whether compliance survives. These are mostly
small and medium units, and the shared plants only function if enough members
can afford to stay connected. Pollution board data shows plants running below
about 30 percent of capacity charging ₹375–450 per kilolitre, against ₹150–220
at well-used ones. Members leave, throughput drops, the charge climbs again.
Cost pressure is what starts that.
