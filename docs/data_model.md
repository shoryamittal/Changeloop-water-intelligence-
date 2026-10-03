# Data model

## Prototype implementation — REAL, in-memory

| Entity | Purpose | Current storage |
|---|---|---|
| Batch | Synthetic queue item used by optimizer | Generated per request |
| Changeover | Transition burden between two batches | Calculated on request |
| Cleaning run | Synthetic sensor trajectory and safety status | Calculated on request |
| Water screen | Illustrative recovery compatibility result | Calculated on request |
| Impact calculation | Common-baseline incremental ledger | Calculated on request |
| Audit event | Action and timestamp | Process-memory list |

The in-memory audit log is real within a running demonstration session but is **not persistent storage**.

## Target database schema — ARCHITECTED

| Table | Key fields | Purpose |
|---|---|---|
| plants / lines | id, site scope, line status | Multi-site configuration |
| products / batches | id, family, deadline, validated constraints | Planning inputs |
| changeovers / cleaning_cycles | ids, baseline, approval, outcome | Traceability |
| sensor_readings | timestamp, signal, validity, source | Signal-quality history |
| water_streams / reuse_recommendations | volume, quality state, destination, approval | Cascade decisions |
| optimization_runs / impact_calculations | config version, baseline, result | Reproducibility |
| model_versions / model_predictions | version, features, confidence, outcome | Governance |
| assumptions / source_register / audit_logs | version, evidence, actor, action | Evidence and audit trail |

## Constraint classification

| Type | Examples | Prototype behavior |
|---|---|---|
| Hard | Non-empty unique batches, valid residue class, non-negative deadline, no automatic safety release | Reject input or return a safe fallback |
| Soft | Modeled water burden and deadline pressure | Weighted in the heuristic objective |
| Unmodeled | Campaigns, tank capacity, staffing, allergen controls, validated CIP recipes | Explicitly out of scope pending site data |
