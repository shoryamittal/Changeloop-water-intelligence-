# Hostile jury defence

Thirty questions an expert panel will actually ask, with the answer we can
defend. Where the honest answer is a weakness, it is written as a weakness —
a jury trusts a team that concedes the right things far more than one that
deflects.

---

## Problem and framing

**1. Why water, and why now?**
Because the regulatory deadline already passed. Zero Liquid Discharge is not
coming — it is in force, imposed by the courts on Tirupur and extended by
CPCB guidance to textiles, tanneries, distilleries and pulp and paper. Units
are already paying for it. We are not asking anyone to care about water; we
are reducing the cost of a compliance obligation they already carry.

**2. Tirupur already recycles 95% of its water. What is left to save?**
That is exactly our starting point. Recovery is solved. The *energy* of
recovery is not — reported as a 25–30% increase in operating cost, and the
industry's own stated route to bringing the dyed-fabric premium from 12–15%
down to about 5% is salt and water recovery. We attack the salt, upstream,
where it is cheapest to not create.

**3. Is this not just scheduling? Dyehouses already run pale-to-dark.**
Yes, and we say so on the Decision screen in the product. Ascending shade
sequencing is standard practice and we do not claim it. Two things are
different. First, ascending order is frequently **infeasible** — firm ship
dates, machine capacity and lot arrival times mean you often cannot simply
sort, and our reference case is one where the water-minimal order breaks a
buyer date. Second, we score the plans on the downstream evaporator
consequence, which no scheduling heuristic contains. Our ablation puts a
number on that second part: a water-only scheduler captures 13% of the
available benefit once carbon is priced.

**4. Why would a small unit care about CO₂?**
Mostly it would not, and we do not pretend otherwise. It cares about steam,
which is coal, which is cash. The carbon number is for the buyer's Scope 3
and for a future internal carbon price. The product shows both, and the
business case is denominated in rupees per shift.

## The technical core

**5. Is `V_reject = M_salt / C_reject_max` really that simple?**
The mass conservation is exact. The ceiling is an assumption, and we label it
ASSUMED at 60,000 mg/L with the reasoning. The important part is not the
exact ceiling but the *structure*: reject scales with salt mass. Change the
ceiling and the magnitude moves proportionally; the conclusion that salt, not
water, drives evaporator load does not.

**6. So cutting salt always wins?**
No, and the model says so. Below a crossover — where
`M_salt = (1 − r_max) × V × C_reject_max` — the RO hydraulic floor takes over
and further salt reduction buys nothing. The engine reports which constraint
binds on every stream, and there is a test for the crossover. A product that
claimed "cut salt, always win" would be wrong.

**7. Your 188 kWh/m³ evaporator figure — where is it from?**
Derived, not looked up, and both inputs are published. Latent heat of
0.62694 kWh/kg comes from standard steam tables. Steam economy of 3.33 kg of
water evaporated per kg of live steam is the reciprocal of the 0.25–0.35 kg
steam per kg evaporated reported for multiple-effect evaporators on textile RO
reject, taken at its midpoint. 0.62694 × 1000 ÷ 3.33 = 188.08 kWh_th/m³.

The check worth noting is that the answer lands inside the 150–250 kWh_th/m³
band independently quoted for the evaporator section of textile ZLD plants.
Two unrelated published figures, multiplied, fall inside a third published
band that was never used in the calculation. Both inputs are shown wherever
the figure appears, and a test re-does the arithmetic.

**8. Where is the AI?**
There is none, and we do not claim any. The decision space is 480 discrete
candidates; we enumerate it exhaustively, so the optimum is *proven* rather
than approximated. A transparent deterministic optimiser is both correct and
auditable here, and it cannot hallucinate. If we added a learned component
later it would be for forecasting effluent load, and it would be labelled and
governed separately. `/api/governance` states this.

**9. Then what is intelligent about it?**
Not the search — the **objective**. Knowing that the quantity to minimise is
salt-driven evaporator duty under hard delivery constraints, rather than
litres, is the contribution. The ablation measures what that is worth.

**10. Your savings are small — 8.8% freshwater.**
Correct, and we report it rather than dressing it up. Freshwater falls 8.8%
while *process* water falls far more, because basin draw tracks salt. Cost
falls 28.7% and CO₂e 30.6% in the same run. A modest, internally consistent
number is worth more to us than an impressive one we cannot defend — and
under a drought or carbon-priced mode the engine buys the salt lever and the
freshwater reduction roughly quintuples.

## Data and model validity

**11. Does a dyehouse even have this data?**
Yes, by regulation. CPCB has mandated continuous online effluent monitoring
for 17 categories of highly polluting industry since 2014, so effluent flow
and TDS already stream to the regulator. Lot sequence and shade depth are in
the ERP. The one thing typically unmetered is steam per m³ of reject, which
is Phase 1 of the pilot.

**12. What if your coefficients are wrong?**
We ran the sweep ourselves and publish it. The lot **order** never changes
across the entire sweep. What flips is the process **strategy**, and it flips
in exactly four coefficients — all of which make evaporator energy more
expensive. So the ranking is robust and the strategy choice is conditional,
which tells a site precisely which two numbers to meter first: steam per m³
of reject, and the reject TDS ceiling.

**13. What is measured here?**
Nothing. Five PUBLISHED, two DERIVED, thirteen ASSUMED, **zero MEASURED** — a
unit test enforces the zero. We will not describe a modelled number as a
result, and the interface labels it on every screen.

**14. Your water-stress multiplier of 11× looks invented.**
It is a disclosed placeholder, not a characterisation factor, and the Evidence
screen says so in those words. It is not AWARE and not WRI Aqueduct; we ship
neither dataset and claim neither. It is a transparent ordering index
occupying the slot a licensed factor would occupy, and the interface is a
single scalar per site so replacing it is a data swap. Our own ablation also
reports that it does not change the answer at a single site — it earns its
place only for multi-site comparison.

**15. Is your baseline fair, or did you build a strawman?**
The baseline is the ERP arrival order under conventional rinsing — what
happens with no intervention. It is not an artificially bad case: it meets
every ship date with zero lateness. Both sides of every difference are
computed by the same code path with the same coefficients, so the delta is a
real difference and not two models disagreeing.

**16. What does the model exclude?**
Pretreatment entirely — desizing, scouring, bleaching. So our
litres-per-kilogram is lower than a whole-mill specific water consumption and
must not be compared to one. Also excluded: permeate salt passage, embodied
impacts, crystalliser performance, and sludge disposal beyond an opex line.
All of this is in `docs/methodology.md`.

## Safety and trust

**17. What if the system is wrong and a lot comes out off-shade?**
That is the failure that matters, and it is why the release gate is
fail-closed. Early release on unfixed dye causes bleeding and a failed
fastness test; the lot is then re-processed, consuming more water, steam and
salt than the baths that were skipped. A wrong release destroys the very
saving it chased. So the system never releases automatically —
`automatic_release` is hardcoded false with no code path that sets it true —
and five fault modes each force lockout.

**18. Show me it cannot be bypassed.**
In the demo: inject calibration drift, then attempt release. It is refused at
the gate *and* independently at the API, the refusal is written to the
tamper-evident ledger, and exactly zero saving is credited. There are tests
asserting this for every fault mode.

**19. Who is accountable?**
A named human, for both decisions. ChangeLoop is advisory: no setpoints, no
control authority, cannot release a bath. Every approval *and* every rejection
is recorded with the actor.

**20. What if the planner just ignores it?**
Then it credits zero, and that is recorded too. A rejection is a first-class
outcome, not an error — and in a pilot the rejections are the most valuable
data we get, because they tell us where the model is wrong.

**21. What stops you double-counting water?**
Eight invariants that run on every read of the ledger, including that reuse
cannot exceed either what was recovered or what the process demanded. If any
invariant fails, the figure is not displayed. Two of these invariants caught a
real defect during development, where the attribution subtracted the wash-off
credit twice.

**22. Is the ledger a blockchain?**
No, and the screen says so. It is an append-only hash chain with an HMAC over
each link. It proves no record was altered after it was written. It does not
prove *who* authored one — that needs asymmetric signing with a key in an HSM,
which is a deployment decision. There is no consensus, no peers and no token,
because there is a single accountable operator of record and no
byzantine-fault problem for a chain to solve. The demo key is a published
constant and the interface states that too.

## Business

**23. Who pays?**
The dyeing unit, priced per machine per year plus a one-off integration. The
common effluent plant is the better *channel* — one integration reaches
hundreds of units, and its own incentive is a lower, steadier inlet salt load.

**24. An MSME will not pay for a modelled saving.**
Agreed, and that is the single hardest commercial objection. The answer is
shadow mode: for four weeks the system recommends and nobody acts, and we
show what it would have advised against what was actually done. Payment comes
after that, against a measured baseline. The business-case screen refuses to
compute an ROI from our assumptions at all — it demands the site's own
tariffs.

**25. What if water is cheap at their site?**
Then the water line is small and the case rests on steam and salt, which is
why they are separate lines in the breakdown. If steam is also cheap, the
product is not worth buying there and we would rather the ROI screen say so
than massage it.

**26. What is your moat?**
Today, weak — and we would rather say that. It is a prototype with a good
insight; the optimiser is a week's work for anyone. The defensible asset is a
consequence model calibrated to a specific cluster's steam economy and reject
ceiling, plus the paired record of what was recommended and what the human
then decided. Neither exists until a pilot runs. The cluster position through
the CETP is the most durable near-term advantage.

**27. How does this scale?**
The cluster is the unit, because units share one effluent plant and therefore
one effluent model, basin weighting and steam cost. Our projection — labelled
PROJECTED — is roughly 399 ML/yr of freshwater and 6,073 t/yr of CO₂e across
400 units. It assumes every unit resembles the modelled one and every
recommendation is approved. Neither has been tested, and it must never be
quoted as achieved impact.

**28. Why has nobody done this?**
Partly because it falls between organisations: the dyeing unit and the
effluent plant are often separate businesses with separate P&Ls, so nobody
owns the joint optimisation. Partly because the obvious framing is "save
water", and the salt insight inverts that. We would not claim the idea is
unthinkable — only that it is currently unexploited.

## Closing

**29. What is your biggest weakness?**
We have not spoken to a dyehouse. Everything is modelled from public
information, our basin weighting is a placeholder, the optimiser handles one
machine rather than a mill, and some of our conclusions will change when real
measurements replace our assumptions. The design anticipates that — Phase 1
of the pilot exists to replace them — but today it is a prototype with an
argument, not a validated product.

**30. Why should SANKALP pick you?**
Because the problem is already regulated, already expensive, and already
costing jobs; because the insight is non-obvious, exact, and demonstrated live
rather than asserted; because the system refuses its own best-looking answer
when that answer breaks a commitment; and because we ablate and sensitivity-
test our own architecture in public and report the parts that do not earn
their place. We would rather be the submission whose numbers survive scrutiny
than the one with the biggest numbers.
