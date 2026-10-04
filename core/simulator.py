"""ClearLoop Physical CIP 4-Phase Telemetry Simulator.
Simulates real-world multi-sensor dynamics (UV-Vis spectrophotometry, conductivity,
temperature, flow velocity, and pH) with deterministic fault injections.
"""
from typing import Dict, Any, Optional
import random
from .safety import SafetyStateMachine
from .domain import CleaningSimulation, SensorReading

def simulate_cleaning_cycle(seed: int = 2026, failure: Optional[str] = None, vessel_id: str = "V-04") -> Dict[str, Any]:
    """Execute dynamic 4-phase physical CIP simulation with multi-sensor telemetry."""
    r = random.Random(seed)
    n = 42
    endpoint = 30 + r.randint(-3, 4)
    readings = []

    # Phase boundaries:
    # 0-7: Pre-rinse purge
    # 8-21: Caustic wash (1.5% NaOH, 72°C)
    # 22-28: Intermediate neutralization rinse
    # 29-41: Final RO polish rinse
    for minute in range(n):
        quality = "valid"
        stage_name = "Phase 4: Final Water Polish"
        if minute < 8:
            stage_name = "Phase 1: Pre-Rinse Purge"
            progress = minute / 7.0
            turb = 45.0 * (1 - progress) ** 1.8 + 3.0 + r.gauss(0, 0.4)
            cond = 2.4 - progress * 1.2 + r.gauss(0, 0.05)
            temp = 22.0 + r.gauss(0, 0.3)
            flow = 11.5 + r.gauss(0, 0.2)
            ph = 7.1 + r.gauss(0, 0.1)
        elif minute < 22:
            stage_name = "Phase 2: Caustic Detergent Wash (1.5% NaOH)"
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
            turb = 14.8
            quality = "invalid spike"
        if failure == "drift" and minute >= 18:
            cond = (cond or 1.5) + (minute - 17) * 0.32
            turb = (turb or 0.5) + (minute - 17) * 0.08
            quality = "drift suspected"

        reading_dict = {
            "minute": minute,
            "conductivity": None if cond is None else round(max(0.0, cond), 2),
            "turbidity": None if turb is None else round(max(0.0, turb), 2),
            "temperature": round(temp, 1),
            "flow": round(flow, 2),
            "ph": round(ph, 2),
            "stage": stage_name,
            "quality": quality
        }
        readings.append(reading_dict)

    # Evaluate safety gate state machine
    safety_gate = SafetyStateMachine.evaluate(readings, failure)
    critical = (safety_gate.state != safety_gate.state.ADVISORY and safety_gate.state != safety_gate.state.NORMAL)

    probability = 0.0 if critical else round(min(0.96, max(0.35, 0.52 + (n - endpoint) / 38.0)), 2)
    minutes_avoided = 0 if critical else max(0, n - endpoint)
    water_avoided = 0.0 if critical else round(minutes_avoided * 10.0, 1)

    phases = [
        {"name": "Pre-Rinse Purge", "start_min": 0, "end_min": 7, "target": "Purge bulk cosmetic emulsion residue", "temp_c": 22},
        {"name": "Caustic Detergent Wash", "start_min": 8, "end_min": 21, "target": "1.5% NaOH Saponification & thermal log-kill", "temp_c": 72},
        {"name": "Intermediate Rinse", "start_min": 22, "end_min": 28, "target": "Detergent purge to neutral pH", "temp_c": 35},
        {"name": "Final Water Polish", "start_min": 29, "end_min": 41, "target": "RO rinse to fresh-water asymptote", "temp_c": 24}
    ]

    sensor_objects = [
        SensorReading(
            minute=x["minute"],
            conductivity_ms_cm=x["conductivity"],
            turbidity_ntu=x["turbidity"],
            temp_c=x["temperature"],
            flow_l_min=x["flow"],
            ph=x["ph"],
            stage=x["stage"],
            quality=x["quality"]
        )
        for x in readings
    ]

    result = CleaningSimulation(
        classification="SYNTHETIC_DATA",
        notice="Simulation — not L'Oréal production data.",
        baseline_minutes=42,
        predicted_endpoint_minute=None if critical else endpoint,
        endpoint_probability=probability,
        confidence="INSUFFICIENT DATA" if critical else ("moderate" if probability < 0.75 else "high"),
        minutes_avoided=minutes_avoided,
        water_avoided_l=water_avoided,
        phases=phases,
        safety_gate=safety_gate,
        readings=sensor_objects
    )
    return result.to_dict()
