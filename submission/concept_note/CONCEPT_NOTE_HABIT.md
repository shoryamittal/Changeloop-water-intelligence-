# ChangeLoop

## 1. Title page

| | |
|---|---|
| **Startup name** | ChangeLoop |
| **Tagline** | In a closed loop, salt sets the coal bill. |
| **Date** | 9 October 2026 |
| **Prepared by** | Shorya Mittal, founder |
| **Contact** | *[email and phone to be filled in before submission]* |
| **Working prototype** | https://changeloop-water-intelligence.onrender.com |

---

## 2. Background and problem statement

### Context

Tirupur in Tamil Nadu is India's knitwear capital. In the year to March 2026 it
exported around Rs 46,000 crore of knitwear, more than half of everything India
sells abroad in cotton knitwear. Its dyeing factories sit on the Noyyal river.

In 2011 the Madras High Court shut around 700 dyeing and bleaching units for
putting salty waste water into the river. They were allowed back only if they
stopped releasing liquid waste completely. The rule is called zero liquid
discharge, or ZLD.

Today about 300 dyeing units run on 18 shared treatment plants, and another 60
have their own. Between them they recycle about 120 million litres of water a
day and recover around 94% of it.

It worked for the river. The waste water stopped going in. But the problem
moved to the boiler house, and nobody is managing it.

### The problem

To recycle the water, a factory has to boil the leftover salty stream until
only dry salt is left. Boiling needs heat, the heat comes from steam, and in
Tirupur the steam mostly comes from coal. Boiling one cubic metre of leftover
takes about 188 kWh of heat.

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
things to the coal bill. Most water-saving work in the cluster aims at the
water. It does not touch the coal.

### Why it has not been fixed

The salt load is decided by a production planner, choosing which dye lots run
in what order and which rinse method to use. They make that call hours before
anything shows up anywhere.

The coal bill arrives weeks later, in a different department's budget, with no
way to trace it back to the choice that caused it. The planner is not being
careless. They are working without the one number that would change their mind.

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
| **Factory owners** | They pay a coal bill they cannot trace or control |
| **The 18 shared treatment plants** | They buy the steam and store the salt. Over one lakh tonnes of recovered salt is sitting in India's textile ZLD plants with nowhere to send it |
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

### What ChangeLoop is

ChangeLoop is a decision-support tool that sits where the dyehouse schedule
gets made. Before a shift starts it looks at the different orders the planner
could run the lots in, and the different rinse methods available. For each
combination it works out the whole chain: water used, salt load, leftover
volume, evaporator steam, CO2, rupees, and whether any delivery date is missed.

Then it recommends one plan, and shows its working.

### What makes it different

**It optimises for the consequence, not for the throughput.** Existing dyehouse
software plans for machine use and delivery dates. ChangeLoop adds the
downstream thermal cost of the schedule, which is the part nobody currently
prices.

**A late delivery is not treated as a trade-off.** If a plan misses a ship
date, it gets removed from the search rather than given a bad score. A factory
cannot accept a schedule that saves water by shipping late, so the tool never
offers one.

**Every input number says where it came from.** All 25 of them are tagged as
published, derived, assumed or measured, with the source and the arithmetic.
Anyone can open the list in the running system and read it.

**It fails safe.** It issues no machine settings and cannot release a dye bath.
Early release needs a named person to approve it. If a sensor reading is
missing or implausible, the system stops and claims zero saving rather than
guessing.

**It only counts savings somebody approved.** If the planner turns a
recommendation down, it counts as zero, even though the tool already worked out
what it would have saved.

**It handles the shared evaporator.** It compares what each machine would pick
on its own against the cheapest combination that actually fits the plant, and
prices the difference.

### Value proposition

For a factory owner: lower coal and water bills from a scheduling change, with
no equipment to buy and no change to the existing approval process.

For a planner: the number that is missing from their screen, at the moment they
need it.

For a shared treatment plant: less salt arriving, which means less steam to buy
and less solid salt to store.

For a regulator: a tool that quantifies what a price change would actually do,
instead of arguing for one in principle.

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

| Objective | Target |
|---|---|
| Reach the cluster through shared treatment plants | 40 paying units across 2 to 3 CETPs by year 3 |
| Make the big saving the default | Low-salt chemistry adopted where the measured case supports it, worth about 47% of water and steam per shift |
| Solve the cluster coordination problem | A method that works for hundreds of member units, not just the 256 combinations the current solver checks |
| Prove the pricing argument | Published, independently reviewed evidence of what carbon or water pricing would change in this sector |
| Extend beyond textiles | One validated application in another closed-loop system, such as evaporative cooling |

---

## 6. Business model

### How it makes money

An annual software subscription per dyeing unit, sold mainly through the shared
treatment plants rather than factory by factory.

| Item | Amount | Notes |
|---|---|---|
| Annual subscription | Rs 2,40,000 per unit | Covers the machines in scope, typically four |
| One-off setup | Rs 4,50,000 per unit | Connecting to the planning system and the effluent meters, plus training |

### Why a factory would pay that

Using today's tariffs and the plan the tool actually recommends right now, for
a unit running 9,000 lots a year:

| | Plan it recommends today | Low-salt plan, once the price gap closes |
|---|---|---|
| Gross saving a year | Rs 4,08,000 | Rs 52,04,000 |
| Less subscription | Rs 2,40,000 | Rs 2,40,000 |
| Net benefit a year | **Rs 1,68,000** | **Rs 49,64,000** |
| Payback on setup | 2.7 years | about 5 weeks |
| Return on cost | 37% | 1,103% |

I am showing both columns on purpose. The left column is what a factory gets
today, and it is a modest, believable return. The right column is what the same
factory gets if the low-salt dye premium falls about 12%, which is the gap my
system measured. The upside is real, but it is not what I would ask anyone to
sign for.

### How customers are reached

**Through the shared treatment plants.** Tirupur has 18 of them serving about
300 units. One commercial relationship reaches roughly 17 factories, which cuts
the cost of selling by an order of magnitude compared with knocking on doors.

The treatment plants also want this for their own reasons. Less salt arriving
means less steam bought and less salt stored. That makes them a partner rather
than just a channel.

**Through running silently first.** Four weeks of being right while changing
nothing is how a tool earns the right to influence a factory's decisions. It
costs the factory nothing.

**Through trade bodies.** The Tiruppur Exporters Association and the dyers'
associations already coordinate on environmental compliance, which is the exact
context this belongs in.

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
| Tirupur, immediate | About 360 dyeing units. At Rs 2,40,000 a year that is roughly **Rs 8.6 crore a year** | 300 units on 18 CETPs plus 60 with their own plants |
| Indian textile ZLD, wider | Tirupur is one of several clusters under ZLD rules. Surat, Erode, Karur, Ludhiana, Panipat and Jetpur have similar processing bases | Directional. I have not counted units outside Tirupur and I am not going to present a number I cannot source |
| Adjacent closed loops, later | Evaporative cooling, boiler blowdown and mine water share the same physics | Unvalidated. Listed as direction, not as market |

The growth driver is regulation that already exists. ZLD is compulsory and
already paid for. ChangeLoop does not ask anyone to install new equipment, it
makes equipment they already own cheaper to run.

The second driver is carbon. European buyers are beginning to ask Indian
suppliers for emissions data, and the border carbon mechanism puts a price on
embedded emissions. A tool that can show measured, traceable reductions in
process emissions becomes a compliance asset, not just a cost saver.

### Competitive landscape

| Who | What they do | Why ChangeLoop is different |
|---|---|---|
| **Dyehouse software**, such as SedoMaster and Datatex | Plan production, manage recipes, track batches | They schedule for throughput and delivery. Neither prices the downstream thermal cost of the schedule, which is the whole point here |
| **ZLD equipment companies**, such as Praj, Thermax, VA Tech Wabag | Build and run the membranes and evaporators | They sell the plant. They do not touch the upstream decision that sets how hard the plant has to work |
| **Water monitoring and IoT dashboards** | Report flows and quality after the fact | They measure water volume, which the table in section 2 shows is the wrong number for the coal bill |
| **Low-salt dye suppliers**, such as DyStar and Archroma | Sell the chemistry that cuts salt | They sell the lever. They cannot tell a factory when it pays, which is exactly what my system computes |
| **Consultancies and energy audits** | One-off studies | A report is read once. This runs every shift and is checked against what was actually approved |

The honest summary: the pieces exist. The membranes exist, the chemistry
exists, the planning software exists. What does not exist is anything that
connects the upstream scheduling decision to the downstream coal bill, which is
where the saving is hiding.

---

## 8. Implementation plan

### Current status

The prototype is built and running. It is a live system anyone can open, not a
mockup.

| | |
|---|---|
| API | 34 endpoints. Every saving is worked out on the server, so the browser cannot claim one |
| Tests | 178, covering the physics, the safety rules, concurrency and the interface |
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

| Milestone | When |
|---|---|
| First pilot site signed | Month 1 |
| First measured coefficient, replacing a published one | Month 2 |
| First saving measured with a confidence interval | Month 6 |
| First paying customer beyond the pilot | Month 10 |
| Cluster coordination working across one CETP | Month 18 |
| 40 paying units | Month 36 |

---

## 9. Financial overview

All figures in this section are plans, not results. I have no revenue and no
customers today.

### What the first year needs

| Item | Amount | What it buys |
|---|---|---|
| Instruments for two pilot sites | Rs 6,00,000 | Steam flow meters and conductivity probes, plus installation and calibration |
| Site integration and engineering | Rs 5,00,000 | Connecting to planning systems and effluent meters at two sites |
| Independent lab testing | Rs 2,00,000 | Colour-fastness testing on every early-released lot |
| Founder stipend, 12 months | Rs 6,00,000 | Full-time work on the pilot |
| Cloud, tooling and travel | Rs 2,00,000 | Hosting, site visits, instrument servicing |
| Contingency | Rs 2,00,000 | About 10% |
| **Total** | **Rs 23,00,000** | |

### Funding requirement

I am seeking **Rs 23,00,000** as grant or seed funding for a 12-month pilot
programme across two to three dyeing units in Tirupur.

The largest single line is instrumentation, and that is deliberate. The
weakness of this project today is that nothing has been measured. Two
instruments at one site turn the two heaviest numbers in the model from
published figures into measured ones, and nothing else buys as much credibility
for as little money.

### Revenue projections

These assume the pilot succeeds and the shared treatment plant channel works.
Both are assumptions.

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Paying units | 2 at pilot rate | 12 | 40 |
| Subscription revenue | Rs 3,00,000 | Rs 28,80,000 | Rs 96,00,000 |
| Setup revenue | included in pilot | Rs 45,00,000 | Rs 1,26,00,000 |
| **Total revenue** | **Rs 3,00,000** | **Rs 73,80,000** | **Rs 2,22,00,000** |

Year 1 is a pilot year and is not meant to make money. Years 2 and 3 assume one
CETP relationship in year 2 and two or three by year 3, at about 17 member
units each.

---

## 10. Impact assessment

### If one factory adopts it

Per shift, on the plan the tool recommends under today's prices, against a
conventional single-stage rinse:

| | Fresh water | Evaporator steam | Cost |
|---|---|---|---|
| Baseline | 11,907 L | 2,239 kWh | Rs 33,897 |
| Recommended today | 11,187 L (-6%) | 2,104 kWh (-6%) | Rs 26,038 |
| Available with low-salt chemistry | 6,369 L (-47%) | 1,198 kWh (-47%) | Rs 29,984 |

### If the cluster adopts it

A straight-line projection across 400 units at 900 lots each a year. This is a
projection and my system labels it as one. It assumes every factory resembles
the modelled one and that every recommendation is approved. Neither has been
tested, and it must not be read as achieved impact.

| Saved per year across the cluster | |
|---|---|
| Fresh water | 75 million litres |
| Salt | 4,500 tonnes |
| Evaporator steam | 14,106 MWh |
| CO2 | 6,376 tonnes |

### Environmental benefit

Less groundwater pulled out of a basin that is already stressed. Less coal
burned for the same output. Less solid salt added to the one lakh tonnes
already stockpiled with no disposal route.

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

That is a finding a regulator can act on, and it came out of the engine rather
than out of an opinion.

---

## 11. Conclusion

ZLD saved the Noyyal river and left the cluster with a coal bill nobody is
managing. That bill is set by salt, not water, so most of the water-saving work
in Tirupur is aimed at the wrong number. ChangeLoop shows the planner what
their choice actually costs, at the moment they make it.

The prototype is built, running and open to inspection. The physics is checked
against published plant measurements. The business case pays back in under
three years on the conservative plan, and in weeks if a small price gap closes.
The route to the cluster runs through 18 shared treatment plants whose own
economics already point the same way.

What it does not have is a single measured number from a real factory, and I
would rather say that plainly than let a reviewer discover it. That is exactly
what the funding is for.

### What I am asking for

- **Rs 23,00,000** for a 12-month pilot across two to three Tirupur dyeing units
- **An introduction to a shared treatment plant** willing to host the pilot
- **Technical review** of the model by someone who knows textile effluent

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
- The cluster figure is a projection, not achieved impact.
- The financial projections in section 9 are plans with stated assumptions.
- The shared-evaporator solver checks every combination, which will not scale to
  a treatment plant with hundreds of members.
- The 60,000 mg/L limit is one modelled figure inside a published range of
  15,000 to 80,000. Whether it holds in real running conditions is unknown.
- The data centre and cooling tower idea is an argument from structure, not a
  result.
- There is no trained model in this system and I do not call it AI-powered. The
  decision record is a hash chain, not a blockchain.

### Sources

| Figure | Where it comes from |
|---|---|
| Tirupur exports of about Rs 46,000 crore in FY26 | Tiruppur Exporters Association, reported March 2026 |
| 300 dyeing units on 18 CETPs, 60 with their own plants, 120 MLD recycled, 94% recovery | Reported cluster data, 2026 |
| 2011 closure of around 700 units | Madras High Court order, widely reported |
| Water strength of 18,340 mg/L, leftover at 20-30%, evaporator steam use | Central Pollution Control Board assessment of textile dyeing units and ZLD at Tirupur |
| Grid emissions, 0.705 kg CO2 per kWh | CO2 Baseline Database for the Indian Power Sector, Central Electricity Authority |
| Carbon price of 82.40 euro a tonne, 5 October 2026 | European carbon prices, S&P Global Commodity Insights |
| Water and steam tariffs | Tamil Nadu Electricity Regulatory Commission tariff orders and state pollution board plant data |
| Latent heat, 0.62694 kWh/kg | Steam tables: 2,257 kJ/kg at 100 C and one atmosphere, divided by 3,600 |
| Evaporator energy band, 150-250 kWh/m3 | EU Best Available Techniques reference document for textiles. Used as a check, never as an input |
