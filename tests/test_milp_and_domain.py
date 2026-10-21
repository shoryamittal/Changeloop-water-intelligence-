# -*- coding: utf-8 -*-
"""ChangeLoop - Comprehensive Tests for MILP Solver, Ionic Calibration, and SaaS Billing."""
import unittest

from core.process import reference_lots, DyeLot, shade_tier
from core.milp import solve_milp_sequence, solve_cluster_milp
from core.plant import machine_queues
from core.calibration import CALIBRATION_ENGINE, TitrationRecord
from core.billing import calculate_billing, evaluate_switching_thresholds, generate_cbam_certificate
from core import provenance


class TestShadeTierAndBoilOut(unittest.TestCase):
    def test_shade_tier_categorization(self):
        self.assertEqual(shade_tier(0.5), "LIGHT")
        self.assertEqual(shade_tier(1.0), "MEDIUM")
        self.assertEqual(shade_tier(2.5), "MEDIUM")
        self.assertEqual(shade_tier(3.0), "MEDIUM")
        self.assertEqual(shade_tier(3.5), "DARK")
        self.assertEqual(shade_tier(6.0), "DARK")

    def test_boil_out_detection(self):
        lots = reference_lots()
        # Find light lot and dark lot
        light_lot = next(l for l in lots if l.depth_owf < 1.0)
        dark_lot = next(l for l in lots if l.depth_owf > 3.0)

        from core.process import changeover_burden
        co_light_to_dark = changeover_burden(light_lot, dark_lot)
        self.assertFalse(co_light_to_dark.is_boil_out)

        co_dark_to_light = changeover_burden(dark_lot, light_lot)
        self.assertTrue(co_dark_to_light.is_boil_out)
        self.assertTrue(any("Machine Boil-Out required" in d for d in co_dark_to_light.drivers))


class TestMILPSolver(unittest.TestCase):
    def test_milp_reference_lots_optimal(self):
        lots = reference_lots()
        res = solve_milp_sequence(lots)
        self.assertEqual(res.status, "OPTIMAL")
        self.assertEqual(len(res.order), len(lots))
        self.assertIsNotNone(res.candidate)
        self.assertTrue(res.candidate.feasible)
        self.assertGreater(res.time_ms, 0)
        self.assertLess(res.time_ms, 5000)  # Should solve well under 5 seconds

    def test_milp_hard_deadline_pruning(self):
        # Create a lot with an impossible due_h deadline (e.g. 0.1 hours when process takes 3+ hours)
        impossible_lot = DyeLot(
            lot_id="L-IMPOSSIBLE",
            buyer_ref="TEST-BUYER",
            article="TEST-FABRIC",
            shade_name="NAVY",
            shade_hex="#000080",
            depth_owf=4.0,
            dye_class="REACTIVE",
            fabric_kg=300.0,
            machine_id="JET-01",
            due_h=0.1,  # Physically impossible to finish in 6 minutes
            priority=1,  # Firm buyer deadline
        )
        res = solve_milp_sequence([impossible_lot])
        self.assertEqual(res.status, "INFEASIBLE")

    def test_cluster_milp_coordination(self):
        queues = machine_queues(4)
        cluster_res = solve_cluster_milp(queues)
        self.assertIn(cluster_res["status"], ["COORDINATED", "BREACH_UNRESOLVED"])
        self.assertIn("selfish", cluster_res)
        self.assertIn("coordinated", cluster_res)
        self.assertGreater(cluster_res["elapsed_ms"], 0)


class TestIonicCalibration(unittest.TestCase):
    def test_alkali_interference_subtraction(self):
        # Test that high pH liquor has alkali conductance correctly subtracted
        res_high_ph = CALIBRATION_ENGINE.calibrate_tds(raw_conductivity_us_cm=18500.0, ph=10.5, temp_c=25.0)
        res_neutral_ph = CALIBRATION_ENGINE.calibrate_tds(raw_conductivity_us_cm=18500.0, ph=7.0, temp_c=25.0)

        # High pH should have significant alkali conductance subtracted
        self.assertGreater(res_high_ph["alkali_conductance_us_cm"], 50.0)
        # Neutral pH should have near-zero alkali conductance subtracted
        self.assertLess(res_neutral_ph["alkali_conductance_us_cm"], 1.0)
        # Net salt conductance should be lower in high pH than neutral pH for same raw conductivity
        self.assertLess(res_high_ph["net_salt_conductance_us_cm"], res_neutral_ph["net_salt_conductance_us_cm"])

    def test_argentometric_titration_math(self):
        titr = TitrationRecord(
            record_id="TITR-TEST",
            timestamp="2026-10-21T06:00:00Z",
            operator_id="LAB-TEST",
            sample_volume_ml=50.0,
            titrant_normality_n=0.1000,
            titre_volume_ml=15.1,
            blank_volume_ml=0.1,
        )
        # Net titre = 15.0 mL
        # [Cl-] = (15.0 * 0.1 * 35453) / 50.0 = 1063.59 mg/L
        expected_cl = (15.0 * 0.1 * 35453.0) / 50.0
        self.assertAlmostEqual(titr.chloride_mg_per_l, expected_cl, places=1)
        expected_nacl = expected_cl * (58.44 / 35.453)
        self.assertAlmostEqual(titr.nacl_equivalent_mg_per_l, expected_nacl, places=1)

    def test_sensor_fault_fail_safe_hold_state(self):
        # Simulate a sensor dropping below 95% completeness
        CALIBRATION_ENGINE.devices["US-FLOW-01"].completeness_pct = 91.2
        try:
            res = CALIBRATION_ENGINE.calibrate_tds(raw_conductivity_us_cm=18500.0, ph=9.8, temp_c=25.0)
            self.assertEqual(res["status"], "HOLD_STATE")
            self.assertFalse(res["savings_claim_allowed"])
            self.assertEqual(res["savings_inr_multiplier"], 0.0)
            self.assertIn("HOLD_STATE", res["fail_reason"])
        finally:
            # Restore device health
            CALIBRATION_ENGINE.devices["US-FLOW-01"].completeness_pct = 99.8


class TestBillingAndCBAM(unittest.TestCase):
    def test_three_pillar_pricing(self):
        quote = calculate_billing(
            lots_processed=10,
            salt_avoided_kg=1000.0,  # 1 tonne
            client_total_savings_inr=50000.0,
            include_cbam=True,
            new_skids=1,
        )
        # Pillar 1: 10 * Rs 15 = Rs 150
        self.assertEqual(quote.pillar_1_subtotal_inr, 150.0)
        # Pillar 2: 1.0 tonne * Rs 150 = Rs 150
        self.assertEqual(quote.pillar_2_subtotal_inr, 150.0)
        # Pillar 3: Rs 100,000 / 12 = Rs 8,333.33
        self.assertAlmostEqual(quote.pillar_3_subtotal_inr, 8333.33, places=1)
        # Onboarding: 1 * Rs 250,000 = Rs 250,000
        self.assertEqual(quote.onboarding_subtotal_inr, 250000.0)

    def test_switching_thresholds(self):
        sw = evaluate_switching_thresholds()
        self.assertEqual(sw["low_salt_chemistry"]["threshold_inr_kg"], 5.74)
        self.assertEqual(sw["evaporator_steam"]["threshold_inr_kg"], 3.13)
        self.assertEqual(sw["freshwater_tariff"]["threshold_inr_m3"], 251.0)

    def test_cbam_certificate_cryptographic_signature(self):
        cert = generate_cbam_certificate(
            site_id="IN-TN-TIRUPUR-01",
            reporting_period="OCT-2026",
            production_kg=10000.0,
            co2e_avoided_kg=1200.0,
            lot_ids=["L-4412", "L-4413"],
        )
        self.assertEqual(cert["status"], "CERTIFIED_VALID")
        self.assertEqual(len(cert["cryptographic_signature"]), 64)  # Valid SHA-256 hex string


class TestLedgerTamperEvidence(unittest.TestCase):
    def test_tamper_detection(self):
        # Reset and add record
        provenance.reset()
        rec = provenance.append("LOT_SEQUENCED", "Lot sequence approved by planner", {"test": True})
        seq = rec["seq"]

        # Verify intact before tampering
        v_before = provenance.verify_chain()
        self.assertTrue(v_before["intact"])

        # Tamper record
        provenance.tamper_record(seq=seq, new_detail="FORGED_DATA")

        # Verify chain detects break
        v_after = provenance.verify_chain()
        self.assertFalse(v_after["intact"])
        self.assertEqual(v_after["first_break_at_seq"], seq)

        # Restore clean state
        provenance.reset()


if __name__ == "__main__":
    unittest.main()
