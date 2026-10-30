# ChangeLoop Water Intelligence — Product Specification & Truth

## 1. PRODUCT MISSION & THESIS

Water waste in textile manufacturing is not a reporting problem. It is a **physics and operations research decision problem**.

A dye lot sequencing decision taken in a dyehouse in the morning directly dictates how much boiler steam the downstream Zero Liquid Discharge (ZLD) thermal evaporator must burn that night. No legacy SCADA, MES, or ERP system connects those two physical realities.

### The Governing Physical Law
**Evaporator steam consumption is set by dissolved salt mass, never by water volume.**
$$\text{RO Reject Volume to Boil } (\text{m}^3) = \frac{\text{Dissolved Salt Mass } (\text{kg})}{60\text{ kg/m}^3 \text{ } (60,000\text{ mg/L})}$$
$$\text{Evaporator Thermal Energy } (\text{kWh}) = \text{RO Reject Volume } (\text{m}^3) \times 188\text{ kWh/m}^3$$

- **Water Volume Invariant:** Counter-current cascade rinsing reduces machine circulation water by `~25%`, but alters evaporator steam by **`0.00%`** (salt mass is conserved).
- **Salt Mass Invariant:** Reducing dissolved salt mass by `20%` directly cuts evaporator steam by **`20.00%`**.
- **CPCB Empirical Invariant:** At the Central Pollution Control Board (CPCB) Tirupur effluent baseline of `18,340 mg/L` TDS and a `60,000 mg/L` membrane limit, the leftover RO reject share is mathematically and empirically **`30.57%` (`~30.6%`)**.

---

## 2. THE FOUR VISITOR MODES (Paul Bakaus `impeccable` Framework)

ChangeLoop addresses four distinct personas through dedicated operational modes:

| Mode | Target User | Primary Objective | UI/UX Doctrine |
| :--- | :--- | :--- | :--- |
| **OPERATE** | Dyehouse Shift Planner, Quality Supervisor | Execute optimal lot sequences, evaluate early wash-off releases, enforce safety gates | High-density SCADA controls, instant keyboard navigation (`[T]`, `[Cmd+K]`), zero decorative clutter, fail-closed safety prompts |
| **EXPLORE** | Process Engineer, CETP Operations Manager | Coordinate multi-mill MEE load shedding, calibrate toroidal conductivity against alkali interference, model boiler fuels | Real-time multi-variable hydrographs, interactive parameter sweeps, live causal flow tracing |
| **PERSUADE** | Mill Owner, CETP Board Member, Export Director | Review 3-Pillar ROI, test "Weekend-Script Defense Simulator", inspect CBAM carbon certificates | Authoritative typography, bold contrast on key verdicts, zero marketing fluff or generic cards |
| **READ** | TNPCB / CPCB Inspector, Textile Researcher | Audit the 25 open coefficients, verify cryptographic SHA-256 hash chains | Editorial clarity, monospaced tabular figures, full citation provenance |

---

## 3. CORE ARCHITECTURAL INVARIANTS

1. **100% Server-Side Mathematical Authority:** The client browser never computes savings, volumes, or emissions. Every figure rendered on screen originates from a signed server response.
2. **Zero Autonomous PLC Actuation:** ChangeLoop is strictly an advisory copilot. It never actuates pumps, valves, or machine drives. Every physical transition requires an authenticated human decision.
3. **Fail-Safe Sensor Hold Governance:** Whenever sensor data drops below `95.0%` completeness, packets drop, or readings drift outside physical bounds, the system enters `STATE = HOLD` and claims **`Rs 0` savings and `0.0 kg` CO2**.
4. **Honesty Gate in Evidence Registry:** All 25 coefficients are maintained strictly as `17 PUBLISHED`, `4 DERIVED`, `4 ASSUMED`, and `0 MEASURED` until live pilot telemetry is cryptographically verified.
5. **Zero Cargo Rejection Guarantee:** Shading sequences strictly enforce monotonic Light-to-Dark transitions (`PASTEL -> LIGHT -> MEDIUM -> DARK -> REACTIVE_BLACK`) and hard delivery pruning, guaranteeing `0` dye bleeds ($\Delta E \le 0.8$) and `0` emergency boil-outs.

---

## 4. ROLE-BASED ACCESS CONTROL (RBAC) MATRIX

ChangeLoop provides 4 core industrial roles with server-side signed `httpOnly` session cookies:

- `PLANNER`: Runs multi-machine MILP solver, reviews shift schedules, submits pre-shift decisions.
- `SUPERVISOR`: Evaluates real-time toroidal rinse curves, authorizes early wash-off terminations, logs SITRA lab tickets.
- `CETP_OPERATOR`: Inspects multi-mill salt attribution, coordinates peak evaporator load shedding, manages consortium dye procurement.
- `ADMIN / AUDITOR`: Manages coefficient evidence registry, recomputes SHA-256 ledger integrity, exports EU CBAM carbon certificates.
