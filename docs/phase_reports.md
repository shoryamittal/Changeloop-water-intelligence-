# Execution protocol phase reports

## Phase 0 — Understand

| Required report | Record |
|---|---|
| What was built | `challenge_interpretation.md`, `challenge_alignment_matrix.md`, and this phase log. |
| What was tested | Workspace and supplied-material inventory. |
| Test results | Official challenge materials were not present. |
| Assumptions | Generic technical foundation may proceed; no official requirements are inferred. |
| What remains | Official statement, rubric, rules, submission format and deadline. |
| Risks discovered | Building against an unverified rubric risks misalignment. |
| Quality gate | **CONDITIONAL PASS** — suitable for foundation work; final alignment is blocked. |

## Phase 1 — Research

| Required report | Record |
|---|---|
| What was built | Rechecked source register, expanded claim-audit fields, and created `assumptions_register.md`. |
| What was tested | Official L’Oréal webpages were checked on 2026-10-03; all UI facts were matched against the register. |
| Test results | The 2030 industrial-purpose ambition and the 2025 56% result remain supported by official L’Oréal sources. No proprietary operation fact was added. |
| Assumptions | All operational figures remain explicitly synthetic or engineering assumptions. |
| What remains | Official challenge material and any plant-specific source data. |
| Risks discovered | The official pages’ presentation can evolve; source date and scope must accompany the claim. |
| Quality gate | **PASS for public-fact integrity; CONDITIONAL for challenge-specific research.** |

## Phase 2 — Architecture

| Required report | Record |
|---|---|
| What was built | `data_model.md` differentiates current in-memory entities from the target persistent schema and defines hard, soft, and unmodeled constraints. |
| What was tested | Existing API objects and audit behavior were reconciled with the documentation. |
| Test results | Current architecture is internally consistent; audit persistence and database tables are not implemented. |
| Assumptions | Real plant integrations are future architecture only. |
| What remains | Persistent database, RBAC, durable audit events, and site-specific constraint configuration. |
| Risks discovered | A user could mistake in-memory audit data for durable records without this distinction. |
| Quality gate | **PASS for prototype architecture; NOT READY for deployment architecture.** |

## Phase 3 — Core engine

| Required report | Record |
|---|---|
| What was built | Fixed-order baseline, configurable transition-burden model, greedy optimizer, objective comparison, baseline-retention safeguard, and invalid-queue response. |
| What was tested | Unit tests for deterministic data, non-negative burden, queue preservation, no-worse water demand, duplicate batches and 100 synthetic scenarios. |
| Test results | Core invariant tests passed; the experiment records 100 feasible synthetic scenarios. |
| Assumptions | Transition burden, duration and deadline pressure are engineering assumptions. |
| What remains | Site-specific hard constraints and a solver selected for the validated constraint set. |
| Risks discovered | The heuristic does not establish global optimum and deadlines are only modeled softly. |
| Quality gate | **PASS for synthetic advisory engine; NOT VALIDATED for plant scheduling.** |

## Phase 4 — Simulation

| Required report | Record |
|---|---|
| What was built | Deterministic synthetic cleaning signals, normal and failure states, endpoint signal, recovery-screen input and mandatory human safety gate. Sensor drift is now implemented as a blocking failure mode. |
| What was tested | Missing and drift sensor tests; safety gate test; live UI failure-state check. |
| Test results | Fault states return insufficient-data status and automatic release remains false. |
| Assumptions | All signal shapes, endpoint probability and stream values are synthetic. |
| What remains | Held-out real-data validation, calibrated signal thresholds, and quality acceptance ground truth. |
| Risks discovered | A synthetic endpoint probability could be mistaken for an ML performance claim; documentation now states it is not trained or validated. |
| Quality gate | **PASS for safe simulation; NOT VALIDATED as a cleaning-control model.** |

## Phase 5 — Impact

| Required report | Record |
|---|---|
| What was built | Common-baseline Prevent → Adapt ledger, separate Cascade potential, negative-volume protections, and recovery compatibility boundary. |
| What was tested | Water invariants covering excessive adaptive input and negative recovery input. |
| Test results | Ledger and cascade paths cannot return negative modeled water volumes. |
| Assumptions | All water amounts are synthetic or illustrative; no CO2e or economics are calculated. |
| What remains | Metered plant-boundary methodology, quality data, treatment method, business inputs and sensitivity analysis. |
| Risks discovered | Potential reuse can be mistaken for avoided demand; the ledger retains it as a separate measure. |
| Quality gate | **PASS for synthetic accounting; NOT VALIDATED for site sustainability reporting.** |

## Phase 6 — Backend

| Required report | Record |
|---|---|
| What was built | Functional local APIs, request IDs, event IDs, structured in-memory audit events, health endpoint and human-readable invalid-input responses. |
| What was tested | Existing endpoint smoke tests and core tests; compilation. |
| Test results | API smoke test and invariant suite previously passed; persistence is intentionally absent. |
| Assumptions | A local in-memory session is sufficient for the competition demo. |
| What remains | SQLite database, durable audit retention, authentication, RBAC, rate limiting, CORS policy and OT-security review. |
| Risks discovered | A process restart clears audit data, so it cannot serve as a compliance record. |
| Quality gate | **PASS for local prototype backend; NOT READY for production integration.** |

## Phase 7 — Frontend

| Required report | Record |
|---|---|
| What was built | Responsive industrial dashboard, decision trace, safety messages, signal chart rendered from API data, missing-sensor and drift controls, impact ledger and pilot section. |
| What was tested | Browser visual review and interaction check for the missing-sensor failure state. |
| Test results | Dashboard rendered; visible failure state reported insufficient data; no control implies automatic release. |
| Assumptions | Presentation uses the local API and deterministic synthetic demo data. |
| What remains | Full keyboard-only audit, screen-reader review, official presentation assets and mobile device testing. |
| Risks discovered | The UI is a single-screen demo, not a complete operational workstation. |
| Quality gate | **PASS for competition prototype UX; NOT validated for plant HMI use.** |

## Phase 8 — Integration

| Required report | Record |
|---|---|
| What was built | End-to-end connection among optimizer, cleaning simulator, safety fallback, cascade screen, impact ledger, pilot architecture and audit events. |
| What was tested | Live local API journey covering optimization, drift fault, water screen, impact, pilot and audit retrieval. |
| Test results | End-to-end integration flow passed. Drift returned insufficient data; impact stayed non-negative; pilot remained architected; audit events were created. |
| Assumptions | A local in-memory session is sufficient for the integration demonstration. |
| What remains | Durable data integration, database persistence, identity controls and plant-system connection. |
| Risks discovered | A local process restart removes the audit history. |
| Quality gate | **PASS for local end-to-end demonstration; NOT READY for deployment integration.** |

## Phase 9 — Validation

| Required report | Record |
|---|---|
| What was built | Expanded malformed-input and accounting-invariant tests, 100-scenario ablation script, and local timing script. |
| What was tested | Python compilation; 13 unit/invariant tests; 100 scenario experiment; 100 scenario ablation; local function timing. |
| Test results | 13/13 tests passed. Optimizer experiment: 100/100 feasible synthetic scenarios; mean modeled Prevent reduction 158.66 L. Ablation output preserves separate Cascade potential. Local means: optimize 0.378 ms, cleaning 0.223 ms, impact 0.270 ms. |
| Assumptions | Scenario, adaptive and cascade values are synthetic / illustrative. Timing is local development-machine timing only. |
| What remains | Real-data holdout validation, production-scale performance testing, browser accessibility audit and durable integration tests. |
| Risks discovered | The complete solver quality and real endpoint model cannot be inferred from synthetic tests. |
| Quality gate | **PASS for reproducible prototype validation; NOT VALIDATED for plant performance.** |
