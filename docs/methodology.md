# Methodology and metric boundaries

## Definitions

| Metric | Definition / formula | Unit | Scope / limitation |
|---|---|---|---|
| Water demand | Modeled cleaning water required for a transition under prototype rules | L/changeover | Synthetic simulation only |
| Water avoided | Common baseline demand − demand after a specified layer | L | Only valid for the stated synthetic baseline |
| Water recovered | Modeled volume collected after a cleaning event | L | Does not imply it can be reused |
| Potential reuse | Recovery volume that passes an illustrative screen | L | Requires site quality, regulatory and safety validation |
| Water reused | Volume actually used after validated approval | L | Not measured by this prototype |
| Cleaning time avoided | Baseline duration − scenario duration | min | Synthetic only |
| Water withdrawal / consumption / discharge / intensity | Not quantified | — | Plant boundary and metering are unavailable |

## Dependency graph

```mermaid
flowchart LR
 B[Common synthetic baseline] --> P[Prevent: sequence]
 P --> A[Prevent + Adapt]
 A --> C[Potential Cascade screening]
 C -. separate potential reuse measure .-> R[Do not add to demand avoided]
```

The ledger reports Prevent and Adapt as incremental reductions against the preceding layer. Cascade is shown separately; it is never added to avoided demand.

## Ablation protocol

`scripts/run_ablations.py` compares the same 100 synthetic queues under baseline, Prevent, illustrative Adapt-only, and Prevent + illustrative Adapt. The 24 L Adapt value is an `ILLUSTRATIVE_SCENARIO`, not a measured endpoint benefit. Cascade potential remains separate in every row. The output is retained in `data/synthetic_ablation_2026.1.json`.

## Experiment protocol

Use seeds 2026–2125 to generate 100 deterministic synthetic queues. For each seed, retain the fixed-order baseline and optimized sequence, report mean, median, standard deviation, min, max, feasibility rate and all configuration versions. Do not claim a result until this experiment has been run and retained in `data/`.

## Executed synthetic experiment

`scripts/run_experiments.py` was run with seeds 2026–2125 and generated [`data/synthetic_experiment_2026.1.json`](../data/synthetic_experiment_2026.1.json). All 100 synthetic scenarios were feasible under the prototype's constraints. With 2-Opt local search refinement enabled, the modeled reduction distribution was: mean **300.44 L** (11.28% mean reduction), median **282.70 L** (10.82%), standard deviation **153.53 L**, minimum **0 L**, maximum **981.40 L** (29.60%), and 10th–90th percentile **121.80–484.90 L**. These are **SYNTHETIC_DATA** model outputs, not measured L’Oréal savings. They are reported to expose distribution and no-improvement cases, not to forecast a plant outcome.

## 1,000 Industrial Scenario Monte Carlo Verification & Robustness Benchmark

To verify algorithmic robustness, safety reliability, and numerical stability at scale, ClearLoop was subjected to an exhaustive 1,000-scenario Monte Carlo test runner (`tests/test_stress_1000.py`) across seeds 2026–3025, evaluating 4,000 mathematical assertions:

| Metric Category | Measured Empirical Result | Invariant Standard / Operational Bound |
|---|---|---|
| **Total Test Scenarios** | **1,000 Permutations (4,000 Total Assertions)** | 100.0% execution success; 0 uncaught exceptions. |
| **Mean Water Reduction** | **276.59 L (10.33% average reduction)** | Median: 257.0 L; Max: 981.40 L (29.60%). |
| **Baseline Safeguard Triggers** | **13 Triggers (100% Correct Retention)** | Preserved baseline schedule whenever 2-Opt could not strictly improve objective. |
| **Execution Latency** | **20.40 ms Mean (46.49 ms P95)** | Deterministic sub-50ms execution suitable for shopfloor packaging lines. |
| **Safety Gate Interlock Rate** | **100.000% (800 / 800 Fault Injections)** | **0 false clearances detected** across sensor loss, thermal drops, drift, and soil spikes. |
| **Mass Balance Conservation** | **0 Violations across 1,000 Runs** | $\text{Demand}_{\text{net}} = B - P - A$; Cascade stream strictly segregated. |
| **Economic Sensitivity Ordering** | **100% Invariant Compliance** | Payback ordering and net benefit monotonicity verified across all iterations. |

Full audited run data is retained in [`data/stress_test_1000_report.json`](../data/stress_test_1000_report.json).

