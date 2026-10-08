# ChangeLoop — video script

**What you do:** screen-record the running website and read this out.

There are **two complete versions** below. Pick one *before* you record:

| Version | Runs | Use it when |
|---|---|---|
| **A — Full** | **~6:12** | the limit allows 6 minutes |
| **B — Short** | **~3:27** | the limit is 3:30 or less |

Both tell the same story in the same order. B is A with shorter sentences —
you never have to cut anything yourself mid-recording.

Everything in a **grey box is what you say.** Everything in **bold outside a
box is what you click.** Lines starting **Need:** are not spoken — they remind
you *why* each step exists, so you can answer if a judge asks.

---

## What the jury must leave knowing

| They must understand | Where it lands |
|---|---|
| **Why this matters** — real people, real harm | Section 1: the river |
| **Where the cost really comes from** | Section 2: filters → salty leftover → boiling → coal |
| **Who has the pain, and why nobody fixes it** | Section 3: decided in one place, paid in another |
| **What is new** | Section 4: the coal is set by salt, not water |
| **That it works, step by step** | Sections 6–10: each step names the pain it removes |
| **That you are honest** | Section 10: zero measured, said by you first |

---

## The thread that holds it together

**Salt is in every part of this video.** If you understand this chain, the
script will feel natural instead of memorised:

```
salt poisoned the farmers' groundwater
   |   so the court said: release nothing
filters clean most of the water — but they cannot get rid of salt
   |   they only squeeze it into less and less water
a small amount of extremely salty water is left, and cannot be poured away
   |   so it is boiled until only dry salt remains
boiling needs steam, and steam comes from a coal boiler
   |
the salt that once poisoned the river now burns coal
   |
every dyehouse pays for that coal — but the amount is decided each morning,
by a planner who never sees the bill
   |
ChangeLoop puts the bill in front of the planner, before the choice is made
```

---

## Set up before recording

```bash
cd changeloop
python backend/server.py
```

Open `http://localhost:8000`

- Click **Reset**
- **Binding constraint** → **Normal operation**
- Full screen (F11), zoom 100%, close every other tab
- Put this script on a second screen or your phone

**Record on your own computer, not the Render link.** Render sleeps and takes
50 seconds to wake.

**The flow picture does not move at the start.** That is correct. It starts
moving when you click **Accept**.

**Speak slowly.** The pauses are doing work.

---
---

# VERSION A — FULL  (~6:12)

---

## A1. The river  (0:00 – 0:48)
*On screen: the Command page. Do not touch the mouse. Let them look.*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Not an NGO. Farmers.
>
> Their river is the Noyyal. Upstream is Tirupur — India's knitwear capital.
>
> To dye cotton you need two things: colour, and a lot of salt. The salt
> pushes the dye into the fibre. For years, both went into that river.

*(pause)*

> You could see the colour. You could not see the salt — and salt stays.
>
> The groundwater turned salty. Wells that had fed that land for generations
> became useless.

*(pause)*

> In 2006 the court ordered zero discharge. Release nothing.
>
> The industry did not. So in 2011, the court shut down seven hundred dyeing
> units.

---

## A2. What "release nothing" really costs  (0:48 – 1:39)
> Tirupur rebuilt. Today it recycles about a hundred and thirty million litres
> of water every day. It worked.
>
> But what does "release nothing" really mean?

*(slow down — this is the step everything rests on)*

> The dirty water goes through filters. Most of it comes out clean and goes
> back into the factory. That part is easy.
>
> But filters do not get rid of salt. They only squeeze it into less and less
> water.
>
> So at the end you are holding a small amount of extremely salty water — and
> you are not allowed to pour it anywhere.
>
> So you boil it, until only dry salt is left.
>
> Boiling needs steam. Steam comes from a coal boiler.

*(pause — the hinge of the whole video)*

> The salt that once poisoned the river now burns coal.

---

## A3. Who pays — and why nobody has fixed it  (1:39 – 2:23)
> Who pays for that coal? Every dyehouse.
>
> The treatment plant charges them about a hundred and eighty-five rupees for
> every kilolitre. River water costs forty-five. Recycled water costs four
> times as much as fresh.

*(pause)*

> So why has nobody fixed it?
>
> Because the cost is decided in one place and paid in another.
>
> Every morning, a planner chooses which batches to run, and how to dye them.
> That choice decides how much salt goes into the water.
>
> But the bill arrives weeks later, at the treatment plant. Nobody connects
> the two.
>
> And the tools that exist today measure water. So every project tries to
> save water.

---

## A4. The thing everyone gets backwards  (2:23 – 2:48)
*Move the mouse to the band at the top. Read the big sentence:*

> In a zero discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath. Not by how much water comes out.

*Explain:*

> The filters can only make that leftover water so salty before they clog. So
> the amount you have to boil depends on the salt.
>
> Use more water with the same salt — and you still boil the same amount.

---

## A5. The proof  (2:48 – 3:01)
*Point at the four numbers on the right of the band.*

> Cut the water by twenty percent. The energy changes by zero point zero
> percent.
>
> Cut the salt by twenty percent. It drops by twenty.
>
> Water is only the carrier. Salt is the load.

---

## A6. Step one — a better plan, every morning  (3:01 – 3:36)
**Need:** the planner makes the salt decision, so the tool must work at the planner's desk.

**Click Run optimiser.** Then **Decisions**.

> So ChangeLoop works where the decision is actually made — the planner's
> morning. The order of the batches, and how each is dyed, decide the salt.
>
> It checks four hundred and eighty possible plans, and recommends Option B.

*Move the mouse to Option C. Slow down.*

> Now look at Option C. It saves almost half the fresh water — the best water
> number on the screen.
>
> And ChangeLoop refuses it. Because it misses a customer's delivery date by
> two point six hours.
>
> No factory will use a tool that loses it a customer.

---

## A7. Step two — a person decides  (3:36 – 3:47)
**Need:** no factory will hand control to software.

**Click Accept.** *The flow picture starts moving — point at it.*

> No factory hands control to software. So a named person approves, and it
> is recorded.
>
> Reject it, and the saving counts as zero.

---

## A8. Step three — knowing when washing is finished  (3:47 – 4:24)
**Need:** fixed-time washing wastes water, steam and salt — but stopping early ruins the batch.

**Click Water.** Scroll to **Inject a fault**.

> Most dyehouses wash for a fixed time, to be safe. Every wash after the cloth
> is already clean wastes water, steam and salt.
>
> But stop too early, and the colour bleeds and the batch is ruined.
>
> So ChangeLoop reads the sensors, and tells you when it is safe to stop.

**Click Calibration drift.** **Click Attempt release.**

> And when a sensor cannot be trusted — refused. At the gate, and again at the
> server. It can never release by itself.

*Stay silent for two seconds.*

**Click No fault.** Then **Grant release.**

---

## A9. Step four — a warning before the limit  (4:24 – 4:51)
**Need:** every factory has a daily water allowance and needs to know *before* it breaks it.

**Click Forecast.**

> Every factory has a daily water allowance. It needs a warning before it
> crosses it — not after.
>
> Doing nothing: a hundred and thirty-two percent of the allowance.
>
> Reusing the rinse water — the obvious fix, the one everyone pays for: a
> hundred and thirty-two percent.

*(pause)*

> The same. Only the low salt chemistry brings it inside, at eighty-two.

---

## A10. Step five — numbers that stand up  (4:51 – 5:22)
**Need:** under a court order, every number must survive an audit.

**Click Evidence.**

> Under a court order, every number has to stand up. So I will say this
> first: nothing here is measured.
>
> Seventeen numbers are published, four calculated, four assumed, zero
> measured.
>
> But the model can still be tested. The Pollution Control Board measured
> eighteen thousand three hundred and forty milligrams per litre at a real
> Tirupur unit. My model predicts thirty point six percent reject — inside the
> twenty to thirty percent that real plants report.

---

## A11. What it means — and the close  (5:22 – 6:12)
**Click Impact.**

> On one machine, in one shift, the model shows about ten thousand rupees of
> cost avoided — with every delivery still on time.
>
> And a dyehouse runs many machines. Every shift. Every day.

*(pause)*

> Right now, every dyehouse pays for its salt twice. Once to buy it. And once
> to boil it back out.

*(pause — slow down for the last four lines)*

> The farmers of the Noyyal proved that salt has a cost. The court made the
> industry pay it.
>
> But nobody ever showed the industry where that cost is decided.
>
> It is decided every morning, by a planner choosing what to run first.
>
> That is the choice we change.

*Stop. Hold still for three seconds. Then end the recording.*

---
---

# VERSION B — SHORT  (~3:27)

Same order, same clicks, shorter sentences. Read this one straight through if
your limit is 3:30. It runs about 3:27 at a calm pace — so speak at your normal
speed between the marked pauses, and do not stretch them.

---

**B1. The river** — *Command page, mouse still*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Their river, the Noyyal, runs below Tirupur — India's knitwear capital.
> Dyeing cotton needs colour and a lot of salt, and for years both went into
> that river. The groundwater turned salty. The wells died.
>
> In 2011 the court shut down seven hundred dyeing units, and ordered zero
> discharge: release nothing.

**B2. The real cost**

> Tirupur rebuilt, and now recycles a hundred and thirty million litres a day.
>
> But filters do not get rid of salt. They squeeze it into less and less
> water, until you hold a small amount of very salty water you cannot pour
> away. So you boil it dry. Boiling needs steam. Steam comes from coal.
>
> The salt that poisoned the river now burns coal.

**B3. The pain**

> Every dyehouse pays for that coal — a hundred and eighty-five rupees a
> kilolitre, four times the price of fresh water.
>
> And nobody fixes it, because the cost is decided each morning by a planner
> choosing which batches to run — but the bill arrives weeks later, somewhere
> else.

**B4. The insight** — *read the big sentence*

> In a zero discharge dyehouse, the coal bill is set by how much salt goes into
> the dye bath. Not by how much water comes out.

**B5. The proof** — *point at the numbers*

> Cut water twenty percent: energy changes zero point zero. Cut salt twenty
> percent: it drops twenty. Water is the carrier. Salt is the load.

**B6. Step one** — **Run optimiser → Decisions**

> So ChangeLoop works at the planner's desk. Four hundred and eighty plans
> checked. Option C saves the most water — and it is refused, because it
> misses a delivery by two point six hours. No factory uses a tool that loses
> it a customer.

**B7. Step two** — **Accept**

> A named person approves, and it is recorded.

**B8. Step three** — **Water → Calibration drift → Attempt release**

> Washing for a fixed time wastes water; stopping early ruins the batch. So it
> reads the sensors — and when a sensor cannot be trusted, release is refused.
> It never releases by itself.

**No fault → Grant release.**

**B9. Step four** — **Forecast**

> Against the daily water limit: doing nothing, a hundred and thirty-two
> percent. Reusing rinse water, the obvious fix — a hundred and thirty-two.
> The same. Only low salt chemistry brings it under, at eighty-two.

**B10. Step five** — **Evidence**

> Nothing here is measured — I say that first. But the Pollution Control Board
> measured a real Tirupur unit, and my model predicts what real plants report.

**B11. Close** — **Impact**

> On one machine, in one shift, the model shows about ten thousand rupees
> avoided — every delivery still on time. And a dyehouse runs many machines,
> every shift, every day.
>
> Right now every dyehouse pays for its salt twice — once to buy it, and once
> to boil it back out.
>
> The farmers of the Noyyal proved that salt has a cost. But nobody showed the
> industry where that cost is decided.
>
> It is decided every morning, by a planner choosing what to run first.
>
> That is the choice we change.

*Hold still for three seconds. Then end the recording.*

---
---

## Numbers to get right

Keep this open in another window. Every one is checked against the running
engine.

| Where | Number |
|---|---|
| Units shut in 2011 | **700** |
| Recycled today | **130 million litres a day** |
| Treatment charge | **₹185 per kilolitre** |
| River water | **₹45 per kilolitre** |
| Recycled vs fresh | **about 4×** |
| Cut water 20% → energy | **0.0%** |
| Cut salt 20% → energy | **−20.0%** |
| Plans checked | **480** |
| Option C late by | **2.6 hours** |
| Do nothing | **132.3%** |
| Reuse rinse water | **132.3%** |
| Low salt chemistry | **82.1%** |
| Evidence | **17 / 4 / 4 / 0** |
| CPCB measured | **18,340 mg/L** |
| Model predicts | **30.6%** |
| Published band | **20–30%** |
| Cost avoided, one machine, one shift | **about ₹10,000** (screen shows ₹10,171) |

**If the screen shows something different, the screen is correct.**

---

## If a judge asks about the market

Short answers, in your own words. All of these are true and sourced.

**Who is the customer?**
The dyehouse owner. They pay the treatment plant for every kilolitre of
effluent, and that charge is driven by the salt they send.

**Who would sell it?**
The common effluent treatment plant. Every kilo of salt its members do not
send is steam it does not have to buy. Its incentive already points the same
way as ours.

**How big is it?**
Tirupur alone has hundreds of dyeing units under the same court order. CPCB
guidance extends zero discharge to textiles, tanneries, distilleries, and pulp
and paper across India.

**Why will they pay?**
Because the saving lands on a bill they already receive every month. We are
not asking anyone to care about the environment — we are lowering the cost of
a rule they already have to follow.

**"Pays for its salt twice" — is that true?**
Yes. The dyehouse buys electrolyte by the kilo for the dye bath, and then pays
the treatment plant to boil that same salt back out of the water. Both costs
are in the model on separate lines, and the model never adds them together
into the water figure.

**Why say "many machines" instead of a bigger number?**
Because a total for the whole cluster would be a projection from one modelled
machine, and the system labels it as one. Saying "many machines, every shift,
every day" is true without claiming a figure we have not measured.

**What is the weakness?**
We have not yet measured a real site. One visit, two instrument readings —
steam flow to the evaporator and the saltiness of the leftover water — turns
this from a checked model into a measured one. That is the first thing we
would do with support.

---

## Words to avoid

| Do not say | Say instead |
|---|---|
| "AI", "machine learning" | "a search that checks every option" |
| "blockchain" | "a tamper-evident record" |
| "we saved", "our result" | "the model shows" |
| "we measured" | "we checked it against published plant data" |
| any jobs figure for 2011 | "tens of thousands" — estimates differ tenfold |

---

## If something goes wrong

- Small mistake — keep going. Calm recovery beats a visible cut.
- Wrong page — go back and say "let me show you that properly".
- Wrong state — click **Reset**, restart from Command.
- Flow not moving — correct before **Accept**.
- A number looks odd — say what is on screen.

---

## The five moments that must survive

Whichever version you use, never lose these. Without them there is no
argument:

1. **"The salt that once poisoned the river now burns coal."** The hinge.
2. **"Zero point zero percent."** The insight.
3. **Option C refused, and why.** The proof you are not chasing one number.
4. **The gate refusing your own release.** A system that says no to its
   operator — on camera.
5. **"Pays for its salt twice — once to buy it, once to boil it out."** The
   line the jury will repeat afterwards.

---

## Sources, if a judge asks

| Claim | From |
|---|---|
| Farmers went to court, 2003 | Down To Earth |
| Court ordered ZLD, 2006 | Madras High Court |
| ~700 units shut, 2011 | Down To Earth; Ecotextile |
| Supreme Court upheld Polluter Pays | *Tirupur Dyeing Factory Owners Assn v. Noyyal River Ayacutdars Protection Assn*, 2009 |
| 130 million L/day today | The Better India; CETP operator data |
| ₹150–220/kL treatment charge (we use ₹185) | Tamil Nadu Pollution Control Board plant data |
| ₹45/kL river water | Down To Earth, Bhavani supply to Tirupur |
| 18,340 mg/L inlet; reject 20–30% of inlet | CPCB Tirupur ZLD assessment |

Full register: [`docs/data_sources.md`](../docs/data_sources.md)

---

## One last thing

The jury will see hundreds of projects that say "we save water." Yours is the
one that explains why saving water does not save the money — and then shows,
step by step, who pays, why nobody has fixed it, and how the fix fits into a
planner's morning without ever risking a delivery.

Do not rush the first two minutes to reach the software. The story is what
makes the software matter.
