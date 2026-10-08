# ChangeLoop — video script

**What you do:** screen-record the running website and read this out.

Two complete versions, for two different moments:

| Version | Runs | Use it for |
|---|---|---|
| **B — Video** | **~3:24** | **the submission video. Record this one.** |
| **A — Live pitch** | **~8:30** | if you are shortlisted and present live to the jury — the full story, with every reason spelled out |

B tells the same story as A, in the same order, with the same clicks — just
shorter. Learn B for the video now. Read A before any live round: it is the
version you will be speaking from when a judge says "tell us more".


Everything in a **grey box is what you say.** Everything in **bold outside a
box is what you click.** Lines starting **Need:** are not spoken — they remind
you why each step exists, so you can answer if a judge asks.

---

## What the jury must think, in order

By the end of each part, the jury should be thinking one sentence:

| Part | What the jury should be thinking |
|---|---|
| The river | *"Real people were harmed by this."* |
| Today | *"This is a big problem — and it is still getting worse."* |
| One morning | *"I can see exactly how it happens, every single day."* |
| Why nobody fixes it | *"Nobody is even looking in the right place."* |
| Why it cannot wait | *"This has to be solved."* |
| The insight | *"I did not know that. Nobody told me that."* |
| Steps 1–5 | *"He has actually solved it — and I can see how."* |
| The ending | *"This is the right answer."* |

**Salt is the thread through all of it:**

```
salt poisoned the farmers' wells
   → the court said: release nothing
filters clean the water — but cannot get rid of salt
   → so it is boiled out, and boiling burns coal
and then the salt is still there — over a lakh tonnes, in sheds, with nowhere to go
   → everyone is trying to get rid of it at the end
but the amount is decided at the start — at six in the morning, by one planner
   → ChangeLoop works at that desk
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

# VERSION A — LIVE PITCH  (~8:30)

---

## A1. The river

*On screen: the Command page. Do not touch the mouse. Let them look.*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Not an NGO. Farmers.
>
> Their river is the Noyyal. Upstream is Tirupur — the town that makes more
> than half of India's knitwear exports.
>
> To dye cotton you need two things: colour, and a lot of salt. The salt
> pushes the dye into the fibre. For years, both went into that river.

*(pause)*

> You could see the colour. You could not see the salt — and salt stays.
>
> The groundwater turned salty. Wells that had fed that land for generations
> became useless.
>
> In 2011, the court shut down seven hundred dyeing units, and gave one order.
> Release nothing.

---

## A2. Today — the coal, and the mountain

> Tirupur rebuilt. Four hundred and fifty dyeing units spent over a thousand
> crore rupees on shared treatment plants. Today they recycle a hundred and
> thirty million litres of water every day.
>
> It worked. The river is cleaner.

*(pause — slow down, this is the step everything rests on)*

> But filters do not get rid of salt. They only squeeze it into less and less
> water — until you are holding a small amount of extremely salty water that
> you are not allowed to pour anywhere.
>
> So you boil it, until only dry salt is left. Boiling needs steam. Steam
> comes from a coal boiler.
>
> The salt that once poisoned the river now burns coal.

*(pause)*

> And when the boiling is done — the salt is still there.
>
> Last year, the Dyers Association of Tiruppur said more than one lakh tonnes
> of it is sitting in sheds at the treatment plants. Three years earlier, it
> was fifty thousand. It has doubled.
>
> In their own words: "We don't have the technology for this salt, so we pile
> up huge amounts of salt."
>
> So every dyehouse pays for its salt twice. Once to buy it. And once to boil
> it back out. And then nobody knows where to put it.

---

## A3. One morning in one dyehouse

*Still on Command.*

> Here is how that happens, on an ordinary morning.
>
> It is six o'clock. Five orders came in overnight. Deep indigo. Pale mint.
> Dusty rose. Carbon black. And natural ecru — almost white.
>
> The planner runs them in the order they arrived.
>
> So after the carbon black, the machine has to be scrubbed clean before the
> ecru goes in — or the white cloth comes out grey. That one clean-out uses
> over seven thousand litres of water, and every litre carries salt to the
> treatment plant.
>
> The washing runs on a fixed timer, to be safe — even after the cloth is
> already clean.
>
> And by two in the afternoon, this one machine has used up its share of the
> factory's water allowance.

*(pause)*

> Nobody did anything wrong. They followed the system they were given.
>
> And this happens every morning, in every one of those four hundred and
> fifty units.

---

## A4. Why nobody has fixed it

> So why has nobody solved this? Three reasons.
>
> First — everyone is working at the end of the pipe. Better filters. Better
> boilers. Some way to get rid of the salt. The Dyers Association says that
> technology is "yet to evolve." Nobody is working on the start — on how much
> salt goes in.
>
> Second — the person who decides that is the planner, at six in the morning.
> And the planner never sees the bill. It arrives weeks later, at a shared
> plant, split across four hundred and fifty factories.
>
> Third — the tools that exist count water. And that is exactly what almost
> everyone gets backwards.

---

## A5. Why it cannot wait

> And this cannot wait.
>
> That salt cannot be released. There is nowhere to send it. And it grows by
> up to seventy tonnes, every single day.
>
> And the same rule — release nothing — now applies across India. To
> tanneries. To distilleries. To paper mills. Every one of them will meet the
> same salt, and the same coal.

---

## A6. The insight

*Move the mouse to the band at the top. Read the big sentence:*

> Here is what I found.
>
> In a zero discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath. Not by how much water comes out.

*Explain:*

> The filters can only make that leftover water so salty before they clog. So
> how much you boil depends on the salt. Use more water with the same salt —
> and you still boil the same amount.

*Point at the four numbers on the right of the band.*

> Cut the water by twenty percent: the energy changes by zero point zero
> percent.
>
> Cut the salt by twenty percent: it drops by twenty.
>
> Water is the carrier. Salt is the load. And this is ChangeLoop — the system
> I built to act on it. Let me show you, step by step, the same morning —
> fixed.

---

## A7. Step one — the six o'clock plan

**Need:** the salt is decided at the planner's desk, so the solution has to work there.

**Click Run optimiser.** Then **Decisions**.

> Step one. ChangeLoop starts where the problem starts — the planner's desk,
> at six in the morning.
>
> It takes those same five orders and checks four hundred and eighty ways to
> run them.
>
> Its answer: run the ecru first, while the machine is still clean. That one
> change removes the seven thousand litre clean-out.
>
> It cannot simply sort them light to dark — the indigo is due by ten. So it
> finds the order that saves the most and still keeps every deadline.

*Move the mouse to Option C. Slow down.*

> And look at Option C. It would save almost half the fresh water.
>
> ChangeLoop refuses it. It makes one order two point six hours late — and no
> factory will use a tool that loses it a customer.

---

## A8. Step two — the planner decides

**Need:** no factory will hand control of its machines to software.

**Click Accept.** *The flow picture starts moving — point at it.*

> Step two. Nothing happens until a person says yes. The planner approves, and
> it is recorded under their name.
>
> Reject it — and the saving counts as zero.

---

## A9. Step three — stop washing when it is actually clean

**Need:** a fixed timer wastes water and salt — but stopping too early ruins the batch.

**Click Water.** Scroll to **Inject a fault**.

> Step three — the washing. Instead of a fixed timer, ChangeLoop watches the
> sensors and tells the operator when the cloth is truly clean.
>
> But stop too early and the colour bleeds, and the whole batch is washed
> again. So the rule is strict.

**Click Calibration drift.** **Click Attempt release.**

> When a sensor cannot be trusted — refused. At the gate, and again at the
> server. It never releases a batch on its own.

*Stay silent for two seconds.*

**Click No fault.** Then **Grant release.**

---

## A10. Step four — no more surprise at two o'clock

**Need:** a factory must know it will break its water allowance *before* it happens.

**Click Forecast.**

> Step four — the two o'clock problem. ChangeLoop shows it at six in the
> morning, while there is still time to act.
>
> Doing nothing: a hundred and thirty-two percent of the allowance.
>
> Reusing the rinse water — the fix everyone pays for: still a hundred and
> thirty-two.

*(pause)*

> The same. Only cutting the salt brings it inside — at eighty-two.

---

## A11. Step five — numbers that hold up

**Need:** under a court order, every number must survive an audit.

**Click Evidence.**

> Step five. Under a court order, every number has to stand up. So I will say
> this first: nothing here is measured yet.
>
> Seventeen numbers come from published sources. Four are calculated. Four
> are assumed.
>
> But the model can be tested. The Pollution Control Board measured the salt
> in a real Tirupur unit's water. Fed that number, my model predicts thirty
> point six percent — inside the twenty to thirty percent real plants report.

---

## A12. The ending

**Click Impact.**

> On one machine, in one shift: sixty kilos less salt sent to the treatment
> plant. About ten thousand rupees. Every delivery on time.
>
> And a dyehouse runs many machines. Every shift. Every day.

*(pause)*

> Remember that shed. More than a lakh tonnes of salt — and the industry is
> still searching for a way to get rid of it.
>
> But every kilo in that shed started in a dye bath. Decided at six in the
> morning, by a planner who never saw the bill.

*(pause — slow down for the last three lines)*

> Getting rid of the salt is one answer.
>
> Not putting it in is a better one.
>
> That is the choice we change.

*Hold still for three seconds. Then end the recording.*

---
---

# VERSION B — VIDEO  (~3:43)

**This is the one to record.** Same story, same order, same clicks as A —
shorter sentences. Read it straight through, at your normal pace between the
marked pauses. The greeting adds about twenty seconds versus the old 3:24
cut — if your limit is a hard 3:30, drop B0 and start straight at B1.

---

**B0. The greeting** — *Command page, mouse still, before anything else*

> Good morning everyone. My name is Shorya Mittal, and I am going to show
> you something that surprised me while I was building this project.
>
> Before I explain how my system works, let me tell you why it needed to
> exist in the first place.

**B1. The river** — *same screen, continue*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Upstream of their river sits Tirupur, which makes more than half of India's
> knitwear exports. Dyeing cotton needs colour and a lot of salt — and for
> years both went into that river. The wells turned salty.
>
> In 2011 the court shut down seven hundred dyeing units, and ordered: release
> nothing.

**B2. Today**

> Tirupur rebuilt, and now recycles a hundred and thirty million litres a day.
>
> But filters do not get rid of salt. They squeeze it into less water, until
> it has to be boiled dry — with steam, from coal.
>
> And then the salt is still there. The Dyers Association says more than one
> lakh tonnes now sits in sheds — double what it was three years ago. In their
> words: "We don't have the technology for this salt."

**B3. One morning**

> On an ordinary morning, five orders arrive — from deep indigo to almost-white
> ecru. Run in the order they came, the machine must be scrubbed after carbon
> black before the ecru: seven thousand litres of cleaning. Washing runs on a
> fixed timer. By two in the afternoon, the machine is over its water limit —
> in every one of four hundred and fifty units.

**B4. Why nobody fixes it — and why it cannot wait**

> Nobody fixes this because everyone works at the end of the pipe. The planner
> who decides the salt never sees the bill. And today's tools count water.
>
> And it cannot wait: the salt grows by seventy tonnes a day, and the same rule
> now covers tanneries, distilleries and paper mills across India.

**B5. The insight** — *read the big sentence, then point at the numbers*

> Here is what I found. In a zero discharge dyehouse, the coal bill is set by
> how much salt goes into the dye bath. Not by how much water comes out.
>
> Cut water twenty percent: energy moves zero point zero. Cut salt twenty
> percent: it drops twenty. This is ChangeLoop. Step by step:

**B6. Step one** — **Run optimiser → Decisions**

> One: at the planner's desk, it checks four hundred and eighty plans — run the
> ecru first, while the machine is clean, and keep every deadline. Option C
> saves more water but makes an order late, so it is refused.

**B7. Step two** — **Accept**

> Two: a person approves, and it is recorded.

**B8. Step three** — **Water → Calibration drift → Attempt release**

> Three: washing stops when the sensors say the cloth is clean — and when a
> sensor cannot be trusted, release is refused.

**No fault → Grant release.**

**B9. Step four** — **Forecast**

> Four: the two o'clock problem is visible at six. Reusing rinse water: still
> a hundred and thirty-two percent. Only cutting salt brings it inside.

**B10. Step five** — **Evidence**

> Five: nothing here is measured yet — I say that first. But fed real plant
> data, the model predicts what real plants report.

**B11. The ending** — **Impact**

> One machine, one shift: sixty kilos less salt, about ten thousand rupees,
> every delivery on time.
>
> Every kilo in that shed started in a dye bath — decided at six in the
> morning, by a planner who never saw the bill.
>
> Getting rid of the salt is one answer. Not putting it in is a better one.
>
> That is the choice we change.

*Hold still for three seconds. Then end the recording.*

---
---

## Numbers to get right

Keep this open in another window.

| Where | Number | Source |
|---|---|---|
| Units shut in 2011 | **700** | Down To Earth; Economic Times |
| Tirupur's share of India's knitwear exports | **more than half** (54%) | Economic Times, June 2025 |
| Dyeing units / shared plants | **450 / 18** | Economic Times, June 2025 |
| Spent on treatment plants | **over ₹1,000 crore** (₹1,013 cr) | Economic Times, June 2025 |
| Recycled today | **130 million litres a day** | Economic Times, June 2025 |
| Salt piled in sheds, 2022 | **~50,000 tonnes** | DT Next, Oct 2022 |
| Salt piled in sheds, 2025 | **over 1 lakh tonnes** | Dyers Association, via Economic Times, June 2025 |
| Salt added per day | **up to 70 tonnes** | DT Next, Oct 2022 |
| Clean-out after carbon black | **over 7,000 L** (7,200 L) | the engine |
| Indigo due | **by 10 am** | the engine |
| Cut water 20% → energy | **0.0%** | the engine |
| Cut salt 20% → energy | **−20.0%** | the engine |
| Plans checked | **480** | the engine |
| Option C late by | **2.6 hours** | the engine |
| Do nothing / reuse rinse / low salt | **132.3% / 132.3% / 82.1%** | the engine |
| Model predicts at CPCB inlet | **30.6%** vs published **20–30%** | the engine; CPCB |
| Salt avoided, one machine, one shift | **about 60 kg** (62.6 kg) | the engine |
| Cost avoided, same | **about ₹10,000** (₹10,171) | the engine |

**If the screen shows something different, the screen is correct.**

---

## If a judge asks

**Is the one lakh tonnes real?**
Yes. The Dyers Association of Tiruppur told the Economic Times in June 2025
that accumulated mixed waste salt at the treatment plants exceeds 100,000
tonnes, stored in sheds because no disposal method has been found. DT Next
reported nearly 50,000 tonnes in October 2022, growing by up to 70 tonnes a
day.

**Is the six o'clock morning a real factory?**
It is the exact queue the engine runs — five real-shaped orders with real
shade depths and delivery times. Every number in that story is what the
screen shows. It is a worked example, not a named customer, and I would say
so.

**Who is the customer?**
The dyehouse owner. They buy the salt, and they pay the treatment plant to
boil it out.

**Who would sell it?**
The shared treatment plant. Every kilo of salt its members do not send is
steam it does not buy and salt it does not have to store. Its incentive
already points the same way as ours.

**"Pays for its salt twice" — true?**
Yes. Once to buy it for the dye bath, once through the treatment charge to
boil it out. Both are separate costs in the model and never added together
into the water figure.

**Why "many machines" rather than a bigger number?**
Because a cluster-wide total would be a projection from one modelled machine.
"Many machines, every shift, every day" is true without claiming a figure we
have not measured.

**What is the weakness?**
We have not measured a real site yet. One visit and two instrument readings —
steam flow to the evaporator and the saltiness of the leftover water — would
turn this from a checked model into a measured one. That is the first thing
we would do with support.

---

## Words to avoid

| Do not say | Say instead |
|---|---|
| "AI", "machine learning" | "a search that checks every option" |
| "blockchain" | "a tamper-evident record" |
| "we saved", "our result" | "the model shows" |
| "we measured" | "we checked it against published plant data" |
| any jobs figure for 2011 | "tens of thousands" |
| "a factory we worked with" | "a typical morning" — it is a worked example |

---

## If something goes wrong

- Small mistake — keep going. Calm recovery beats a visible cut.
- Wrong page — go back and say "let me show you that properly".
- Wrong state — click **Reset**, restart from Command.
- Flow not moving — correct before **Accept**.
- A number looks odd — say what is on screen.

---

## The five moments that must survive

Whichever version you use, never lose these:

1. **"The salt that once poisoned the river now burns coal."**
2. **The shed — over a lakh tonnes, doubled in three years.** The real, current problem.
3. **"Zero point zero percent."** The insight.
4. **Option C refused, and the gate refusing your own release.** The proof it can be trusted.
5. **"Getting rid of the salt is one answer. Not putting it in is a better one."**

---

## One last thing

Every other team will say "we save water." You are the one who will show the
jury a shed with a lakh tonnes of salt in it, explain why saving water does not
shrink it, and then show the exact desk, at the exact hour, where it can be
shrunk — without ever missing a delivery.

Do not rush the first two minutes. The story is what makes the software matter.
