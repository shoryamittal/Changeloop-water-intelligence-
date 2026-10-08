# ChangeLoop — video script

**What you do:** screen-record the running website and read this out.

**Length: 695 spoken words.** With the marked pauses and the clicking, the
full version runs about **5:00**.

| Version | Runs |
|---|---|
| Full script | **~5:00** |
| Minus the five cut-list blocks | **~4:20** |
| Minus those *and* section 9 | **~3:50** |

The cut list is at the end of this file. It also names the four moments that
must survive whatever else goes — read that part before you decide anything.

**Check the SANKALP limit first, then pick a version.** Do not start recording
and find out halfway.

Everything in a **grey box is what you say.** Read it as written.
Everything in **bold outside a box is what you click.**

---

## The one idea holding this together

Read this before you record. If you understand it, the whole script will feel
inevitable instead of memorised.

**Salt is the thread.** It is the same substance in every part of the video:

```
salt poisoned the farmers' groundwater
   |   so the court said: release nothing
salt now stays inside the factory
   |   and the only way to remove it is to boil the water off it
boiling needs steam, and steam comes from a coal boiler
   |
the salt that once poisoned the river now burns coal instead
   |
and the coal is set by the salt — not by the water
```

That last line is the project. Everything before it is the reason it matters.
Never let the audience wonder where coal came from — you will have walked them
there, one step at a time.

---

## Set up before recording

```bash
cd changeloop
python backend/server.py
```

Open `http://localhost:8000`

- Click **Reset**
- **Binding constraint** → **Normal operation**
- Full screen, zoom 100%, close all other tabs

**Record on your own computer, not the Render link.** Render sleeps and takes
50 seconds to wake.

**The flow picture does not move at the start.** That is correct. It starts
when you click **Accept** in section 6.

**Speak slowly.** The pauses are doing work.

---

# 1. The river  (0:00 – 0:55)
*On screen: the Command page. Do not touch the mouse. Let them look.*

> In 2003, farmers in Tamil Nadu took an industry to court.
>
> Not an NGO. Farmers.
>
> Their river is the Noyyal. Most of the year it is dry — nothing flows in it
> to carry anything away.
>
> Upstream sits Tirupur, which makes most of India's knitted clothing.
>
> To dye cloth you need two things. Colour, and a lot of salt. The salt is
> what drives the dye into the fibre.
>
> Both went into that river.

*(pause)*

> You could see the colour. You could not see the salt. And salt is the one
> that stays.
>
> The groundwater turned salty. Wells that had watered that land for
> generations stopped being usable.

*(pause)*

> In 2006 the court ordered zero discharge. Release nothing.
>
> The industry did not do it.
>
> So in 2011 the court shut it down. Seven hundred dyeing units.

---

# 2. What "release nothing" really costs  (0:55 – 1:40)
*Still on the Command page.*

> Tirupur rebuilt. Today it recycles about a hundred and thirty million
> litres of water every day.
>
> It worked. The river is cleaner.

*(pause)*

> But think about what "release nothing" actually means.
>
> The salt did not disappear. It is still dissolved in that water. And the
> only way to get clean water back out is to boil the water off and leave the
> salt behind.
>
> Boiling needs steam. Steam comes from a coal boiler.

*(pause — this is the hinge of the whole video)*

> So the salt that used to poison that river now burns coal instead.
>
> That is why cloth from here costs twenty-five to thirty percent more than
> it used to.

---

# 3. The thing nobody noticed  (1:40 – 2:12)
*Move the mouse to the band at the top.*

> And this is where almost everyone gets it backwards.

*Read the big sentence on screen:*

> In a zero discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath. Not by how much water comes out.

*Explain:*

> Every water-saving project in this industry attacks the water. But you are
> not boiling that water off because there is too much of it. You are boiling
> it to get the salt out.
>
> This is ChangeLoop. And it proves that, live.

---

# 4. The proof  (2:12 – 2:28)
*Point at the four numbers on the right of the band.*

> Cut the water by twenty percent. The evaporator energy changes by zero
> point zero percent.
>
> Cut the salt by twenty percent. It drops by twenty.
>
> Water is only the carrier. Salt is the load.

---

# 5. It refuses its own best answer  (2:28 – 3:05)
**Click Run optimiser.** Then **Decisions**.

> So we put that cost back where the decision is made — in the morning, when
> a planner picks what order to run today's batches in.
>
> Four hundred and eighty plans, all of them checked. Option B is the
> recommendation.

*Move the mouse to Option C. Slow down.*

> But look at Option C. It saves almost half the fresh water — the best
> water number on the screen.
>
> And ChangeLoop refuses it. Because it misses a customer's delivery date by
> two point six hours.
>
> A delivery date cannot be traded for water.

---

# 6. A person decides  (3:05 – 3:18)
**Click Accept.** *The flow picture starts moving — point at it.*

> Approved, and recorded under a named person. The system only shows itself
> as running after a human has decided something.
>
> Reject it instead, and the saving is exactly zero.

---

# 7. The gate refuses me  (3:18 – 3:45)
**Click Water.** Scroll to **Inject a fault**.

> Second decision. When is the washing actually finished?
>
> Stop too early and the colour bleeds, and the batch is washed again —
> costing more than you saved.

**Click Calibration drift.** **Click Attempt release.**

> Refused at the gate. Refused again at the server. Written into the record,
> and the saving stays at zero.
>
> It can never release by itself.

*Stay silent for two seconds.*

**Click No fault.** Then **Grant release.**

---

# 8. The surprise  (3:45 – 4:15)
**Click Forecast.**

> Against this machine's real water allowance, doing nothing runs at a
> hundred and thirty-two percent.
>
> Now reuse the rinse water — the obvious answer, the one everybody funds.
> A hundred and thirty-two percent.

*(pause)*

> The same. Not close — the same. Because the fresh water you take in
> replaces the water you boiled away, and that is set by salt.
>
> Only the low salt chemistry brings it inside, at eighty-two.

---

# 9. We measured nothing  (4:15 – 4:45)
**Click Evidence.**

> Nothing here is measured, and I will say that before anyone asks.
> Seventeen numbers published, four calculated, four assumed, zero measured.
>
> But a model can still be tested. The Pollution Control Board measured
> eighteen thousand three hundred and forty milligrams per litre at a real
> Tirupur unit. Plants separately report their reject at twenty to thirty
> percent.
>
> I give my model the first number. It predicts thirty point six. Inside the
> band.

---

# 10. Ending  (4:45 – 5:03)
> Those farmers got their river back.
>
> The salt is out of the water now. It is in the coal.
>
> Nobody has counted it — and it is decided every morning, by a planner
> choosing what to run first.
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
| any jobs figure for 2011 | "tens of thousands" — estimates differ tenfold |

---

## If something goes wrong

- Small mistake — keep going. Calm recovery beats a visible cut.
- Wrong page — go back and say "let me show you that properly".
- Wrong state — click **Reset**, restart from Command.
- Flow not moving — correct before section 6.
- A number looks odd — say what is on screen.

---

## Cut list — 5:03 down to 4:20

Five blocks, **114 words**, about **43 seconds**. Mark them in your copy
before you start — deciding mid-take is how people lose their place.

| Cut | Words | Section |
|---|---|---|
| "Most of the year it is dry — nothing flows in it to carry anything away." | 16 | 1 |
| "Every water-saving project in this industry attacks the water. But you are not boiling that water off because there is too much of it. You are boiling it to get the salt out." | 33 | 3 |
| "So we put that cost back where the decision is made — in the morning, when a planner picks what order to run today's batches in." | 26 | 5 |
| "Stop too early and the colour bleeds, and the batch is washed again — costing more than you saved." | 19 | 7 |
| "Approved, and recorded under a named person. The system only shows itself as running after a human has decided something." | 20 | 6 |

Losing these costs you the *reasons* but keeps every *fact*. Section 3's
explanation, for instance, is immediately proved by the numbers in section 4 —
so the audience still gets the point, just without being walked to it.

### The four that must survive

Whatever else goes, these stay. Without them the video has no argument:

1. **"The salt that used to poison that river now burns coal instead."**
   The hinge. Cut this and the second half of your video is about a different
   subject from the first half.
2. **"Zero point zero percent."** The insight itself.
3. **Option C being refused — and the reason why.** This is what separates
   you from every submission that only shows its best number.
4. **The gate refusing your own release attempt.** A system that says no to
   its operator on camera is something a jury has not seen before.

### If you are still over

Drop section 9 entirely (72 words, 27 seconds) and say the one sentence
"nothing here is measured, and a test enforces that" while the Evidence screen
is visible. You lose the CPCB validation, which is painful — but it is the
only remaining block that can go without breaking the argument.

---

## Sources, if a judge asks

| Claim | From |
|---|---|
| Farmers went to court, 2003 | Down To Earth |
| Court ordered ZLD, 2006 | Madras High Court |
| ~700 units shut, Feb 2011 | Down To Earth; Ecotextile |
| Fewer than half reopened in a year | Ecotextile |
| Supreme Court upheld Polluter Pays | *Tirupur Dyeing Factory Owners Assn v. Noyyal River Ayacutdars Protection Assn*, 2009 |
| 130 million L/day today | The Better India; CETP operator data |
| Costs up 25–30% | Down To Earth |
| Reject 20–30% of inlet; 18,340 mg/L inlet | CPCB Tirupur ZLD assessment |

Full register: [`docs/data_sources.md`](../docs/data_sources.md)

---

## Why this version is built the way it is

The earlier draft told the river story, then jumped to a coal bill. The
audience had no idea where coal came from, so the second half sounded like a
different presentation.

The fix was not better wording. It is that **salt is the same substance in both
halves**, and the script now says so out loud. The salt that ruined those wells
is the salt that now has to be boiled out of the water, and boiling is where
the coal goes. Section 2 exists entirely to walk the audience across that
bridge, one step at a time, so that when the headline sentence arrives in
section 3 it lands as something they had half worked out themselves.

That is also the honest shape of the project. You did not start with a
thermodynamics insight and go looking for a story. The story is the reason the
physics is worth anything.

So do not rush sections 1 and 2 to reach the software. They are not an
introduction to the project. They *are* the project — the software is the part
that proves it.
