# ChangeLoop

## 1. Title page

| | |
|---|---|
| **Startup name** | ChangeLoop |
| **Tagline** | Cut the water by a fifth. The evaporator burns exactly the same fuel. |
| **Date** | 9 October 2026 |
| **Prepared by** | Shorya Ashish Mittal, project lead and sole developer |
| **Contact** | shoryamittal9653@gmail.com |
| **Working prototype** | https://changeloop-water-intelligence.onrender.com |

---

## 2. Background and problem statement

### Context

Tirupur in Tamil Nadu is India's knitwear capital, with over 54% of the
country's knitwear exports. In the year to March 2026 it exported around Rs
46,000 crore of knitwear. Its dyeing factories sit on the Noyyal river.

In 2011 the Madras High Court ordered every dyeing and bleaching unit in Tirupur
shut to save the Noyyal. Over 700 units and treatment plants closed, 40,000 to
50,000 workers lost their jobs, and the cluster lost an estimated Rs 50 crore a
day. The units were allowed back only if they stopped releasing liquid waste
completely. The rule is called zero liquid discharge, or ZLD.

Today 360 dyeing units operate in and around the city: 60 with their own
treatment plants, and the rest sharing 18 common ones. Between them they treat
about 130 million litres of effluent a day and recover about 92% of it for
reuse.

It worked for the river. The waste water stopped going in. But it is costly to
run. The dyers' association says the 18 common plants spend around Rs 30 crore
a month on electricity alone, and the problem moved to the boiler house, where
nobody is managing it.

### The problem

To recycle the water, a factory has to boil the leftover salty stream until
only dry salt is left. Boiling needs heat and the heat comes from steam.
Energy audits of more than sixty dyeing units in Tiruppur during 2024 and early
2025 found each one burning on average about 2,000 tonnes of solid fuel a year,
primarily wood, with coal and briquettes also in use. Boiling one cubic metre of leftover
takes about 188 kWh of heat.

One caveat I want up front rather than buried. The rupee and carbon figures in
this note are derived on a coal-fired basis, which is what my coefficient
registry states. A wood-fired boiler has different fuel economics and a
different carbon profile, so those two conversions need re-deriving for any
particular site. The physics underneath does not move: salt sets how much has
to be boiled whatever fuel raises the steam.

Here is the part almost nobody acts on.

**The amount you have to boil is fixed by the salt, not by the water.**

```
leftover volume  =  salt mass  /  strongest the membranes can make it
```

Water goes round the loop and comes back. Salt does not. Salt has to leave as a
solid, and the only way out is through the evaporator. So the evaporator must
boil whatever amount of water that salt happens to be sitting in.

The result is easy to test, and my system tests it on every request:

| Change a factory makes | What happens to evaporator energy |
|---|---|
| Uses 20% less water | **no change at all** |
| Puts in 20% less salt | **20% less energy** |

Zero, not a small amount. It falls straight out of the arithmetic.

So two changes that look identical on a water meter do completely different
things to the evaporator's fuel bill. Most water-saving work in the cluster aims
at the water, and leaves the evaporator burning exactly what it burned before.

### Why a problem this simple is still not solved

It is fair to ask why, if the arithmetic is this plain, a cluster that exports
Rs 46,000 crore a year has not already fixed it. The honest answer is that the
saving is not hidden. It is known, documented, and still not taken.

Energy audits of more than sixty dyeing units in Tiruppur during 2024 and early
2025 found that simple efficiency measures could cut about **15% of fuel
consumption**. Many of those measures needed little or no investment. Adoption
stayed low anyway.

That is the real problem, and it is not a technical one. Four things keep it
in place.

**An audit produces a report, not a decision.** A consultant visits, measures,
writes it up and leaves. On Monday the planner schedules the day exactly as
before, because nothing in their actual workflow changed. Reports do not run
shifts.

**Changing anything feels like risking production.** The audits name fear of
disrupting production as a barrier even for measures that cost nothing. In a
job-work cluster running to tight delivery dates, a late or off-shade lot costs
far more than the fuel it might have saved. Any proposal that cannot guarantee
the ship date is dead on arrival, however good its numbers are.

**The person who decides does not see the bill.** The salt load is set by a
production planner choosing which lots run in what order and which rinse method
to use. They make that call hours before anything shows up. The fuel bill
arrives weeks later, in a different department's budget, with no way to trace it
back. The planner is not being careless. They are working without the one number
that would change their mind.

**Nobody meters the thing that matters.** Water is metered because it is billed
and regulated. Salt is bought by the sack and dissolved into a bath, and no
Indian dyehouse I can find reports salt load per lot. What is not measured does
not get managed, and here the unmeasured variable is the one driving the cost.

So the gap is not knowledge. It is that no tool puts the consequence in front of
the person making the choice, at the moment they make it, without asking them to
risk a delivery.

There is a second problem one level up. A factory runs several dyeing machines
into one shared evaporator. Each planner picks what is best for their own
machine, and every choice is correct on its own. Added together they can still
be more than the evaporator can boil. In my model four machines each picking
their own best plan put the shared evaporator at **121.9% of what it can
handle**. No tool that looks at one machine can see this.

### Target audience

The people most affected are the ones running these factories under a rule they
did not choose and cannot opt out of.

| Who | Why this matters to them |
|---|---|
| **Production planners** in Tirupur dyeing units | They make this decision every shift and cannot see what it costs |
| **Factory owners** | They pay a fuel bill they cannot trace or control |
| **The 18 shared treatment plants** | They buy the steam and store the salt. Over 1,00,000 tonnes of mixed waste salt now sits in sheds on their premises, with no disposal method yet found |
| **Households and farmers in the Noyyal basin** | Groundwater here is heavily stressed. Every litre not pulled out matters more than a litre saved somewhere easy |

---

## 3. Vision and mission

### Vision

**Every closed water loop in Indian industry is run on what it actually costs,
not on what is easy to measure.**

Water meters are everywhere and they measure the wrong thing. In a closed loop
the environmental and financial damage is driven by dissolved load, and almost
nothing in industry is set up to see that. The long-term aim is to make the
hidden number visible wherever this physics applies, starting with textiles and
extending to cooling towers, boiler blowdown and other closed systems.

### Mission

**Put the downstream cost in front of the person making the upstream decision,
at the moment they make it, with every number open to inspection.**

In practice that means three things. Build the decision layer and prove the
physics. Prove it on one factory with real instruments. Then reach the rest of
the cluster through the shared treatment plants, whose own economics already
point the same way.

---

## 4. Solution overview

### What it does, in one paragraph

ChangeLoop sits where the schedule is made. Before a shift starts, it takes the
lots that have to run and works out every order they could run in, and every
rinse method available for each. For each of those combinations it computes the
full consequence: water drawn, salt added, leftover volume to boil, evaporator
steam, CO2 and rupees, and whether any delivery date would be missed. It throws
away everything that ships late, ranks what is left, and shows the planner the
best plan with its working.

The planner can accept it or ignore it. Nothing else changes: no new equipment,
no new chemistry, no change to who approves what.

### Why this is the right place to intervene

Every other way of attacking this problem asks the factory to change something
physical, and that is why they stall.

Buy a better evaporator and you have spent capital on treating the symptom. Buy
low-salt chemistry and you have raised the cost per kilogram today for a fuel
saving you cannot yet see. Run an energy audit and you get a report. All three
ask for money or risk up front against a benefit nobody has measured.

Changing the order lots run in costs nothing and is reversible the same day,
and the tool never offers an order that misses a ship date. It is the one lever
in this process that is free to pull. What I
have added is making it a visible lever rather than an invisible one.

### What makes it different

**One line, if you only read one.** Every planning tool in a dyehouse optimises
for throughput and delivery. ChangeLoop is the only one I have found that
prices what the schedule does to the boiler, and it does that while the schedule is still being
chosen.

The rest follows from treating that as a safety-critical decision rather than a
dashboard.

| | How ChangeLoop behaves | Why it matters here |
|---|---|---|
| **Delivery dates** | A plan that ships late is deleted from the search, not scored badly | Removes the single objection that kills every efficiency proposal in a job-work cluster |
| **Every input number** | All 25 are labelled published, derived, assumed or measured, with the source and the arithmetic, readable in the live system | A process engineer can audit the model instead of trusting it. None is MEASURED yet and a test enforces that |
| **Authority** | Issues no machine settings and cannot release a dye bath. Early release needs a named person | The quality supervisor keeps the decision that carries the quality risk |
| **Bad sensor data** | Holds and claims zero saving rather than estimating | An advisory tool that quietly guesses is worse than no tool |
| **Credit for savings** | A recommendation the planner declines counts as zero, even though the engine computed it | The ledger records what was done, not what was advised, so it can be billed against |
| **More than one machine** | Compares what each machine would pick alone against the cheapest combination the shared evaporator can take | Four locally correct choices can still breach the plant, and no single-machine tool can see it |

### Value proposition

| Who | What they get |
|---|---|
| **Factory owner** | Lower fuel and water bills from a scheduling change, with nothing to buy and no change to the approval process |
| **Production planner** | The missing number on their screen, at the moment they need it, with the ship date protected by construction |
| **Shared treatment plant** | Less salt arriving, so less steam bought and less solid salt stored |
| **Regulator or tariff-setter** | A figure for what a price change would actually do, instead of an argument in principle |

---

## 5. Objectives and goals

### Short term, the next 12 months

| Objective | Measure of success |
|---|---|
| Install instruments at one pilot factory | Steam flow and reject conductivity metered for 28 days at over 95% completeness |
| Prove the recommendations are sound | Planner agrees with over 60% of them unprompted, during four weeks where the tool changes nothing |
| Measure a real saving | Water and steam reduction measured with a confidence interval, on alternate weeks on and off |
| Keep quality intact | Zero colour-fastness failures attributable to an approved plan |
| Turn assumptions into measurements | Move the two heaviest input numbers from published to measured |

### Long term, two to five years

The first two are the ones that matter. They change the cluster whether or not
anyone buys the software.

| Objective | Target | Why it has leverage |
|---|---|---|
| **Get treatment plants charging by salt, not by volume** | Two CETPs running a salt-indexed tariff for their members | As far as I can find, CETP charges are set by the volume a member sends, not by how salty it is, so the cost of the salt a unit creates lands on the plant. Change that and every member has the incentive on day one. This is the highest-leverage outcome in the project, and since section 6 it is also what I sell rather than something I hope somebody does |
| **Make salt load per lot a number the industry reports** | Salt per lot metered and reported at 40 units, the way water already is | Water got managed once it got metered. Nothing gets managed until it is measured, and right now nobody measures the variable that drives the cost |
| Close the dye premium gap by buying together | A joint procurement approach across CETP members, aimed at the 12% gap my engine computes | 12% is small enough that aggregated demand across a few hundred units could close it. Then the 47% plan becomes the cheap plan and nobody has to be persuaded |
| Solve cluster coordination properly | A method that works for hundreds of member units, not the 256 combinations the current solver checks exhaustively | The current approach is proven but will not scale, and I would rather say that than imply it will |
| Put the evidence in the open | The measured coefficients published, with the method, for anyone to use or contest | A model nobody can check is worth less than one people argue with |
| Extend beyond textiles | One validated application in another closed-loop system, such as evaporative cooling | The physics is not specific to dyeing, but it is unproven anywhere else |

---

## 6. Business model

### Who actually pays for salt

My first business model billed the factory a share of its savings, and the
arithmetic talked me out of it. A dyeing unit buys salt at about Rs 9 a
kilogram and buys water by volume. Salt is cheap to a factory. That is
precisely why nobody acts on it, and charging the party with the weakest
incentive is a hard way to build a business.

Then I worked out who does carry the cost.

Every tonne of salt that reaches a treatment plant forces about 17 cubic
metres of reject to be boiled. Using my own coefficients, that is Rs 6,363 of
steam, Rs 3,000 of evaporator operating cost and Rs 527 of power:
**Rs 9,891 a tonne**.

A single CETP in Tirupur handles roughly a sixth of the cluster's 100 million
litres a day. At the recovery rates these plants report, that is about
**7,700 tonnes of salt a year, costing it around Rs 7.62 crore** to deal with.

It chose none of it. Its seventeen member factories did. And because the plant
bills members by the volume they send rather than how salty it is, it has no
way to charge for any of it. The dyers' association says the 18 plants together
spend around Rs 30 crore a month on electricity, and this is a large part of
why.

That is the same misaligned incentive as section 2, one level up. The factory
decides, somebody else pays, and nobody can see the link.

### How it makes money

So I sell to the plant, and give the planner to the factory cheaply enough that
adopting it is not a decision anyone has to defend.

| Who pays | What for | Price |
|---|---|---|
| **Treatment plant** | Salt attribution: how much salt each member sent, what it cost the plant, and a tariff engine to bill for it | Rs 12,00,000 a year, plus 20% of the verified reduction |
| **Treatment plant, once** | Onboarding: conductivity meters on member discharge lines, attribution set up against the plant's own costs | Rs 2,50,000 |
| **Member factory** | The planner itself, priced per lot so it scales with use | Rs 15 a lot, about Rs 75,000 a year |

A 3% cut in salt arriving saves a plant about Rs 22,80,000 a year, so the
platform pays for itself in the first year at a reduction small enough to be
plausible. At 10% it saves about Rs 76,20,000.

### Why this way round

**The factory ask becomes signable.** Rs 75,000 a year is an operating expense
a dyeing-unit owner approves without a board meeting. A share of savings on my
earlier model would have been Rs 19,65,000, and no owner signs that for
software against a saving nobody has measured yet.

**Eighteen conversations instead of three hundred and sixty.** One plant
relationship reaches about seventeen factories. That is the difference between
a business one person can start and one that needs a sales team on day one.

**It creates pull instead of push.** Once a plant bills by salt load, its
members suddenly need a way to manage salt, and the planner is that way. I stop
having to persuade anyone that the problem is real; their invoice does it.

**It is what the system is uniquely able to do.** Plenty of software can
schedule a dyehouse. Attributing a plant's salt load back to the member and the
lot that caused it is the thing only this engine does, because it is the thing
the whole model was built to compute.

**I am paid on what was measured and approved.** Savings are computed on the
server, counted only when a named person approved the plan, and written to a
tamper-evident ledger. That ledger is the billing basis, which turns the
project's weakest point into the mechanism: nothing is measured yet, so nothing
is owed yet.

### What a factory actually gets

The engine reports a net saving per lot against a conventional single-stage
rinse. To turn that into a year I need to know how many lots a real unit runs,
and I would rather anchor that on something measured than multiply my own model
out.

The audits put a Tiruppur dyeing unit at about 2,000 tonnes of fuel a year.
Seasoned wood gives about 15.5 MJ per kilogram, a boiler delivers about 78% of
that as heat, and my engine uses about 1,346 kWh of energy per lot. Put
together, that fuel supports roughly **5,000 lots a year**, and nearer 4,000 if
the wood is wet. I use 5,000.

| | Plan it recommends today | Low-salt plan |
|---|---|---|
| Net saving per lot | Rs 1,572 | Rs 783 |
| Lots a year, mid-size unit | 5,000 | 5,000 |
| Net saving a year | **Rs 78,60,000** | **Rs 39,14,000** |
| My fee at Rs 15 a lot | Rs 75,000 | Rs 75,000 |
| Factory keeps | **Rs 77,85,000** | **Rs 38,39,000** |
| Water and steam cut | 6% | 47% |

Read that table carefully, because it is the point of the whole project.

The fee is the same in both columns because it is charged per lot, not per
rupee saved. The factory keeps essentially all of the benefit.

The plan the optimiser recommends today saves **more money** but only 6% of
the fresh water. The low-salt plan saves **less money** and nearly half the
water and steam. The dye premium eats most of the saving, which is exactly why a
profit-seeking factory does not buy it and why the cluster keeps burning fuel
it does not need to.

Close the 12% gap in the dye premium and the low-salt plan becomes the cheaper
one too. Then the factory saves more money and more water at the same time, and
nobody has to be persuaded to choose between them.

### Where the saving actually comes from

The recommended plan does two things at once: it re-orders the lots, and it
switches the rinse to a counter-current cascade. They are worth separating,
because they behave very differently.

| Source of the saving | Per lot | Per year, 5,000 lots | Effect on fresh water and evaporator steam | Who gets it |
|---|---|---|---|---|
| Re-ordering the lots | Rs 607 | Rs 30,37,000 | All of the 6% cut | Every unit, whatever rinse it already uses |
| Switching to counter-current rinsing | Rs 964 | Rs 48,22,000 | None at all | Only units still on a single-stage rinse |
| **Both together, the plan it recommends** | **Rs 1,572** | **Rs 78,60,000** | **6%** | |

Rows may not add exactly because of rounding.

The second row is worth a moment. Counter-current rinsing cuts the water
circulated through the machines by about a quarter, and changes the fresh water
drawn and the evaporator steam by exactly nothing, because it does not change
the salt. It is the same finding as section 2, turning up on its own inside the
engine.

It also answers the obvious objection. Counter-current cascade is an
established best available technique, and a unit already running it has
already taken the rinse part of the saving. It still gets the re-ordering part,
about Rs 607 a lot, and all of the cut in fresh water and evaporator steam,
because that comes from the order, not the rinse. The first thing a pilot does
is establish which kind of unit it is in.

All of these rupees are modelled, on a modelled order book of five lots. The
direction and the ranking are what I would defend; a pilot establishes the
amounts.

### How customers are reached

**Through the shared treatment plants, which are the customer.** Tirupur has
18 of them serving about 300 units. One conversation reaches about seventeen
factories instead of one, which is the difference between a sales effort one
person can run and one that needs a team from the start.

They are not only a channel. The Rs 7.62 crore a year of salt-driven cost is
theirs, so the attribution platform is bought for their own reasons, not as a
favour to their members.

**Through running silently first.** Four weeks of being right while changing
nothing is how a tool earns the right to influence a factory's decisions. It
costs the factory nothing.

**Through the dyers' own association.** The Dyers Association of Tiruppur
already speaks for its members on salt disposal and effluent, which is exactly
the problem this addresses.

### Partnerships that would help

| Partner | What it brings |
|---|---|
| A shared treatment plant in Tirupur | The pilot site, the steam data, and the route to its member units |
| A dye chemistry supplier | Real pricing on low-salt chemistry, which is the lever with the smallest gap to close |
| A state pollution control board or CPCB | Credibility, and access to the measured data that would replace my published figures |
| An academic water or chemical engineering group | Independent review of the model before anyone relies on it |

---

## 7. Market analysis and competition

### Market size

| Level | Size | Basis |
|---|---|---|
| Tirupur, immediate | 18 treatment plants at about Rs 20,00,000 a year is Rs 3.6 crore, and 360 factories at Rs 75,000 is Rs 2.7 crore. Together of the order of **Rs 6.3 crore a year** | 360 units operating in 2025, 300 of them on 18 CETPs, per the Dyers Association of Tiruppur. The plant fee is anchored on a cost I can derive, not on a saving nobody has measured, which is why this is far below what a share-of-savings model would have claimed |
| Indian textile ZLD, wider | Tirupur is one of several clusters under ZLD rules. Surat, Erode, Karur, Ludhiana, Panipat and Jetpur have similar processing bases. The whole Indian ZLD equipment market across all industries is put at about **USD 1.33 billion in 2025**, growing to USD 2.52 billion by 2032 | The dollar figure is a commercial market estimate covering all ZLD, not textile software. I have not counted dyeing units outside Tirupur and will not present a number I cannot source |
| Adjacent closed loops, later | Evaporative cooling, boiler blowdown and mine water share the same physics | Unvalidated. Listed as direction, not as market |

The growth driver is regulation that already exists. ZLD is compulsory and
already paid for. ChangeLoop does not ask anyone to install new equipment, it
makes equipment they already own cheaper to run.

The second driver is carbon reporting. European buyers increasingly ask
Indian suppliers for emissions data. The EU carbon border mechanism does not
cover textiles today, since it applies to iron and steel, cement, aluminium,
fertilisers, electricity and hydrogen, but textiles have been named as a
candidate for a later phase. If that happens, a tool that can show measured
and traceable reductions in process emissions becomes a compliance asset as
well as a cost saver. I am treating that as a possible tailwind, not as a
commitment anyone has made.

### Competitive landscape

| Who | What they do | Why ChangeLoop is different |
|---|---|---|
| **Dyehouse software**, such as SedoMaster and Datatex | Plan production, manage recipes, track batches | They schedule for throughput and delivery. Neither prices the downstream thermal cost of the schedule, which is the whole point here |
| **ZLD equipment companies**, such as Praj and VA Tech Wabag | Build and run the membranes and evaporators. Praj has worked on Tirupur textile effluent; VA Tech Wabag builds evaporator-based ZLD plants | They sell the plant. They do not touch the upstream decision that sets how hard the plant has to work |
| **Water monitoring and IoT dashboards** | Report flows and quality after the fact | They measure water volume, which the table in section 2 shows is the wrong number for the evaporator's fuel bill |
| **Cleaner dye chemistry**, such as Archroma's Avitera reactive range, and CIRCOT's low-salt dyeing technology in India | Sell or license chemistry that cuts salt, water or energy in the dye bath | They sell the lever. They cannot tell a factory when it pays, which is exactly what my system computes |
| **Consultancies and energy audits** | One-off studies | A report is read once. This runs every shift and is checked against what was actually approved |

The honest summary: the pieces exist. The membranes exist, the chemistry
exists, the planning software exists. What I have not found anywhere is
something that connects the upstream scheduling decision to the downstream fuel
bill, which is where the saving is hiding.

---

## 8. Implementation plan

### Current status

The prototype is built and running. It is a live system anyone can open, not a
mockup.

| | |
|---|---|
| API | 34 endpoints. Every saving is worked out on the server, so the browser cannot claim one |
| Tests | 180, covering the physics, the safety rules, concurrency and the interface |
| Input numbers | 25, each labelled with its source. 17 published, 4 derived, 4 assumed, 0 measured |
| Validation | Fed the water strength CPCB measured at a Tirupur unit, 18,340 mg/L, the model predicted 30.6% leftover. Indian plants report 20 to 30% |

### Timeline

| Stage | Weeks | What happens | Gate to pass |
|---|---|---|---|
| 1. Measure the baseline | 1-4 | Instruments installed. Nothing changes on the floor | 28 days of data at over 95% completeness |
| 2. Run it silently | 5-8 | The tool recommends, nobody acts | Planner agrees with over 60% unprompted |
| 3. Planner may approve | 9-16 | Reordering only, no chemistry change | Measured water reduction, zero off-shade lots |
| 4. Early release trial | 17-24 | Quality supervisor may allow early wash-off release | Every released lot lab tested. One failure ends the trial |
| 5. Decide on chemistry | 25-32 | With steam cost now measured, decide if low-salt dye pays | A decision backed by measured, not assumed, numbers |
| 6. More factories | 33-52 | Second and third unit on the same treatment plant | Two more units live and paying |

The weeks run on and off in alternate blocks, so the comparison is against the
same season, the same order mix and the same crew. The whole point is to answer
one question: did the tool cause the saving, or would it have happened anyway?

### Key milestones

| Milestone | When | Why this date |
|---|---|---|
| First pilot site agreed | Month 4 | Three months of introductions, site visits and a safety review before anyone lets a student near a steam header |
| First measured coefficient replacing a published one | Month 6 | Instruments in, 28 days of clean data |
| First saving measured with a confidence interval | Month 10 | Needs alternate on and off weeks through stage 3 |
| First treatment plant signs for attribution | Month 15 | After the pilot has a measured result to show |
| Salt-indexed tariff piloted at one plant | Month 24 | The plant's members have to agree to it, which is a governance step, not a technical one |
| 3 plants and 30 factories live | Month 36 | About the ceiling for one person without hiring |

---

## 9. Financial overview

All figures in this section are plans, not results. I have no revenue and no
customers today. The software already exists and runs, so what follows is the
cost of proving it on a real factory, not the cost of building it.

### What the pilot actually costs

Instrumentation per site. These are the two readings that turn the heaviest
assumptions in the model into measurements.

| Item | Cost | Why this figure |
|---|---|---|
| Vortex steam flow meter, DN50, steam rated | Rs 60,000 | Indian suppliers quote Rs 35,500 to Rs 96,000 depending on line size and specification |
| Inductive conductivity transmitter and sensor | Rs 50,000 | The reject stream fouls contacting electrodes, so an inductive probe is the correct type. Indian industrial units run Rs 25,000 to Rs 60,000 |
| Tapping, wiring and commissioning | Rs 35,000 | Hot line tapping and a safe install on an existing steam header |
| Data logger and gateway | Rs 15,000 | So readings reach the system without someone copying them down |
| Calibration and first-year checks | Rs 15,000 | A drifting sensor is worse than no sensor |
| **Per site** | **Rs 1,75,000** | |

The whole pilot across twelve months, for two sites.

| Item | Cost | Why this figure |
|---|---|---|
| Instrumentation, two sites | Rs 3,50,000 | Two sites so the result is not one factory's quirk |
| Independent colour-fastness testing | Rs 50,000 | About 150 samples. SITRA in Coimbatore publishes Rs 300 to Rs 350 per sample for colour fastness to washing |
| Travel to Tirupur, about twelve visits | Rs 60,000 | About Rs 5,000 a visit including travel and a night's stay, assuming travel within Tamil Nadu. From further away it is closer to double. Install, calibrate, and sit with the planner during the shadow weeks |
| Cloud hosting and domain | Rs 20,000 | The system runs on a small instance today |
| Contingency, about 10% | Rs 48,000 | |
| **Total** | **Rs 5,28,000** | |

### What costs nothing

The software is built, tested and running. Extending it to a second or third
factory is configuration, not development.

The host factory contributes in kind rather than in cash: access to the steam
header and the reject line, an extract from its planning system, and some of
the planner's time during the weeks when the tool changes nothing. None of that is a
cheque, and without it the cash above buys nothing.

My own work on the pilot is not costed here. I am doing it either way.

### How a pilot like this gets funded

Three routes, and they are not exclusive. A treatment plant can co-fund the
instruments, because the steam saving lands on its own bill. A state or
central scheme for cluster-level environmental work can cover metering. Or the
first site pays a reduced fee and keeps the saving, which is the cleanest test
of whether anyone actually wants this.

I am not putting a funding request in this note. The number above is here so
the cost of the next step is visible, and because a plan that cannot say what
it costs is not a plan.

### Unit economics

| Item | Amount |
|---|---|
| Treatment plant platform | Rs 12,00,000 a year |
| Treatment plant onboarding, once | Rs 2,50,000 |
| Share of the plant's verified reduction | 20% |
| Member factory planner | Rs 15 a lot, about Rs 75,000 a year |

The plant fee is anchored on a cost I can derive rather than a saving nobody
has measured. A plant carries about Rs 7.62 crore a year of salt-driven cost,
so Rs 12,00,000 is about 1.6% of it, and a 3% reduction returns about
Rs 22,80,000. That is a case a plant manager can check without trusting my
model.

The factory fee deliberately does not scale with savings. At Rs 15 a lot it is
roughly 1% of what the engine says the plan saves, which means I am never
arguing with an owner about whether the saving was real.

### Revenue projections

The binding constraint on these is not demand. It is that I am one person.

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Treatment plants live | 0, pilot only | 1 | 3 |
| Member factories live | 2, pilot | 10 | 30 |
| Plant platform fees | none | Rs 12,00,000 | Rs 36,00,000 |
| Plant onboarding, new plants only | none | Rs 2,50,000 | Rs 5,00,000 |
| Factory planner fees | waived during pilot | Rs 7,50,000 | Rs 22,50,000 |
| **Total revenue** | **nil** | **Rs 22,00,000** | **Rs 63,50,000** |

Year 1 earns nothing on purpose. The two pilot factories pay nothing while
their baseline is being established, because the whole point of that year is to
find out whether the saving is real, and charging for it would bias the answer.

Year 2 assumes one plant signs after seeing pilot results, bringing about ten
of its members. Year 3 assumes two more plants. Onboarding is billed once per
plant, so year 3 bills two, not three.

The 20% share of verified reduction is deliberately left out of these totals. I
can compute what it would be, but it rests on a reduction no instrument has
confirmed, and a projection that depends on my own model being right is not a
projection.

Three plants and thirty factories by year three is roughly the ceiling for one
person doing integration, training and support. Past that I would need to hire,
and I would rather show a number I could deliver alone than one that quietly
assumes a team I do not have.

## 10. Impact assessment

### If one factory adopts it

For the modelled five-lot queue, on the plan the tool recommends under today's
prices, against a conventional single-stage rinse:

| | Fresh water | Evaporator steam | Cost |
|---|---|---|---|
| Baseline | 11,907 L | 2,239 kWh | Rs 33,897 |
| Recommended today | 11,187 L (-6%) | 2,104 kWh (-6%) | Rs 26,038 |
| Available with low-salt chemistry | 6,369 L (-47%) | 1,198 kWh (-47%) | Rs 29,984 |

### If the cluster adopts it

A straight-line projection across 400 units at 900 lots each a year. The 400 is
the figure my engine uses, a little above the 360 units operating today. It is
still deliberately cautious overall: it assumes 900 lots a unit
a year against the 5,000 used in section 6, so its totals sit well below what a
single unit's own figures would multiply out to. This is a projection and my system labels it as one. It assumes every factory resembles
the modelled one and that every recommendation is approved. Neither has been
tested, and it must not be read as achieved impact.

| Saved per year across the cluster | |
|---|---|
| Fresh water | 75 million litres |
| Salt | 4,500 tonnes |
| Evaporator steam | 14,106 MWh |
| CO2 | 6,376 tonnes |

### Environmental benefit

Less groundwater pulled out of a basin that is already stressed. Less solid fuel
burned for the same output, which in Tiruppur mostly means less wood. Less solid salt added to the more than 1,00,000
tonnes already stored in sheds at Tirupur's treatment plants, for which no
disposal method has yet been found.

### Economic benefit

A lower cost base for a cluster that exports around Rs 46,000 crore a year and
competes on price. The 2011 shutdown is living memory in Tirupur, so anything
that strengthens environmental compliance also protects the jobs that depend on
staying open.

### The policy finding

My system can compute what price would make the bigger saving worth buying. It
walks each price up or down, re-running the whole calculation at every step,
and finds the point where a factory chasing profit picks the 47% plan on its
own.

| Price | Today | Changes at | Move needed |
|---|---|---|---|
| Low-salt dye premium | Rs 6.50/kg fabric | Rs 5.74/kg fabric | **12% cheaper** |
| Boiler steam | Rs 2.03/kWh heat | Rs 3.13/kWh heat | 54% dearer |
| Fresh water | Rs 45/m3 | Rs 251/m3 | 457% dearer |

The steam row converts into a carbon price. Steam would need to rise Rs 1.09
per kWh of heat, and making that heat gives off 0.452 kg of CO2, so the carbon
price that produces the rise is **Rs 2,423 a tonne, about 21 euro**.

The EU carbon market was charging 82.40 euro a tonne on 5 October 2026, close
to four times more. So this saving is not waiting for an impossible price. It
is waiting for any price at all.

Three caveats travel with that figure. It assumes the whole carbon cost reaches
the factory as a higher steam price, which is the best case. It is the point
where this decision flips in my model, not a recommendation for what a carbon
price ought to be. And it is computed on a coal-fired boiler, so at a
wood-fired site the carbon lever is weaker and the dye premium matters more.

The direction does not depend on the fuel, but the size of the gap does.
Every switching price is computed against my coal-based steam cost. Where steam
is cheaper, saved steam is worth less and the gap is wider: if steam cost a
quarter less, the dye premium would need to fall about 17% instead of 12%. The
dye premium itself is one of my four assumed coefficients, so the 12% is a
computed result on an assumed input, and the first thing a chemistry supplier
conversation would do is replace it with a real quote.

---

## 11. Conclusion

ZLD saved the Noyyal river and left the cluster with a fuel bill nobody is
managing. That bill is set by salt, not water, so most of the water-saving work
in Tirupur is aimed at the wrong number. ChangeLoop shows the planner what
their choice actually costs, at the moment they make it.

The prototype is built, running and open to inspection. The physics is checked
against published plant measurements. The business model follows the money
rather than the obvious buyer: a treatment plant carries about Rs 7.62 crore a
year of cost created by salt it never chose, so it buys the attribution that
lets it charge for it, and its member factories get the planner for about
Rs 75,000 a year. Eighteen plants, not three hundred and sixty factories, is a
cluster one person can actually reach.

What it does not have is a single measured number from a real factory, and I
would rather say that plainly than let a reviewer discover it. Closing that gap
costs about Rs 5,28,000 and needs one factory willing to let me put two
instruments on its pipework.

### What would help most

None of these is money.

- **An introduction to a shared treatment plant** in Tirupur willing to host a
  pilot. This is the single thing standing between the project and its first
  measured number.
- **A technical review** of the model by someone who knows textile effluent. I
  would rather be told a coefficient is wrong now than after a factory has
  relied on it.
- **An introduction to a dye chemistry supplier**, to put a real price on the
  lever my system says has the smallest gap to close.

### Next steps

I can demonstrate the live system in under ten minutes, including the parts
that show its own limits. I would welcome a technical review of the
coefficients before any pilot begins, and I am happy to be told a number is
wrong. Every one of them is open at the link below.

**https://changeloop-water-intelligence.onrender.com**

---

## 12. Appendix

### How the figures in this note can be checked

Every engine figure quoted here is produced by the live system and can be
reproduced. The input numbers, with their sources and arithmetic, are at
https://changeloop-water-intelligence.onrender.com/api/evidence

A script in the repository re-checks every number in this document against the
engine and fails if any has drifted.

### Evidence position

| Label | How many | What it means |
|---|---|---|
| Published | 17 | From CPCB, the Central Electricity Authority, Tamil Nadu tariff orders, state pollution board data, the EU reference document, steam tables |
| Derived | 4 | Worked out from those by arithmetic a test re-checks |
| Assumed | 4 | My assumptions, labelled as such. All four are commercial prices public sources do not settle |
| Measured | 0 | No instrument on a real factory has fed this system. A test enforces this |

### What this project has not done

- No deployment, no customer, no pilot, no measured result.
- The baseline is a conventional single-stage rinse. Units already on
  counter-current cascade have taken the rinse part of the saving, about Rs 964
  a lot, and keep the re-ordering part. I do not know what share of Tirupur
  they are.
- The 12% dye premium gap is computed on an assumed premium of Rs 6.50 a
  kilogram of fabric. It is the coefficient I most want replaced by a quote.
- The cluster figure is a projection, not achieved impact.
- The financial projections in section 9 are plans with stated assumptions. The pilot costs are built from quoted supplier and lab prices. The revenue figures rest on a modelled per-lot saving that no instrument has confirmed, and I have priced the projection at about half of the re-ordering share for that reason. The 5,000 lots a year is derived from audited fuel use, not measured at a site.
- The shared-evaporator solver checks every combination, which will not scale to
  a treatment plant with hundreds of members.
- The 60,000 mg/L limit is one modelled figure inside a published range of
  15,000 to 80,000. Whether it holds in real running conditions is unknown.
- The rupee and carbon conversions assume a coal-fired boiler. Tiruppur units
  mostly burn wood, so both need re-deriving per site. The physics does not
  depend on the fuel; the size of every switching price does.
- The data centre and cooling tower idea is an argument from structure, not a
  result.
- There is no trained model in this system and I do not call it AI-powered. The
  decision record is a hash chain, not a blockchain.

### Sources

| Figure | Where it comes from |
|---|---|
| Tirupur exports of about Rs 46,000 crore in FY26 (April 2025 to March 2026) | Tiruppur Exporters Association, as reported in trade press |
| Over 54% of India's knitwear exports; 2011 closure of over 700 units and plants, 40,000 to 50,000 jobs, about Rs 50 crore a day; 360 units, 60 with their own plants, 18 CETPs; 130 million litres a day treated, 92% recovered; over 1,00,000 tonnes of mixed waste salt in sheds; around Rs 30 crore a month on CETP electricity | Economic Times, 25 June 2025, quoting the Dyers Association of Tiruppur |
| Salt backlog of about 60,000 tonnes in 2022, for comparison | Dyers Association of Tiruppur, reported by Ecotextile News, October 2022 |
| EU carbon border mechanism covers iron and steel, cement, aluminium, fertilisers, electricity and hydrogen, not textiles | European Commission scope; textiles named as a candidate for a later phase |
| Indian ZLD market of about USD 1.33 billion in 2025, USD 2.52 billion by 2032 | MarkNtel Advisors, India Zero Liquid Discharge Market report. A commercial estimate, cited as such |
| Archroma Avitera SE reactive dye range, reported to cut water and energy in dyeing by about half | Ecotextile News, January 2024 |
| Praj on Tirupur textile effluent; VA Tech Wabag on evaporator-based ZLD | Company and trade press reporting |
| Tiruppur dyeing units burn about 2,000 tonnes of solid fuel a year each, primarily wood | Energy audits of more than sixty dyeing MSMEs in Tiruppur, 2024 to early 2025, reported by India Development Review |
| About 15% of fuel consumption available from simple efficiency measures, with adoption still low | The same energy audits of more than sixty Tiruppur dyeing MSMEs, 2024 to early 2025 |
| Water strength of 18,340 mg/L, leftover at 20-30%, evaporator steam use | Central Pollution Control Board assessment of textile dyeing units and ZLD at Tirupur |
| Grid emissions, 0.705 kg CO2 per kWh | CO2 Baseline Database for the Indian Power Sector, Central Electricity Authority |
| Carbon price of 82.40 euro a tonne, 5 October 2026 | European carbon prices, S&P Global Commodity Insights |
| Fresh water at Rs 45 a kilolitre | Reported price of Bhavani river water supplied to Tirupur dyeing units |
| CETP treatment charge of Rs 185 a kilolitre | Midpoint of the Rs 150 to 220 charged by Tirupur CETPs, Tamil Nadu pollution board plant-level data |
| Steam at Rs 2.03 a kWh of heat | Derived from published imported coal pricing at 78% boiler efficiency |
| Electricity tariff | Tamil Nadu Electricity Regulatory Commission tariff order, March 2025 |
| Low-salt dye premium of Rs 6.50 a kg of fabric | My assumption, sized against dye cost, labelled ASSUMED in the registry |
| Seasoned wood at about 15.5 MJ a kilogram | FAO, comparison of energy values for fuelwood at 20% moisture |
| Latent heat, 0.62694 kWh/kg | Steam tables: 2,257 kJ/kg at 100 C and one atmosphere, divided by 3,600 |
| Evaporator energy band, 150-250 kWh/m3 | EU Best Available Techniques reference document for textiles. Used as a check, never as an input |
