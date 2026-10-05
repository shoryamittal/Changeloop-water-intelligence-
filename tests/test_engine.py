"""ChangeLoop engine tests.

Run:  python -m unittest discover -s tests -v

These are not smoke tests. Each one asserts a property the product's
credibility depends on, and several of them exist because they caught a real
defect during development:

  - the water and salt balance invariants caught an attribution that
    double-subtracted the wash-off release credit;
  - the tamper test caught a ledger MAC that excluded the human-readable
    detail field, so a record's meaning could be rewritten silently.
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core
from core import (
    basin, economics, factors, ledger, optimizer, process, provenance,
    scenarios, telemetry, zld,
)


# ---------------------------------------------------------------------------
# coefficient registry
# ---------------------------------------------------------------------------

class TestFactors(unittest.TestCase):

    def test_every_coefficient_is_fully_documented(self):
        for f in factors.FACTORS.values():
            self.assertTrue(f.unit, f.key + " has no unit")
            self.assertTrue(f.basis, f.key + " has no basis")
            self.assertIn(f.evidence,
                          {"MEASURED", "DERIVED", "PUBLISHED", "ASSUMED",
                           "SIMULATED"},
                          f.key + " has an unknown evidence class")
            self.assertGreater(len(f.basis), 40,
                               f.key + " basis is too thin to audit")

    def test_nothing_claims_to_be_measured(self):
        """No value in this prototype may claim MEASURED status."""
        measured = [f.key for f in factors.FACTORS.values()
                    if f.evidence == "MEASURED"]
        self.assertEqual(measured, [],
                         "a prototype must not claim metered values")

    def test_unregistered_coefficient_raises(self):
        with self.assertRaises(KeyError):
            factors.get("not_a_real_coefficient")

    def test_mee_specific_energy_matches_its_derivation(self):
        h = factors.get("h_vap_kwh_per_kg")
        econ = factors.get("mee_steam_economy")
        self.assertAlmostEqual(
            factors.get("mee_specific_thermal_kwh_per_m3"),
            (h * 1000.0) / econ, places=1)

    def test_recycled_water_costs_more_than_fresh(self):
        """The central economic fact of ZLD. If this inverts, the whole
        'avoid demand rather than recover water' argument collapses."""
        self.assertGreater(factors.get("recycled_water_cost_inr_per_m3"),
                           factors.get("freshwater_cost_inr_per_m3"))


# ---------------------------------------------------------------------------
# the core insight
# ---------------------------------------------------------------------------

class TestSaltIsWater(unittest.TestCase):

    def test_reject_volume_is_set_by_salt_not_water(self):
        """Halving water at constant salt must not change reject volume."""
        a = zld.treat(60000.0, 700.0)
        b = zld.treat(30000.0, 700.0)
        self.assertEqual(a.binding_constraint, "SALT_BALANCE")
        self.assertEqual(b.binding_constraint, "SALT_BALANCE")
        self.assertAlmostEqual(a.reject_l, b.reject_l, places=1)
        self.assertAlmostEqual(a.mee_thermal_kwh, b.mee_thermal_kwh, places=1)

    def test_halving_salt_halves_duty_while_salt_binds(self):
        """Only true while the SALT balance is the binding constraint."""
        a = zld.treat(200000.0, 2400.0)
        b = zld.treat(200000.0, 1200.0)
        self.assertEqual(a.binding_constraint, "SALT_BALANCE")
        self.assertEqual(b.binding_constraint, "SALT_BALANCE")
        self.assertAlmostEqual(b.reject_l, a.reject_l / 2.0, places=1)
        self.assertAlmostEqual(b.mee_thermal_kwh, a.mee_thermal_kwh / 2.0,
                               places=1)

    def test_hydraulic_floor_takes_over_below_the_crossover(self):
        """Salt reduction stops paying once the membrane floor binds.

        The crossover sits where salt_mass / reject_TDS_ceiling equals
        (1 - recovery_ceiling) x volume. Below it, further salt reduction
        buys no evaporator saving and water volume becomes the lever again.
        A product that claimed "cut salt, always win" would be wrong here,
        which is why the engine reports which constraint binds.
        """
        v = 60000.0
        ceiling = factors.get("ro_max_reject_tds_mg_l")
        floor_l = (1.0 - factors.get("ro_max_recovery_frac")) * v
        crossover_salt = floor_l * ceiling / 1e6

        above = zld.treat(v, crossover_salt * 1.5)
        below = zld.treat(v, crossover_salt * 0.5)
        self.assertEqual(above.binding_constraint, "SALT_BALANCE")
        self.assertEqual(below.binding_constraint, "RO_HYDRAULIC")

        # Below the crossover, halving salt again changes nothing.
        lower = zld.treat(v, crossover_salt * 0.25)
        self.assertAlmostEqual(lower.mee_thermal_kwh, below.mee_thermal_kwh,
                               places=1)

    def test_hydraulic_limit_binds_when_salt_is_low(self):
        r = zld.treat(60000.0, 1.0)
        self.assertEqual(r.binding_constraint, "RO_HYDRAULIC")
        self.assertAlmostEqual(
            r.reject_l,
            (1.0 - factors.get("ro_max_recovery_frac")) * 60000.0, places=1)

    def test_published_insight_matches_live_computation(self):
        d = zld.sensitivity_salt_vs_water()
        self.assertAlmostEqual(d["cut_water_20pct_only"]
                               ["mee_energy_change_pct"], 0.0, places=1)
        self.assertAlmostEqual(d["cut_salt_20pct_only"]
                               ["mee_energy_change_pct"], -20.0, places=1)

    def test_mass_and_salt_balances_close(self):
        for v, m in [(60000.0, 700.0), (1000.0, 0.0), (0.0, 0.0),
                     (500.0, 5000.0)]:
            r = zld.treat(v, m)
            self.assertTrue(r.check_mass_balance(),
                            "water balance failed for {} {}".format(v, m))
            self.assertTrue(r.check_salt_balance(),
                            "salt balance failed for {} {}".format(v, m))

    def test_reject_never_exceeds_feed(self):
        r = zld.treat(100.0, 10000.0)      # absurdly salty
        self.assertLessEqual(r.reject_l, 100.0)
        self.assertGreaterEqual(r.permeate_l, 0.0)

    def test_non_finite_input_rejected(self):
        for bad in [float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                zld.treat(bad, 100.0)
            with self.assertRaises(ValueError):
                zld.treat(1000.0, bad)

    def test_closed_loop_freshwater_equals_evaporative_loss(self):
        """In a closed loop the basin draw IS what the evaporator destroyed."""
        r = zld.treat(60000.0, 700.0)
        acct = zld.account_for_water(60000.0, r)
        self.assertTrue(acct.check_closes())
        self.assertAlmostEqual(acct.freshwater_intake_l,
                               acct.evaporative_loss_l, places=1)


# ---------------------------------------------------------------------------
# process model
# ---------------------------------------------------------------------------

class TestProcess(unittest.TestCase):

    def setUp(self):
        self.lots = process.reference_lots()

    def test_all_reference_lots_validate(self):
        for lot in self.lots:
            self.assertIsNone(lot.validate(), lot.lot_id)

    def test_going_darker_needs_no_cleaning(self):
        pale = [l for l in self.lots if l.depth_owf < 0.4][0]
        deep = [l for l in self.lots if l.depth_owf > 4.0][0]
        co = process.changeover_burden(pale, deep)
        self.assertEqual(co.cleaning_baths, 0)
        self.assertEqual(co.water_l, 0.0)
        self.assertEqual(co.direction, "LIGHT_TO_DARK")

    def test_going_lighter_costs_cleaning(self):
        pale = [l for l in self.lots if l.depth_owf < 0.4][0]
        deep = [l for l in self.lots if l.depth_owf > 4.0][0]
        co = process.changeover_burden(deep, pale)
        self.assertGreater(co.cleaning_baths, 0)
        self.assertGreater(co.water_l, 0.0)
        self.assertEqual(co.direction, "DARK_TO_LIGHT")
        self.assertTrue(co.drivers, "a burden must explain itself")

    def test_deeper_shades_need_more_salt_and_more_rinsing(self):
        self.assertGreater(process.salt_dose_g_per_l(6.0),
                           process.salt_dose_g_per_l(0.2))
        self.assertGreater(process.washoff_baths(6.0),
                           process.washoff_baths(0.2))

    def test_deeper_shades_tolerate_more_carryover(self):
        self.assertGreater(process.shade_tolerance(6.0),
                           process.shade_tolerance(0.2))

    def test_changeover_burden_is_asymmetric(self):
        """Dark->light and light->dark must not cost the same. If they did,
        sequencing would have nothing to optimise."""
        pale = [l for l in self.lots if l.depth_owf < 0.4][0]
        deep = [l for l in self.lots if l.depth_owf > 4.0][0]
        self.assertNotEqual(process.changeover_burden(deep, pale).water_l,
                            process.changeover_burden(pale, deep).water_l)

    def test_unknown_lot_in_order_raises(self):
        with self.assertRaises(KeyError):
            process.evaluate_sequence(self.lots, ["NOPE"])

    def test_counter_current_cuts_water_but_not_salt(self):
        order = process.arrival_order()
        conv = process.evaluate_sequence(self.lots, order, "CONVENTIONAL")
        cc = process.evaluate_sequence(self.lots, order, "COUNTER_CURRENT")
        self.assertLess(cc["process_water_l"], conv["process_water_l"])
        self.assertAlmostEqual(cc["process_salt_kg"], conv["process_salt_kg"],
                               places=2)

    def test_low_salt_cuts_salt_but_not_water(self):
        order = process.arrival_order()
        conv = process.evaluate_sequence(self.lots, order, "CONVENTIONAL")
        ls = process.evaluate_sequence(self.lots, order, "LOW_SALT")
        self.assertLess(ls["process_salt_kg"], conv["process_salt_kg"])
        self.assertAlmostEqual(ls["process_water_l"], conv["process_water_l"],
                               places=1)

    def test_every_strategy_has_a_cost(self):
        for sid, s in process.strategies().items():
            if sid == "CONVENTIONAL":
                self.assertEqual(s.cost_inr_per_kg_fabric, 0.0)
            else:
                self.assertGreater(s.cost_inr_per_kg_fabric, 0.0,
                                   sid + " must not be a free win")


# ---------------------------------------------------------------------------
# optimiser
# ---------------------------------------------------------------------------

class TestOptimiser(unittest.TestCase):

    def setUp(self):
        self.lots = process.reference_lots()
        self.arrival = process.arrival_order()
        self.result = optimizer.optimise(self.lots, self.arrival)

    def test_search_is_exhaustive_and_says_so(self):
        self.assertEqual(self.result["optimality"], "PROVEN_GLOBAL_OPTIMUM")
        self.assertEqual(self.result["candidates_evaluated"],
                         120 * len(process.strategies()))

    def test_recommendation_is_always_feasible(self):
        rec = next(o for o in self.result["options"]
                   if o["option_id"] == self.result["recommended_option_id"])
        self.assertTrue(rec["feasible"])
        self.assertEqual(rec["violations"], [])
        self.assertEqual(rec["firm_date_breaches"], 0)

    def test_water_minimal_plan_is_refused_for_breaching_a_firm_date(self):
        """The constraint layer must be visible, not merely asserted."""
        opt_c = [o for o in self.result["options"]
                 if o["option_id"] == "OPTION_C"]
        self.assertTrue(opt_c, "the water-minimal extreme should be shown")
        c = opt_c[0]
        self.assertFalse(c["feasible"])
        self.assertGreater(c["firm_date_breaches"], 0)
        self.assertFalse(c["is_recommended"])
        self.assertLess(c["freshwater_intake_l"],
                        self.result["options"][1]["freshwater_intake_l"],
                        "it should genuinely save more, and still be refused")

    def test_optimiser_never_recommends_a_constraint_violation(self):
        """Even with lateness priced at zero, feasibility still binds."""
        r = optimizer.optimise(
            self.lots, self.arrival,
            weights=optimizer.ObjectiveWeights(
                lateness_penalty_inr_per_hour=0.0))
        rec = next(o for o in r["options"]
                   if o["option_id"] == r["recommended_option_id"])
        self.assertEqual(rec["firm_date_breaches"], 0)

    def test_impossible_constraints_yield_no_recommendation(self):
        r = optimizer.optimise(
            self.lots, self.arrival,
            constraints=optimizer.HardConstraints(
                max_total_lateness_h=-1.0))
        self.assertEqual(r["status"], "NO_FEASIBLE_OPTION")
        self.assertNotIn("options", r)

    def test_mismatched_arrival_order_rejected(self):
        r = optimizer.optimise(self.lots, ["L-4412"])
        self.assertEqual(r["status"], "INFEASIBLE_INPUT")

    def test_rationale_explains_itself(self):
        rat = self.result["rationale"]
        for key in ("recommendation", "why", "constraints_satisfied",
                    "uncertainty", "what_would_change_this"):
            self.assertIn(key, rat)
        self.assertTrue(rat["why"])

    def test_novelty_disclaimer_present(self):
        text = self.result["not_claimed"].lower()
        self.assertIn("claimed as our invention", text)
        self.assertIn("established dyehouse practice", text)

    def test_determinism(self):
        a = optimizer.optimise(self.lots, self.arrival)
        b = optimizer.optimise(self.lots, self.arrival)
        for o1, o2 in zip(a["options"], b["options"]):
            self.assertEqual(o1["order"], o2["order"])
            self.assertEqual(o1["strategy_id"], o2["strategy_id"])
            self.assertEqual(o1["cost_inr"], o2["cost_inr"])


# ---------------------------------------------------------------------------
# release gate
# ---------------------------------------------------------------------------

class TestReleaseGate(unittest.TestCase):

    def _run(self, fault=None, depth=6.0):
        return telemetry.simulate_washoff(
            lot_id="T-1",
            scheduled_baths=process.washoff_baths(depth),
            bath_litres=2400.0,
            bath_minutes=22.0,
            depth_owf=depth,
            salt_dose_g_per_l=process.salt_dose_g_per_l(depth),
            fault_mode=fault,
        )

    def test_never_releases_automatically(self):
        for fault in [None] + [f for f in telemetry.FAULT_MODES if f]:
            r = self._run(fault)
            self.assertFalse(r.gate.automatic_release,
                             "automatic release must never be true")

    def test_every_fault_forces_lockout_and_zero_saving(self):
        for fault in [f for f in telemetry.FAULT_MODES if f]:
            r = self._run(fault)
            self.assertEqual(r.gate.state, telemetry.GateState.LOCKED_OUT,
                             fault + " did not lock out")
            self.assertIsNotNone(r.gate.lockout_reason, fault)
            self.assertEqual(r.water_avoidable_l, 0.0, fault)
            self.assertEqual(r.salt_avoidable_kg, 0.0, fault)
            self.assertEqual(r.baths_avoidable, 0, fault)

    def test_clean_deep_shade_reaches_a_releasable_endpoint(self):
        r = self._run(None, depth=6.0)
        self.assertEqual(r.gate.state,
                         telemetry.GateState.AWAITING_HUMAN_RELEASE)
        self.assertTrue(r.gate.checks.all_pass())
        self.assertGreater(r.baths_avoidable, 0)
        self.assertGreater(r.water_avoidable_l, 0.0)

    def test_short_schedule_has_no_slack_and_reports_zero(self):
        r = self._run(None, depth=0.18)
        self.assertEqual(r.baths_avoidable, 0)
        self.assertEqual(r.water_avoidable_l, 0.0)

    def test_avoided_water_is_integrated_from_flow_not_a_constant(self):
        r = self._run(None, depth=6.0)
        skipped = [s for s in r.samples
                   if s.bath_index >= r.scheduled_baths - r.baths_avoidable]
        per_sample_min = r.bath_minutes / 4.0
        expected = sum(s.flow_l_min * per_sample_min for s in skipped)
        self.assertAlmostEqual(r.water_avoidable_l, expected, places=1)

    def test_deterministic_for_a_given_seed(self):
        a = self._run(None)
        b = self._run(None)
        self.assertEqual(a.baths_avoidable, b.baths_avoidable)
        self.assertAlmostEqual(a.water_avoidable_l, b.water_avoidable_l,
                               places=4)

    def test_missing_reading_is_never_treated_as_clean(self):
        r = self._run("sensor_dropout")
        self.assertFalse(r.gate.checks.data_completeness)
        self.assertFalse(r.gate.checks.all_pass())


# ---------------------------------------------------------------------------
# ledger and provenance
# ---------------------------------------------------------------------------

class TestProvenance(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = Path(self.path)
        os.remove(self.path)

    def tearDown(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

    def test_empty_chain_is_intact(self):
        v = provenance.verify_chain(self.db)
        self.assertTrue(v["intact"])
        self.assertEqual(v["records"], 0)

    def test_chain_verifies_after_appends(self):
        for i in range(6):
            provenance.append("ACTION_{}".format(i), "detail {}".format(i),
                              {"i": i}, actor="tester", db_path=self.db)
        v = provenance.verify_chain(self.db)
        self.assertTrue(v["intact"])
        self.assertEqual(v["records"], 6)

    def test_editing_the_detail_breaks_the_chain(self):
        """This test exists because an earlier revision left `detail` out of
        the MAC, so a record's human-readable meaning could be rewritten
        while the chain still verified."""
        for i in range(4):
            provenance.append("A", "original detail {}".format(i), {"i": i},
                              db_path=self.db)
        self.assertTrue(provenance.verify_chain(self.db)["intact"])
        conn = sqlite3.connect(str(self.db))
        try:
            conn.execute("UPDATE decision_ledger SET detail=? WHERE seq=2",
                         ("quietly rewritten",))
            conn.commit()
        finally:
            conn.close()
        v = provenance.verify_chain(self.db)
        self.assertFalse(v["intact"])
        self.assertEqual(v["first_break_at_seq"], 2)

    def test_editing_the_payload_breaks_the_chain(self):
        provenance.append("A", "d", {"water": 100}, db_path=self.db)
        conn = sqlite3.connect(str(self.db))
        try:
            conn.execute("UPDATE decision_ledger SET payload_json=? "
                         "WHERE seq=1", ('{"water": 999}',))
            conn.commit()
        finally:
            conn.close()
        self.assertFalse(provenance.verify_chain(self.db)["intact"])

    def test_deleting_a_record_breaks_the_chain(self):
        for i in range(4):
            provenance.append("A", "d{}".format(i), {"i": i}, db_path=self.db)
        conn = sqlite3.connect(str(self.db))
        try:
            conn.execute("DELETE FROM decision_ledger WHERE seq=2")
            conn.commit()
        finally:
            conn.close()
        self.assertFalse(provenance.verify_chain(self.db)["intact"])

    def test_disclosure_does_not_overclaim(self):
        k = provenance.key_provenance()
        # It must deny distributed consensus rather than imply one.
        blockchain = k["not_a_blockchain"].lower()
        self.assertIn("no distributed consensus", blockchain)
        self.assertIn("no token", blockchain)
        # It must state the authorship limit of a shared-key MAC.
        self.assertIn("asymmetric", k["does_not_prove"].lower())
        # It must describe itself as a MAC over a hash chain, not a signature.
        self.assertIn("hmac", k["mechanism"].lower())
        self.assertNotIn("signature", k["mechanism"].lower())
        # The demonstration key must not be presented as a secret.
        self.assertFalse(k["is_secret"])


# ---------------------------------------------------------------------------
# session, attribution and invariants
# ---------------------------------------------------------------------------

class TestSession(unittest.TestCase):

    def test_nothing_is_credited_before_any_decision(self):
        s = core.Session()
        s.run_optimisation()
        i = s.impact()
        self.assertEqual(i["freshwater_avoided_l"], 0.0)
        self.assertEqual(i["sequencing_water_avoided_l"], 0.0)
        self.assertEqual(i["washoff_water_avoided_l"], 0.0)
        self.assertTrue(i["validation"]["all_pass"])

    def test_rejection_credits_exactly_zero(self):
        s = core.Session()
        s.run_optimisation()
        s.decide_sequence(False, "planner", "buyer escalation")
        i = s.impact()
        self.assertEqual(i["sequencing_water_avoided_l"], 0.0)
        self.assertEqual(i["freshwater_avoided_l"], 0.0)
        self.assertEqual(s.current_order, s.arrival)
        self.assertEqual(s.selected_strategy, process.DEFAULT_STRATEGY)
        self.assertTrue(i["validation"]["all_pass"])

    def test_approval_adopts_both_order_and_strategy(self):
        s = core.Session()
        s.run_optimisation()
        rec = next(o for o in s.optimisation["options"]
                   if o["option_id"] == s.optimisation["recommended_option_id"])
        s.decide_sequence(True, "planner")
        self.assertEqual(s.current_order, rec["order"])
        self.assertEqual(s.selected_strategy, rec["strategy_id"])

    def test_full_golden_path_passes_every_invariant(self):
        s = core.Session()
        s.run_optimisation()
        s.decide_sequence(True, "planner")
        s.run_washoff(None)
        s.release_washoff(True, "qa")
        i = s.impact()
        self.assertTrue(i["validation"]["all_pass"],
                        [c for c in i["validation"]["checks"]
                         if not c["pass"]])
        self.assertGreater(i["freshwater_avoided_l"], 0.0)
        self.assertGreater(i["mee_thermal_avoided_kwh"], 0.0)
        self.assertGreater(i["co2e_avoided_kg"], 0.0)

    def test_invariants_hold_across_every_decision_combination(self):
        for approve in (True, False):
            for fault in [None, "sensor_drift", "thermal_deficit"]:
                for release in (True, False):
                    s = core.Session()
                    s.run_optimisation()
                    s.decide_sequence(approve)
                    s.run_washoff(fault)
                    s.release_washoff(release)
                    i = s.impact()
                    self.assertTrue(
                        i["validation"]["all_pass"],
                        "approve={} fault={} release={} failed {}".format(
                            approve, fault, release,
                            [c["rule"] for c in i["validation"]["checks"]
                             if not c["pass"]]))

    def test_release_is_blocked_under_every_fault(self):
        for fault in [f for f in telemetry.FAULT_MODES if f]:
            s = core.Session()
            s.run_optimisation()
            s.decide_sequence(True)
            s.run_washoff(fault)
            res = s.release_washoff(True)
            self.assertIn("error", res, fault + " was not blocked")
            self.assertEqual(s.impact()["washoff_water_avoided_l"], 0.0)

    def test_approval_blocked_when_recommendation_is_infeasible(self):
        s = core.Session()
        s.run_optimisation()
        # Force the recommendation to look infeasible.
        for o in s.optimisation["options"]:
            if o["option_id"] == "OPTION_B":
                o["feasible"] = False
                o["violations"] = ["forced for the test"]
        res = s.decide_sequence(True)
        self.assertIn("error", res)
        self.assertEqual(s.sequencing_status, "PENDING")

    def test_deciding_before_optimising_is_refused(self):
        s = core.Session()
        self.assertIn("error", s.decide_sequence(True))

    def test_releasing_before_running_washoff_is_refused(self):
        s = core.Session()
        s.run_optimisation()
        self.assertIn("error", s.release_washoff(True))

    def test_unknown_fault_mode_refused(self):
        s = core.Session()
        s.run_optimisation()
        self.assertIn("error", s.run_washoff("not_a_fault"))

    def test_changing_site_invalidates_the_decision(self):
        s = core.Session()
        s.run_optimisation()
        s.decide_sequence(True)
        self.assertEqual(s.sequencing_status, "APPROVED")
        s.set_site("IN-RJ-PALI-03")
        self.assertEqual(s.sequencing_status, "PENDING")
        self.assertIsNone(s.optimisation)
        self.assertEqual(s.selected_strategy, process.DEFAULT_STRATEGY)

    def test_ten_identical_runs_agree_exactly(self):
        sigs = set()
        for _ in range(10):
            s = core.Session()
            s.run_optimisation()
            s.decide_sequence(True)
            s.run_washoff(None)
            s.release_washoff(True)
            i = s.impact()
            sigs.add((
                tuple(s.current_order), s.selected_strategy,
                round(i["freshwater_avoided_l"], 3),
                round(i["salt_avoided_kg"], 3),
                round(i["mee_thermal_avoided_kwh"], 3),
                round(i["co2e_avoided_kg"], 3),
                round(i["cost_avoided_inr"], 2),
            ))
        self.assertEqual(len(sigs), 1, "the golden path is not deterministic")

    def test_export_agrees_with_the_ledger_the_ui_reads(self):
        s = core.Session()
        s.run_optimisation()
        s.decide_sequence(True)
        s.run_washoff(None)
        s.release_washoff(True)
        i = s.impact()
        x = s.export()
        self.assertEqual(x["impact"]["freshwater_avoided_l"],
                         i["freshwater_avoided_l"])
        self.assertEqual(x["impact"]["co2e_avoided_kg"], i["co2e_avoided_kg"])
        self.assertIn("export_sha256", x)
        self.assertTrue(x["ledger_integrity"]["intact"])

    def test_every_site_runs_end_to_end(self):
        for site_id in basin.BASINS:
            s = core.Session(site_id)
            s.run_optimisation()
            if s.optimisation.get("status") != "FEASIBLE":
                continue
            s.decide_sequence(True)
            s.run_washoff(None)
            s.release_washoff(True)
            i = s.impact()
            self.assertTrue(i["validation"]["all_pass"], site_id)


# ---------------------------------------------------------------------------
# basin
# ---------------------------------------------------------------------------

class TestBasin(unittest.TestCase):

    def test_stress_weight_orders_basins_sensibly(self):
        tirupur = basin.get_basin("IN-TN-TIRUPUR-01")
        erode = basin.get_basin("IN-TN-ERODE-02")
        pali = basin.get_basin("IN-RJ-PALI-03")
        self.assertGreater(pali.stress_weight, tirupur.stress_weight)
        self.assertGreater(tirupur.stress_weight, erode.stress_weight)

    def test_stress_equivalence_is_linear_and_zero_safe(self):
        b = basin.get_basin("IN-TN-TIRUPUR-01")
        self.assertEqual(b.stress_equivalent_litres(0.0), 0.0)
        self.assertEqual(b.stress_equivalent_litres(-5.0), 0.0)
        self.assertAlmostEqual(b.stress_equivalent_litres(2000.0),
                               2 * b.stress_equivalent_litres(1000.0), places=1)

    def test_unknown_site_falls_back_to_the_reference_site(self):
        self.assertEqual(basin.get_basin("NOT-A-SITE").site_id,
                         basin.DEFAULT_SITE)

    def test_methodology_disclaims_aware_and_aqueduct(self):
        m = basin.methodology()
        self.assertEqual(m["evidence"], "ASSUMED")
        text = m["what_this_is_not"].lower()
        self.assertIn("aware", text)
        self.assertIn("aqueduct", text)


# ---------------------------------------------------------------------------
# economics
# ---------------------------------------------------------------------------

class TestEconomics(unittest.TestCase):

    GOOD = {
        "lots_per_year": 9000,
        "freshwater_avoided_per_lot_l": 1108,
        "salt_avoided_per_lot_kg": 12.5,
        "freshwater_cost_inr_per_m3": 45,
        "recycled_water_cost_inr_per_m3": 135,
        "steam_cost_inr_per_kwh_th": 2.4,
        "salt_cost_inr_per_kg": 9,
        "implementation_cost_inr": 450000,
        "annual_subscription_inr": 240000,
    }

    def test_refuses_to_invent_missing_inputs(self):
        r = economics.business_case({})
        self.assertEqual(r["status"], "INPUT_REQUIRED")
        self.assertEqual(sorted(r["missing"]),
                         sorted(economics.REQUIRED_INPUTS))

    def test_rejects_negative_and_non_finite_inputs(self):
        bad = dict(self.GOOD)
        bad["lots_per_year"] = -1
        self.assertEqual(economics.business_case(bad)["status"],
                         "INVALID_INPUT")
        bad2 = dict(self.GOOD)
        bad2["steam_cost_inr_per_kwh_th"] = float("inf")
        self.assertEqual(economics.business_case(bad2)["status"],
                         "INVALID_INPUT")

    def test_computes_from_inputs_and_discloses_exclusions(self):
        r = economics.business_case(self.GOOD)
        self.assertEqual(r["status"], "CALCULATED")
        self.assertGreater(r["annual_gross_benefit_inr"], 0)
        self.assertTrue(r["excluded_from_this_calculation"])
        self.assertEqual(len(r["sensitivity"]), 3)

    def test_evaporator_benefit_follows_salt_not_water(self):
        base = economics.business_case(self.GOOD)
        more_water = dict(self.GOOD)
        more_water["freshwater_avoided_per_lot_l"] *= 2
        r1 = economics.business_case(more_water)
        self.assertAlmostEqual(
            r1["annual_quantities"]["evaporator_steam_avoided_kwh_th"],
            base["annual_quantities"]["evaporator_steam_avoided_kwh_th"],
            places=1)
        more_salt = dict(self.GOOD)
        more_salt["salt_avoided_per_lot_kg"] *= 2
        r2 = economics.business_case(more_salt)
        self.assertAlmostEqual(
            r2["annual_quantities"]["evaporator_steam_avoided_kwh_th"],
            base["annual_quantities"]["evaporator_steam_avoided_kwh_th"] * 2,
            delta=1.0)

    def test_cluster_projection_is_labelled_a_projection(self):
        p = economics.cluster_projection()
        self.assertEqual(p["classification"], "PROJECTED")
        self.assertIn("not a result", p["honesty"].lower())

    def test_cluster_projection_handles_zero(self):
        p = economics.cluster_projection(units=0)
        self.assertEqual(p["lots_per_year_total"], 0)
        self.assertEqual(p["co2e_avoided_tonnes_per_year"], 0)


# ---------------------------------------------------------------------------
# scenarios: modes, sensitivity, ablation
# ---------------------------------------------------------------------------

class TestScenarios(unittest.TestCase):

    def test_constraint_modes_change_the_recommended_plan(self):
        """If the optimiser returned the same plan whatever the binding
        constraint, it would be decoration rather than decision support."""
        c = scenarios.compare_modes()
        self.assertGreater(c["distinct_recommended_plans"], 1)

    def test_drought_and_carbon_modes_buy_the_salt_lever(self):
        rows = {r["mode_id"]: r for r in scenarios.compare_modes()["modes"]}
        self.assertIn(rows["DROUGHT"]["recommended_strategy"],
                      {"LOW_SALT", "COMBINED"})
        self.assertIn(rows["CARBON_PRIORITY"]["recommended_strategy"],
                      {"LOW_SALT", "COMBINED"})

    def test_sensitivity_reports_which_coefficients_move_the_decision(self):
        s = scenarios.sensitivity()
        self.assertTrue(s["coefficients"])
        for c in s["coefficients"]:
            self.assertEqual(len(c["variants"]), 2)
            for v in c["variants"]:
                self.assertIn("recommendation_changed", v)
        self.assertIsInstance(s["decision_robust"], bool)

    def test_sensitivity_restores_every_coefficient(self):
        before = {k: f.value for k, f in factors.FACTORS.items()}
        scenarios.sensitivity()
        after = {k: f.value for k, f in factors.FACTORS.items()}
        self.assertEqual(before, after,
                         "the sweep leaked a patched coefficient")

    def test_hard_constraint_layer_binds_in_every_mode(self):
        """The one layer that must always matter. Without it the optimiser
        recommends breaching a firm buyer ship date."""
        for mode_id in scenarios.constraint_modes():
            a = scenarios.ablation(mode_id=mode_id)
            v = {x["variant"]: x for x in a["variants"]}
            self.assertEqual(v["full"]["firm_breaches"], 0, mode_id)
            self.assertGreater(v["no_hard_constraints"]["firm_breaches"], 0,
                               mode_id)

    def test_zld_coupling_binds_once_carbon_is_priced(self):
        """Under normal economics counter-current rinsing is cheapest whether
        or not the optimiser can see the evaporator, so the coupling layer is
        inert. Price carbon and it becomes decisive. The engine reports this
        honestly instead of claiming every layer always earns its place."""
        carbon = scenarios.ablation(mode_id="CARBON_PRIORITY")
        v = {x["variant"]: x for x in carbon["variants"]}
        self.assertLess(v["no_zld_coupling"]["freshwater_avoided_l"],
                        v["full"]["freshwater_avoided_l"])
        self.assertLess(v["no_salt_model"]["freshwater_avoided_l"],
                        v["full"]["freshwater_avoided_l"])
        self.assertIn("Without downstream ZLD coupling",
                      carbon["layers_binding"])

    def test_ablation_reports_inert_layers_rather_than_hiding_them(self):
        a = scenarios.ablation(mode_id="NORMAL")
        self.assertIn("layers_binding", a)
        self.assertIn("layers_inert_in_this_mode", a)
        for v in a["variants"]:
            if v["variant"] != "full":
                self.assertIn("layer_binds_in_this_mode", v)
        # The conclusion must name the mode it was computed under.
        self.assertIn("normal", a["conclusion"].lower())

    def test_every_ablation_variant_explains_what_is_lost(self):
        for v in scenarios.ablation()["variants"]:
            self.assertTrue(v["capability_lost"])


# ---------------------------------------------------------------------------
# traceability
# ---------------------------------------------------------------------------

class TestTrace(unittest.TestCase):

    def test_headline_metrics_are_all_traceable(self):
        for metric in ["freshwater_avoided_l", "mee_thermal_avoided_kwh",
                       "co2e_avoided_kg", "stress_equivalent_avoided_l_eq",
                       "cost_avoided_inr"]:
            t = ledger.trace(metric)
            self.assertNotIn("error", t, metric)
            self.assertTrue(t["formula"], metric)
            self.assertTrue(t["upstream"], metric)
            self.assertTrue(t["evidence"], metric)

    def test_unknown_metric_lists_what_is_available(self):
        t = ledger.trace("nope")
        self.assertIn("error", t)
        self.assertTrue(t["available"])

    def test_traced_coefficients_resolve_in_the_registry(self):
        for metric in ["freshwater_avoided_l", "mee_thermal_avoided_kwh",
                       "co2e_avoided_kg", "cost_avoided_inr"]:
            for c in ledger.trace(metric)["coefficient_detail"]:
                self.assertIn(c["key"], factors.FACTORS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
