# Assumptions register

| ID | Description | Value / unit | Reason | Source | Range | Sensitivity | Replace with real data | Impact if wrong |
|---|---|---|---|---|---|---|---|---|
| A-001 | Base changeover water demand | 120–260 L, synthetic base | Required for optimizer demonstration | Not publicly verified — engineering assumption | Configurable by residue class | High | Per-line meter records | Changes modeled demand and ranking |
| A-002 | Base cleaning duration | 18–40 min, synthetic base | Required for deadline-pressure display | Not publicly verified — engineering assumption | Configurable by residue class | High | Validated work instructions / historian | Changes schedule feasibility |
| A-003 | Transition multipliers | 1.0–1.7 | Creates causal synthetic transition burden | Not publicly verified — engineering assumption | `config/changeover_rules.json` | High | Qualified process data | Changes optimizer recommendations |
| A-004 | Sensor curve and noise | Synthetic curve, fixed seed | Demonstrates safe signal handling | SYNTHETIC_DATA | Missing, spike, drift cases | Medium | Calibrated sensor + quality-release data | Invalidates model demonstration if presented as real |
| A-005 | Adaptive increment | 24 L illustrative | Demonstrates incremental accounting | ILLUSTRATIVE_SCENARIO | Not a forecast | High | Controlled comparable trial | Alters modeled impact only |
| A-006 | Recovered volume | 42 L illustrative | Demonstrates cascade screening | ILLUSTRATIVE_SCENARIO | Not a forecast | High | Stream meter and lab assessment | Alters potential reuse only |
