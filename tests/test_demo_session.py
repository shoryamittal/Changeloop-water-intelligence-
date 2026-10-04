import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import math
from core.demo import DemoSession, DEMO_STEPS

class TestDemoSession(unittest.TestCase):

    def setUp(self):
        self.session = DemoSession(seed=2030)

    def test_initialization(self):
        d = self.session.to_dict()
        self.assertEqual(d["plant"], "FR-AULNAY-04")
        self.assertEqual(d["line"], "Line 04 (Lipstick & Emulsions)")
        self.assertEqual(d["baseline_sequence"], ["B-217", "B-220", "B-218", "B-219", "B-221"])
        self.assertEqual(d["current_sequence"], d["baseline_sequence"])
        self.assertEqual(d["baseline_burden_l"], 862.0)
        self.assertEqual(d["decision_status"], "PENDING_REVIEW")

    def test_optimization_and_recommendation(self):
        opt = self.session.run_optimization()
        self.assertEqual(opt["status"], "FEASIBLE")
        self.assertEqual(opt["optimized"]["order"], ["B-217", "B-218", "B-219", "B-220", "B-221"])
        self.assertEqual(opt["water_avoided_l"], 284.0)
        
        self.assertIsNotNone(self.session.recommendation)
        self.assertIn("B-218 ahead of Batch B-220", self.session.recommendation["action"])

    def test_accept_vs_retain(self):
        # Optimization run
        self.session.run_optimization()
        
        # Accept
        acc = self.session.accept_recommendation()
        self.assertEqual(acc["status"], "ACCEPTED")
        self.assertEqual(self.session.current_sequence, ["B-217", "B-218", "B-219", "B-220", "B-221"])
        self.assertEqual(self.session.selected_changeover["from_batch"], "B-217")
        self.assertEqual(self.session.selected_changeover["to_batch"], "B-218")
        self.assertEqual(self.session.selected_changeover["transition_water_l"], 38.0)

        # Retain baseline
        ret = self.session.retain_baseline()
        self.assertEqual(ret["status"], "RETAINED")
        self.assertEqual(self.session.current_sequence, ["B-217", "B-220", "B-218", "B-219", "B-221"])

    def test_cleaning_and_safety_gate(self):
        # Nominal run
        sim = self.session.start_cleaning(None)
        self.assertIsNotNone(sim)
        self.assertEqual(self.session.operator_validation, "PENDING_VALIDATION")
        
        # Authorize cutoff
        auth = self.session.authorize_early_cutoff()
        self.assertEqual(auth["status"], "AUTHORIZED")
        self.assertEqual(auth["water_saved_l"], 130.0)

        # Fault run blocks authorization
        self.session.start_cleaning("drift")
        blocked = self.session.authorize_early_cutoff()
        self.assertEqual(blocked["status"], "BLOCKED")

    def test_cascade_and_impact_mass_balance(self):
        self.session.run_optimization()
        self.session.accept_recommendation()
        self.session.start_cleaning(None)
        self.session.authorize_early_cutoff()
        self.session.execute_cascade_screening()
        self.session.authorize_cascade_committal()

        imp = self.session.impact_record
        self.assertEqual(imp["upstream_avoided_l"], 284.0)
        self.assertEqual(imp["adaptive_avoided_l"], 130.0)
        self.assertEqual(imp["total_water_demand_avoided_l"], 414.0)
        self.assertEqual(imp["cascade_reclaimed_l"], self.session.recovery_result["volume_l"])

        # Strict mass balance
        expected_gross = imp["common_baseline_l"] - imp["total_water_demand_avoided_l"]
        self.assertAlmostEqual(imp["gross_consumed_l"], expected_gross, places=1)
        expected_net = imp["gross_consumed_l"] - imp["cascade_reclaimed_l"]
        self.assertAlmostEqual(imp["net_water_intake_l"], expected_net, places=1)

    def test_session_reset(self):
        self.session.run_optimization()
        self.session.accept_recommendation()
        self.session.reset_session()
        self.assertEqual(self.session.decision_status, "PENDING_REVIEW")
        self.assertEqual(self.session.current_sequence, ["B-217", "B-220", "B-218", "B-219", "B-221"])

if __name__ == "__main__":
    unittest.main()
