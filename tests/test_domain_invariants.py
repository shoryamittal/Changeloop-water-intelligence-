"""Exhaustive Domain Invariants & Physical Conservation Test Suite.
Validates mass-balance conservation, zero-double-counting locks,
Safety State Machine transitions, 2-Opt monotonicity, and edge cases.
"""
import sys, unittest, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core

class DomainInvariantsTests(unittest.TestCase):
    def test_01_mass_balance_conservation(self):
        """Invariant: Baseline - Prevent - Adapt = Gross Consumed, and Gross - Reclaim = Net Intake."""
        for seed in [2026, 2030, 2040, 2050]:
            impact_res = core.calculate_impact({
                "seed": seed,
                "adapt_incremental_l": 50,
                "recovered_l": 40
            })
            self.assertEqual(impact_res["classification"], "MODEL_OUTPUT")
            baseline = impact_res["common_baseline_l"]
            prevent = impact_res["prevent_incremental_l"]
            adapt = impact_res["adapt_incremental_l"]
            gross = impact_res["water_demand_after_prevent_adapt_l"]

            # Gross Consumed Mass-Balance
            expected_gross = round(max(0.0, (baseline - prevent) - adapt), 1)
            self.assertAlmostEqual(gross, expected_gross, delta=0.2)

            # Prevent + Adapt = Total Avoided
            total_avoided = impact_res["total_water_demand_avoided_l"]
            self.assertAlmostEqual(total_avoided, round(prevent + adapt, 1), delta=0.2)

    def test_02_zero_double_counting_invariant(self):
        """Invariant: Cascade Reclaim is never added to Water Demand Avoidance."""
        res = core.calculate_impact({
            "seed": 2030,
            "adapt_incremental_l": 30,
            "recovered_l": 100
        })
        self.assertIn("not added", res["accounting_note"])
        # Total avoided must strictly equal prevent + adapt, unaffected by cascade volume
        self.assertEqual(
            res["total_water_demand_avoided_l"],
            round(res["prevent_incremental_l"] + res["adapt_incremental_l"], 1)
        )

    def test_03_timespan_ledger_mass_balance(self):
        """Invariant: Every timespan (24h, 7d, 30d, 90d, ytd) satisfies exact mass balance."""
        for span in ["24h", "7d", "30d", "90d", "ytd"]:
            data = core.calculate_impact_timespan_ledger(span)
            base = data["baselineDemandL"]
            up_avoid = abs(data["upstreamDeltaL"])
            adapt_avoid = abs(data["adaptiveDeltaL"])
            gross = data["grossConsumedL"]
            reclaim = abs(data["cascadeReclaimL"])
            net = data["netWaterIntakeL"]
            total_saved = data["savedL"]

            # Gross = Base - Upstream - Adaptive
            self.assertAlmostEqual(gross, base - up_avoid - adapt_avoid, delta=0.2)
            # Net = Gross - Reclaim
            self.assertAlmostEqual(net, gross - reclaim, delta=0.2)
            # Total Saved = Upstream + Adaptive + Reclaim
            self.assertAlmostEqual(total_saved, up_avoid + adapt_avoid + reclaim, delta=0.2)

    def test_04_safety_state_machine_deterministic_transitions(self):
        """Invariant: Fail-safe state machine engages appropriate interlocks for all faults."""
        # 1. Normal run -> Advisory monitoring, 3/3 clearances pass
        normal_sim = core.simulate_cleaning_cycle(seed=2026, failure=None)
        gate_normal = normal_sim["safety_gate"]
        self.assertEqual(gate_normal["safety_state"], core.SafetyLevel.ADVISORY.value)
        self.assertFalse(gate_normal["automatic_release"])
        self.assertTrue(gate_normal["three_point_clearance"]["asymptotic_conductivity"])
        self.assertTrue(gate_normal["three_point_clearance"]["turbidity_below_threshold"])
        self.assertTrue(gate_normal["three_point_clearance"]["thermal_contact_satisfied"])
        self.assertGreater(normal_sim["water_avoided_l"], 0)

        # 2. Sensor drift -> Fault lockout, early cutoff aborted, 0 L avoided
        drift_sim = core.simulate_cleaning_cycle(seed=2026, failure="drift")
        gate_drift = drift_sim["safety_gate"]
        self.assertEqual(gate_drift["safety_state"], core.SafetyLevel.FAULT.value)
        self.assertFalse(gate_drift["automatic_release"])
        self.assertIn("drift", gate_drift["lockout_reason"].lower())
        self.assertEqual(drift_sim["water_avoided_l"], 0)
        self.assertIsNone(drift_sim["predicted_endpoint_minute"])

        # 3. Thermal deficit -> Interlock hold, thermal contact unsatisfied
        thermal_sim = core.simulate_cleaning_cycle(seed=2026, failure="thermal")
        gate_thermal = thermal_sim["safety_gate"]
        self.assertEqual(gate_thermal["safety_state"], core.SafetyLevel.INTERLOCK.value)
        self.assertFalse(gate_thermal["three_point_clearance"]["thermal_contact_satisfied"])
        self.assertEqual(thermal_sim["water_avoided_l"], 0)

        # 4. Turbidity spike -> Interlock hold, turbidity ceiling breached
        spike_sim = core.simulate_cleaning_cycle(seed=2026, failure="spike")
        gate_spike = spike_sim["safety_gate"]
        self.assertEqual(gate_spike["safety_state"], core.SafetyLevel.INTERLOCK.value)
        self.assertFalse(gate_spike["three_point_clearance"]["turbidity_below_threshold"])
        self.assertEqual(spike_sim["water_avoided_l"], 0)

        # 5. Missing telemetry -> Fault lockout
        missing_sim = core.simulate_cleaning_cycle(seed=2026, failure="missing")
        gate_missing = missing_sim["safety_gate"]
        self.assertEqual(gate_missing["safety_state"], core.SafetyLevel.FAULT.value)
        self.assertEqual(missing_sim["confidence"], "INSUFFICIENT DATA")

    def test_05_two_opt_local_search_monotonicity(self):
        """Invariant: 2-Opt candidate objective is never worse than baseline."""
        for seed in range(2030, 2045):
            res = core.optimize_schedule({"seed": seed, "algorithm": "two_opt"})
            self.assertEqual(res["status"], "FEASIBLE")
            base_obj = res["baseline"]["objective"]
            opt_obj = res["optimized"]["objective"]
            self.assertLessEqual(opt_obj, base_obj + 1e-4)

    def test_06_cascade_stream_segregation(self):
        """Invariant: Effluent stream separation produces 3 distinct closed loops."""
        res = core.analyze_cascade({"volume_l": 200, "quality": "screened"})
        self.assertEqual(len(res["streams"]), 3)
        stream_names = [s["stream_name"] for s in res["streams"]]
        self.assertTrue(any("Stream 1" in s for s in stream_names))
        self.assertTrue(any("Stream 2" in s for s in stream_names))
        self.assertTrue(any("Stream 3" in s for s in stream_names))
        self.assertEqual(res["available_volume_l"], 200)

    def test_07_edge_cases_and_robustness(self):
        """Invariant: Invalid or boundary inputs fail gracefully without throwing."""
        # Empty queue
        self.assertEqual(core.optimize_schedule({"batches": []})["status"], "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS")
        # Non-numeric weights
        self.assertEqual(core.optimize_schedule({"water_weight": "invalid"})["status"], "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS")
        # Negative volume cascade
        casc_neg = core.analyze_cascade({"volume_l": -50})
        self.assertEqual(casc_neg["available_volume_l"], 0)
        # Empty business case
        bc = core.calculate_business_case({})
        self.assertEqual(bc["status"], "INSUFFICIENT DATA")

if __name__ == "__main__":
    unittest.main()
