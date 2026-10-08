# ChangeLoop — Question 3

## The question

**What is new here? What is the closest existing method, and how is yours
different?**

## My answer

Let me name what already exists, because most of this problem is already served
by good technology.

Production planning and ERP systems already schedule dye lots against delivery
dates. Counter-current rinsing already reduces water use inside the dyehouse, and
it has been Best Available Technique for decades. Low-electrolyte reactive dyes
are a commercial product you can buy today. Reverse osmosis, evaporators and ZLD
control systems already handle the effluent once it arrives.

**None of that is my invention, and I do not claim any of it.** Sequencing lots
light-to-dark is standard dyehouse practice. If someone tells the jury that
resequencing production is not new, they are right.

What is new is where the decision gets made, and what information is inside it.

Today the sequence runs one way: production chooses a plan, the effluent arrives
at the treatment plant, and the cost shows up afterwards on somebody else's
account. ChangeLoop moves the downstream consequence into the upstream decision,
so the plan is chosen with the treatment cost already visible.

Three things follow from that, and these are what I would defend as the actual
contribution.

**Salt becomes the lever, not water.** Every tool in this space counts water.
But in a closed loop, the reject you must boil is set by salt mass over the
concentration ceiling, so water volume on its own barely moves the energy bill.
The engine demonstrates this live: cut water 20 percent, evaporator energy moves
0.0 percent; cut salt 20 percent, it falls 20. A planner optimising water alone
is pulling a lever that is not connected to the cost.

**The downstream cost is computed during planning, not billed afterwards.** Steam,
carbon and treatment cost are evaluated for each candidate plan before one is
chosen, instead of appearing weeks later at a shared plant.

**Operational commitments are constraints, not penalties.** A firm ship date
cannot be traded for an environmental gain, no matter how large. In the worked
example, the plan that saves almost half the fresh water is refused because it
delays one order by 2.6 hours. That refusal is the design working, not failing.

There is a fourth difference that matters commercially: this is advisory. It is
not a controller. A named person approves the plan, and the quality gate stays
human. I am not trying to replace ERP, MES, SCADA or ZLD control. I am trying to
connect two decisions that are currently made in separate rooms — what production
chooses today, and what treatment has to pay for tonight.

---

## Supporting notes

### Why I answered it this way

The fastest way to lose a technical jury is to claim novelty over something they
know is forty years old. Counter-current rinsing and low-salt chemistry are both
well-established, and a textile or chemical engineer on the panel will know it
immediately. So the answer concedes all of it in the first three sentences, by
name, before claiming anything.

The concession also does real work: by clearing away what is *not* new, the
remaining claim becomes sharp and defensible instead of vague. The contribution
is integration and framing, which is a legitimate and common form of innovation.

I included the refused plan again because it is the clearest single proof that
the system was designed around factory reality rather than a competition metric.

### Evidence behind each claim

| Claim | Basis |
|---|---|
| Counter-current rinsing is established BAT | EU IPPC BAT Reference Document for the Textiles Industry |
| Low-electrolyte reactive dyes are commercial | Published reactive dyeing literature; 5–40 g/L low-salt vs 50–80 g/L conventional |
| Ascending shade sequencing is standard practice | Stated as not-invented in `core/optimizer.py` and in the UI |
| 0.0% vs −20.0% | `zld.sensitivity_salt_vs_water()`, computed live |
| Option C refused at 2.6 h late | `figures.json` → `options.OPTION_C`; `firm_date_breaches = 1` |
| Constraints are feasibility, not penalty | `core/optimizer.py` → `check_constraints()`; infeasible plans cannot be recommended at any objective value |
| Advisory, never autonomous | `automatic_release` is hardcoded `False`; no code path sets it true |

### What I deliberately did not claim

- No ownership of sequencing, rinsing methods, low-salt chemistry, RO, ZLD or
  evaporator technology.
- No claim that existing ERP or ZLD systems are bad or missing. They solve their
  own problems well. The gap is between them, not inside them.
- No claim to replace any of those systems.

### The hardest follow-up, and my answer

**"So it is just scheduling software with extra reporting?"**

The scheduling is the delivery mechanism, not the contribution. The contribution
is that the objective being optimised includes a consequence nobody currently
prices at decision time, and that the consequence turns out to be driven by a
different variable than the whole industry is targeting. If the answer were only
"reorder your lots," the engine would not refuse its own lowest-water plan, and
the 0.0 percent result would not exist.
