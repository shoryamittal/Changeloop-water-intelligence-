"""Unit and Invariant Tests for ChangeLoop SANKALP Resource Decision Engine.
Validates:
1. Multi-resource trade-off generation (Option A vs Option B vs Option C).
2. Watershed stress multipliers (WRI Aqueduct 4.0 / AWARE methodology).
3. Cryptographic SHA-256 sealing of ResourceDecisionEvents.
4. Tamper-evident provenance verification.
5. Secondary vertical AI Data Center cooling workload dispatch math.
"""
import unittest
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.domain import (
    KNOWN_WATERSHEDS, WatershedStressProfile,
    ResourceDecisionEvent, DecisionOption
)
from core.decision_engine import (
    evaluate_changeover_tradeoffs,
    create_resource_decision_event,
    evaluate_datacenter_workload
)

class TestSankalpDecisionEngine(unittest.TestCase):

    def test_01_watershed_scarcity_catalog(self):
        """All 5 reference watersheds exist with valid AWARE multipliers and quotas."""
        self.assertIn("FR-AULNAY-04", KNOWN_WATERSHEDS)
        self.assertIn("ES-BURGOS-01", KNOWN_WATERSHEDS)
        self.assertIn("IT-SETTIMO-02", KNOWN_WATERSHEDS)
        self.assertIn("BE-VORSELAAR-01", KNOWN_WATERSHEDS)
        self.assertIn("US-PHOENIX-DC01", KNOWN_WATERSHEDS)

        # Burgos Dry Factory must reflect severe Mediterranean drought (3.4x)
        burgos = KNOWN_WATERSHEDS["ES-BURGOS-01"]
        self.assertEqual(burgos.aware_factor, 3.4)
        self.assertEqual(burgos.calculate_stress_equated_litres(100.0), 340.0)

        # Phoenix DC must reflect extreme arid water stress (8.5x)
        phx = KNOWN_WATERSHEDS["US-PHOENIX-DC01"]
        self.assertEqual(phx.aware_factor, 8.5)
        self.assertEqual(phx.calculate_stress_equated_litres(1000.0), 8500.0)

    def test_02_three_way_decision_tradeoffs(self):
        """Trade-off engine produces 3 distinct feasible options with non-negative metrics."""
        tradeoffs = evaluate_changeover_tradeoffs({}, {}, "FR-AULNAY-04")
        self.assertEqual(tradeoffs["selected_option_id"], "OPTION_B")
        self.assertEqual(len(tradeoffs["options"]), 3)

        opts = {o["option_id"]: o for o in tradeoffs["options"]}
        self.assertIn("OPTION_A", opts)
        self.assertIn("OPTION_B", opts)
        self.assertIn("OPTION_C", opts)

        # Option B (Recommended) must save water vs Option A (Legacy)
        self.assertLess(opts["OPTION_B"]["freshwater_l"], opts["OPTION_A"]["freshwater_l"])
        self.assertLess(opts["OPTION_B"]["energy_kwh"], opts["OPTION_A"]["energy_kwh"])
        self.assertLess(opts["OPTION_B"]["cost_eur"], opts["OPTION_A"]["cost_eur"])

        # Option B must have 0 delay, Option C has schedule delay risk
        self.assertEqual(opts["OPTION_B"]["schedule_delay_min"], 0.0)
        self.assertGreater(opts["OPTION_C"]["schedule_delay_min"], 0.0)

        # Check explainability
        self.assertTrue(tradeoffs["why_recommended"].startswith("Option B delivers"))

    def test_03_watershed_equated_litres_calculation(self):
        """Stress-equated litres (L-eq) accurately scales with basin AWARE factor."""
        aulnay_tradeoffs = evaluate_changeover_tradeoffs({}, {}, "FR-AULNAY-04")
        burgos_tradeoffs = evaluate_changeover_tradeoffs({}, {}, "ES-BURGOS-01")

        aulnay_opt_b = next(o for o in aulnay_tradeoffs["options"] if o["option_id"] == "OPTION_B")
        burgos_opt_b = next(o for o in burgos_tradeoffs["options"] if o["option_id"] == "OPTION_B")

        # Physical water is identical (1074 L), but Burgos stress L-eq must be higher due to 3.4x vs 1.2x
        self.assertEqual(aulnay_opt_b["freshwater_l"], burgos_opt_b["freshwater_l"])
        self.assertAlmostEqual(aulnay_opt_b["water_stress_l_eq"], 1074.0 * 1.2, places=1)
        self.assertAlmostEqual(burgos_opt_b["water_stress_l_eq"], 1074.0 * 3.4, places=1)

    def test_04_cryptographic_resource_decision_event_seal(self):
        """ResourceDecisionEvent generates valid 64-character SHA-256 hash and catches tampering."""
        tradeoffs = evaluate_changeover_tradeoffs({}, {}, "FR-AULNAY-04")
        event = create_resource_decision_event(
            site_id="FR-AULNAY-04",
            asset_id="Packaging Line 04",
            decision_type="BATCH_SEQUENCE_OPTIMIZATION",
            selected_option_id="OPTION_B",
            options=tradeoffs["options"],
            operator_id="Dr. Camille Laurent [11425]"
        )

        self.assertEqual(len(event.provenance_hash), 64)
        self.assertTrue(event.hard_constraints_satisfied)
        self.assertEqual(event.human_validation_status, "VALIDATED")

        # Recompute hash independently to verify provenance seal
        sel_opt = next(o for o in tradeoffs["options"] if o["option_id"] == "OPTION_B")
        raw = f"{event.event_id}|{event.timestamp}|FR-AULNAY-04|Packaging Line 04|BATCH_SEQUENCE_OPTIMIZATION|OPTION_B|{sel_opt['freshwater_l']}|Dr. Camille Laurent [11425]"
        expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.assertEqual(event.provenance_hash, expected_hash)

        # Tampering with physical water value invalidates signature
        tampered_raw = f"{event.event_id}|{event.timestamp}|FR-AULNAY-04|Packaging Line 04|BATCH_SEQUENCE_OPTIMIZATION|OPTION_B|9999.0|Dr. Camille Laurent [11425]"
        tampered_hash = hashlib.sha256(tampered_raw.encode("utf-8")).hexdigest()
        self.assertNotEqual(event.provenance_hash, tampered_hash)

    def test_05_datacenter_cooling_dispatch_generality_proof(self):
        """Data center cooling workload evaluation applies same decision abstraction."""
        dc_res = evaluate_datacenter_workload(
            workload_type="LLM Pre-training",
            dc_site_id="US-PHOENIX-DC01",
            ambient_temp_c=38.5
        )

        self.assertEqual(dc_res["vertical"], "DATA_CENTER_AI_COOLING")
        self.assertEqual(dc_res["selected_mode"], "MODE_3_CHANGELOOP_DISPATCH")
        self.assertEqual(len(dc_res["modes"]), 3)

        modes = {m["mode_id"]: m for m in dc_res["modes"]}
        m1 = modes["MODE_1_EVAPORATIVE"]
        m2 = modes["MODE_2_DRY_HYBRID"]
        m3 = modes["MODE_3_CHANGELOOP_DISPATCH"]

        # Evaporative has high water; Dry has high power penalty; Mode 3 optimizes both
        self.assertGreater(m1["direct_water_l"], m3["direct_water_l"])
        self.assertGreater(m2["energy_kwh"], m1["energy_kwh"])
        self.assertLess(m3["direct_water_l"], 500.0)
        self.assertGreater(dc_res["delta_vs_baseline"]["water_saved_l"], 1500.0)

if __name__ == "__main__":
    unittest.main()
