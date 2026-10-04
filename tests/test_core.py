import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import (
    batches, burden, sequence_payload, cleaning, cascade, impact,
    pilot, models, business_case, record, audit_events, transition_matrix
)

class CoreTests(unittest.TestCase):
    def test_deterministic_batches(self):
        self.assertEqual(batches(), batches())

    def test_burden_non_negative(self):
        for a in batches()[:4]:
            for b in batches()[4:8]:
                x = burden(a, b)
                self.assertGreaterEqual(x['litres'], 0)
                self.assertGreaterEqual(x['minutes'], 0)

    def test_optimizer_preserves_batches(self):
        r = sequence_payload({})
        self.assertEqual(set(r['baseline']['order']), set(r['optimized']['order']))

    def test_optimizer_has_traceable_run_id(self):
        self.assertTrue(sequence_payload({})['optimization_id'])

    def test_default_optimizer_never_worsens_water(self):
        for seed in range(2026, 2046):
            r = sequence_payload({'seed': seed})
            self.assertLessEqual(r['optimized']['water_demand_l'], r['baseline']['water_demand_l'])

    def test_two_opt_and_greedy_algorithms(self):
        r_greedy = sequence_payload({'algorithm': 'greedy'})
        r_two_opt = sequence_payload({'algorithm': 'two_opt'})
        self.assertIn(r_greedy['status'], ['FEASIBLE'])
        self.assertIn(r_two_opt['status'], ['FEASIBLE'])
        self.assertLessEqual(r_two_opt['optimized']['objective'], r_two_opt['baseline']['objective'])

    def test_duplicate_batches_are_rejected(self):
        q = batches()[:2]
        q[1]['id'] = q[0]['id']
        r = sequence_payload({'batches': q})
        self.assertEqual(r['status'], 'NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS')

    def test_invalid_objective_and_deadline_are_rejected(self):
        self.assertEqual(sequence_payload({'water_weight': 'bad'})['status'], 'NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS')
        q = batches()[:1]
        q[0]['deadline_h'] = 'bad'
        self.assertEqual(sequence_payload({'batches': q})['status'], 'NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS')

    def test_impact_propagates_infeasibility(self):
        r = impact({'batches': []})
        self.assertEqual(r['status'], 'NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS')

    def test_pilot_and_model_are_architected(self):
        self.assertEqual(pilot()['classification'], 'ARCHITECTED')
        self.assertEqual(models()['classification'], 'ARCHITECTED')

    def test_missing_sensor_blocks_release(self):
        r = cleaning(failure='missing')
        self.assertFalse(r['safety_gate']['automatic_release'])
        self.assertEqual(r['confidence'], 'INSUFFICIENT DATA')

    def test_sensor_drift_blocks_release(self):
        r = cleaning(failure='drift')
        self.assertFalse(r['safety_gate']['automatic_release'])
        self.assertEqual(r['confidence'], 'INSUFFICIENT DATA')

    def test_thermal_deficit_blocks_release(self):
        r = cleaning(failure='thermal')
        self.assertFalse(r['safety_gate']['automatic_release'])
        self.assertEqual(r['confidence'], 'INSUFFICIENT DATA')
        self.assertFalse(r['safety_gate']['three_point_clearance']['thermal_contact_satisfied'])

    def test_reuse_not_approved(self):
        r = cascade({'quality': 'screened'})
        self.assertIn('No reuse is approved', r['notice'])
        self.assertIn('streams', r)
        self.assertEqual(len(r['streams']), 3)

    def test_ledger_separates_cascade(self):
        self.assertIn('not added', impact({})['accounting_note'])

    def test_water_invariants(self):
        ledger = impact({'adapt_incremental_l': 999999, 'recovered_l': -1})
        self.assertGreaterEqual(ledger['water_demand_after_prevent_adapt_l'], 0)
        self.assertGreaterEqual(ledger['cascade_potential_l'], 0)
        self.assertEqual(cascade({'volume_l': -1})['available_volume_l'], 0)

    def test_sustainability_ledger_computes_energy_and_ghg(self):
        r = impact({})
        ledger = r['sustainability_ledger']
        self.assertGreaterEqual(ledger['thermal_energy_avoided_kwh'], 0)
        self.assertGreaterEqual(ledger['scope1_ghg_avoided_kg_co2e'], 0)
        self.assertGreaterEqual(ledger['caustic_detergent_avoided_kg'], 0)

    def test_business_case_requires_site_inputs(self):
        self.assertEqual(business_case({})['status'], 'INSUFFICIENT DATA')

    def test_business_case_is_input_driven(self):
        r = business_case({
            'changeovers_per_year': 10,
            'water_avoided_per_changeover_l': 20,
            'water_cost_per_l': 1,
            'implementation_cost': 100,
            'annual_software_cost': 10
        })
        self.assertEqual(r['status'], 'CALCULATED')
        self.assertEqual(r['direct_water_cost_benefit'], 200)
        self.assertIn('npv_3yr', r)

    def test_transition_matrix_returns_complete_pairs(self):
        m = transition_matrix()
        self.assertEqual(m['classification'], 'ENGINEERING_ASSUMPTION')
        self.assertEqual(len(m['matrix']), 36)

    def test_audit_event_is_durable_when_sqlite_available(self):
        event = record('TEST_EVENT', 'database test')
        self.assertTrue(any(x['event_id'] == event['event_id'] for x in audit_events()))

if __name__ == '__main__':
    unittest.main()
