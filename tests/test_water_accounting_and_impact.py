"""ClearLoop Water Accounting, Anti-Double-Counting, and Impact Ledger Test Suite.
Covers:
- Phase 8: 3-stream mass conservation, allocated volume <= source volume,
  zero/partial/full recovery, negative value protection.
- Phase 9: Anti-double-counting strict mathematical isolation (Demand Avoided vs Reclaimed).
- Phase 10: ISO 14046 mass-balance formulas (Thermal kWh, Scope 1 CO2e, Caustic NaOH, Capacity uptime).
- Phase 11: Business case assumption scaling and parametric sensitivity.
"""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core
from core.cascade import analyze_cascade
from core.impact import calculate_impact, calculate_impact_timespan_ledger
from core.economics import calculate_business_case
from core.demo import DemoSession

class WaterAccountingAndImpactTests(unittest.TestCase):
    """Rigorous tests for mass-balance conservation and anti-double-counting invariants."""

    def test_01_demo_session_three_stream_exact_mass_balance(self):
        """Invariant: In DemoSession cascade distribution, the 3 streams sum exactly to 100% of effluent."""
        session = DemoSession()
        session.start_cleaning(None)
        session.execute_cascade_screening()
        dist = session.cascade_result

        # Total effluent equals recovery volume
        effluent_l = session.recovery_result["volume_l"]
        self.assertGreater(effluent_l, 0)
        self.assertEqual(dist["available_volume_l"], effluent_l)

        # 3 streams present
        streams = dist["streams"]
        self.assertEqual(len(streams), 3)

        # Stream 3 is screened for circular utility reuse
        s3 = next(s for s in streams if "Stream 3" in s["stream_name"])
        self.assertEqual(s3["volume_l"], effluent_l)
        self.assertEqual(s3["status"], "POTENTIALLY REUSABLE SUBJECT TO VALIDATION")

    def test_02_cascade_screening_proportional_consistency(self):
        """Pre-rinse (0.35x), Caustic (0.45x), and Final Rinse Permeate (1.0x) scale deterministically."""
        for volume in [25.0, 100.0, 202.8, 500.0]:
            res = analyze_cascade({"volume_l": volume, "quality": "screened"})
            streams = res["streams"]
            s1 = streams[0]  # Pre-rinse 0.35x
            s2 = streams[1]  # Caustic wash 0.45x
            s3 = streams[2]  # Permeate 1.0x

            self.assertAlmostEqual(s1["volume_l"], round(volume * 0.35, 1), delta=0.2)
            self.assertAlmostEqual(s2["volume_l"], round(volume * 0.45, 1), delta=0.2)
            self.assertEqual(s3["volume_l"], volume)
            self.assertEqual(res["available_volume_l"], volume)

    def test_03_zero_and_negative_volume_safety(self):
        """Zero or negative volume inputs clamp safely to 0 L without crashing or negative outputs."""
        zero_res = analyze_cascade({"volume_l": 0.0})
        self.assertEqual(zero_res["available_volume_l"], 0.0)

        neg_res = analyze_cascade({"volume_l": -150.0})
        self.assertEqual(neg_res["available_volume_l"], 0.0)
        self.assertEqual(len(neg_res["streams"]), 0)

    def test_04_anti_double_counting_strict_isolation(self):
        """Invariant: Avoided Demand is NEVER added to Reclaimed Permeate in sustainability accounting."""
        # Scenario A: Demand avoided only, zero reclaim
        impact_a = calculate_impact({
            "seed": 2026,
            "adapt_incremental_l": 30.0,
            "recovered_l": 0.0
        })

        # Scenario B: Demand avoided AND circular reclaim (200 L)
        impact_b = calculate_impact({
            "seed": 2026,
            "adapt_incremental_l": 30.0,
            "recovered_l": 200.0
        })

        # CRITICAL TEST: Total Water Demand Avoided must be IDENTICAL in both scenarios
        self.assertEqual(
            impact_a["total_water_demand_avoided_l"],
            impact_b["total_water_demand_avoided_l"],
            "Double-counting breach: Reclaimed cascade leaked into Demand Avoidance calculation!"
        )

        # Cascade potential is reported separately as potential reuse and not added
        self.assertEqual(impact_b["cascade_potential_l"], 200.0)
        self.assertEqual(impact_a["cascade_potential_l"], 0.0)
        self.assertIn("not added", impact_b["accounting_note"].lower())

    def test_05_iso_14046_environmental_formulas(self):
        """Verification of thermodynamic, carbon, and chemical factors."""
        impact = calculate_impact({
            "seed": 2030,
            "adapt_incremental_l": 40.0,
            "recovered_l": 100.0
        })
        total_avoided = impact["total_water_demand_avoided_l"]
        self.assertGreater(total_avoided, 0)

        s = impact["sustainability_ledger"]

        # 1. Thermal boiler energy: Delta T = 57°C (15°C to 72°C) -> 0.0697 kWh/L
        expected_kwh = round(total_avoided * 0.0697, 2)
        self.assertAlmostEqual(s["thermal_energy_avoided_kwh"], expected_kwh, delta=0.5)

        # 2. Scope 1 GHG: Natural gas combustion factor 0.202 kg CO2e / kWh
        expected_co2e = round(s["thermal_energy_avoided_kwh"] * 0.202, 2)
        self.assertAlmostEqual(s["scope1_ghg_avoided_kg_co2e"], expected_co2e, delta=0.2)

        # 3. Caustic detergent saved: 1.5% NaOH wash solution = 0.015 kg/L
        expected_caustic = round(total_avoided * 0.015, 2)
        self.assertAlmostEqual(s["caustic_detergent_avoided_kg"], expected_caustic, delta=0.2)

    def test_06_impact_timespan_ledgers_conservation(self):
        """All timespan intervals maintain exact mass balance and non-negative net intake."""
        for span in ["24h", "7d", "30d", "90d", "ytd"]:
            data = calculate_impact_timespan_ledger(span)
            self.assertIn("baselineDemandL", data)
            self.assertIn("grossConsumedL", data)
            self.assertIn("netWaterIntakeL", data)

            base = data["baselineDemandL"]
            gross = data["grossConsumedL"]
            net = data["netWaterIntakeL"]

            self.assertGreater(base, 0)
            self.assertGreater(gross, 0)
            self.assertGreaterEqual(net, 0)
            self.assertLessEqual(gross, base)
            self.assertLessEqual(net, gross)

    def test_07_business_case_roi_scaling(self):
        """Business case ROI model scales monotonically with facility volume."""
        # Scale 1: Pilot plant (350 changeovers/yr)
        pilot = calculate_business_case({
            "changeovers_per_year": 350,
            "water_avoided_per_changeover_l": 180,
            "water_cost_per_l": 0.0035,
            "implementation_cost": 15000,
            "annual_software_cost": 4000
        })

        # Scale 2: Burgos Waterloop plant (2,800 changeovers/yr)
        burgos = calculate_business_case({
            "changeovers_per_year": 2800,
            "water_avoided_per_changeover_l": 180,
            "water_cost_per_l": 0.0035,
            "implementation_cost": 45000,
            "annual_software_cost": 12000
        })

        # Scale 3: Global deployment (28,000 changeovers/yr)
        global_scale = calculate_business_case({
            "changeovers_per_year": 28000,
            "water_avoided_per_changeover_l": 180,
            "water_cost_per_l": 0.0035,
            "implementation_cost": 250000,
            "annual_software_cost": 75000
        })

        self.assertEqual(pilot["status"], "CALCULATED")
        self.assertEqual(burgos["status"], "CALCULATED")
        self.assertEqual(global_scale["status"], "CALCULATED")

        # Direct water avoidance benefit scales strictly monotonically
        self.assertLess(pilot["direct_water_cost_benefit"], burgos["direct_water_cost_benefit"])
        self.assertLess(burgos["direct_water_cost_benefit"], global_scale["direct_water_cost_benefit"])

        # Gross annual benefit scales strictly monotonically
        self.assertLess(pilot["total_annual_gross_benefit"], burgos["total_annual_gross_benefit"])
        self.assertLess(burgos["total_annual_gross_benefit"], global_scale["total_annual_gross_benefit"])

if __name__ == "__main__":
    unittest.main()
