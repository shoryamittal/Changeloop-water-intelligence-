# Assumption audit

| Assumption | Why needed | Value / range | Classification | Sensitivity | Replace with real data |
|---|---|---|---|---|---|
| Changeover water burden | Optimizer needs an objective | 120–260 L base, multiplied by transition type | ENGINEERING_ASSUMPTION | High | Validated per-line changeover records |
| Changeover duration | Deadline-pressure display | 18–40 min base | ENGINEERING_ASSUMPTION | High | Validated work instructions and historian data |
| Sensor curves | Demonstrate safety behavior | Noise, missing readings and spike scenarios | SYNTHETIC_DATA | Medium | Calibrated sensor and quality-release data |
| 24 L adaptive increment | Demonstrate ledger dependency | illustrative | ILLUSTRATIVE_SCENARIO | High | Controlled plant trial with common baseline |
| 42 L recovery stream | Demonstrate screening | illustrative | ILLUSTRATIVE_SCENARIO | High | Measured stream volume and quality analysis |

All code-visible operational numbers are synthetic or assumed. They are not L’Oréal data.
