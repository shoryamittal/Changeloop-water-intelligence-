# ChangeLoop

## In one paragraph

In a dyehouse running zero liquid discharge, the coal bill is set by how much
salt goes into the dye bath, not by how much water comes out. That single fact
is counter-intuitive, it is provable from mass conservation, and almost nobody
acts on it. It means most water-saving work in India's largest textile cluster
is aimed at a number that does not drive the emissions. ChangeLoop puts the
downstream thermal consequence in front of the person making the upstream
scheduling decision, at the moment they make it. It is live, it is open to
inspection, and every figure in it carries a label saying how much it should
be trusted.

**Live prototype:** https://changeloop-water-intelligence.onrender.com

---

## 1. Problem Statement

### The place

Tirupur, in the Noyyal sub-basin of the Cauvery system, is India's knitwear
capital. In 2011 the Madras High Court ordered roughly 700 dyeing and
bleaching units shut for discharging saline effluent into the Noyyal. They
were allowed to reopen only under zero liquid discharge: nothing leaves the
site as liquid.

ZLD worked. The river stopped receiving effluent. But it moved the problem
rather than removing it, and the place it moved to is the boiler house.

### What ZLD actually does

Under ZLD, effluent goes through membranes. The clean permeate returns to the
process. The concentrated reject goes to a multiple-effect evaporator, which
boils it until only solid salt remains. Boiling water takes heat, the heat
comes from steam, and in Tirupur the steam comes overwhelmingly from coal.

So a regulation written to protect a river created a large, permanent thermal
load. Evaporating one cubic metre of reject takes about 188 kWh of thermal
energy. Latent heat of 0.627 kWh/kg from steam tables, divided by a steam
economy of 3.33 kg of water per kg of live steam, which is the reciprocal of
the 0.25-0.35 kg steam per kg evaporated that textile MEE trains are reported
to achieve. The result lands inside the 150-250 kWh/m3 band independently
published for the evaporator section of textile ZLD plants, which is a useful
check: two unrelated published numbers, multiplied, fall inside a third that
was never used in the calculation.

### The mechanism nobody is looking at

Here is the part that matters, and it is the reason this project exists.

In a closed loop, the volume the evaporator has to boil is not set by how much
water you used. It is set by how much salt you put in:

```
V_reject  =  M_salt  /  C_reject_max
```

Salt mass divided by the maximum concentration the membranes can push the
reject to, which for a textile RO train is around 60,000 mg/L. Water entering
the loop comes back round. Salt does not. Salt has to leave as a solid, and
the only exit is through the evaporator, which means the evaporator must boil
whatever volume of water that salt is dissolved in at the concentration
ceiling.

The consequence is sharp enough to be tested, and the running system tests it
on every request:

| Intervention | Effect on evaporator energy |
|---|---|
| Cut effluent water volume by 20% | **+0.0%** |
| Cut salt load by 20% | **−20.0%** |

Not "a little". Zero, to the precision of the arithmetic. It falls directly
out of salt mass conservation.

This is why a water dashboard cannot find this saving. Two interventions that
both read as "saving water" on any volume meter do completely different things
to the coal bill, and nothing on the factory floor distinguishes them.

### Why it has stayed unsolved

The decision that sets salt load is made by a production planner, choosing
what order to run today's dye lots in and which rinse strategy to use. They
make it hours before anything is visible. The evaporator's fuel bill arrives
weeks later, on a different cost centre, with no way to trace it back to the
decision that caused it.

That is a broken feedback loop, not a technology gap. The planner is not
careless. They are working without the one number that would change their
mind, and no system currently puts it in front of them.

### And one layer above that

There is a second failure, and it only appears when you stop looking at one
machine.

A real mill runs several machines into one shared evaporator. Each planner
picks the plan that is best for their own machine. Every one of those choices
is locally correct. Their sum can still exceed what the shared plant is able
to boil.

In the modelled site, four machines each choosing their own optimum put the
shared evaporator at **121.9% of capacity**. Nobody chose badly. The sum does
not fit. No tool that looks at one machine at a time can see this, and no
planner can be blamed for it.

---

## 2. Proposed Solution

ChangeLoop prices the downstream consequence into the upstream decision.

It is a decision-support layer that sits where the schedule is made. Before a
shift starts, it searches the combinations of lot order and process strategy
available to the planner, and for each one computes the full consequence
chain: water demand, salt load, reject volume, evaporator steam, CO2e, rupees,
and whether any ship date is missed.

Four design choices do the actual work.

**Hard constraints are feasibility, not penalty.** A plan that misses a ship
date is not a worse plan. It is not a plan. It is removed from the search
rather than given a bad score, because a schedule that saves water by
shipping late is not a trade-off a factory can accept and should never be
offered as one.

**Every coefficient is classified and visible.** Each of the 25 numbers that
drive the model is labelled PUBLISHED, DERIVED, ASSUMED or MEASURED, with its
source and its arithmetic. Anyone can open the registry in the running system
and check. Currently: 17 published, 4 derived, 4 assumed, and **zero
measured** — a test enforces that last count so it cannot quietly become a
marketing claim.

**The system fails closed.** It issues no setpoints. It cannot release a dye
bath. Early wash-off release requires a named human to approve it, and
`automatic_release` is hardcoded to `False`. If a sensor reading is missing,
frozen or implausible, the system holds and credits zero saving rather than
estimating. An advisory tool that quietly guesses is worse than no tool.

**Savings are credited only when a human approved the action.** If a
recommendation is not approved, it contributes zero to the ledger, even though
the engine computed it. The ledger records the decision actually taken, not
the decision that would have looked best.

### The plant layer

The newest component answers the coordination failure described above. It
compares two plans over the same day: what each machine would choose alone,
and the cheapest combination that actually fits the shared evaporator.

The capacity figure is **derived, not invented**. In a closed loop the
freshwater makeup is the evaporative loss is the reject volume, so the site's
daily abstraction allowance and the volume the evaporator must boil are the
same number read two ways. This matters, because the easiest way to make a
coordination demo impressive is to pick a capacity that guarantees a breach.
That number is the basin allowance the rest of the system already runs on.

And the result is the most interesting finding in the project:

| Binding constraint | Plant load | Coordination needed | Premium |
|---|---|---|---|
| Normal operation | 121.9% | Yes — 2 of 4 machines forced off their own optimum | ₹4,123/day |
| Scarcity priced (drought) | 68.8% | None | ₹0 |

Under today's tariffs, freshwater is cheap enough that every machine privately
prefers the water-saving plan, and their sum breaks the evaporator. Price
scarcity properly, and all four machines choose the low-salt plan on their own
account. The plant fits, nobody is made worse off, and the premium disappears.

Nothing was rescheduled to get there. **The breach is a pricing failure, not a
scheduling failure.** The plan the site has to force onto two machines today is
the plan every machine would pick for itself if water cost what it is worth.
That is a policy argument that comes out of the engine rather than out of an
opinion, and a test pins it so it cannot drift.

---

## 3. Prototype Details

A working system, publicly reachable, not a mockup.

**https://changeloop-water-intelligence.onrender.com**

| | |
|---|---|
| Backend | Python standard library only — no framework, no install step |
| API | 33 REST endpoints, every impact figure computed server side |
| Tests | 163, covering physics, safety interlocks, concurrency and the UI |
| Front end | Dependency-free; nine operating views |
| Ledger | HMAC-SHA256 append-only hash chain, verified on every health check |

### What you can do in it

Choose a site and a binding constraint. Watch the optimiser change its
recommendation as the constraint changes — it returns two genuinely different
plans across four modes, which is the test of whether it is optimising or just
replaying an answer. Open any number and trace it to its coefficient, its
source classification and its arithmetic. Approve a sequence, or decline it,
and watch the ledger credit accordingly. Trigger a sensor fault and watch the
system hold instead of guessing. Open the Plant view and see four correct
decisions produce one breach.

### How it is validated

Nothing here has been measured on a real asset, and the system says so in
every view. What it has instead is external cross-validation.

Fed the inlet TDS that CPCB measured at an assessed Tirupur dyeing unit —
18,340 mg/L — the model predicts a reject fraction of **30.6%**. Indian textile
ZLD operators independently report RO reject at 20-30% of inlet volume. The
model lands inside that band using an input it never reads back, and the check
runs as a test rather than sitting in a slide.

The honest reading of that: the physics is behaving like real plants. It is
not evidence that any specific figure describes any specific site. Those are
different claims and the system keeps them apart.

### Deliberate scope limits, stated in the product

The interface carries its own limitations rather than hiding them: no
scheduling of machines against each other in time, no surge storage modelling,
machines within one unit rather than a CETP's hundreds of members, a simulated
order book, and nothing measured anywhere.

---

## 4. Target Audience

### Who uses it

**The production planner** is the primary user. They already make this
decision every shift; ChangeLoop changes what they can see when they make it.
This matters for adoption — the tool does not ask anyone to do a new job.

**The quality supervisor** holds authority over wash-off release and keeps it.
The system can recommend early release; only they can grant it.

**The unit owner** takes the financial benefit and signs off the chemistry
decision, which runs on a procurement cycle rather than a daily one.

### Who buys it

**The common effluent treatment plant is the efficient channel.** One
connection reaches many member units, and the incentive already points the
right way: less salt arriving means less steam bought and less solid salt to
store. India's textile ZLD plants are holding over one lakh tonnes of
recovered salt with no viable disposal route, so reducing salt at source is
something a CETP operator wants for reasons that have nothing to do with us.

### Who benefits without using it

Households and farmers in the Noyyal sub-basin, whose groundwater carries a
basin stress weight of 11.08 in this model — every litre not abstracted here
counts for far more than a litre elsewhere. And the cluster's workforce, for
whom the 2011 shutdown is living memory rather than history.

---

## 5. Impact and Feasibility

### What one shift looks like

Baseline is a conventional single-stage rinse. Everything below is MODELLED
on a simulated order book of five lots.

| | Freshwater | Evaporator steam | Cost |
|---|---|---|---|
| Baseline | 11,907 L | 2,239 kWh | ₹33,897 |
| Recommended under normal economics | 11,187 L (−6%) | 2,104 kWh (−6%) | ₹26,038 |
| Available under priced scarcity | 6,369 L (−47%) | 1,198 kWh (−47%) | ₹29,984 |

That 6% against 47% gap is the most important number in this document, and it
is not a weakness in the optimiser. The 47% plan is fully feasible — it misses
no ship date. It is not selected under normal operation because the low-salt
chemistry premium costs more than the steam it saves at today's tariffs. The
engine is telling the truth about the economics it was given.

Which is precisely the finding. **The large saving is available and nobody is
buying it, because the price signal does not reach the person deciding.** Price
water and carbon properly and the same engine, unchanged, recommends the 47%
plan. We did not hide this behind the better number.

### At cluster scale

A linear projection across 400 units, 900 lots each per year. This is a
PROJECTION and the system labels it as one — it assumes every unit resembles
the modelled one and that every recommendation is approved, neither of which
has been tested.

| Freshwater avoided | 75 million litres/year |
|---|---|
| Salt avoided | 4,500 tonnes/year |
| Evaporator steam avoided | 14,106 MWh/year |
| CO2e avoided | 6,376 tonnes/year |

Freshwater avoided equals reject avoided exactly, because in a closed loop the
makeup water is the water that was evaporated. That identity is enforced by a
test, after an earlier version of this projection violated it and overstated
water by a factor of five. Finding and fixing that is part of why the identity
is now a test rather than a convention.

### Why it is feasible

**No capital equipment.** The intervention is a decision, not a retrofit. The
first two phases change nothing on the floor at all.

**It rides an existing mandate.** ZLD is already compulsory and already paid
for. ChangeLoop makes existing assets cheaper to run; it does not ask anyone
to install one.

**Advisory from the start.** The existing planning procedure stays
authoritative throughout. That is what makes a pilot approvable.

**A 32-week staged pilot**, defined in the engine rather than written for this
document: baseline metering, then shadow mode where recommendations are
produced and nobody acts, then advisory with approval, then a controlled
wash-off release trial, then the chemistry decision, then expansion. Alternate
weeks on and off, so the comparison is against the same season, order mix and
crew.

The pilot is designed to answer one question: *did ChangeLoop cause the
reduction, or would it have happened anyway?* A single wash-fastness failure
stops the release trial, because a re-processed lot costs more water than was
saved.

### What would falsify this

Worth stating plainly. If a pilot measures evaporator steam per cubic metre
far from 188 kWh, or finds the 60,000 mg/L concentration ceiling does not hold
across a real operating range, the magnitude of everything here changes. The
direction would survive — it follows from mass conservation — but the numbers
would not. That is exactly what phase 1 exists to find out, and better to know
in week six than after a cluster has paid for it.

---

## 6. Pitch and Idea Diffusion

### The pitch, in three sentences

Zero liquid discharge saved the Noyyal and handed the cluster a coal bill.
That bill is set by salt, not water, so most water-saving work in Tirupur is
aimed at the wrong number. ChangeLoop shows the planner the real consequence
at the moment they choose, and the engine proves the claim rather than
asserting it.

### How the idea spreads

**Through the CETP, not unit by unit.** One commercial relationship reaches
many members, and the CETP's own economics already favour less salt arriving.

**Through shadow mode.** Four weeks of being correct while changing nothing is
how a tool earns the right to influence a factory's decisions. It is the
cheapest trust-building mechanism available and it costs the site nothing.

**Through the open coefficient registry.** Every number, source and derivation
is inspectable in the running system. A process engineer who disagrees with a
coefficient can see exactly what it is and what it changes. That is a faster
route to credibility in an engineering community than any amount of
marketing, and it invites the correction rather than defending against it.

**Through the pricing argument.** The plant result generalises past one
cluster: where a shared environmental resource is under-priced, individually
rational decisions overload it, and the fix is a price rather than a
schedule. That argument is aimed at regulators and tariff-setters, and it
arrives with an engine behind it that anyone can re-run.

**Through being wrong in public.** This submission names its own largest gaps.
That is a diffusion strategy as much as an honesty one — in a field full of
unverifiable impact claims, the system that publishes its own weak points is
the one an engineer will actually try.

---

## 7. Future Scope

### Near term — make it measured

The single biggest upgrade is two instruments: evaporator steam flow, and
reject conductivity. Those two readings promote the two coefficients carrying
the most weight in the result from PUBLISHED to MEASURED. Nothing else moves
the credibility of this system as far for as little. They also need
calibration and health monitoring, because a drifting sensor is worse than no
sensor, and the existing rule — missing or implausible data means hold and
credit zero — has to survive scale rather than being relaxed for throughput.

### Medium term — the cluster

The current plant solver is exhaustive. It optimises each machine's queue
within every strategy, then checks all 256 combinations against capacity and
returns the cheapest that fits, so the answer is proven rather than
approximated. That stops being possible at a CETP with hundreds of member
units, and the method has to change. This is a real limit and not a detail:
cluster-scale coordination is a different optimisation problem, not a bigger
version of the same one.

The commercial question underneath it is harder than the mathematics. If the
cheapest plant-wide plan requires one unit to accept a worse outcome, somebody
has to pay them. The engine can already compute what that transfer should be —
₹4,123 a day in the modelled site, attributable per machine. Whether a CETP
can actually administer it is an institutional question, and it is open.

### Longer term — the same identity elsewhere

The physics ChangeLoop runs on is not specific to textiles. Any closed-loop
water system that concentrates dissolved solids and removes them thermally
obeys the same relation: the volume you must evaporate is set by the dissolved
mass divided by the concentration ceiling, not by the water you circulated.

Evaporative data centre cooling has exactly this shape. Makeup water equals
evaporation plus blowdown; blowdown volume is set by the cycles of
concentration the water chemistry permits; and cycles of concentration are
limited by dissolved solids. The same structural blind spot should therefore
exist — operators optimising water withdrawal while the dissolved-solids
ceiling quietly sets the thermal and chemical load.

Stated carefully: that is a structural argument, not a validated finding. No
data centre has run this and the coefficients would all need re-sourcing.
Cooling towers, boiler blowdown and mine water management share the same
structure. It would be dishonest to present any of them as solved, and the
textile case has to be proven on a real site first.

---

## Closing

ChangeLoop is a working system, publicly reachable, with 163 tests, 25
classified coefficients, external validation against CPCB measurements, and
zero measured data — and it tells you that last part itself, in every view.

The core claim is small enough to check and large enough to matter: in a
closed loop, salt sets the coal bill. The person who controls salt is a
planner who cannot see the consequence. We built the thing that shows them,
proved the physics, priced the gap, and found that at plant scale the problem
is not that anyone is deciding badly — it is that water is too cheap for good
decisions to add up.

**https://changeloop-water-intelligence.onrender.com**
