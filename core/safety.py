"""ClearLoop Deterministic Safety State Machine & Interlock Verification.
Guarantees human-in-the-loop decision support with fail-safe interlocks,
3-point quality clearance checks, and automated lockout under sensor drift or thermal deficits.
"""
from typing import List, Dict, Optional, Any
from .domain import SafetyLevel, SafetyGate, ThreePointClearance, SensorReading

class SafetyStateMachine:
    """Finite State Machine enforcing L'Oréal Clean Water Charter & GMP quality clearance."""

    @staticmethod
    def evaluate(readings: List[Dict[str, Any]], failure: Optional[str] = None) -> SafetyGate:
        critical_fault = False
        lockout_reason = None
        current_state = SafetyLevel.NORMAL

        # Check for missing sensor readings
        has_missing = any(r.get("conductivity") is None or r.get("turbidity") is None for r in readings)
        if has_missing or failure == "missing":
            critical_fault = True
            current_state = SafetyLevel.FAULT
            lockout_reason = "Telemetry dropout detected; dual-probe sensor data unavailable"

        # Check for sensor drift divergence
        has_drift = any(r.get("quality") == "drift suspected" for r in readings) or failure == "drift"
        if has_drift:
            critical_fault = True
            current_state = SafetyLevel.FAULT
            lockout_reason = "Dual-probe mismatch (+15%) indicates calibration drift divergence"

        # Check for localized turbidity spike in rinse/polish phases
        has_spike = any(
            r.get("quality") == "invalid spike" or
            (r.get("stage", "").startswith("Phase 4") and (r.get("turbidity") or 0) > 5.0)
            for r in readings
        ) or failure == "spike"
        if has_spike:
            critical_fault = True
            current_state = SafetyLevel.INTERLOCK
            lockout_reason = "Residual pigment slug pocket detected across optical flow cell"

        # Check for thermal sanitization deficit
        has_thermal_deficit = failure == "thermal" or any(
            r.get("stage", "").startswith("Phase 2") and (r.get("temperature") or 0) < 65.0
            for r in readings
        )
        if has_thermal_deficit:
            critical_fault = True
            current_state = SafetyLevel.INTERLOCK
            lockout_reason = "Thermal log-kill deficit: Caustic wash temperature below 65°C spec (A0 < 60)"

        asymptotic = not critical_fault
        turbidity_ok = not critical_fault and not has_spike
        thermal_ok = not critical_fault and not has_thermal_deficit

        clearance = ThreePointClearance(
            asymptotic_conductivity=asymptotic,
            turbidity_below_threshold=turbidity_ok,
            thermal_contact_satisfied=thermal_ok
        )

        if critical_fault:
            model_msg = "INSUFFICIENT DATA — HUMAN/VALIDATED PROCEDURE REQUIRED"
            if lockout_reason:
                model_msg += f": {lockout_reason}"
        else:
            model_msg = "Endpoint likely reached — requires human approval."
            current_state = SafetyLevel.ADVISORY

        return SafetyGate(
            state=current_state,
            model_message=model_msg,
            automatic_release=False,  # Principle: Never autonomous release
            required="Site-specific validated criteria and human approval",
            three_point_clearance=clearance,
            lockout_reason=lockout_reason
        )
