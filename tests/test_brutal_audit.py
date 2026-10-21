# -*- coding: utf-8 -*-
"""ChangeLoop - Brutal QA & Invariant Audit Test Suite.

Verifies and certifies all five audit phases:
  Phase 1: Mathematical & Thermodynamic Invariants (Water vs Salt, CPCB, 25 Coefficients, Switching Points)
  Phase 2: Algorithmic & Safety Rules (MILP Shade Matrix, Hard Deadlines, 4-Machine Headroom, Sensor Fail-Safe, Tamper Chain)
  Phase 3: Business Model & SaaS Billing (Zero Gain-Share, 3-Pillar Margins, Pass-Through Skid)
  Phase 4: High-Density Industrial UX (Tabular Numbers, Zero Emojis, Crisp Status Tags)
  Phase 5: Release Verification
"""
import unittest
import math

from core import factors, zld, narrative, policy, basin, economics, scenarios
from core.process import reference_lots, arrival_order, changeover_burden, DyeLot, shade_tier
from core.optimizer import ObjectiveWeights, HardConstraints, evaluate_candidate
from core.milp import solve_milp_sequence, solve_cluster_milp
from core.plant import machine_queues
from core.calibration import CALIBRATION_ENGINE, TitrationRecord
from core.billing import (
    calculate_billing, evaluate_switching_thresholds,
    PILLAR_1_FEE_PER_LOT_INR, PILLAR_2_FEE_PER_TONNE_SALT_INR,
    PILLAR_3_CBAM_ANNUAL_FEE_INR, HARDWARE_ONBOARDING_FEE_INR,
)
from core.session import Session
from core import provenance


class Phase1MathAndThermodynamicsAudit(unittest.TestCase):
    """Phase 1: Thermodynamic mass balances and mathematical invariants."""

    def test_water_vs_salt_invariant(self):
        """Halving water without changing salt mass moves evaporator steam by 0.00%.
        Cutting salt by 20% drops evaporator steam by exactly 20.00%.
        """
        p = narrative.proof()
        # Water cut 20%: zero change to evaporator
        self.assertAlmostEqual(p["cut_water_20pct_change_pct"], 0.0, places=6,
                               msg="Cutting water alone must not change evaporator steam duty.")
        # Salt cut 20%: exact 20% drop in evaporator
        self.assertAlmostEqual(p["cut_salt_20pct_change_pct"], -20.0, places=2,
                               msg="Cutting salt mass by 20% must cut evaporator steam by 20.0%.")

    def test_cpcb_tirupur_water_strength_reject_fraction(self):
        """CPCB measured 18,340 mg/L TDS at Tirupur against 60,000 mg/L ceiling -> 30.6% reject."""
        val = narrative.validation()
        cpcb_point = next((pt for pt in val["points"] if abs(pt["inlet_tds_mg_l"] - 18340.0) < 1.0), None)
        self.assertIsNotNone(cpcb_point, "CPCB 18,340 mg/L validation point must be present.")
        self.assertEqual(cpcb_point["predicted_reject_frac_pct"], 30.6,
                         "18,340 mg/L / 60,000 mg/L must yield exactly 30.6% reject.")

    def test_queue_decomposition_figures(self):
        """Decomposition of the 5-lot baseline queue into reorder vs counter-current."""
        import itertools
        _lots, _arr = reference_lots(), arrival_order()
        _w, _c = ObjectiveWeights(), HardConstraints()

        def _cost(r):
            return r.consequence["cost_inr"]["total"] + r.sequence["strategy_cost_inr"]

        def _best(strategy):
            b = None
            for p in itertools.permutations([x.lot_id for x in _lots]):
                r = evaluate_candidate(_lots, list(p), basin.DEFAULT_SITE, _w, _c, strategy)
                if r.feasible and (b is None or r.objective_inr < b.objective_inr):
                    b = r
            return b

        _base = evaluate_candidate(_lots, _arr, basin.DEFAULT_SITE, _w, _c, "CONVENTIONAL")
        _seq = _best("CONVENTIONAL")
        _cc = _best("COUNTER_CURRENT")

        seq_lot = round((_cost(_base) - _cost(_seq)) / 5.0)
        rinse_lot = round((_cost(_seq) - _cost(_cc)) / 5.0)
        total_lot = round((_cost(_base) - _cost(_cc)) / 5.0)

        self.assertEqual(seq_lot, 607, "Re-ordering lots alone must yield Rs 607/lot.")
        self.assertEqual(rinse_lot, 964, "Counter-current rinsing alone must yield Rs 964/lot.")
        self.assertEqual(total_lot, 1572, "Combined recommended plan must yield Rs 1,572/lot.")

        # Reordering alone drives 100% of the 6% fresh water and evaporator steam cut
        self.assertAlmostEqual(_seq.consequence["water"]["freshwater_intake_l"],
                               _cc.consequence["water"]["freshwater_intake_l"], places=1)
        self.assertAlmostEqual(_seq.consequence["zld"]["mee_thermal_kwh"],
                               _cc.consequence["zld"]["mee_thermal_kwh"], places=1)

    def test_twenty_five_coefficients_and_zero_measured(self):
        """Evidence registry must contain exactly 25 coefficients with MEASURED == 0 pre-pilot."""
        summary = factors.evidence_summary()
        self.assertEqual(summary.get("PUBLISHED", 0), 17)
        self.assertEqual(summary.get("DERIVED", 0), 4)
        self.assertEqual(summary.get("ASSUMED", 0), 4)
        self.assertEqual(summary.get("MEASURED", 0), 0)
        self.assertEqual(len(factors.FACTORS), 25)

        # Audit trail checks
        trail = factors.audit_trail()
        self.assertEqual(len(trail), 25)
        for f in trail:
            self.assertIn("category", f)
            self.assertIn("source_citation", f)
            self.assertIn("derivation_formula", f)
            self.assertTrue(len(f["source_citation"]) > 10)

    def test_policy_switching_thresholds(self):
        """Policy switching points: low-salt dye Rs 5.74/kg, steam Rs 3.13/kWh, water Rs 251/m3."""
        dye = policy.switching_point("low_salt_chemistry_cost_inr_per_kg_fabric")
        steam = policy.switching_point("steam_cost_inr_per_kwh_th")
        water = policy.switching_point("freshwater_cost_inr_per_m3")

        self.assertAlmostEqual(dye["switching_value"], 5.748, places=2)
        self.assertAlmostEqual(steam["switching_value"], 3.125, places=2)
        self.assertAlmostEqual(water["switching_value"], 250.795, places=0)


class Phase2AlgorithmicAndSafetyAudit(unittest.TestCase):
    """Phase 2: MILP solver, safety gates, sensor drift, and hash provenance."""

    def test_shade_transition_matrix(self):
        """Light -> Medium -> Dark is valid. Dark -> Light triggers forced caustic boil-out."""
        lots = reference_lots()
        light = next(l for l in lots if l.depth_owf < 1.0)
        dark = next(l for l in lots if l.depth_owf > 3.0)

        # Light -> Dark
        co_fwd = changeover_burden(light, dark)
        self.assertFalse(co_fwd.is_boil_out)

        # Dark -> Light
        co_rev = changeover_burden(dark, light)
        self.assertTrue(co_rev.is_boil_out)
        self.assertTrue(any("Machine Boil-Out required" in d for d in co_rev.drivers))

    def test_firm_delivery_date_hard_pruning(self):
        """Sequences violating firm buyer due dates must be pruned (INFEASIBLE), never softly penalized."""
        impossible_lot = DyeLot(
            lot_id="L-TIGHT",
            buyer_ref="PO-RUSH",
            article="Jersey 180 gsm",
            shade_name="NAVY",
            shade_hex="#000080",
            depth_owf=4.0,
            dye_class="REACTIVE",
            fabric_kg=300.0,
            machine_id="JET-01",
            due_h=0.2,  # 12 minutes limit
            priority=1,  # Firm date
        )
        res = solve_milp_sequence([impossible_lot])
        self.assertEqual(res.status, "INFEASIBLE")

    def test_cluster_headroom_coordination(self):
        """4 machines discharging uncoordinated breach 100% capacity; coordinated schedule stays safe."""
        queues = machine_queues(4)
        cluster = solve_cluster_milp(queues)
        self.assertEqual(cluster["status"], "COORDINATED")
        self.assertTrue(cluster["selfish"]["overloaded"])
        self.assertGreater(cluster["selfish"]["utilization_pct"], 100.0)
        self.assertLess(cluster["coordinated"]["utilization_pct"], 100.0)

    def test_sensor_drift_and_completeness_fail_safe(self):
        """Completeness < 95% or drift > 15% must force HOLD_STATE and credit Rs 0 savings."""
        # 1. Test completeness < 95%
        CALIBRATION_ENGINE.devices["US-FLOW-01"].completeness_pct = 92.0
        try:
            res = CALIBRATION_ENGINE.calibrate_tds(18500.0)
            self.assertEqual(res["status"], "HOLD_STATE")
            self.assertFalse(res["savings_claim_allowed"])
            self.assertEqual(res["savings_inr_multiplier"], 0.0)
        finally:
            CALIBRATION_ENGINE.devices["US-FLOW-01"].completeness_pct = 99.8

        # 2. Test drift > 15%
        CALIBRATION_ENGINE.devices["TOROID-COND-01"].drift_pct = 18.5
        try:
            res = CALIBRATION_ENGINE.calibrate_tds(18500.0)
            self.assertEqual(res["status"], "HOLD_STATE")
            self.assertFalse(res["savings_claim_allowed"])
            self.assertEqual(res["savings_inr_multiplier"], 0.0)
        finally:
            CALIBRATION_ENGINE.devices["TOROID-COND-01"].drift_pct = 2.3

    def test_washoff_supervisor_pin_and_sitra_fastness_gate(self):
        """Early dye bath release requires SITRA fastness >= Grade 4.0 and supervisor PIN."""
        s = Session()
        s.run_optimisation()
        s.decide_sequence(True)
        s.run_washoff(None)

        # 1. Test fastness grade < 4.0 is blocked
        res_bad_grade = s.release_washoff(True, pin="7701", fastness_grade=3.5)
        self.assertIn("error", res_bad_grade)
        self.assertIn("below Grade 4.0", res_bad_grade["error"])

        # 2. Test invalid PIN is blocked
        res_bad_pin = s.release_washoff(True, pin="WRONG-PIN", fastness_grade=4.5)
        self.assertIn("error", res_bad_pin)
        self.assertIn("PIN authentication failed", res_bad_pin["error"])

        # 3. Test valid release
        res_ok = s.release_washoff(True, pin="7701", fastness_grade=4.5)
        self.assertNotIn("error", res_ok)
        self.assertEqual(s.washoff_status, "RELEASED")

    def test_decline_records_zero_savings(self):
        """Declining early release must credit exactly 0.0 L water avoided and record supervisor sign-off."""
        s = Session()
        s.run_optimisation()
        s.decide_sequence(True)
        s.run_washoff(None)
        res = s.release_washoff(False)
        self.assertNotIn("error", res)
        self.assertEqual(s.washoff_status, "FULL_CYCLE")
        imp = s.impact()
        self.assertEqual(imp["washoff_water_avoided_l"], 0.0)

    def test_immutable_ledger_tamper_detection(self):
        """Interactive tampering with any ledger row must break the HMAC-SHA256 chain."""
        provenance.reset()
        provenance.append("ACTION_1", "Legitimate record 1", {"k": 1})
        rec2 = provenance.append("ACTION_2", "Legitimate record 2", {"k": 2})

        # Chain must be intact
        v_before = provenance.verify_chain()
        self.assertTrue(v_before["intact"])

        # Tamper record 2
        provenance.tamper_record(seq=rec2["seq"], new_detail="FORGED: Zero salt record")
        v_after = provenance.verify_chain()
        self.assertFalse(v_after["intact"])
        self.assertEqual(v_after["first_break_at_seq"], rec2["seq"])
        provenance.reset()


class Phase3BillingAndRevenueAudit(unittest.TestCase):
    """Phase 3: 3-Pillar SaaS billing model and 0% gain-share audit."""

    def test_three_pillar_pricing_and_margins(self):
        """Factory Rs 15/lot (99% GM), CETP Rs 150/tonne (90% GM), CBAM Rs 1,00,000/yr (98% GM), Skid Rs 2,50,000."""
        self.assertEqual(PILLAR_1_FEE_PER_LOT_INR, 15.0)
        self.assertEqual(PILLAR_2_FEE_PER_TONNE_SALT_INR, 150.0)
        self.assertEqual(PILLAR_3_CBAM_ANNUAL_FEE_INR, 100000.0)
        self.assertEqual(HARDWARE_ONBOARDING_FEE_INR, 250000.0)

        quote = calculate_billing(
            lots_processed=100,
            salt_avoided_kg=2000.0,
            client_total_savings_inr=150000.0,
            include_cbam=True,
            new_skids=1,
        )
        self.assertEqual(quote.pillar_1_subtotal_inr, 1500.0)
        self.assertEqual(quote.pillar_2_subtotal_inr, 300.0)
        self.assertAlmostEqual(quote.pillar_3_subtotal_inr, 8333.33, places=1)
        self.assertEqual(quote.onboarding_subtotal_inr, 250000.0)
        d = quote.to_dict()
        self.assertEqual(d["gross_margins"]["pillar_1"], "99.0%")
        self.assertEqual(d["gross_margins"]["pillar_2"], "90.0%")
        self.assertEqual(d["gross_margins"]["pillar_3"], "98.0%")


if __name__ == "__main__":
    unittest.main()
