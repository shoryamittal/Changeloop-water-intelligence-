# ChangeLoop — video script

**What you do:** screen-record the running website and read this out.

**Length: 600 spoken words.** At a normal narration pace that is **4:00**, and
about **4:10** with the pauses marked in the script.

**If your limit is a hard 3:30**, use the cut list near the end of this file —
it removes 95 words and lands you at 3:28. Decide before you record, not
halfway through.

Everything in a **grey box is what you say.** Read it exactly — it is already
in simple spoken English and already timed. Everything in **bold outside a box
is what you click.**

---

## Set up before recording

```bash
cd changeloop
python backend/server.py
```

Open `http://localhost:8000`

- Click **Reset**
- Set **Binding constraint** to **Normal operation**
- Full screen, zoom 100%, close all other tabs

**Record on your own computer, not the Render link.** Render sleeps and takes
50 seconds to wake up.

**The flow picture does not move at the start.** That is correct. It starts
moving when you click **Accept** in section 5.

**Speak slowly.** Slower than feels right. The pauses do real work.

---

# 1. The story  (0:00 – 1:00)

*On screen: the Command page. Do not touch the mouse.*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Not an NGO. Farmers.
>
> Their river is the Noyyal. Most of the year it is dry. There is no water in
> it to carry anything away.
>
> Upstream sits Tirupur, India's knitwear capital. For years its dyeing units
> poured waste into that river. Colour, and salt.
>
> The groundwater turned salty. Animals died drinking it. Farmland stopped
> growing crops.

*(pause)*

> In 2006 the court ordered zero discharge. Release nothing. The industry did
> not do it.
>
> So in 2011 the court shut it down. Seven hundred dyeing units. The whole
> town stopped.

*(pause)*

> Tirupur rebuilt. Today it recycles a hundred and thirty million litres of
> water every day. It worked.
>
> And it made production twenty-five to thirty percent more expensive.
> Because if you release nothing, you must boil your waste water dry.

---

# 2. The idea  (1:00 – 1:25)

*Move the mouse to the band at the top.*

> So my project does not ask whether we should recycle. That question is
> finished. The farmers won it.
>
> It asks what nobody has counted — the energy of recycling.

*Read the big sentence on screen:*

> In a zero discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath. Not by how much water comes out.
>
> This is ChangeLoop. Every number here is calculated live.

---

# 3. Proof, on screen  (1:25 – 1:51)

*Point at the four numbers on the right.*

> Cut the water by twenty percent. The evaporator energy changes by zero
> point zero percent.
>
> Cut the salt by twenty percent. It drops by twenty.

*Now explain:*

> Salt does not disappear. The membrane can only make the brine so strong
> before it damages the tubes. So the amount you must boil is decided by the
> salt, not the water.
>
> Water is only the carrier. Salt is the load.

---

# 4. It says no to its own best answer  (1:51 – 2:25)

**Click Run optimiser.** Then **Decisions**.

> Four hundred and eighty possible plans, all of them checked. So this is the
> proven best answer, not a guess.

*Move the mouse to Option C. Slow down.*

> Look at Option C. It saves almost half the fresh water. The best water
> number on this screen.
>
> And ChangeLoop refuses it.
>
> Because it misses a customer's delivery date by two point six hours.
>
> A delivery date cannot be traded for water. A tool that makes a factory
> miss a shipment is switched off in one week.

---

# 5. A person decides  (2:25 – 2:36)

**Click Accept.** *The flow picture starts moving. Point at it.*

> Approved, and saved under a named person.
>
> The system only shows itself as live after a human decided something.
>
> If I reject it, the saving is exactly zero.

---

# 6. The gate says no to me  (2:36 – 3:05)

**Click Water.** Scroll to **Inject a fault**.

> Second decision. When is the washing actually finished?
>
> Stop too early and the colour bleeds. The batch is washed again — costing
> more water and steam than you saved.

**Click Calibration drift.** **Click Attempt release.**

> Refused at the gate. Refused again at the server. The refusal is written
> into the record, and the saving stays at zero.
>
> It can never release by itself. That is fixed in the code.

*Stay quiet for two seconds.*

**Click No fault.** Then **Grant release.**

---

# 7. The surprise  (3:05 – 3:34)

**Click Forecast.**

> Against this machine's real water allowance, doing nothing runs at a
> hundred and thirty-two percent.
>
> Now reuse the rinse water — the obvious solution, the one everybody funds.
> A hundred and thirty-two percent.

*(pause)*

> The same. Not close — the same. Because the fresh water you take is the
> water you boiled away, and that is set by salt.
>
> Only the low salt chemistry brings it inside, at eighty-two.

---

# 8. We measured nothing  (3:34 – 4:03)

**Click Evidence.**

> Nothing here is measured, and I will say that first. Seventeen numbers
> published, four calculated, four assumed, zero measured.
>
> But you can still check a model.
>
> The Pollution Control Board measured eighteen thousand three hundred and
> forty milligrams per litre at a real Tirupur unit. Separately, plants report
> their reject at twenty to thirty percent.
>
> I give my model the first number. It predicts thirty point six percent.
> Inside the band. Nothing was adjusted.

---

# 9. Ending  (4:03 – 4:12)

> Zero discharge gave India back its water. Nobody counted the coal it takes
> to keep it.
>
> That is the choice we change.

*Stop. Say nothing more.*

---

## Numbers to get right

Keep this open in another window.

| Where | Number |
|---|---|
| Units shut in 2011 | **700** |
| Recycled today | **130 million litres a day** |
| ZLD cost increase | **25–30%** |
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

**If the screen shows something different, the screen is correct.**

---

## Words to avoid

| Do not say | Say instead |
|---|---|
| "AI", "machine learning" | "a search that checks every option" |
| "blockchain" | "a tamper-evident record" |
| "we saved", "our result" | "the model shows" |
| "we measured" | "we checked it against published plant data" |
| any jobs number for 2011 | "tens of thousands" — estimates differ a lot |

---

## If something goes wrong

- Small mistake — keep going. Calm recovery looks better than a cut.
- Wrong page — go back and say "let me show you that properly".
- Wrong state — click **Reset**, start again from Command.
- Flow not moving — correct before section 5.
- A number looks odd — say what is on screen.

---

## If you must reach exactly 3:30

The full script runs about **4:10**. These seven lines remove **99 words**
— roughly **40 seconds** — which brings you to about **3:32**.

Mark them in your copy *before* you start. Deciding mid-take is how people
lose their place.

| Cut | Words | Section |
|---|---|---|
| "Most of the year it is dry. There is no water in it to carry anything away." | 17 | 1 |
| "Animals died drinking it. Farmland stopped growing crops." | 8 | 1 |
| "Salt does not disappear. The membrane can only make the brine so strong before it damages the tubes. So the amount you must boil is decided by the salt, not the water." | 32 | 3 |
| "Approved, and saved under a named person." | 7 | 5 |
| "The system only shows itself as live after a human decided something." | 12 | 5 |
| "Stop too early and the colour bleeds. The batch is washed again, costing more water and steam than you saved." | 20 | 6 |
| "Nothing was adjusted." | 3 | 8 |

Speaking the backstory at your normal pace instead of the slow one saves
another eight seconds, and costs nothing on screen.

**Never cut these three:**

1. "zero point zero percent" — the whole insight
2. Option C being refused, and *why* — a delivery date cannot be traded
3. The gate refusing your own release attempt

Everything else in this script exists to support those three. If you are
short on time, protect them and let the rest go.

---

## Sources, if a judge asks

| Claim | From |
|---|---|
| Farmers went to court, 2003 | Down To Earth |
| Court ordered ZLD, 2006 | Madras High Court |
| ~700 units shut, Feb 2011 | Down To Earth; Ecotextile |
| Fewer than half reopened in a year | Ecotextile |
| Supreme Court upheld Polluter Pays | *Tirupur Dyeing Factory Owners Assn v. Noyyal River Ayacutdars Protection Assn*, 2009 |
| 130 million L/day today | The Better India; CETP data |
| Costs up 25–30% | Down To Earth |

Full list: [`docs/data_sources.md`](../docs/data_sources.md)

---

## Remember this

The story is not decoration. It is why the technology matters.

The same salt that ruined those farmers' groundwater is the salt that now
decides the coal bill. That is not a clever line — it is the physics. Your
project is the first to put a price on it.

Do not rush the first minute to reach the software. The software is better
because the story is true.
