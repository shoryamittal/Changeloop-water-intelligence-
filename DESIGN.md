# ChangeLoop Design System & Impeccable UI/UX Specification

**Design Director:** Principal Industrial Systems Architect & Staff Frontend Engineer  
**Framework:** [Paul Bakaus's `impeccable` Design Methodology](https://github.com/pbakaus/impeccable)  
**Target Cluster:** Tirupur Textile Dyeing & CETP Network (360 Dyehouses, 18 CETPs)  
**Primary Aesthetic:** Palantir Foundry, Linear, Samsara Cyber-Physical SCADA  

---

## 1. PRODUCT TRUTH & VISITOR MODE

ChangeLoop is an industrial cyber-physical operating system, not a consumer SaaS landing page. It operates in two visitor modes:

- **OPERATE (Primary):** Mission-critical shop-floor production scheduling, Branch-and-Cut Mixed-Integer Linear Program (MILP) dispatch, and fail-closed wash-off release gates. Requires rapid keyboard navigation, zero visual noise, and instantaneous state feedback.
- **EXPLORE (Secondary):** CPCB cluster hydrograph load-shedding, thermodynamic mass-balance tracing, CBAM carbon certificate accounting, and tamper-evident HMAC hash chain auditing.

### The Governing Physical Grammar
> **Water is volume moving through constrained physical paths.**
- The thickness of any stream, bar, or pipe is mathematically proportional to its volumetric flow ($m^3/\text{hr}$ or $L$).
- Evaporator steam is dictated exclusively by dissolved salt mass ($188\,\text{kWh/m}^3$), never water volume.
- Counter-current rinsing reduces machine circulation by $25\%$ but changes evaporator steam by exactly $0.00\%$.
- Every pixel communicates physical mass, thermal energy, or operator authority. Zero decorative gradients, zero neon glows, zero cartoon emojis.

---

## 2. THE 4-TIER TONAL SURFACE ARCHITECTURE

To eliminate "card-nesting hell" and generic grey washouts, ChangeLoop enforces a 4-tier dark-mode surface elevation system infused with subtle mineral slate and oceanic teal undertones:

```css
/* --- Tonal Surface Layers (Dark Theme Default) --- */
--ground-0: #090D0F; /* Deepest Abyssal Mineral Slate (Canvas Background) */
--ground-1: #0F1619; /* Operational Substrate (Navigation Rail, Context HUD) */
--ground-2: #151F23; /* Telemetry Workbench (Instrument Panels, Timeline Canvas) */
--ground-3: #1C292E; /* Tactile Interactive Components (Lots, Skid Blocks, Inputs) */
--ground-4: #23343A; /* High-Focus Overlays (Explainability Sheet, Command Palette) */

/* --- Hairlines & Structural Boundaries (Never Heavy Borders) --- */
--hair-quiet:  rgba(255, 255, 255, 0.06); /* Structural separator */
--hair-medium: rgba(255, 255, 255, 0.12); /* Interactive boundary */
--hair-focus:  rgba(56, 189, 248, 0.40);  /* Keyboard focus & selection */
```

---

## 3. STRICT TYPOGRAPHIC HIERARCHY (`/impeccable typeset`)

All numeric readouts use tabular, monospaced figures to prevent character jitter during live telemetry updates:

```css
/* Typography Engine */
--sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--mono: "JetBrains Mono", "IBM Plex Mono", Menlo, Consolas, monospace;

/* Numeric Precision Settings */
.font-tabular {
  font-feature-settings: "cv05", "cv08", "tnum", "zero";
  font-variant-numeric: tabular-nums;
}
```

### Scale & Tracking Matrix:
1. **Hero KPI Value:** `38px` / `44px` font size, `-0.04em` letter-spacing, semi-bold (`600`).
2. **Section Header (H2):** `18px` / `24px` font size, `-0.02em` letter-spacing, medium (`500`).
3. **Telemetry & Body Text:** `13.5px` / `20px` font size, normal (`400`).
4. **SCADA Parameter Label:** `10px` / `12px` font size, uppercase, `+0.12em` letter-spacing, monospace (`IBM Plex Mono`).

---

## 4. SEMANTIC PHYSICAL PALETTE

Every color maps to a physical medium or regulatory state:

| Token | Hex | Physical Medium / Meaning |
| :--- | :--- | :--- |
| `--water` | `#38BDF8` | Fresh raw water / RO permeate circulation |
| `--salt` | `#F59E0B` | Dissolved inorganic salt load ($NaCl$, $Na_2SO_4$, TDS) |
| `--steam` | `#A78BFA` | Thermal evaporator boiling duty ($188\,\text{kWh/m}^3$) |
| `--carbon` | `#94A3B8` | Scope 1 boiler combustion emissions ($CO_2e$) |
| `--emerald` | `#10B981` | Mass-balance closure, verified CBAM compliance, gate release |
| `--crimson` | `#EF4444` | Hard-pruned delivery violation, membrane limit breach, PLC lock |

---

## 5. MICRO-PHYSICS & INTERACTION CURVES (`/impeccable animate`)

- **Response Latency:** Instantaneous feedback on operator clicks (`80ms`).
- **Tactile Depress:** Physical button downstroke: `transform: translateY(1px); filter: brightness(0.94);`.
- **Easing Curve:** Fast, damped deceleration: `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Zero Slinky Springs:** No cartoon bounces, no slow layout shifts (CLS), no floating bubbles.
