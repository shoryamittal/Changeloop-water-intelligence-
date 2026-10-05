"""ClearLoop Physical CIP Simulation, Sensor Telemetry & Safety State Machine Test Suite.
Covers:
- Phase 5: Normal 4-phase CIP telemetry, stage transitions, endpoint estimation,
  physical limits (no negative water, no negative time, valid temperature and turbidity).
- Phase 6: Sensor fault injection (dropout, drift, thermal deficit, slug spike),
  verification that underlying state changes, decisions change, water avoided drops to 0.
- Phase 7: Safety state machine transitions and fail-safe guarantees (fault cannot be released).
"""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core
from core.simulator import simulate_cleaning_cycle
from core.domain import SafetyLevel

class CleaningSimulationAndFaultsTests(unittest.TestCase):
    """Rigorous physical telemetry and deterministic safety gate tests."""

    def test_01_nominal_cleaning_cycle_physics(self):
        """Nominal run models 4 CIP phases, passes 3/3 clearances, and calculates early cutoff."""
        sim = simulate_cleaning_cycle(seed=2026, failure=None)

        self.assertEqual(sim["classification"], "SYNTHETIC_DATA")
        self.assertEqual(sim["baseline_minutes"], 42)
        self.assertGreater(sim["predicted_endpoint_minute"], 0)
        self.assertLess(sim["predicted_endpoint_minute"], sim["baseline_minutes"])
        self.assertGreater(sim["water_avoided_l"], 0)
        self.assertGreater(sim["minutes_avoided"], 0)

        # 3-point clearance must pass completely under nominal conditions
        gate = sim["safety_gate"]
        self.assertEqual(gate["safety_state"], SafetyLevel.ADVISORY.value)
        self.assertFalse(gate["automatic_release"], "Release must remain advisory human-in-the-loop")
        self.assertTrue(gate["three_point_clearance"]["asymptotic_conductivity"])
        self.assertTrue(gate["three_point_clearance"]["turbidity_below_threshold"])
        self.assertTrue(gate["three_point_clearance"]["thermal_contact_satisfied"])

    def test_02_sensor_telemetry_curves_physical_bounds(self):
        """Multi-sensor telemetry points adhere to physical bounds (no negative values, realistic limits)."""
        sim = simulate_cleaning_cycle(seed=2026, failure=None)
        series = sim["readings"]
        self.assertGreaterEqual(len(series), 35)

        for pt in series:
            # 1. Time progression >= 0
            self.assertGreaterEqual(pt["minute"], 0)
            self.assertLessEqual(pt["minute"], 45)

            # 2. Temperature in realistic cosmetic CIP bounds (15°C to 95°C)
            self.assertGreaterEqual(pt["temperature"], 15.0)
            self.assertLessEqual(pt["temperature"], 95.0)

            # 3. Turbidity is non-negative and finite
            self.assertGreaterEqual(pt["turbidity"], 0.0)
            self.assertLessEqual(pt["turbidity"], 100.0)

            # 4. Conductivity is non-negative and within realistic CIP bounds (<= 50.0 mS/cm for 1.5% NaOH)
            self.assertGreaterEqual(pt["conductivity"], 0.0)
            self.assertLessEqual(pt["conductivity"], 50.0)

            # 5. Flow velocity is positive
            self.assertGreaterEqual(pt["flow"], 0.0)

            # 6. pH is within valid chemical bounds [2.0, 14.0]
            self.assertGreaterEqual(pt["ph"], 2.0)
            self.assertLessEqual(pt["ph"], 14.0)

    def test_03_sensor_dropout_fault_lockout(self):
        """Sensor dropout (missing telemetry) triggers FAULT lockout, 0 L avoided, SOP timer fallback."""
        sim = simulate_cleaning_cycle(seed=2026, failure="missing")
        gate = sim["safety_gate"]

        self.assertEqual(gate["safety_state"], SafetyLevel.FAULT.value)
        self.assertFalse(gate["automatic_release"])
        self.assertEqual(sim["water_avoided_l"], 0)
        self.assertEqual(sim["minutes_avoided"], 0)
        self.assertIsNone(sim["predicted_endpoint_minute"])
        self.assertEqual(sim["confidence"], "INSUFFICIENT DATA")

    def test_04_sensor_drift_fault_lockout(self):
        """Sensor probe mismatch > 15% triggers FAULT lockout, early cutoff aborted, 0 L avoided."""
        sim = simulate_cleaning_cycle(seed=2026, failure="drift")
        gate = sim["safety_gate"]

        self.assertEqual(gate["safety_state"], SafetyLevel.FAULT.value)
        self.assertFalse(gate["automatic_release"])
        self.assertEqual(sim["water_avoided_l"], 0)
        self.assertIn("drift", gate["lockout_reason"].lower())

    def test_05_thermal_deficit_interlock_hold(self):
        """Thermal sanitization deficit (<65°C kill requirement) engages INTERLOCK, 0 L avoided."""
        sim = simulate_cleaning_cycle(seed=2026, failure="thermal")
        gate = sim["safety_gate"]

        self.assertEqual(gate["safety_state"], SafetyLevel.INTERLOCK.value)
        self.assertFalse(gate["three_point_clearance"]["thermal_contact_satisfied"])
        self.assertEqual(sim["water_avoided_l"], 0)
        self.assertIn("thermal", gate["lockout_reason"].lower())

    def test_06_turbidity_slug_spike_interlock_hold(self):
        """Pocket slug turbidity spike (>2.5 NTU safety ceiling) engages INTERLOCK, 0 L avoided."""
        sim = simulate_cleaning_cycle(seed=2026, failure="spike")
        gate = sim["safety_gate"]

        self.assertEqual(gate["safety_state"], SafetyLevel.INTERLOCK.value)
        self.assertFalse(gate["three_point_clearance"]["turbidity_below_threshold"])
        self.assertEqual(sim["water_avoided_l"], 0)
        self.assertIn("slug", gate["lockout_reason"].lower())

    def test_07_safety_gate_cannot_automatically_release_on_fault(self):
        """Invariant: Under ANY fault mode, automatic release is strictly False and water avoided is 0."""
        for fault in ["missing", "drift", "thermal", "spike"]:
            sim = simulate_cleaning_cycle(seed=2026, failure=fault)
            gate = sim["safety_gate"]
            self.assertFalse(gate["automatic_release"], f"Fault {fault} permitted automatic release!")
            self.assertEqual(sim["water_avoided_l"], 0, f"Fault {fault} allowed avoided water!")
            self.assertIn(gate["safety_state"], {SafetyLevel.FAULT.value, SafetyLevel.INTERLOCK.value})

    def test_08_authoritative_safety_state_source_coherence(self):
        """Simulation safety gate and DemoSession safety state maintain 100% agreement."""
        session = core.DemoSession()
        session.start_cleaning(None)
        self.assertEqual(session.fault_mode, None)

        # Inject drift on session
        session.start_cleaning("drift")
        self.assertEqual(session.fault_mode, "drift")
        sim = session.cleaning_simulation
        self.assertEqual(sim["safety_gate"]["safety_state"], SafetyLevel.FAULT.value)

        # Attempt to authorize cutoff under drift must be rejected
        auth_res = session.authorize_early_cutoff()
        self.assertEqual(auth_res["status"], "BLOCKED")
        self.assertIn("Safety interlocks active", auth_res["error"])

if __name__ == "__main__":
    unittest.main()
