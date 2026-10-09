# ChangeLoop

## The short version

Dyeing factories in Tirupur are not allowed to let any waste water out. So they
boil the leftover salty water until only dry salt is left. The boiling runs on
solid fuel, mostly wood, with coal and briquettes also used.

How much they have to boil depends on how much salt went into the dye bath. It
does not depend on how much water they used. This sounds wrong, but it comes
straight out of mass conservation, and I can show it.

So if a factory cuts its water use by 20%, the evaporator burns exactly the same
fuel. Cut the salt by 20% and the evaporator's fuel drops by 20%. Both of those
look identical on a water meter. Most water-saving work in the cluster aims at the
water.

The person who sets the salt load is the production planner, choosing what
order to run the day's dye lots in. They decide hours before anything shows up,
and the fuel bill lands weeks later in another department's budget. Nobody
connects the two.

I built a tool that puts the fuel cost in front of that planner while they are
still choosing. It is running now and the numbers can be checked.

**Live:** https://changeloop-water-intelligence.onrender.com

What I can show, and what I cannot:

| | |
|---|---|
| The physics holds up | I fed it the water strength that CPCB measured at a real Tirupur factory. It predicted 30.6% reject. Indian plants report 20 to 30%. I did not tune it to land there. |
| The tool works | 34 API endpoints, 180 tests, 25 input numbers each labelled with where it came from, and a tamper-proof record of every decision. |
| It found something I did not expect | The better plan is blocked by a small price gap, not by technology. About 12% off the price of low-salt dye would be enough. |
| Nothing has been measured | No sensor on any real factory has ever fed this system. A test checks that I never quietly claim otherwise. |

That last row matters. I have not run a pilot and I have no customer. What I
have is the decision logic, the physics behind it, and a check against
published plant data.

---

## 1. The problem

### Where it happens

Tirupur in Tamil Nadu makes over 54% of India's knitwear exports. Its dyeing
factories sit on the Noyyal river. In 2011 the Madras High Court ordered every
dyeing and bleaching unit shut for putting salty waste water into the river.
Over 700 units and treatment plants closed and 40,000 to 50,000 workers lost
their jobs. They were allowed to reopen only if they stopped releasing liquid
waste completely. The rule is called zero liquid discharge, or ZLD.

It worked for the river. The waste water stopped going in.

The problem moved to the boiler house.

### What ZLD actually involves

The waste water goes through membranes. The clean part goes back into
production. The salty leftover goes into an evaporator, which boils it down
until only solid salt remains.

Boiling needs heat and the heat comes from steam. Energy audits of more than
sixty dyeing units in Tiruppur during 2024 and early 2025 found each one
burning about 2,000 tonnes of solid fuel a year, primarily wood. Boiling one
cubic metre of leftover takes about 188 kWh of heat. So a rule written to
protect a river created a large and permanent fuel bill.

The rupee and carbon figures in this note are derived on a coal-fired basis,
which is what my coefficient registry states. A wood-fired boiler has different
fuel economics and a different carbon profile, so both need re-deriving per
site. The physics does not move: salt sets how much has to be boiled whatever
raises the steam.

### The part people miss

This is what the whole project is built on.

In a closed loop, the amount you have to boil is fixed by the salt.

```
leftover volume  =  salt mass  /  strongest the membranes can make it
```

Salt mass, divided by the strongest the membranes can make the leftover, which
is around 60,000 mg/L for dyeing water.

Water goes round the loop and comes back. Salt does not. Salt has to leave as a
solid, and the only way out is through the evaporator. So the evaporator has to
boil whatever amount of water that salt happens to be sitting in.

Using less water makes the loop smaller. Only using less salt makes the boiling
smaller, and the boiling is what burns fuel.

The system checks this on every request:

| Change you make | What happens to evaporator energy |
|---|---|
| Use 20% less water | **no change at all** |
| Put in 20% less salt | **20% less energy** |

Zero, not a small amount. It falls out of the arithmetic.

This is why a water dashboard cannot find the saving. Two changes that look the
same on a water meter do completely different things to the fuel bill, and
nothing on the factory floor tells them apart.

### Why it has not been fixed

The salt load is set by a production planner. They choose which dye lots run in
what order, and which rinse method to use.

They make that choice hours before any of it shows up anywhere. The fuel bill
arrives weeks later, in a different department's budget, with no way to trace
it back to the choice that caused it.

The planner is not being careless. They are working without the one number that
would change their mind.

### A second problem, one level up

This one only appears when you stop looking at a single machine.

A real factory runs several dyeing machines into one shared evaporator. Each
planner picks what is best for their own machine. Every one of those choices is
correct on its own. Added together, they can still be more than the evaporator
can physically boil.

In my model, four machines each picking their own best plan put the shared
evaporator at **121.9% of what it can handle**. Nobody made a bad call. A tool
that looks at one machine at a time cannot see this at all.

---

## 2. What I built

ChangeLoop sits where the schedule gets made. Before a shift starts it looks at
the different orders the planner could run the lots in, and the different rinse
methods available. For each combination it works out the whole chain: water
used, salt load, leftover volume, evaporator steam, CO2, rupees, and whether
any delivery date gets missed.

Then it recommends one, and shows its working.

### Four rules I made it follow

**A late delivery is not a trade-off.** If a plan misses a ship date it gets
removed from the search, not given a bad score. A factory cannot accept a
schedule that saves water by shipping late, so the tool never offers one.

**Every input number says where it came from.** All 25 of them are tagged as
published, derived, assumed, or measured, along with the source and the
arithmetic. You can open the list in the running system and read it yourself.

**It fails safe.** It issues no machine settings and cannot release a dye bath.
Early release needs a named person to approve it. If a sensor reading is
missing or looks wrong, the system stops and claims zero saving rather than
guessing.

**It only counts savings somebody approved.** If the planner turns a
recommendation down, it counts as zero, even though the tool already worked out
what it would have saved. The record shows what was actually done.

### The shared evaporator

The newest part deals with the problem from the end of section 1. It compares
two plans for the same day: what each machine would pick on its own, and the
cheapest combination that actually fits the shared evaporator.

I did not invent the capacity figure. In a closed loop the water you bring in
equals the water you boil off, so the factory's daily water allowance and the
amount the evaporator has to boil are the same number looked at twice. This
matters, because the easiest way to make a demo like this look impressive is to
pick a capacity that guarantees a problem.

| Conditions | Load on the evaporator | Does anyone have to give way? |
|---|---|---|
| Today's prices | 121.9% | Yes. Two of four machines take a worse plan, costing Rs 4,123 a day |
| Water priced for scarcity | 68.8% | No. Everything fits |

At today's prices, water is cheap enough that every machine prefers the
water-saving plan, and together they overload the evaporator. Price water
properly and all four machines pick the low-salt plan by themselves. The
factory fits, nobody loses out, and the extra cost disappears.

Nothing got rescheduled to get there. The plan the factory has to force on two
machines today is the plan every machine would choose on its own if water cost
what it is worth. A test checks this, and if it ever stops being true the test
tells me to rewrite the claim rather than adjust a number.

---

## 3. The prototype

It is a working system that anyone can open, not a mockup or a set of
screenshots.

**https://changeloop-water-intelligence.onrender.com**

| | |
|---|---|
| Backend | Plain Python, no framework, nothing to install |
| API | 34 endpoints. Every saving is worked out on the server, so the browser cannot claim one |
| Tests | 180, covering the physics, the safety rules, concurrency and the interface |
| Front end | No libraries. Ten screens |
| Record of decisions | A chained hash of every entry, re-checked on every health check. It is not a blockchain and the system says so |

### What you can try in it

Change the operating conditions in the top bar and watch the recommendation
change. Across four modes it gives two genuinely different answers, which is
how you tell whether it is working something out or replaying a stored result.

Click any number and trace it back to the input it came from, the source of
that input, and the arithmetic. Approve a recommendation, or turn it down, and
watch the record update. Break a sensor and watch the system stop instead of
guessing. Open the Plant screen to see four correct choices overload one
evaporator. Open the Policy screen to watch the tool search for the price that
would change its own answer.

### How I checked it

No instrument on a real factory has ever fed this system, and it says so on
every screen. What I could do instead was check it against measurements
somebody else published.

CPCB measured the water strength going into evaporation at a Tirupur dyeing
unit: 18,340 mg/L. I fed that in. The model said **30.6%** of the volume would
end up as leftover to boil. Indian ZLD plants report 20 to 30% of inlet volume.

So it lands where real plants sit, using a number it never gets to see the
answer to. That check runs as a test, not as a line on a slide.

The 188 kWh figure gets the same treatment. Latent heat of 0.627 kWh/kg comes
from steam tables. Steam economy of 3.33 kg per kg comes from what textile
evaporators are reported to achieve. Multiply them out and you get 188, which
sits inside the 150 to 250 band published for this kind of plant. That band was
not used anywhere in the calculation, so it is a real check.

What this does and does not mean: the physics behaves like real plants do. It
does not mean any number here describes any particular factory. Those are
different claims and I keep them apart.

### What it does not do

The interface carries its own limits rather than hiding them. It does not
schedule machines against each other in time. It does not model storage tanks
that would absorb some of the problem. It handles machines inside one factory,
not the hundreds of members of a shared treatment plant. The order book is made
up. And nothing in it has been measured.

---

## 4. Who it is for

The person who uses it and the person who pays for it are not the same.

| Who | What they do with it |
|---|---|
| **Production planner** | The main user. They already make this decision every shift. The tool only changes what they can see while making it, so nobody is being asked to do a new job. |
| **Quality supervisor** | Keeps control of early wash-off release. The tool can suggest it. Only they can allow it. |
| **Factory owner** | Gets the money saved, and signs off the dye chemistry decision, which happens on a buying cycle rather than a daily one. |
| **Shared treatment plant** | The best way in commercially. One relationship reaches many member factories. |
| **People living in the basin** | Gain without ever touching it. Groundwater here carries a stress weight of 11.08 in my model, so a litre saved here counts for much more than a litre saved somewhere easy. |

### Why the treatment plant already wants this

Less salt arriving means less steam to buy and less solid salt to store.
Over 1,00,000 tonnes of mixed waste salt now sits in sheds at Tirupur's
treatment plants, and no disposal method has yet been found.

So cutting salt at source is something a treatment plant operator wants for
their own reasons, which have nothing to do with me. That is a good position
for a new tool to be in.

There is also the workforce. For people in Tirupur the 2011 shutdown is
something they remember, not something they read about. The commercial case and
the keep-the-factory-open case point the same way here.

---

## 5. What it saves, and whether it can work

The big saving is already available and nobody is buying it, because the price
signal never reaches the person deciding. I would rather put that up front than
hide it behind the better number.

### One shift

The baseline is a conventional single-stage rinse, on a made-up order book of
five lots. All of this is modelled.

| Plan | Fresh water | Evaporator steam | Cost |
|---|---|---|---|
| Baseline | 11,907 L | 2,239 kWh | Rs 33,897 |
| What it recommends today | 11,187 L (-6%) | 2,104 kWh (-6%) | Rs 26,038 |
| What is available | 6,369 L (-47%) | 1,198 kWh (-47%) | Rs 29,984 |

6% against 47% is the most important comparison in this document.

The 47% plan works. It misses no delivery date. The tool does not pick it
because low-salt dye chemistry costs more than the steam it saves at today's
prices. The tool is telling the truth about the money it was given.

So the thing standing in the way is a price, not the technology and not the
schedule.

### What price would change the answer

Saying "price water properly" is easy. I wanted to know what that actually
means, so the tool works it out. It walks each price up or down, re-running the
whole calculation at every step, and finds the first point where a factory
chasing profit picks the 47% plan on its own.

| Price | Today | Changes at | Move needed |
|---|---|---|---|
| Low-salt dye premium | Rs 6.50/kg fabric | Rs 5.74/kg fabric | **12% cheaper** |
| Boiler steam | Rs 2.03/kWh heat | Rs 3.13/kWh heat | 54% dearer |
| Fresh water | Rs 45/m3 | Rs 251/m3 | 457% dearer |

The dye premium only needs to come down by about 12%. That is the whole
distance between what the cluster runs today and a plan that nearly halves both
water and steam. It is a buying problem, not a research problem.

Two honest limits on that 12%. The dye premium of Rs 6.50 a kilogram is one of
my four assumed coefficients, so the 12% is a computed result on an assumed
input. And it is computed against a coal-based steam price: where steam is a
quarter cheaper, the premium would need to fall about 17% instead.

The steam row turns into a carbon price. Steam would need to go up Rs 1.09 per
kWh of heat. Making that heat gives off 0.452 kg of CO2. Divide one by the
other and you get **Rs 2,423 a tonne, about 21 euro**.

The EU carbon market was charging 82.40 euro a tonne on 5 October 2026. Close
to four times more. So this saving is not waiting for some impossible price. It
is waiting for any price at all.

Two things to be careful about, and the system says both. It assumes the whole
carbon cost reaches the factory as a higher steam price, which is the best
case. And it is the point where this decision flips in my model, not a
recommendation for what a carbon price ought to be.

### If the whole cluster did this

A straight-line projection across 400 factories at 900 lots each a year. The
system labels this as a projection, because it assumes every factory is like
the modelled one and that every recommendation gets approved. Neither has been
tested.

| Saved per year | |
|---|---|
| Fresh water | 75 million litres |
| Salt | 4,500 tonnes |
| Evaporator steam | 14,106 MWh |
| CO2 | 6,376 tonnes |

Water saved equals leftover saved exactly, because in a closed loop the water
you bring in is the water you boiled off. A test enforces that. An earlier
version of this projection broke it and overstated water by five times, which
is why it is now a test and not a convention.

### Why it can actually happen

There is no equipment to buy. The change is a decision, and the first two
stages of the pilot change nothing on the floor at all.

It also rides a rule that already exists. ZLD is compulsory and already paid
for. The tool makes equipment a factory already owns cheaper to run.

And it stays advisory. The existing planning process stays in charge the whole
way through, which is what makes a pilot something a factory might actually
agree to.

### The pilot

Thirty-two weeks, in six stages. These are defined in the engine, not written
for this document.

| Stage | Weeks | What happens |
|---|---|---|
| 1. Measure the baseline | 1-4 | Nothing changes. Just metering. |
| 2. Run it silently | 5-8 | The tool recommends, nobody acts. Compare against what the planner actually did. |
| 3. Planner may approve | 9-16 | Reordering only. No chemistry change yet. |
| 4. Early release trial | 17-24 | Quality supervisor may allow early wash-off release. |
| 5. Decide on chemistry | 25-32 | With steam cost now measured, decide if low-salt dye pays. |
| 6. More factories | 33+ | Second and third unit on the same treatment plant. |

Two points can stop it. The planner has to agree with more than 60% of
recommendations on their own in stage 2. And one colour-fastness failure ends
the release trial in stage 4.

The weeks run on and off in alternate blocks, so the comparison is against the
same season, the same order mix and the same crew.

The whole point is to answer one question: did the tool cause the saving, or
would it have happened anyway? If a lot fails its colour-fastness test after
early release, the trial stops, because reprocessing a lot wastes more water
than the release saved.

### What would prove me wrong

If a pilot measures evaporator steam a long way from 188 kWh per cubic metre,
or finds that the 60,000 mg/L limit does not hold in real running conditions,
then every number in this document changes size. The direction would survive,
because it comes out of mass conservation. The amounts would not.

That is what stage 1 is for. Better to find out in week six than after a whole
cluster has paid for it.

---

## 6. The pitch, and how it spreads

### The pitch in three sentences

ZLD saved the Noyyal river and left the cluster with a fuel bill. That bill is
set by salt, not water, so most of the water-saving work in Tirupur is aimed at
the wrong thing. ChangeLoop shows the planner what their choice actually costs,
at the moment they make it.

### Five ways it spreads

**Through the treatment plant, not factory by factory.** One commercial
relationship reaches many members, and their own economics already favour less
salt coming in.

**By running silently first.** Four weeks of being right while changing nothing
is how a tool earns the right to influence a factory's decisions. It costs the
factory nothing and it is the cheapest trust I can buy.

**By showing the working.** Every input number, its source and its arithmetic
can be read in the running system. An engineer who thinks one of my numbers is
wrong can see exactly what it is and what it changes. In an engineering
community that gets you taken seriously faster than any amount of marketing,
and it invites the argument rather than avoiding it.

**With a price attached.** When a shared resource is under-priced, sensible
individual decisions add up to overloading it, and the fix is a price rather
than a schedule. Most submissions stop at that sentence. Mine names the price:
about 21 euro a tonne of CO2, or 12% off the dye premium. A regulator can act
on a number. They cannot act on a principle.

**By being wrong in public.** This document lists the biggest holes in my own
project. In a field full of impact claims nobody can check, the one that
publishes its own weak points is the one an engineer will try.

---

## 7. What comes next

### First: measure something

The biggest single upgrade is two instruments. A steam flow meter on the
evaporator, and a conductivity probe on the leftover stream. Those two readings
turn the two most important numbers in the model from published figures into
measured ones. Nothing else buys as much credibility for as little money.

They need calibration and health checks too, because a sensor drifting quietly
is worse than no sensor. The rule I already built, that missing or odd data
means stop and claim nothing, has to survive being scaled up rather than
getting relaxed to keep throughput.

### Then: the cluster

Right now the shared-evaporator solver checks every combination. It works out
each machine's best plan under each method, then tests all 256 combinations
against capacity and returns the cheapest that fits. The answer is proved, not
estimated.

That stops being possible at a treatment plant with hundreds of member
factories. The method has to change. This is a real limit and I am not going to
call it a detail. Coordinating a whole cluster is a different problem, not a
bigger version of the same one.

The harder part is not the maths. If the cheapest plan for the whole plant
needs one factory to accept a worse result, somebody has to pay them for it. My
tool can already work out what that payment should be, Rs 4,123 a day in the
model, and which machine it belongs to. Whether a treatment plant could
actually run such a scheme is an open question.

### Later: the same idea elsewhere

The physics is not specific to textiles. Any closed water loop that
concentrates dissolved solids and then boils them off follows the same rule.
What you have to evaporate is set by the dissolved mass divided by the
concentration limit, not by how much water went round.

Data centre cooling has this shape. The make-up water equals what evaporates
plus what gets bled off. How much gets bled off depends on how many times the
water can be cycled, and that is limited by dissolved solids. So the same blind
spot should exist, with operators watching water withdrawal while the dissolved
solids quietly set the load.

I want to be careful here. That is an argument from structure, not a result. No
data centre has run this and every input number would need re-sourcing. Cooling
towers, boiler blowdown and mine water have the same shape too. None of them is
solved, and the textile case has to be proven on a real site first.

---

## What I can and cannot claim

This section is here so you can stop reading and still know how much to trust
everything above.

The system runs on 25 input numbers. Each one is labelled in the product, with
its source and its arithmetic.

| Label | How many | What it means |
|---|---|---|
| Published | 17 | Taken from CPCB, the Central Electricity Authority, Tamil Nadu tariff orders, state pollution board plant data, the EU reference document, and steam tables. |
| Derived | 4 | Worked out from those by arithmetic that a test re-checks. |
| Assumed | 4 | My assumptions, labelled as such. They stay that way because they are commercial prices that public sources do not settle. |
| Measured | 0 | No instrument on a real factory has fed this system. A test enforces this. |

That makes 17 published, 4 derived, 4 assumed out of 25, so 84% of the inputs
are sourced. I did not relabel anything I could not back up.

### Things this project has not done

- No deployment, no customer, no pilot, no measured result.
- The cluster number is a projection. It is not achieved impact and the system
  refuses to display it as one.
- The switching prices say what would change my tool's answer. They are not a
  forecast of what a real factory's accountant would decide.
- The carbon price assumes the full cost reaches the factory as a higher steam
  price. If it does not, the real price needed is higher.
- The shared-evaporator work does not scale to a treatment plant yet. Checking
  every combination will not survive hundreds of members.
- The 60,000 mg/L limit is one modelled figure inside a published range of
  15,000 to 80,000. Whether it holds in real running conditions, I do not know.
- The tool handles machines inside one factory. It does not schedule them
  against each other in time.
- The rupee and carbon conversions assume a coal-fired boiler. Tiruppur units
  mostly burn wood, so both need re-deriving per site.
- The data centre idea is an argument from structure. It is not a result.
- There is no trained model in here and I do not call it AI-powered. The
  decision record is a hash chain, not a blockchain, and the system says so.

### What would make this credible

One site visit and two instrument readings. Steam flow to the evaporator, and
conductivity of the leftover. Those two promote the numbers that carry the most
weight in everything above.

Until then, the fair reading is this. The physics is proved and checked against
published measurements. The money is modelled from published tariffs. The
decision logic works and is tested. And nothing here describes a real factory
yet.

---

## Sources

The real sourcing is not in this document. It is in the running system, where
all 25 input numbers carry their own source text and arithmetic and can be read
without asking me:

https://changeloop-water-intelligence.onrender.com/api/evidence

I did it that way on purpose. A reading list in a document can drift away from
the model. A list the model itself reads cannot.

The outside reading behind the figures above:

| Figure | Where it comes from |
|---|---|
| Grid emissions, 0.705 kg CO2 per kWh | CO2 Baseline Database for the Indian Power Sector, Central Electricity Authority (cea.nic.in) |
| Carbon price, 82.40 euro a tonne on 5 October 2026 | European carbon prices, S&P Global Commodity Insights. A market price, so it goes out of date. The system stores it with its date. |
| Tirupur ZLD rule, treatment plant capacity, water recovery | "Towards zero discharge", Down To Earth |
| Tirupur cluster effluent load and disposal | "Study of Tirupur textile industry cluster", India Water Portal |
| Water strength of 18,340 mg/L, reject at 20-30%, evaporator steam use | Central Pollution Control Board assessment of textile dyeing units and ZLD at Tirupur. Quoted in full in the system against each number it feeds. |
| Water and steam tariffs | Tamil Nadu Electricity Regulatory Commission tariff orders and state pollution board plant data, cited per number in the system |
| Latent heat, 0.62694 kWh/kg | Steam tables: 2,257 kJ/kg at 100 C and one atmosphere, divided by 3,600 |
| Evaporator energy band, 150-250 kWh/m3 | EU Best Available Techniques reference document for textiles. Used only as a check, never as an input. |

Where a source gives a range, the system stores the range and takes a stated
point inside it. Where I could not find a public figure, the number is labelled
as an assumption rather than attached to a source that does not actually say
it. Four numbers are in that state and all four are commercial prices.

---

## Closing

ChangeLoop is a working system anyone can open, with 180 tests, 25 labelled
input numbers, a check against CPCB measurements, and no measured data at all.
It tells you that last part itself, on every screen.

The claim is small enough to check and big enough to matter. In a closed loop,
salt sets the fuel bill. The person who controls the salt cannot see what it
costs. I built the thing that shows them, proved the physics, and then worked
out what the saving is actually waiting on.

It is waiting on a price. About 21 euro a tonne of CO2, or 12% off a dye
premium. That is a much smaller problem than it looked like at the start.

**https://changeloop-water-intelligence.onrender.com**
