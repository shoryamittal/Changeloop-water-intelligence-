# ChangeLoop — Question 3

## The question

**What is new here? What is the closest existing method, and how is yours
different?**

## My answer

Let me name what already exists first, because most of this problem is served by
technology that works.

Production planning and ERP systems already schedule dye lots against delivery
dates. Counter-current rinsing already cuts water use inside the dyehouse, and
has been Best Available Technique for decades. Low-electrolyte reactive dyes are
a commercial product anyone can buy. Reverse osmosis, evaporators and ZLD control
systems already handle the effluent once it arrives at the plant.

None of that is mine and I claim none of it. Running lots light to dark is
ordinary dyehouse practice. If somebody on the panel says resequencing
production is not a new idea, they are completely right.

What is new is where the decision happens, and what information is inside it
when it does.

At the moment the chain runs one way. Production picks a plan, the effluent
turns up at the treatment plant, and the cost appears afterwards on a different
account. ChangeLoop moves that downstream cost into the upstream decision, so
the plan is chosen with the consequence already visible.

Three things come out of that, and they are what I would actually defend.

Salt becomes the lever instead of water. Everything in this space counts litres,
but in a closed loop the reject you have to boil is set by salt mass over the
concentration ceiling. Water volume on its own barely touches the energy bill.
The engine demonstrates it live: cut water 20 percent and evaporator energy moves
0.0 percent, cut salt 20 percent and it drops 20. A planner optimising water
alone is pulling a lever that is not connected to anything.

The treatment cost is computed while planning rather than billed afterwards.
Steam, carbon and treatment charge are evaluated for every candidate plan before
one is picked.

And operational commitments are constraints, not penalties. A firm ship date
cannot be traded away for an environmental gain of any size. In the worked
example the plan that saves nearly half the fresh water gets refused, because it
delays one order by 2.6 hours.

> A water tool that makes a factory miss a shipment gets switched off in a week.
> That refusal is the design working.

There is a fourth difference that matters commercially. This is advisory, not a
controller. A person approves the plan and the quality gate stays human. I am
not trying to replace ERP, MES, SCADA or ZLD control. I am trying to connect two
decisions that currently happen in separate rooms: what production picks today,
and what treatment pays for tonight.

---

## Supporting notes

### Why the answer is shaped this way

The quickest way to lose a technical panel is claiming novelty over something
they know is forty years old. Counter-current rinsing and low-salt chemistry are
both well established, and a textile or chemical engineer will know it
immediately. So everything gets conceded by name in the first three sentences,
before anything is claimed.

Clearing away what is not new also does real work. Once that ground is given up,
the remaining claim is narrow enough to defend properly. Integration and
reframing are legitimate forms of innovation, but only if they are stated as
that rather than dressed up as invention.

### Evidence behind each claim

| Claim | Basis |
|---|---|
| Counter-current rinsing is established BAT | EU IPPC BAT Reference Document for the Textiles Industry |
| Low-electrolyte reactive dyes are commercial | Reactive dyeing literature: 5–40 g/L low-salt against 50–80 g/L conventional |
| Ascending shade sequencing is standard practice | Stated as not-invented in `core/optimizer.py` and in the interface |
| 0.0% against −20.0% | `zld.sensitivity_salt_vs_water()`, computed live |
| Option C refused at 2.6 h late | `figures.json` → `options.OPTION_C`, `firm_date_breaches = 1` |
| Constraints are feasibility, not penalty | `core/optimizer.py` → `check_constraints()`; an infeasible plan cannot be recommended at any objective value |
| Advisory, never autonomous | `automatic_release` is hardcoded `False` and no code path sets it true |

### What the answer deliberately avoids claiming

- No ownership of sequencing, rinsing methods, low-salt chemistry, RO, ZLD or
  evaporator technology.
- No suggestion that existing ERP or ZLD systems are bad or missing something.
  They solve their own problems well. The gap is between them.
- No claim to replace any of those systems.

### The hardest follow-up

**"So it's scheduling software with extra reporting?"**

The scheduling is how it gets delivered, not what the contribution is. The
contribution is that the objective being optimised now contains a consequence
nobody prices at decision time, and that this consequence turns out to be driven
by a different variable than the whole industry is targeting. If it were really
just "reorder your lots", the engine would not refuse its own lowest-water plan,
and the 0.0 percent result would not exist to be found.
