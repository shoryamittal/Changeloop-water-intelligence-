# ChangeLoop — screen-recording walkthrough

**Format:** you screen-record the running interface and explain it in your own
words.
**Target:** about 3 minutes. Check the SANKALP rules for the exact limit before
you record, and cut from the priority list near the end of this file if needed.

This is not a script to read out. It is a **click path plus talking points**.
Say it in your own words — you understand this system, and that will show. The
only things to get exactly right are the **numbers in bold**, because they are
on screen behind you and a mismatch is the one thing a reviewer will catch.

---

## Before you press record

```bash
cd changeloop
python backend/server.py          # http://localhost:8000
```

**Record locally, not on the Render URL.** The free plan sleeps and takes about
fifty seconds to wake, and the public instance shares one session with every
visitor. Local starts in a second and nothing can interfere.

Then:

1. Open `http://localhost:8000`
2. Click **Reset** (top right) — start from nothing
3. Set **Binding constraint** to **Normal operation**
4. Browser at 1920×1080, zoom 100%, dark theme (the default)
5. Close every other tab — the tab bar is in frame
6. Full-screen the browser (F11) if your recorder captures the whole screen

**A note on the flow diagram.** It is deliberately *static* when you start,
because no decision has been taken yet. It begins animating the moment you
click **Accept** in Beat 4. That transition is one of the better moments in the
video — do not skip past it, and do not panic that it is frozen at the start.

**Try for one take.** A single unbroken recording of a working system is worth
more than a polished edit, because it proves the thing runs. If you fumble, see
"If it goes wrong" near the end.

---

## Beat 1 — The hook  (~0:00–0:20)

**On screen:** the **Command** screen as it loads. The plain-language band is
the first thing at the top.

**Read the band's headline sentence out loud, exactly:**

> "In a zero-discharge dyehouse, the coal bill is set by how much salt goes
> into the dye bath — not by how much water comes out."

**Then explain, in your own words:**

- Tirupur recycles around **130 million litres a day** under a zero-discharge
  regime a court imposed after the Noyyal river was destroyed.
- It worked. It also raised operating costs **25 to 30 percent**, and when
  units could not comply the courts closed them — about **₹11 billion** of
  exports and **100,000 jobs**.
- So water *recovery* is solved. Nobody has costed the **energy** of recovering
  it — and that cost is decided upstream, by a planner who never sees the
  evaporator.

Pause for a beat after the hook sentence. Let it land before you explain it.

---

## Beat 2 — The insight, proved live  (~0:20–0:50)

**On screen:** still **Command**. Point at the four figures on the right of the
band.

**Say, pointing at each:**

- "Cut water twenty percent — evaporator energy moves **0.0 percent**."
- "Cut salt twenty percent — it falls **20 percent**."
- "Same code path, same baseline, one variable each."

**Then explain why, in your own words:**

Salt is conserved. Reverse osmosis can only concentrate it so far before the
brine scales the tubes — about **60,000 mg/L**. So the volume you have to boil
is the salt mass divided by that ceiling. Add water with the same salt and the
membranes just recover more clean water; the brine left at the end is
identical, and so is the steam.

**One sentence worth saying exactly:** *"Water is the carrier. Salt is the
load."*

**Click:** **Read the reasoning** → the side sheet opens with six rungs.

Scroll it briefly — do not read it out. Say something like: "the same finding
at six levels, from one sentence to the equation to the live proof." Then
**close the sheet**.

---

## Beat 3 — The optimiser refuses its own best answer  (~0:50–1:25)

**Click:** **Run optimiser** (if the session is fresh), then nav → **Decisions**.

**On screen:** the three options, A / B / C.

**Explain:**

- **480 candidate plans**, enumerated exhaustively — so this optimum is
  **proven**, not approximated. Say "proven" deliberately; most submissions
  cannot claim it.
- **Option B** is recommended.
- Now move the cursor to **Option C** and slow down. This is the moment.

**Say this part close to verbatim:**

> "Option C saves almost half the freshwater — and ChangeLoop refuses it,
> because it breaks a firm buyer ship date by **2.6 hours**. A confirmed
> delivery date is a hard constraint, not a penalty you can buy your way out of
> with a big enough water saving. A water tool that misses a shipment gets
> switched off in a week."

That single point does more for your credibility than any saving figure.

---

## Beat 4 — A human decides, and the system comes alive  (~1:25–1:40)

**Click:** **Accept**.

**Watch the flow diagram start moving**, and say so:

> "Recorded against a named planner. And notice — the interface only shows a
> live system once a human has actually decided something."

**Add:** "Reject it instead and it credits exactly **zero**, and the rejection
goes on the record too."

---

## Beat 5 — The safety gate refuses you  (~1:40–2:10)

**Click:** nav → **Water**. Scroll to **Inject a fault — each must force
lockout**.

**Set up the problem first:**

The second decision is: when is wash-off actually finished? Release early on
unfixed dye and the lot bleeds, fails wash-fastness, and gets reprocessed —
costing **more** water, steam and salt than the baths you skipped. A wrong
cutoff does not merely risk quality; it destroys the saving it was chasing.

**Click:** **Calibration drift** → the gate shows **Lockout**.

**Click:** **Attempt release**.

**Then say, slowly:**

> "Refused at the gate. Refused again at the API. The refusal is written to the
> ledger, and the credited saving stays at exactly zero. `automatic_release` is
> hardcoded false — there is no code path that sets it true."

**Let two seconds of silence sit here.** The pause after "refused" is the most
persuasive moment in the whole video.

**Then:** click **No fault** → **Grant release**.

---

## Beat 6 — The finding nobody expects  (~2:10–2:35)

**Click:** nav → **Forecast**.

This is your strongest operational point. Deliver it in four steps and do not
rush the third.

1. "Judged against this machine's real abstraction allowance, doing nothing
   runs at **132.3 percent** and breaches at **two in the afternoon**."
2. "Now reuse the rinse water — counter-current rinsing, the obvious move, the
   one every water programme funds. It runs at **132.3 percent** and breaches
   at two in the afternoon."
3. **Pause.** Then: "**Identical.** Not similar — identical. Because in a
   closed loop the basin draw *is* the evaporative loss, and that is set by
   salt."
4. "Only buying the low-salt chemistry gets the shift inside, at **82.1
   percent**."

**Worth adding if you have time:** "That is the same conclusion as the first
screen, reached by a completely different code path — the forecast never reads
the ZLD model."

---

## Beat 7 — How a model with no meters is checked  (~2:35–2:55)

**Click:** nav → **Evidence**.

**State the weakness before anyone asks:**

> "Nothing in this system is measured, and we will not pretend otherwise.
> **17 published, 4 derived, 4 openly assumed, zero measured** — and a test
> enforces that zero."

**Then turn it around:**

> "But a model with no meters can still be checked. CPCB measured **18,340
> milligrams per litre** entering the evaporator at a real Tirupur unit.
> Separately, operators report RO reject at **20 to 30 percent** of inlet.
> Different sources, neither one an input to our engine. Feed it the first and
> it predicts **30.6 percent** — inside the band. Nothing is tuned to make that
> happen."

*(If you want it on screen: the **How we checked it** button on the Command
band opens this as a table. Decide beforehand whether you have the time.)*

---

## Beat 8 — Close  (~2:55–3:00)

**Say, close to verbatim:**

> "Zero Liquid Discharge gave India back its water. Nobody costed the coal it
> takes to keep it — and that cost is decided by a scheduling choice nobody
> connects to it. That is the choice we change."

Stop talking. Do not add anything after this line.

---

## Numbers card — keep this open while you record

| Where | Figure | Value |
|---|---|---|
| Band | cut water 20% → evaporator | **0.0%** |
| Band | cut salt 20% → evaporator | **−20.0%** |
| Decisions | candidates enumerated | **480** |
| Decisions | Option C lateness | **2.6 h** |
| Forecast | do nothing | **132.3%** |
| Forecast | counter-current (water lever) | **132.3%** |
| Forecast | low-salt (salt lever) | **82.1%** |
| Evidence | published / derived / assumed / measured | **17 / 4 / 4 / 0** |
| Evidence | CPCB measured inlet | **18,340 mg/L** |
| Evidence | model predicts | **30.6%** |
| Evidence | published band | **20–30%** |
| Context | cluster recycles | **130 million L/day** |
| Context | ZLD cost increase | **25–30%** |
| Tests | automated tests | **140** |

**If the screen disagrees with this card, the screen is right.** Say what is on
screen and fix the card afterwards. To refresh everything from the engine:

```bash
python submission/build_figures.py          # regenerate
python submission/build_figures.py --check  # non-zero if stale
node   submission/build_deck.js             # rebuild the deck
```

---

## Do not say

| Don't | Because |
|---|---|
| "AI" or "machine learning" | There is no trained model here. A judge who asks will catch it — and the honest answer, that a deterministic optimiser is correct at this problem size and cannot hallucinate, is stronger anyway. |
| "Blockchain" | It is an HMAC hash chain, the interface says so explicitly, and claiming more is the easiest thing to disprove. |
| "Result", "we achieved", "we saved" | Everything is modelled. Say "the model shows". |
| "Proven saving" | The *optimum* is proven. The saving is modelled. Different words, different places. |
| The cluster projection as impact | It is a projection from one modelled unit, and it is labelled as one. |
| "We measured" | You did not. "Cross-validated against published plant data" is accurate and still impressive. |

---

## If it goes wrong mid-take

- **Small fumble:** keep going. Confidence recovering beats an obvious cut.
- **Wrong screen:** navigate back and say "let me show you that properly" — it
  reads as a person, not an error.
- **State is wrong:** click **Reset**, then resume from the Command screen.
- **Flow diagram not moving:** correct before Beat 4. It starts on Accept.
- **A number looks wrong:** say what is on screen, not what is in this file.

---

## What the video must prove, in priority order

1. **It runs.** A live system, not a mock-up.
2. **The insight is real and counter-intuitive.** The 0.0% vs −20% moment.
3. **It refuses its own best-looking answer.** Option C, and the locked gate.
4. **The numbers are honest.** Zero measured, said out loud by you.

If you are over time, cut in this order: Beat 7's validation detail, then the
Beat 2 side sheet, then Beat 6's closing remark about the second code path.
**Never cut Beats 3, 5, or the 0.0% line** — those are the video.

---

## 45-second version, if a short cut is wanted

> Tirupur recycles 130 million litres a day under a court-mandated
> zero-discharge regime. It worked — and it raised costs 25 to 30 percent,
> because evaporating the reject takes enormous steam.
>
> Here is what nobody acts on. That reject volume is set by the **salt** in the
> water, not the water. So cutting water without cutting salt saves no energy
> at all — the engine shows it live: **zero point zero percent**.
>
> ChangeLoop puts that downstream consequence inside the upstream scheduling
> decision. A planner sees, before committing a lot order, what it will cost
> the evaporator tonight. And it refuses any plan that breaks a buyer ship date
> — including the one that saves the most water.
>
> Nothing here is measured, and we say so on every screen. But fed the inlet
> CPCB measured at a real Tirupur unit, the model predicts the reject fraction
> real plants report. That is the difference between a claim and a check.

---

## One last thing

The strongest thing you have is not a saving figure. It is that this system
**refuses things** — a plan that saves water but misses a shipment, a release
the sensors cannot justify, a coefficient that would claim to be measured when
it is not.

Most submissions spend three minutes claiming. Spend yours showing a system
that declines to over-claim, and say the weakness out loud before anyone asks.
A jury trusts a team that concedes the right things far more than one that
deflects.
