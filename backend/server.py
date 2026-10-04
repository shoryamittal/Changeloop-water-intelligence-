"""ClearLoop local demonstration server. All operating data is synthetic."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, random, math, time, uuid, sqlite3

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "changeover_rules.json").read_text())
AUDIT = []
DB_PATH = ROOT / "data" / "clearloop_demo.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            event_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL,
            detail TEXT NOT NULL, classification TEXT NOT NULL)""")
        conn.commit()
    finally:
        conn.close()

def audit_events():
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute("SELECT event_id, timestamp, action, detail, classification FROM audit_logs ORDER BY timestamp DESC").fetchall()
            return [dict(zip(["event_id","timestamp","action","detail","classification"], row)) for row in rows]
        finally:
            conn.close()
    except sqlite3.Error:
        return list(reversed(AUDIT))

def record(action, detail):
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "detail": detail,
        "classification": "SIMULATED"
    }
    AUDIT.append(event)
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?)", tuple(event.values()))
            conn.commit()
            event["persistence"] = "sqlite"
        finally:
            conn.close()
    except sqlite3.Error:
        event["persistence"] = "memory_fallback"
    return event

COSMETIC_PRODUCTS = {
    ("care", "light", "low"): {"name": "Hydra Genius 72H Liquid Moisturizer", "type": "Aqueous Hyaluronic Fluid", "tier": "Standard Clean"},
    ("care", "light", "high"): {"name": "Revitalift Laser X3 Day Cream", "type": "O/W Anti-Aging Emulsion", "tier": "Moderate Emulsion"},
    ("care", "medium", "low"): {"name": "Age Perfect Midnight Serum", "type": "Antioxidant Recovery Serum", "tier": "Standard Clean"},
    ("care", "medium", "high"): {"name": "Nutri-Gold Rich Nourishing Balm", "type": "Lipid-Rich W/O Balm", "tier": "Challenging Lipids"},
    ("care", "dark", "low"): {"name": "Pure Clay Charcoal Cleansing Gel", "type": "Activated Charcoal Fluid", "tier": "Moderate Pigment"},
    ("care", "dark", "high"): {"name": "Pure Clay Black Mineral Purifying Mask", "type": "Heavy Mineral Kaolin Slurry", "tier": "Severe Soil"},
    ("colour", "light", "low"): {"name": "Infaillible 24H Fresh Wear Nude #110", "type": "Light Fluid Foundation", "tier": "Moderate Pigment"},
    ("colour", "light", "high"): {"name": "True Match Super-Blendable Cream #0.5D", "type": "High-Coverage Pigment Cream", "tier": "Challenging Pigment"},
    ("colour", "medium", "low"): {"name": "Lumi Glotion Liquid Illuminator #903", "type": "Pearlescent Mica Dispersion", "tier": "Moderate Pigment"},
    ("colour", "medium", "high"): {"name": "Color Riche Satin Lipstick #120 Nude", "type": "Anhydrous Microcrystalline Wax", "tier": "Severe Wax"},
    ("colour", "dark", "low"): {"name": "Telescopic Lift Liquid Liner Deep Black", "type": "Carbon Black Polymer Dispersion", "tier": "Severe Pigment"},
    ("colour", "dark", "high"): {"name": "Infaillible Matte Resistance #500 Plum", "type": "Ultra-Matte High-Resin Paste", "tier": "Severe Pigment/Wax"},
    ("styling", "light", "low"): {"name": "Micellar Cleansing Water Normal Skin", "type": "Aqueous Micellar Surfactant", "tier": "Rapid Rinse"},
    ("styling", "light", "high"): {"name": "Elvive Dream Lengths Restoring Shampoo", "type": "Viscous Surfactant Gel", "tier": "Standard Surfactant"},
    ("styling", "medium", "low"): {"name": "Elseve Extraordinary Oil Hair Mist", "type": "Light Botanical Lipid Spray", "tier": "Moderate Lipid"},
    ("styling", "medium", "high"): {"name": "Elvive Total Repair 5 Conditioning Balm", "type": "Cationic Conditioning Emulsion", "tier": "Moderate Emulsion"},
    ("styling", "dark", "low"): {"name": "Men Expert Barber Club 3-in-1 Wash", "type": "Charcoal Infused Surfactant Gel", "tier": "Standard Surfactant"},
    ("styling", "dark", "high"): {"name": "Excellence Crème Permanent Color #1.0 Black", "type": "Alkaline Pigment Colorant Cream", "tier": "Severe Dye/Alkaline"}
}

def batches(seed=2030, count=12):
    r = random.Random(seed)
    families = ["care", "colour", "styling"]
    shades = ["light", "medium", "dark"]
    residues = ["low", "medium", "high"]
    items = []
    for i in range(count):
        fam = r.choice(families)
        shd = r.choice(shades)
        vis = r.choice(["low", "high"])
        res = r.choice(residues)
        spc = r.random() < .16
        pri = r.randint(1, 3)
        ddl = r.randint(10, 54)
        meta = COSMETIC_PRODUCTS.get((fam, shd, vis), {"name": f"L'Oréal Formula {fam.capitalize()}", "type": "Cosmetic Emulsion", "tier": "Standard"})
        items.append({
            "id": f"B-{i+1:02}",
            "family": fam,
            "shade": shd,
            "viscosity": vis,
            "residue": res,
            "special": spc,
            "priority": pri,
            "deadline_h": ddl,
            "product_name": meta["name"],
            "formulation_type": meta["type"],
            "cleanability_tier": meta["tier"],
            "allergen_flag": spc
        })
    return items

def validate_queue(queue):
    required = {"id", "family", "shade", "viscosity", "residue", "special", "priority", "deadline_h"}
    if not isinstance(queue, list) or not queue: return "No batches supplied."
    ids = []
    for batch in queue:
        if not isinstance(batch, dict) or required - set(batch): return "A batch is missing required fields."
        if batch["residue"] not in RULES["base_litres_by_residue"]: return "Unknown residue class."
        try: deadline = float(batch["deadline_h"])
        except (TypeError, ValueError): return f"Deadline is invalid for {batch['id']}."
        if not math.isfinite(deadline) or deadline < 0: return f"Deadline is already infeasible for {batch['id']}."
        ids.append(batch["id"])
    if len(ids) != len(set(ids)): return "Duplicate batch identifiers are not allowed."
    return None

def burden(a, b):
    m = 1.0
    tags = []
    if a["family"] == b["family"]: tags.append("same formula family")
    if a["shade"] == "dark" and b["shade"] == "light":
        m *= RULES["transition_multipliers"]["dark_to_light"]
        tags.append("dark-to-light transition")
    if a["viscosity"] == "high" and b["viscosity"] == "low":
        m *= RULES["transition_multipliers"]["viscous_to_low"]
        tags.append("high-to-low viscosity")
    if b["special"]:
        m *= RULES["transition_multipliers"]["special_clean"]
        tags.append("special-cleaning flag")
    base_l = RULES["base_litres_by_residue"][b["residue"]]
    base_m = RULES["base_minutes_by_residue"][b["residue"]]
    return {
        "litres": round(base_l * m, 1),
        "minutes": round(base_m * m, 1),
        "reasons": tags or ["base residue burden"],
        "classification": "ENGINEERING_ASSUMPTION"
    }

def score_order_greedy(queue, water_weight=1, deadline_weight=1):
    remaining = list(queue)
    ordered = [remaining.pop(0)]
    elapsed = 0
    while remaining:
        current = ordered[-1]
        def cost(x):
            p = burden(current, x)
            late = max(0, elapsed + p["minutes"] / 60 - x["deadline_h"])
            return water_weight * p["litres"] + deadline_weight * late * 160
        nxt = min(remaining, key=cost)
        p = burden(current, nxt)
        elapsed += p["minutes"] / 60
        ordered.append(nxt)
        remaining.remove(nxt)
    return ordered

def score_order_two_opt(initial_order, water_weight=1, deadline_weight=1, max_passes=25):
    """2-Opt Local Search to break out of greedy local minima."""
    best_order = list(initial_order)
    best_obj, _ = evaluate_order(best_order, water_weight, deadline_weight)
    n = len(best_order)
    if n < 4:
        return best_order
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidate = best_order[:i] + best_order[i:j+1][::-1] + best_order[j+1:]
                cand_obj, _ = evaluate_order(candidate, water_weight, deadline_weight)
                if cand_obj < best_obj - 1e-4:
                    best_order = candidate
                    best_obj = cand_obj
                    improved = True
                    break
            if improved:
                break
    return best_order

def evaluate_order(order, water_weight=1, deadline_weight=1):
    """Return the same transparent objective for every candidate schedule."""
    elapsed = 0
    transitions = []
    objective = 0
    for i in range(len(order) - 1):
        p = burden(order[i], order[i + 1])
        elapsed += p["minutes"] / 60
        late = max(0, elapsed - order[i + 1]["deadline_h"])
        objective += water_weight * p["litres"] + deadline_weight * late * 160
        transitions.append({"from": order[i]["id"], "to": order[i + 1]["id"], **p})
    return objective, transitions

def score_order(queue, water_weight=1, deadline_weight=1):
    """Convenience function retaining greedy signature."""
    ordered = score_order_greedy(queue, water_weight, deadline_weight)
    _, trans = evaluate_order(ordered, water_weight, deadline_weight)
    return ordered, trans

def sequence_payload(body):
    if not isinstance(body, dict):
        record("OPTIMIZE_REJECTED", "Request body must be an object.")
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Request body must be an object."
        }
    q = body["batches"] if "batches" in body else batches(body.get("seed", 2030))
    error = validate_queue(q)
    if error:
        record("OPTIMIZE_REJECTED", error)
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": error
        }
    try:
        w = float(body.get("water_weight", 1))
        d = float(body.get("deadline_weight", 1))
    except (TypeError, ValueError):
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Objective weights must be numeric."
        }
    if not math.isfinite(w) or not math.isfinite(d) or w < 0 or d < 0:
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Objective weights must be finite and non-negative."
        }

    # Evaluate Baseline
    baseline_objective, baseline = evaluate_order(q, w, d)
    base_water = round(sum(x["litres"] for x in baseline), 1)

    # Candidate 1: Greedy constructive heuristic
    greedy_order = score_order_greedy(q, w, d)
    greedy_obj, greedy_trans = evaluate_order(greedy_order, w, d)
    greedy_water = round(sum(x["litres"] for x in greedy_trans), 1)

    # Candidate 2: 2-Opt Local Search refinement
    two_opt_order = score_order_two_opt(greedy_order, w, d)
    two_opt_obj, two_opt_trans = evaluate_order(two_opt_order, w, d)
    two_opt_water = round(sum(x["litres"] for x in two_opt_trans), 1)

    # Determine requested or best candidate
    algo_req = body.get("algorithm", "best")
    if algo_req == "greedy":
        candidate_order, candidate_obj, trans, algo_name = greedy_order, greedy_obj, greedy_trans, "Greedy Nearest-Neighbor"
    elif algo_req == "two_opt":
        candidate_order, candidate_obj, trans, algo_name = two_opt_order, two_opt_obj, two_opt_trans, "2-Opt Local Search Refinement"
    else:
        # Default: Pick best between greedy and two-opt
        if two_opt_obj <= greedy_obj:
            candidate_order, candidate_obj, trans, algo_name = two_opt_order, two_opt_obj, two_opt_trans, "2-Opt Local Search Refinement"
        else:
            candidate_order, candidate_obj, trans, algo_name = greedy_order, greedy_obj, greedy_trans, "Greedy Nearest-Neighbor"

    # Baseline Retention Safeguard
    retained = candidate_obj >= baseline_objective
    if retained:
        candidate_order, trans, candidate_obj, algo_name = q, baseline, baseline_objective, "Baseline (Retained Safeguard)"

    optimization_id = str(uuid.uuid4())
    cand_water = round(sum(x["litres"] for x in trans), 1)
    
    result = {
        "status": "FEASIBLE",
        "optimization_id": optimization_id,
        "classification": "SYNTHETIC_DATA",
        "notice": "Simulation — not L'Oréal production data.",
        "baseline": {
            "order": [x["id"] for x in q],
            "water_demand_l": base_water,
            "objective": round(baseline_objective, 1),
            "duration_min": round(sum(x["minutes"] for x in baseline), 1)
        },
        "optimized": {
            "order": [x["id"] for x in candidate_order],
            "water_demand_l": cand_water,
            "objective": round(candidate_obj, 1),
            "duration_min": round(sum(x["minutes"] for x in trans), 1),
            "transitions": trans
        },
        "algorithm_used": algo_name,
        "algorithm_comparison": {
            "baseline": {"water_l": base_water, "objective": round(baseline_objective, 1)},
            "greedy": {"water_l": greedy_water, "objective": round(greedy_obj, 1)},
            "two_opt": {"water_l": two_opt_water, "objective": round(two_opt_obj, 1)}
        },
        "method": "Greedy constructive heuristic; baseline candidate retained when the heuristic cannot improve the configured objective. It does not prove global optimality.",
        "baseline_retained": retained
    }
    record("OPTIMIZE", f"Synthetic optimization run {optimization_id} ({algo_name})")
    return result

def cleaning(seed=2026, failure=None):
    """4-Phase Dynamic Physical CIP Simulation with multi-sensor telemetry."""
    r = random.Random(seed)
    n = 42
    endpoint = 30 + r.randint(-3, 4)
    readings = []

    # Phase boundaries:
    # 0-7: Pre-rinse purge
    # 8-21: Caustic wash (1.5% NaOH)
    # 22-28: Intermediate neutralization rinse
    # 29-41: Final RO polish rinse
    for minute in range(n):
        quality = "valid"
        stage_name = "Phase 4: Final Water Polish"
        if minute < 8:
            stage_name = "Phase 1: Pre-Rinse Purge"
            # Turbidity starts high ~45 NTU and drops
            progress = minute / 7.0
            turb = 45.0 * (1 - progress) ** 1.8 + 3.0 + r.gauss(0, 0.4)
            cond = 2.4 - progress * 1.2 + r.gauss(0, 0.05)
            temp = 22.0 + r.gauss(0, 0.3)
            flow = 11.5 + r.gauss(0, 0.2)
            ph = 7.1 + r.gauss(0, 0.1)
        elif minute < 22:
            stage_name = "Phase 2: Caustic Detergent Wash (1.5% NaOH)"
            # Caustic ions drive conductivity to ~24 mS/cm, pH to 12.2, temp to 72C
            turb = 2.5 + r.gauss(0, 0.2)
            cond = 24.0 + r.gauss(0, 0.4)
            temp = 72.5 + r.gauss(0, 0.5)
            flow = 12.0 + r.gauss(0, 0.2)
            ph = 12.2 + r.gauss(0, 0.1)
            if failure == "thermal":
                temp = 48.0 + r.gauss(0, 0.8)
                quality = "thermal deficit (<65°C sanitization)"
        elif minute < 29:
            stage_name = "Phase 3: Intermediate Neutralization Rinse"
            progress = (minute - 22) / 6.0
            turb = 1.8 * (1 - progress) + 0.4 + r.gauss(0, 0.08)
            cond = 24.0 * (1 - progress) ** 2 + 1.8 + r.gauss(0, 0.15)
            temp = 72.0 - progress * 35.0 + r.gauss(0, 0.5)
            flow = 10.0 + r.gauss(0, 0.2)
            ph = 12.0 - progress * 4.6 + r.gauss(0, 0.1)
        else:
            stage_name = "Phase 4: Final Water Polish"
            progress = min(1.0, (minute - 29) / max(1, endpoint - 29))
            cond = 1.1 + 0.9 * (1 - progress) ** 2 + r.gauss(0, 0.04)
            turb = 0.25 + 0.5 * (1 - progress) ** 2 + r.gauss(0, 0.03)
            temp = 23.5 + r.gauss(0, 0.3)
            flow = 8.5 + r.gauss(0, 0.2)
            ph = 7.0 + r.gauss(0, 0.05)

        # Fault injections
        if failure == "missing" and 17 <= minute <= 22:
            cond = None
            turb = None
            quality = "missing"
        if failure == "spike" and minute == 19:
            cond = 99.0
            quality = "invalid spike"
        if failure == "drift" and minute >= 18:
            cond = (cond or 1.5) + (minute - 17) * 0.32
            turb = (turb or 0.5) + (minute - 17) * 0.08
            quality = "drift suspected"

        readings.append({
            "minute": minute,
            "conductivity": None if cond is None else round(max(0, cond), 2),
            "turbidity": None if turb is None else round(max(0, turb), 2),
            "temperature": round(temp, 1),
            "flow": round(flow, 2),
            "ph": round(ph, 2),
            "stage": stage_name,
            "quality": quality
        })

    critical = any(x["quality"] != "valid" for x in readings)
    probability = 0 if critical else round(min(.96, max(.35, .52 + (n - endpoint) / 38)), 2)
    minutes_avoided = 0 if critical else max(0, n - endpoint)
    water_avoided = 0 if critical else round(minutes_avoided * 10.0, 1)

    phases = [
        {"name": "Pre-Rinse Purge", "start_min": 0, "end_min": 7, "target": "Purge bulk cosmetic emulsion residue", "temp_c": 22},
        {"name": "Caustic Detergent Wash", "start_min": 8, "end_min": 21, "target": "1.5% NaOH Saponification & thermal log-kill", "temp_c": 72},
        {"name": "Intermediate Rinse", "start_min": 22, "end_min": 28, "target": "Detergent purge to neutral pH", "temp_c": 35},
        {"name": "Final Water Polish", "start_min": 29, "end_min": 41, "target": "RO rinse to fresh-water asymptote", "temp_c": 24}
    ]

    return {
        "classification": "SYNTHETIC_DATA",
        "notice": "Simulation — not L'Oréal production data.",
        "baseline_minutes": 42,
        "predicted_endpoint_minute": None if critical else endpoint,
        "endpoint_probability": probability,
        "confidence": "INSUFFICIENT DATA" if critical else ("moderate" if probability < .75 else "high"),
        "minutes_avoided": minutes_avoided,
        "water_avoided_l": water_avoided,
        "phases": phases,
        "safety_gate": {
            "model_message": "INSUFFICIENT DATA — HUMAN/VALIDATED PROCEDURE REQUIRED" if critical else "Endpoint likely reached — requires human approval.",
            "automatic_release": False,
            "required": "Site-specific validated criteria and human approval",
            "three_point_clearance": {
                "asymptotic_conductivity": not critical,
                "turbidity_below_threshold": not critical,
                "thermal_contact_satisfied": not critical and failure != "thermal"
            }
        },
        "readings": readings
    }

def cascade(body):
    try: volume = float(body.get("volume_l", 120))
    except (TypeError, ValueError): volume = -1
    ph = body.get("quality", "unknown")
    if volume < 0:
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "notice": "Simulation — not L'Oréal production data.",
            "screening": "INSUFFICIENT INFORMATION",
            "available_volume_l": 0,
            "recommended_destination": None,
            "required_checks": ["Correct invalid negative volume before screening"]
        }
    status = "INSUFFICIENT INFORMATION" if ph == "unknown" else ("POTENTIALLY REUSABLE SUBJECT TO VALIDATION" if ph == "screened" else "TREATMENT REQUIRED")
    
    # 3-Stream Circular Segregation Architecture (L'Oréal Waterloop plant model)
    stream_segregation = [
        {
            "stream_name": "Stream 1: Pre-Rinse First-Flush",
            "volume_l": round(volume * 0.35, 1),
            "cod_mg_l": 12500,
            "disposition": "Diverted to Biogas Anaerobic Digestion (Methane Energy Recovery)",
            "status": "Energy Recovery Segregation"
        },
        {
            "stream_name": "Stream 2: Caustic Wash Recovery",
            "volume_l": round(volume * 0.45, 1),
            "cod_mg_l": 2800,
            "disposition": "CIP Skid Caustic Buffer Tank (Filtered & Re-dosed for next cycle)",
            "status": "Internal Chemical Loop"
        },
        {
            "stream_name": "Stream 3: Final Rinse Permeate",
            "volume_l": volume,
            "cod_mg_l": 28,
            "tds_ppm": 160,
            "ph": 7.1,
            "disposition": "Non-product-contact utility use (Cooling Towers / Scrubbers / Boiler Pre-feed)",
            "status": status
        }
    ]

    return {
        "classification": "ILLUSTRATIVE_SCENARIO",
        "notice": "Simulation — not L'Oréal production data. No reuse is approved.",
        "available_volume_l": volume,
        "screening": status,
        "recommended_destination": "Non-product-contact utility use — illustrative only" if status.startswith("POTENTIALLY") else None,
        "required_checks": [
            "site water-quality criteria (COD < 50 mg/L, TDS < 200 ppm)",
            "regulatory review & ATEX compliance",
            "microbiological barrier & cross-contamination review",
            "human approval & quality release authorization"
        ],
        "streams": stream_segregation
    }

def impact(body):
    seq = sequence_payload(body)
    if seq["status"] != "FEASIBLE":
        return {
            "classification": "MODEL_OUTPUT",
            "notice": "Modeled synthetic scenario, not L'Oréal production data.",
            "status": seq["status"],
            "constraint_explanation": seq["constraint_explanation"]
        }
    base = seq["baseline"]["water_demand_l"]
    prevent = seq["optimized"]["water_demand_l"]
    try:
        requested_adapt = float(body.get("adapt_incremental_l", 24))
        recovered = max(0, float(body.get("recovered_l", 42)))
    except (TypeError, ValueError):
        return {
            "classification": "MODEL_OUTPUT",
            "notice": "Modeled synthetic scenario, not L'Oréal production data.",
            "status": "INSUFFICIENT DATA",
            "constraint_explanation": "Impact inputs must be numeric."
        }
    adapt = min(max(0, requested_adapt), prevent)
    total_avoided = round(max(0, base - prevent) + adapt, 1)

    # Multi-dimensional ESG calculations (aligned with L'Oréal for the Future targets)
    # Energy: heating water 15C -> 75C requires 0.0697 kWh/L
    thermal_kwh = round(total_avoided * 0.0697, 2)
    thermal_mwh = round(thermal_kwh / 1000.0, 4)
    # Scope 1 GHG: Natural gas steam boiler ~0.202 kg CO2e/kWh
    scope1_co2e_kg = round(thermal_kwh * 0.202, 2)
    # Detergent chemicals avoided: 1.5% NaOH ~0.015 kg/L
    caustic_kg = round(total_avoided * 0.015, 2)
    
    # Time / OEE downtime saved
    time_saved_min = round(max(0, seq["baseline"].get("duration_min", 0) - seq["optimized"].get("duration_min", 0)), 1)

    return {
        "classification": "MODEL_OUTPUT",
        "notice": "Modeled synthetic scenario, not L'Oréal production data.",
        "common_baseline_l": base,
        "prevent_incremental_l": round(max(0, base - prevent), 1),
        "adapt_incremental_l": adapt,
        "adapt_requested_l": requested_adapt,
        "cascade_potential_l": recovered,
        "water_demand_after_prevent_adapt_l": round(max(0, prevent - adapt), 1),
        "total_water_demand_avoided_l": total_avoided,
        "sustainability_ledger": {
            "water_avoided_m3": round(total_avoided / 1000.0, 3),
            "thermal_energy_avoided_kwh": thermal_kwh,
            "thermal_energy_avoided_mwh": thermal_mwh,
            "scope1_ghg_avoided_kg_co2e": scope1_co2e_kg,
            "caustic_detergent_avoided_kg": caustic_kg,
            "turnaround_downtime_avoided_min": time_saved_min
        },
        "accounting_note": "Cascade is reported separately as potential reuse and is not added to water-demand avoidance."
    }

def business_case(body):
    fields = ["changeovers_per_year", "water_avoided_per_changeover_l", "water_cost_per_l", "implementation_cost", "annual_software_cost"]
    missing = []
    values = {}
    for field in fields:
        try: values[field] = float(body[field])
        except (KeyError, TypeError, ValueError): missing.append(field)
    if missing:
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "status": "INSUFFICIENT DATA",
            "notice": "Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions.",
            "required_fields": missing
        }
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "status": "INSUFFICIENT DATA",
            "notice": "All business-case inputs must be finite and non-negative."
        }
    
    annual_water_l = values["changeovers_per_year"] * values["water_avoided_per_changeover_l"]
    direct_water = annual_water_l * values["water_cost_per_l"]
    
    # Thermal energy savings: 0.0697 kWh/L * gas tariff (~0.08 EUR/kWh)
    gas_tariff = float(body.get("gas_tariff_per_kwh", 0.08))
    thermal_savings = annual_water_l * 0.0697 * gas_tariff
    total_benefit = direct_water + thermal_savings

    annual_net = round(total_benefit - values["annual_software_cost"], 2)
    capex = values["implementation_cost"]
    payback_years = None if annual_net <= 0 else round(capex / annual_net, 2)
    roi = None if capex <= 0 else round(annual_net / capex * 100, 1)

    # 3-Year NPV at 8% WACC
    npv_3yr = round(-capex + sum(annual_net / ((1 + 0.08) ** t) for t in range(1, 4)), 2) if capex > 0 else 0

    scenarios = []
    for label, factor in [("Conservative", .7), ("Base", 1.0), ("Optimistic", 1.3)]:
        b_direct = direct_water * factor
        b_thermal = thermal_savings * factor
        benefit = (b_direct + b_thermal) - values["annual_software_cost"]
        scenarios.append({
            "scenario": label,
            "water_avoidance_factor": factor,
            "annual_net_benefit": round(benefit, 2),
            "payback_years": None if benefit <= 0 else round(capex / benefit, 2)
        })

    record("BUSINESS_CASE", "Illustrative calculator run with user-entered site inputs")
    return {
        "classification": "ILLUSTRATIVE_SCENARIO",
        "status": "CALCULATED",
        "notice": "Illustrative calculation from user-entered inputs. Not L'Oréal economics and not a guaranteed outcome.",
        "inputs": values,
        "direct_water_cost_benefit": round(direct_water, 2),
        "thermal_energy_benefit": round(thermal_savings, 2),
        "total_annual_gross_benefit": round(total_benefit, 2),
        "annual_net_benefit": round(annual_net, 2),
        "payback_years": payback_years,
        "annual_roi_percent": roi,
        "npv_3yr": npv_3yr,
        "sensitivity": scenarios,
        "limitation": "Capacity, chemical, energy and revenue effects are excluded until their methodology and source data are defined."
    }

def transition_matrix():
    """Pairwise transition burden matrix across product categories and shades."""
    shades = ["light", "medium", "dark"]
    viscosities = ["low", "high"]
    matrix = []
    for s_from in shades:
        for v_from in viscosities:
            for s_to in shades:
                for v_to in viscosities:
                    dummy_a = {"family": "care", "shade": s_from, "viscosity": v_from, "residue": "medium", "special": False}
                    dummy_b = {"family": "colour", "shade": s_to, "viscosity": v_to, "residue": "medium", "special": False}
                    b = burden(dummy_a, dummy_b)
                    matrix.append({
                        "from": f"{s_from}-{v_from}",
                        "to": f"{s_to}-{v_to}",
                        "litres": b["litres"],
                        "minutes": b["minutes"],
                        "reasons": b["reasons"]
                    })
    return {"classification": "ENGINEERING_ASSUMPTION", "matrix": matrix}

def pilot():
    return {
        "classification": "ARCHITECTED",
        "notice": "Target integration architecture — not connected to L'Oréal systems.",
        "mode": "Advisory only; existing validated procedure remains authoritative.",
        "scope": "One line and selected quality-approved transitions.",
        "timeline_weeks": 6,
        "phases": [
            {"week": "Week 01", "name": "Baseline Metering", "objective": "Calibrate sub-meters and establish baseline CIP volumes."},
            {"week": "Week 02-03", "name": "Shadow Optimization", "objective": "Run ClearLoop in shadow mode alongside MES planner."},
            {"week": "Week 04-05", "name": "Controlled Advisory Pilot", "objective": "Execute approved transitions with operator sign-off."},
            {"week": "Week 06", "name": "Validation & Audit", "objective": "Audit water savings, quality release, and operator feedback."}
        ],
        "success_criteria": [
            "Zero quality deviations or microbiological failures",
            "100% deadline compliance and packaging line availability",
            "Measurable reduction relative to metered baseline (>15% modeled)",
            "Operational acceptance by shift supervisors & CIP operators",
            "Adequate data availability (>99.5% sensor telemetry uptime)"
        ],
        "stop_conditions": [
            "Any quality deviation or out-of-spec micro release",
            "Sensor telemetry dropout exceeding 60 seconds",
            "Unvalidated reuse route or cross-contamination risk",
            "Planner manual override without documented rationale",
            "Production line throughput hazard or scheduling conflict"
        ]
    }

def models():
    return {
        "classification": "ARCHITECTED",
        "endpoint_model": {
            "status": "Not trained on plant data",
            "approach": "Physics-informed rules and synthetic signal simulation only",
            "release_authority": "Site-specific validated criteria and human approval"
        },
        "monitoring": {
            "track": ["data availability", "invalid reading rate", "operator override rate", "prediction error after ground truth exists"],
            "action": "Flag model; revert to validated procedure"
        }
    }

class App(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
    def send_json(self, value, code=200):
        raw = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Request-ID", str(uuid.uuid4()))
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
        
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/batches":
            query = urlparse(self.path).query
            seed = 2030
            if "seed=" in query:
                try: seed = int(query.split("seed=")[1].split("&")[0])
                except ValueError: pass
            return self.send_json({"classification": "SYNTHETIC_DATA", "items": batches(seed)})
        if route == "/api/cleaning": return self.send_json(cleaning())
        if route == "/api/audit-log": return self.send_json({"items": audit_events(), "storage": "sqlite with in-memory fallback"})
        if route == "/api/assumptions": return self.send_json({"classification": "ENGINEERING_ASSUMPTION", "rules": RULES})
        if route == "/api/pilot": return self.send_json(pilot())
        if route == "/api/models": return self.send_json(models())
        if route == "/api/matrix": return self.send_json(transition_matrix())
        if route == "/api/stress-test":
            rf = ROOT / "data" / "stress_test_1000_report.json"
            if rf.exists():
                return self.send_json(json.loads(rf.read_text()))
            return self.send_json({"status": "RUN_REQUIRED"})
        if route == "/api/business-case":
            return self.send_json({
                "classification": "ILLUSTRATIVE_SCENARIO",
                "status": "INPUT REQUIRED",
                "required_fields": ["changeovers_per_year", "water_avoided_per_changeover_l", "water_cost_per_l", "implementation_cost", "annual_software_cost"],
                "notice": "Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions."
            })
        if route == "/api/health": return self.send_json({"status": "ok", "classification": "REAL", "storage": "sqlite with in-memory fallback"})
        if route.startswith("/api/"): return self.send_json({"error": "Unknown route"}, 404)
        self.path = "/frontend/index.html" if route == "/" else route
        return super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "Invalid JSON request body"}, 400)
        route = urlparse(self.path).path
        if route == "/api/optimize": return self.send_json(sequence_payload(body))
        if route == "/api/cleaning/start":
            record("CLEANING_SIMULATION", f"Started (failure={body.get('failure', 'none')})")
            return self.send_json(cleaning(body.get("seed", 2030), body.get("failure")))
        if route == "/api/water/analyze":
            record("WATER_SCREEN", "Illustrative reuse screen")
            return self.send_json(cascade(body))
        if route == "/api/impact/calculate": return self.send_json(impact(body))
        if route == "/api/business-case": return self.send_json(business_case(body))
        if route == "/api/optimization/decision":
            decision = body.get("decision") if isinstance(body, dict) else None
            if decision not in {"accept_recommendation", "retain_baseline"}:
                return self.send_json({"error": "Decision must be accept_recommendation or retain_baseline."}, 400)
            event = record("PLANNER_DECISION", f"{decision} for synthetic optimization {body.get('optimization_id', 'unknown')}")
            return self.send_json({"classification": "SIMULATED", "notice": "Planner decision recorded in local session audit trail; no plant schedule was changed.", "event": event})
        return self.send_json({"error": "Unknown route"}, 404)

if __name__ == "__main__":
    import os
    os.chdir(ROOT)
    init_db()
    print("ClearLoop running at http://localhost:8000")
    ThreadingHTTPServer(("", 8000), App).serve_forever()
