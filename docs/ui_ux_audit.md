# UI/UX audit — existing application

## What works and should be preserved

- The local Python backend has working endpoints for optimization, synthetic cleaning signals and failure states, water screening, impact accounting, pilot guidance, model governance, business-case calculation, audit retrieval and health.
- The default queue is deterministic; the optimizer preserves the baseline when it cannot improve the objective.
- The cleaning safety gate is prominent and does not allow automatic release.
- The impact ledger prevents negative values and keeps cascade potential separate from avoided demand.
- Existing visual foundations are usable: restrained navy / green palette, readable typography, responsive fallback, deterministic judge mode.

## Current visual problems

- One long page makes executive overview, planning, engineering evidence and pilot content compete for attention.
- The left sidebar is too sparse to operate as an application shell and does not represent application state, plant context or status.
- Content uses repeated generic white cards with inconsistent density; visual hierarchy is weak once several sections are visible.
- The current “ring” KPI is isolated from the operating workflow and the water journey is not visible as a single system.
- Button styles, warning messages and metric cards use repeated hand-built variants instead of a compact component pattern.
- A single sensor chart is helpful but not framed as a live operational panel with context, state, controls and decision implication.

## Broken or incomplete interactions

- There is no page-level navigation state: sidebar anchors only scroll the long document.
- The Scenario Lab is only an “explore another queue” button; users cannot set or compare a reproducible seed.
- The business-case API is not exposed in the interface.
- Audit events are not surfaced in the interface.
- Reset clears content and then leaves the user waiting for the caller to repopulate it; it does not restore all visible state deterministically.
- Decision buttons record a session event, but the result is only small inline text and lacks an audit view.

## Duplicated components and code patterns

- `card()` is reused, but section markup independently builds similar header, notice and control combinations.
- Alert, status, data-source and assumption treatments are repeated as plain strings rather than reusable semantic components.
- The frontend is a single HTML file, one CSS file and one compact JavaScript file; page behaviors and visual patterns are tightly coupled.

## Missing states

- Dedicated loading, empty, API-error, no-feasible-plan, and audit-empty states.
- Executive versus engineer mode.
- Business-case input-required and calculated states.
- Scenario setup, comparison and replay state.
- Live data / simulation data status at the global level.
- Clear storage state for the audit trail.

## Existing APIs and reusable backend functionality

| Endpoint | Reuse in redesign |
|---|---|
| `GET /api/batches` | Planning queue and batch details |
| `POST /api/optimize` | Planning, optimizer and scenario pages |
| `GET /api/cleaning`, `POST /api/cleaning/start` | Adaptive Cleaning page and failure demonstrations |
| `POST /api/water/analyze` | Water Cascade page |
| `POST /api/impact/calculate` | Overview and Analytics ledger |
| `GET/POST /api/business-case` | Business Case input and sensitivity page |
| `GET /api/pilot` | Pilot page |
| `GET /api/models` | Data Trust / engineering panel |
| `GET /api/audit-log`, `POST /api/optimization/decision` | Alerts and decision history |
| `GET /api/assumptions` | Data & Assumptions drawer |
| `GET /api/health` | Global connection / storage status |

## Redesign direction

Preserve the backend contract and rebuild the UI as an application shell with global simulation status, compact sidebar, executive overview, purpose-built Planning, Adaptive Cleaning, Water Cascade, Scenario Lab, Business Case, Pilot and Data Trust views. Use a small component vocabulary: status badge, source badge, metric tile, decision panel, signal panel, flow stage and empty/error state. Do not add controls that imply automatic execution or plant connectivity.
