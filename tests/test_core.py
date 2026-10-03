import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import batches, burden, sequence_payload, cleaning, cascade, impact, pilot, models

class CoreTests(unittest.TestCase):
    def test_deterministic_batches(self): self.assertEqual(batches(), batches())
    def test_burden_non_negative(self):
        for a in batches()[:4]:
            for b in batches()[4:8]:
                x=burden(a,b); self.assertGreaterEqual(x['litres'], 0); self.assertGreaterEqual(x['minutes'], 0)
    def test_optimizer_preserves_batches(self):
        r=sequence_payload({}); self.assertEqual(set(r['baseline']['order']), set(r['optimized']['order']))
    def test_default_optimizer_never_worsens_water(self):
        for seed in range(2026, 2046):
            r=sequence_payload({'seed':seed})
            self.assertLessEqual(r['optimized']['water_demand_l'], r['baseline']['water_demand_l'])
    def test_duplicate_batches_are_rejected(self):
        q=batches()[:2]; q[1]['id']=q[0]['id']
        r=sequence_payload({'batches':q})
        self.assertEqual(r['status'],'NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS')
    def test_pilot_and_model_are_architected(self):
        self.assertEqual(pilot()['classification'],'ARCHITECTED'); self.assertEqual(models()['classification'],'ARCHITECTED')
    def test_missing_sensor_blocks_release(self):
        r=cleaning(failure='missing'); self.assertFalse(r['safety_gate']['automatic_release']); self.assertEqual(r['confidence'],'INSUFFICIENT DATA')
    def test_sensor_drift_blocks_release(self):
        r=cleaning(failure='drift'); self.assertFalse(r['safety_gate']['automatic_release']); self.assertEqual(r['confidence'],'INSUFFICIENT DATA')
    def test_reuse_not_approved(self):
        r=cascade({'quality':'screened'}); self.assertIn('No reuse is approved', r['notice'])
    def test_ledger_separates_cascade(self): self.assertIn('not added', impact({})['accounting_note'])
    def test_water_invariants(self):
        ledger=impact({'adapt_incremental_l':999999,'recovered_l':-1})
        self.assertGreaterEqual(ledger['water_demand_after_prevent_adapt_l'],0); self.assertGreaterEqual(ledger['cascade_potential_l'],0)
        self.assertEqual(cascade({'volume_l':-1})['available_volume_l'],0)

if __name__ == '__main__': unittest.main()
