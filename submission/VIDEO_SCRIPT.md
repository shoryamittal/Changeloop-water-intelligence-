# ChangeLoop — 3-minute submission video

**Format:** screen recording of the running product with voice-over.
**Target:** 2:50–3:00. Judges stop watching at the limit, so land the hook early.

Before recording:

```bash
python backend/server.py          # http://localhost:8000
```

Press **Reset session**. Set the binding constraint to **Normal operation**.
Browser at 1920×1080, zoom 100%, dark theme (the default). Close every other
tab — the tab bar is in the frame.

**Record in one take if you can.** A single unbroken take of a working system
is worth more than a polished edit, because it proves the thing runs.

---

## The shot list

| Time | On screen | What you say |
|---|---|---|
| **0:00–0:12** | Slide: title card, or the Command screen still | "Tirupur recycles a hundred and thirty million litres of water a day, under a zero-discharge regime a court imposed after the Noyyal river was destroyed. It worked. It also raised costs twenty-five to thirty percent — and when units couldn't comply, the courts closed them. Eleven billion rupees of exports. A hundred thousand jobs." |
| **0:12–0:30** | **Command** screen, cursor resting on the flow diagram | "So water recovery is solved. What nobody has costed is the energy it takes to keep recovering it. This is ChangeLoop. Everything you see is computed by the engine behind it — nothing on this screen is hardcoded." |
| **0:30–0:55** | Scroll to **Salt is water** panel. Pause on the two bars. | "Here is the thing almost everyone gets wrong. Salt is conserved — reverse osmosis can only concentrate it so far. So the volume you have to boil dry is set by salt mass, not by water. Watch: cut water by twenty percent at constant salt, and evaporator energy moves **zero point zero percent**. Cut salt by twenty percent, and it falls twenty. In a closed loop, salt *is* water." |
| **0:55–1:05** | Click **Why this holds** → side sheet opens | "That's not a claim on a slide. It's mass conservation, computed live, and the product shows you where it stops being true." *(close the sheet)* |
| **1:05–1:35** | **Decisions** screen. Let the comparison table land. Cursor down the Option C row. | "Four hundred and eighty candidate plans, enumerated exhaustively — so this optimum is proven, not approximated. Option B is recommended. But look at Option C: it saves almost half the freshwater, and ChangeLoop **refuses** it, because it breaks a firm buyer ship date by two point six hours. A water tool that misses a shipment gets switched off in a week." |
| **1:35–1:45** | Click **Accept** | "Accept. Recorded against a named planner. Reject it instead and it credits exactly zero — and the rejection goes on the record too." |
| **1:45–2:10** | **Water** screen. Click **Calibration drift**, then **Attempt release** | "Second decision: when is wash-off actually finished? Release early on unfixed dye and the lot is re-processed, costing more than you saved. So — inject a probe fault. The gate locks. I'll try to release anyway." *(click)* "Refused at the gate, refused again at the API, the refusal written to the ledger, and the saving stays at zero. It never releases on its own." |
| **2:10–2:30** | Click **No fault** → **Grant release** → go to **Forecast** | "Clean run, release granted. Now the part that matters operationally. Judged against this machine's real abstraction allocation: doing nothing runs at a hundred and thirty-two percent and breaches at two in the afternoon. Resequencing and reusing rinse water — the obvious move — **still** breaches, at a hundred and twenty-four. Only buying the low-salt chemistry gets the shift inside, at seventy-one." |
| **2:30–2:45** | **Scenarios**, scroll to the ablation table | "And we test ourselves. We remove our own layers and publish what breaks. A scheduler that optimises dyehouse water alone captures thirteen percent of the benefit. Two variants over-report their savings — we label that, because over-reporting is the defect." |
| **2:45–3:00** | **Evidence** screen, the registry visible | "Nothing here is measured. Five published, two derived, thirteen assumed, zero measured — and a test enforces that zero. Zero Liquid Discharge gave India back its water. Nobody costed the coal it takes to keep it — and that cost is decided by a scheduling choice nobody connects to it. That's the choice we change." |

---

## Recording notes

**Do**

- Say the number that is on the screen. If the engine shows something
  different from this script, say what is on screen and fix the script.
- Let the refusal moments breathe. The two seconds after "refused" are the
  most persuasive in the video.
- Keep the cursor still while you talk. Moving it reads as nervous.

**Do not**

- Do not say "AI" — there is no trained model in this system, and a judge
  who asks will catch it.
- Do not say "blockchain" — it is a hash chain and the interface says so.
- Do not call any figure a result. Everything is modelled, and the product
  labels it on every screen.
- Do not quote the cluster projection as impact. It is a projection.

**If something goes wrong mid-take**

Press Reset session and resume from the Command screen. A visible recovery
is better than an obvious cut.

---

## 30-second cut, if a shorter version is wanted

> Tirupur recycles a hundred and thirty million litres a day under a
> court-mandated zero-discharge regime. It worked, and it raised costs
> twenty-five to thirty percent, because evaporating the reject takes enormous
> steam.
>
> Here's what nobody acts on: that reject volume is set by the **salt** in the
> water, not the water itself. So cutting water without cutting salt saves no
> energy at all — our engine shows it live: zero point zero percent.
>
> ChangeLoop puts that downstream consequence inside the upstream scheduling
> decision. A planner sees, before committing a lot order, what it will cost
> the evaporator tonight — and the system refuses any plan that breaks a buyer
> ship date, even the one that saves the most water.

---

## What the video must prove, in priority order

1. **It runs.** A live system, not a mock-up.
2. **The insight is real and counter-intuitive.** The 0.0% vs −20% moment.
3. **It refuses its own best-looking answer.** Option C, and the locked gate.
4. **The numbers are honest.** Zero measured coefficients, stated out loud.

If you run short on time, cut the ablation section (2:30–2:45) before
cutting any of these four.
