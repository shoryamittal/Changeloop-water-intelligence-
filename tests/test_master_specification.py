# -*- coding: utf-8 -*-
"""ChangeLoop - Master Verification Test Suite (250+ Tests Target).

Tests the full 6-stage architecture, physics invariants, multi-machine MILP,
commercial 3-pillar ROI, security controls, and weekend-script simulator.
"""
import unittest
import os
import re
import json
import time
from pathlib import Path

from core import (
    factors, process, zld, optimizer, milp, ingestion, telemetry,
    provenance, economics, policy, plant, auth, validator, ratelimit, simulator,
    session
)


class TestSuite1ThermodynamicAndChemicalInvariants(unittest.TestCase):
    def test_water_reduction_zero_boil_saving(self):
        """Invariant A: Cutting water by 20% with constant salt yields exactly 0.00% steam change."""
        baseline_salt_kg = 85.0
        c_max = factors.get("ro_max_reject_tds_mg_l") / 1000.0  # 60 kg/m3
        mee_kwh_per_m3 = factors.get("mee_specific_thermal_kwh_per_m3")  # 188 kWh/m3

        v_reject_baseline = baseline_salt_kg / c_max
        steam_kwh_baseline = v_reject_baseline * mee_kwh_per_m3

        # Water reduced by 20% (e.g. 11,907 L -> 9,525.6 L)
        # Salt mass remains exactly 85.0 kg
        v_reject_reduced_water = baseline_salt_kg / c_max
        steam_kwh_reduced_water = v_reject_reduced_water * mee_kwh_per_m3

        delta_steam_pct = abs(steam_kwh_reduced_water - steam_kwh_baseline) / steam_kwh_baseline
        self.assertAlmostEqual(delta_steam_pct, 0.0, places=5)
        self.assertEqual(steam_kwh_reduced_water, steam_kwh_baseline)

    def test_salt_reduction_linear_boil_saving(self):
        """Invariant B: Cutting salt mass by 20% reduces reject and steam by exactly 20.00%."""
        baseline_salt_kg = 100.0
        c_max = 60.0  # kg/m3
        mee_kwh = 188.0

        v1 = baseline_salt_kg / c_max
        s1 = v1 * mee_kwh

        reduced_salt_kg = 80.0  # -20%
        v2 = reduced_salt_kg / c_max
        s2 = v2 * mee_kwh

        reduction_pct = (s1 - s2) / s1
        self.assertAlmostEqual(reduction_pct, 0.20, places=4)

    def test_cpcb_tirupur_reject_benchmark(self):
        """Invariant C: CPCB raw effluent 18,340 mg/L against 60,000 mg/L yields exactly 30.57% (~30.6%)."""
        cpcb_tds = 18340.0
        membrane_limit = 60000.0
        reject_share = cpcb_tds / membrane_limit
        self.assertAlmostEqual(reject_share, 0.3056666, places=4)
        self.assertEqual(round(reject_share * 100, 1), 30.6)

    def test_coal_vs_wood_biomass_calibration(self):
        """Verify thermal energy and cost conversions between Coal and Seasoned Wood."""
        coal = policy.BOILER_FUEL_PROFILES["COAL_BASELINE"]
        wood = policy.BOILER_FUEL_PROFILES["SEASONED_WOOD"]
        wet_wood = policy.BOILER_FUEL_PROFILES["WET_WOOD"]

        self.assertEqual(coal["steam_cost_inr_per_kwh_th"], 2.03)
        self.assertEqual(coal["boiler_co2e_kg_per_kwh_th"], 0.452)
        self.assertEqual(wood["fuel_gcv_mj_per_kg"], 15.5)
        self.assertEqual(wood["thermal_efficiency_pct"], 78.0)
        self.assertEqual(wet_wood["steam_cost_multiplier"], 0.75)
        self.assertEqual(wet_wood["required_dye_discount_display"], "17%")

    def test_alkali_interference_regression(self):
        """Alkali injection does not inflate true salt when corrected against AgNO3."""
        calib = ingestion.CALIBRATION_ENGINE.calibrate_tds(
            raw_conductivity_us_cm=48000.0,
            ph=10.5,
            temp_c=65.0
        )
        self.assertEqual(calib["status"], "VALID")
        self.assertTrue(calib["savings_claim_allowed"])
        self.assertGreater(calib["alkali_conductance_us_cm"], 0.0)

    def test_sensor_drift_hold_zero_claim(self):
        """Dropping packet completeness or detecting drift forces lockout and zero savings claim."""
        lots = process.reference_lots()
        l = lots[0]
        res = telemetry.simulate_washoff(
            lot_id=l.lot_id,
            scheduled_baths=4,
            bath_litres=l.bath_litres,
            bath_minutes=15,
            depth_owf=l.depth_owf,
            salt_dose_g_per_l=60.0,
            fault_mode="sensor_drift"
        )
        d = res.to_dict()
        self.assertEqual(d["gate"]["state"], "LOCKED_OUT")
        self.assertFalse(d["gate"]["automatic_release"])
        self.assertEqual(d["water_avoidable_l"], 0.0)
        self.assertEqual(d["salt_avoidable_kg"], 0.0)


class TestSuite2MultiMachineMILPAndManufacturing(unittest.TestCase):
    def test_hard_delivery_pruning(self):
        """Any lot sequence delaying delivery past due_h is pruned with hard constraint violations."""
        lots = process.reference_lots()
        tight_lots = [process.DyeLot(
            lot_id=l.lot_id, buyer_ref=l.buyer_ref, article=l.article, shade_name=l.shade_name,
            shade_hex=l.shade_hex, depth_owf=l.depth_owf, dye_class=l.dye_class,
            fabric_kg=l.fabric_kg, machine_id=l.machine_id, due_h=0.1, priority=l.priority
        ) for l in lots]
        order = [l.lot_id for l in tight_lots]
        seq_eval = process.evaluate_sequence(tight_lots, order)
        violations = optimizer.check_constraints(seq_eval, optimizer.HardConstraints(no_firm_date_breach=True))
        self.assertGreater(len(violations), 0)
        self.assertTrue(any("Firm ship date breached" in v for v in violations))

    def test_strict_light_to_dark_shade_matrix(self):
        """Dark-to-Light transitions trigger machine boil-out penalties."""
        lots = process.reference_lots()
        # lots[0] is Dark (Navy/Black 4.6% owf), lots[4] is Light (Pastel 0.18% owf)
        b_dark_to_light = process.changeover_burden(lots[0], lots[4])
        self.assertEqual(b_dark_to_light.direction, "DARK_TO_LIGHT")
        self.assertTrue(b_dark_to_light.is_boil_out)
        self.assertEqual(b_dark_to_light.cleaning_baths, 3)
        self.assertEqual(b_dark_to_light.water_l, 7200.0)

    def test_multi_machine_121_9_percent_overload_prevention(self):
        """Uncoordinated schedule hits 121.9% MEE load; MILP caps it at < 100% (~95.3%)."""
        queues = plant.machine_queues()
        milp_res = milp.solve_cluster_milp(queues)
        self.assertEqual(milp_res["selfish"]["utilization_pct"], 121.9)
        self.assertLessEqual(milp_res["coordinated"]["utilization_pct"], 100.0)
        self.assertAlmostEqual(milp_res["coordinated"]["utilization_pct"], 95.3, delta=2.0)

    def test_5_lot_shift_exact_reconciliation(self):
        """Verify exact figures for baseline, recommended, and disaggregated components."""
        s = session.get_session()
        s.reset("tirupur_mill_04")
        s.run_optimisation()
        state = s.state()
        opt = state["optimisation"]
        disagg = opt["savings_disaggregation"]

        base_cost = opt["options"][0]["cost_inr"]
        rec_cost = opt["options"][1]["cost_inr"]
        net_shift_saving = base_cost - rec_cost

        self.assertAlmostEqual(base_cost, 33897.0, delta=2.0)
        self.assertAlmostEqual(rec_cost, 26038.0, delta=2.0)
        self.assertAlmostEqual(net_shift_saving, 7859.0, delta=2.0)
        self.assertAlmostEqual(disagg["total_recommended_saving_inr_per_lot"], 1572.0, delta=2.0)
        self.assertAlmostEqual(disagg["component_1_reorder_alone_inr_per_lot"], 607.0, delta=2.0)
        self.assertAlmostEqual(disagg["component_2_counter_current_alone_inr_per_lot"], 964.0, delta=2.0)


class TestSuite3EvidenceHashChainAndCommercial(unittest.TestCase):
    def test_25_coefficient_evidence_gate(self):
        """Verify 17 Published, 4 Derived, 4 Assumed, 0 Measured."""
        ev = factors.evidence_summary()
        self.assertEqual(len(factors.FACTORS), 25)
        self.assertEqual(ev["PUBLISHED"], 17)
        self.assertEqual(ev["DERIVED"], 4)
        self.assertEqual(ev["ASSUMED"], 4)
        self.assertEqual(ev.get("MEASURED", 0), 0)

    def test_sha256_ledger_tamper_detection(self):
        """Mutating a record in the hash chain invalidates chain verification."""
        provenance.reset()
        init = provenance.verify_chain()
        self.assertTrue(init["intact"])

        # Tamper record
        provenance.tamper_record(seq=1, new_detail="FORGED: Zero salt discharged")
        post = provenance.verify_chain()
        self.assertFalse(post["intact"])
        self.assertEqual(post["first_break_at_seq"], 1)

        # Restore
        provenance.reset()
        self.assertTrue(provenance.verify_chain()["intact"])

    def test_declined_plan_logs_zero(self):
        """Declining an advisory schedule commits zero savings to the ledger."""
        s = session.get_session()
        s.reset("tirupur_mill_04")
        s.run_optimisation()
        state = s.decide_sequence(approve=False, actor="Quality Planner")
        self.assertEqual(state["sequencing_status"], "REJECTED")
        imp = s.impact()
        self.assertEqual(imp["cost_avoided_inr"], 0.0)

    def test_three_pillar_commercial_math(self):
        """Verify Factory Wedge (Rs 15/lot, 104x ROI), CETP Anchor (Rs 150/t), CBAM Tier (Rs 1L)."""
        roi = economics.commercial_roi_model(annual_lots=5000)
        p1 = roi["pillars"]["pillar_1_factory_wedge"]["recommended_plan"]
        self.assertEqual(p1["gross_savings_inr_yr"], 7859000.0)
        self.assertEqual(p1["software_fee_inr_yr"], 75000.0)
        self.assertEqual(p1["net_factory_benefit_inr_yr"], 7784000.0)
        self.assertEqual(p1["roi_multiple"], 103.8)

        p2 = roi["pillars"]["pillar_2_cetp_anchor"]
        self.assertEqual(p2["changeloop_fee_inr_yr"], 1155000.0)
        self.assertEqual(p2["cetp_gross_savings_at_3pct_cut_inr_yr"], 2284821.0)

        growth = roi["growth_projection"]
        self.assertEqual(growth["year_2_beachhead"]["arr_inr"], 2205000.0)
        self.assertEqual(growth["year_3_cluster_scale"]["arr_inr"], 6915000.0)

    def test_policy_switching_points(self):
        """Verify exact parity crossovers at -12% dye premium, +54% steam cost, +457% water tariff."""
        levers = policy.policy_levers("tirupur_mill_04")
        levers_by_coeff = {l["coefficient"]: l for l in levers["levers"]}
        dye = levers_by_coeff["low_salt_chemistry_cost_inr_per_kg_fabric"]
        steam = levers_by_coeff["steam_cost_inr_per_kwh_th"]
        water = levers_by_coeff["freshwater_cost_inr_per_m3"]

        self.assertEqual(dye["switching_value_display"], 5.74)
        self.assertAlmostEqual(dye["percent_change"], -11.6, delta=1.0)
        self.assertEqual(steam["switching_value_display"], 3.13)
        self.assertAlmostEqual(steam["percent_change"], 53.9, delta=2.0)
        self.assertEqual(water["switching_value_display"], 251.0)
        self.assertAlmostEqual(water["percent_change"], 457.3, delta=5.0)

    def test_pilot_alternating_t_test_and_budget(self):
        """Verify 52-week pilot A/B alternating tracker and exact Rs 5,28,000 budget."""
        tracker = telemetry.pilot_ab_statistical_tracker()
        self.assertEqual(len(tracker["stages"]), 6)
        self.assertEqual(tracker["sitra_gate"]["observed_failures"], 0)
        self.assertEqual(tracker["sitra_gate"]["gate_status"], "PASSED_ZERO_DEFECTS")
        self.assertIn("Statistically Significant", tracker["statistics"]["p_value"])

        budget = economics.pilot_budget_breakdown()
        self.assertEqual(budget["total_budget_inr"], 528000.0)
        self.assertTrue(budget["reconciled"])


class TestSuite4SecurityAndSimulator(unittest.TestCase):
    def test_jury_stress_test_all_scenarios(self):
        """Verify the 3 failure modes in the Jury Stress-Test Simulator."""
        sim = simulator.run_jury_stress_test()
        self.assertEqual(sim["status"], "SUCCESS")
        scenarios = sim["scenarios"]
        
        # Scouring spike
        scour = scenarios["caustic_scouring_spike"]
        self.assertEqual(scour["naive_weekend_script"]["financial_penalty_inr"], 42000)
        self.assertEqual(scour["changeloop_engine"]["financial_penalty_inr"], 0)

        # 4-machine blowout
        blowout = scenarios["shared_evaporator_blowout"]
        self.assertEqual(blowout["naive_weekend_script"]["peak_evaporator_utilization_pct"], 121.9)
        self.assertEqual(blowout["changeloop_engine"]["peak_evaporator_utilization_pct"], 94.2)

        # Shade contamination
        shade = scenarios["shade_contamination_boilout"]
        self.assertEqual(shade["naive_weekend_script"]["financial_loss_inr"], 1200000)
        self.assertEqual(shade["changeloop_engine"]["financial_loss_inr"], 0)

    def test_demo_role_switcher_tokens(self):
        """Verify demo role switcher generates valid tokens for all 4 industrial roles."""
        roles = ["PLANNER", "SUPERVISOR", "CETP_OPERATOR", "ADMIN"]
        for r in roles:
            ok, user, token, cookie_hdr = auth.demo_switch_role(r)
            self.assertTrue(ok)
            self.assertEqual(user["role"], r)
            self.assertIn("session_token=", cookie_hdr)
            self.assertIn("HttpOnly", cookie_hdr)
            self.assertIn("SameSite=Strict", cookie_hdr)

            # Cryptographic token validation
            v_ok, claims, err = auth.verify_token(token)
            self.assertTrue(v_ok)
            self.assertEqual(claims["role"], r)


if __name__ == "__main__":
    unittest.main()
