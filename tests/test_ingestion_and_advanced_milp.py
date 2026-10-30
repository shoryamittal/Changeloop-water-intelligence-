# -*- coding: utf-8 -*-
"""ChangeLoop - Comprehensive Tests for Ingestion, Advanced MILP, Multi-Variable Ionic Calibration & Canonical Blocks."""
import unittest

from core.ingestion import (
    ERPQueueIngestionEngine,
    UltrasonicSteamTelemetryEngine,
    calibrate_multivariable_ionic,
)
from core.plant import machine_queues
from core.milp import solve_cluster_milp
from core.optimizer import optimise
from core.process import reference_lots, arrival_order
from core import provenance, billing


class TestIngestionAndControllers(unittest.TestCase):
    def setUp(self):
        self.engine = ERPQueueIngestionEngine()

    def test_controller_connectivity_status(self):
        status = self.engine.get_controller_status()
        self.assertTrue(status["all_healthy"])
        self.assertEqual(len(status["active_controllers"]), 3)
        types = {c["controller_type"] for c in status["active_controllers"]}
        self.assertEqual(types, {"SEDOMASTER", "DATATEX", "SETEX"})

    def test_ultrasonic_flow_metering_ibr_compliance(self):
        res = UltrasonicSteamTelemetryEngine.calculate_flow(
            pipe_inner_diameter_mm=65.0,
            delta_t_ns=142.5,
            speed_of_sound_m_s=1520.0,
            mount_angle_deg=45.0,
        )
        self.assertTrue(res["ibr_compliant"])
        self.assertFalse(res["hot_tap_required"])
        self.assertTrue(res["zero_downtime_certified"])
        self.assertGreater(res["flow_l_min"], 0.0)
        self.assertGreater(res["velocity_m_s"], 0.0)

    def test_multivariable_alkali_calibration_stages(self):
        # Scouring: high caustic, zero dyeing salt
        scour_res = calibrate_multivariable_ionic(
            raw_toroidal_ec_ms_cm=22.5,
            recipe_alkali_dosage_g_l=20.0,
            batch_stage_flag="SCOURING",
            ph=12.2,
            temp_c=28.0,
        )
        self.assertEqual(scour_res["batch_stage"], "SCOURING")
        self.assertGreater(scour_res["hydroxide_conductance_us_cm"], 5000.0)
        self.assertGreater(scour_res["alkali_overestimate_pct"], 100.0)

        # Fixation: Soda ash present (Na2CO3)
        fix_res = calibrate_multivariable_ionic(
            raw_toroidal_ec_ms_cm=35.0,
            recipe_alkali_dosage_g_l=15.0,
            batch_stage_flag="DYE_FIXATION",
            ph=10.5,
            temp_c=28.0,
        )
        self.assertEqual(fix_res["batch_stage"], "DYE_FIXATION")
        self.assertGreater(fix_res["carbonate_conductance_us_cm"], 1000.0)
        self.assertGreater(fix_res["true_salt_tds_mg_l"], 0.0)

        # Rinsing: neutral wash-off
        rinse_res = calibrate_multivariable_ionic(
            raw_toroidal_ec_ms_cm=18.5,
            recipe_alkali_dosage_g_l=0.0,
            batch_stage_flag="RINSING",
            ph=8.0,
            temp_c=25.0,
        )
        self.assertEqual(rinse_res["batch_stage"], "RINSING")
        self.assertLess(rinse_res["total_alkali_conductance_us_cm"], 50.0)
        self.assertGreater(rinse_res["true_salt_tds_mg_l"], 5000.0)


class TestAdvancedMILPAndDisaggregation(unittest.TestCase):
    def test_cluster_milp_overload_and_hydrograph(self):
        queues = machine_queues(4)
        cluster = solve_cluster_milp(queues)

        self.assertEqual(cluster["status"], "COORDINATED")
        # Selfish must breach at 121.9%
        self.assertAlmostEqual(cluster["selfish"]["utilization_pct"], 121.9, delta=0.2)
        self.assertTrue(cluster["selfish"]["overloaded"])

        # Coordinated must be safe (< 100%)
        self.assertLess(cluster["coordinated"]["utilization_pct"], 100.0)

        # 24-hour hydrograph
        hydro = cluster["hourly_hydrograph"]
        self.assertEqual(len(hydro), 24)
        for h in hydro:
            self.assertIn("hour", h)
            self.assertIn("uncoordinated_pct", h)
            self.assertIn("coordinated_pct", h)
            # Coordinated load stays within capacity
            self.assertLessEqual(h["coordinated_pct"], 100.0)

        # Quota expansion
        quota = cluster["production_quota_expansion"]
        self.assertGreater(quota["headroom_recovered_m3_per_day"], 0.0)
        self.assertGreater(quota["additional_export_lots_permitted_per_day"], 0)

    def test_savings_disaggregation_concept_note(self):
        lots = reference_lots()
        arr = arrival_order()
        opt = optimise(lots, arr)

        self.assertIn("savings_disaggregation", opt)
        disagg = opt["savings_disaggregation"]

        # Component 1: ~Rs 607 / lot (100% of 6% steam & water cut)
        self.assertAlmostEqual(disagg["component_1_reorder_alone_inr_per_lot"], 607.47, delta=1.0)
        self.assertEqual(disagg["reorder_freshwater_cut_pct"], 6.0)
        self.assertEqual(disagg["reorder_steam_cut_pct"], 6.0)

        # Component 2: ~Rs 964 / lot
        self.assertAlmostEqual(disagg["component_2_counter_current_alone_inr_per_lot"], 964.47, delta=1.0)
        self.assertEqual(disagg["counter_current_freshwater_cut_pct"], 0.0)
        self.assertEqual(disagg["counter_current_steam_cut_pct"], 0.0)

        # Total: ~Rs 1,572 / lot
        self.assertAlmostEqual(disagg["total_recommended_saving_inr_per_lot"], 1571.94, delta=1.0)


class TestCanonicalBlocksAndBilling(unittest.TestCase):
    def test_canonical_10_field_blocks(self):
        blocks = provenance.get_canonical_blocks(limit=10)
        self.assertGreater(len(blocks), 0)
        b0 = blocks[0]

        required_fields = [
            "block_index", "timestamp_utc", "operator_id", "machine_ids",
            "baseline_schedule_hash", "approved_schedule_hash",
            "predicted_salt_cut_kg", "predicted_steam_saved_kwh",
            "evidence_registry_version_hash", "previous_block_hash",
            "block_hash",
        ]
        for f in required_fields:
            self.assertIn(f, b0, f"Field {f} missing from canonical block")

    def test_three_pillar_pricing_model(self):
        quote = billing.calculate_billing(
            lots_processed=5000,
            salt_avoided_kg=62500.0,
            client_total_savings_inr=7860000.0,
            include_cbam=True,
            new_skids=1,
        )
        self.assertEqual(quote.pillar_1_subtotal_inr, 75000.0)  # 5000 * Rs 15
        self.assertEqual(quote.pillar_2_subtotal_inr, 9375.0)   # 62.5 tonnes * Rs 150
        self.assertEqual(quote.onboarding_subtotal_inr, 250000.0)
        self.assertGreater(quote.client_savings_inr, quote.total_invoice_inr * 15.0)


if __name__ == "__main__":
    unittest.main()
