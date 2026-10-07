# Archive — the project this one grew out of

ChangeLoop began as **ClearLoop**, a decision-support prototype for reducing
cleaning-water demand around product changeovers in cosmetics manufacturing
(clean-in-place, or CIP). It was then repositioned onto Indian textile
wet-processing under a court-mandated Zero Liquid Discharge regime, which is
where it is now.

The repositioning kept the *method* and replaced the *domain*. Several ideas
that look original in the current system were worked out in that earlier
project, and this folder is where that provenance is recorded rather than
quietly absorbed.

## What is kept here, and why

| File | Why it survived |
|---|---|
| [`loreal_edition.md`](loreal_edition.md) | The full specification of the cosmetics edition, written so it could be rebuilt if that domain is ever wanted again. |
| [`clearloop_theory_and_method.md`](clearloop_theory_and_method.md) | The intellectual lineage. The Prevent / Adapt / Cascade / Measure structure and the REAL / SIMULATED / ASSUMED / ARCHITECTED evidence labels were set out here first, and became the evidence classes enforced in `core/factors.py`. Also the rule that recovered water is never added to avoided demand, which is still the accounting rule the invariants check. |
| [`clearloop_red_team_reviews.md`](clearloop_red_team_reviews.md) | The red-team *method*, not its conclusions. Each reviewer persona — plant director, sustainability director, ML lead, financial controller — is asked for five strengths, ten weaknesses, ten questions, five reasons to reject, and five highest-impact fixes. Forcing a fixed count produces criticism that a looser review never reaches. Worth re-running against the current system. |
| [`clearloop_judge_qa.md`](clearloop_judge_qa.md) | The earlier hostile-question bank. Superseded by [`../jury_defence.md`](../jury_defence.md), which is longer, sharper and written for this domain — but a few questions here have no equivalent there, in particular the ML-lead line of attack on choosing local search over deep reinforcement learning. |

## What was deliberately not kept

The earlier repository held 81 files that are not here: eleven engine modules
for the CIP domain, fifteen test suites against them, synthetic changeover
datasets, benchmark and ablation scripts, process images, and roughly thirty
further documents.

None of it is dead weight that was dropped carelessly — it simply does not
describe this product. The engine computes caustic-wash cleanability and
cascade recovery for cosmetics lines; ChangeLoop computes reactive-dye
electrolyte load and evaporator duty. Carrying code for a product that no
longer exists would make the repository harder to read and would imply a
shared lineage at the code level that is not real. The lineage is at the
level of method, and that is what this folder preserves.

The earlier work also included `research/sankalp_textile_module/` — a
nine-file first sketch of the textile domain. Every one of those files has a
direct descendant in `core/`, rewritten rather than copied, so keeping the
sketch would preserve nothing the current code does not say better.

## Provenance

All of it came from `github.com/shoryamittal/Zero-Waste-Changeover-Engine`,
branch `main`, at commit:

```
cfda19bcb4386ea54e187415639ec49013137323
```

That repository's `sankalp-changeloop` branch is **fully contained** in this
repository's history — its commits `6994b35`, `c69d25e`, `df5e581`,
`9c4d252` and `c2ff505` are all reachable from `main` here, so nothing on
that branch was lost in the move.

The 19 commits that are unique to the old `main` are the CIP-domain work and
the later dashboard styling. They exist only in that repository. If it is
deleted, those 81 files go with it, and that is a decision taken knowingly
rather than by accident.

## A note on reading these

Everything in this folder describes a **different product**. The numbers,
coefficients, process physics and claims in these files do not apply to
ChangeLoop and were never re-validated against it. Nothing here feeds the
engine, and no test reads it. Treat it as history.
