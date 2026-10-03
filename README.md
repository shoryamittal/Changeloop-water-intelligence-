# ClearLoop — Zero-Waste Changeover Engine

**A synthetic, executable decision-support prototype for the L'Oréal Sustainability Challenge 2026.**

> Simulation — not L'Oréal production data. Target integration architecture — not connected to L'Oréal systems.

ClearLoop explores one hypothesis: production sequencing, process-signal monitoring, and reuse opportunity screening can reduce **modeled** changeover water demand before water enters an existing circular loop. It does not replace validated cleaning, quality release, water treatment, or plant controls.

## Run

Requires Python 3. From this folder:

```powershell
python backend/server.py
```

Open http://localhost:8000. The API and interface run without external packages so the demonstration is reproducible in a clean environment.

If Python is not on your PATH, use the Python interpreter installed with your environment.

If Docker is available:

```powershell
docker compose up --build
```

## What is real

| Capability | Classification | Evidence |
|---|---|---|
| Optimizer, simulation, impact ledger, safety gate, audit trail | REAL | Executable local code |
| Batches, sensors, water streams, all operational values | SIMULATED | Deterministic synthetic generator |
| Changeover rules and economic parameters | ASSUMED | Configurable; documented in `docs/assumption_audit.md` |
| Plant-system connections and deployment topology | ARCHITECTED | `docs/deployment.md` |
| L'Oréal 2030 target and 2025 progress figure | VERIFIED_PUBLIC_FACT | `docs/source_register.md` |

## Core journey

1. **Prevent** — order a batch queue by modeled transition burden and deadline pressure.
2. **Adapt** — simulate sensor signals; make an endpoint *recommendation*, then enforce a human and validated-procedure gate.
3. **Cascade** — screen recovered water against illustrative compatibility rules and do not auto-approve reuse.
4. **Measure** — report incremental layers from one common baseline, avoiding double counting.

See `docs/demo_script.md`, `docs/methodology.md`, and `docs/limitations.md` before presenting.
