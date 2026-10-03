# Optimization engine

## Implemented method — REAL

The server runs a deterministic greedy constructive heuristic on a synthetic batch queue. Each candidate transition uses the configurable burden rules in `config/changeover_rules.json`.

```
objective = water_weight × modeled_transition_water
          + deadline_weight × modeled_lateness_penalty
```

The fixed input order is evaluated as the common baseline. The heuristic result is accepted only if its objective is strictly better; otherwise the baseline is returned with `baseline_retained: true`.

## Constraints

Hard input constraints are non-empty batch queues, unique identifiers, known residue classes, non-negative deadline values, and no safety-release decision. The API returns `NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS` with an explanation for an invalid queue.

Modeled deadline pressure is a soft objective term. It is not a validated production deadline constraint. Campaign, tank, staffing, allergen, recipe and line-availability constraints are not modeled and must not be inferred.

## Verification

`tests/test_core.py` checks deterministic generation, non-negative burdens, order preservation, no-worse default water demand, and invalid input rejection. `scripts/run_experiments.py` evaluates 100 synthetic seeds rather than a selected scenario.

## Limitation

This is not a proof of global optimality. A future plant pilot should replace the synthetic data and solve the agreed site constraint set with an appropriate optimizer.
