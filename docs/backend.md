# Backend and audit system

## Implemented — REAL

The Python standard-library server exposes functional JSON APIs for batch retrieval, optimization, cleaning simulation, water screening, impact calculation, pilot architecture, model governance, assumptions, audit events and health. Responses carry `X-Request-ID` headers. Audit events contain an event ID, UTC timestamp, action, detail and classification.

## Persistence boundary

The server keeps audit events in process memory for the active local demonstration session. There is no SQLite or PostgreSQL database in this build. A restart clears the audit trail. The target durable schema is in `data_model.md`; calling this database-backed would be inaccurate.

## Error behavior

Invalid JSON returns HTTP 400 with a human-readable error. Invalid batch queues return a no-feasible-plan response with a constraint explanation. Missing or degraded sensor signals return a safe fallback rather than a cleaning release.
