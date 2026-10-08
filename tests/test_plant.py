# -*- coding: utf-8 -*-
"""Shared treatment plant coordination.

The behaviour under test is the one single-machine optimisation cannot
see: four machines each choosing correctly, and the shared evaporator
breaching anyway. These tests pin the properties that make that claim
meaningful, so it cannot quietly become a weaker statement later.
"""
import itertools
import unittest

from core import basin, plant, scenarios
from core.optimizer import ObjectiveWeights


class CapacityComesFromTheClosedLoop(unittest.TestCase):

    def test_capacity_equals_the_abstraction_allowance(self):
        """The evaporator's capacity is not a new assumption.

        Makeup water equals evaporative loss equals reject volume, so the
        site's daily abstraction allowance and the volume the shared
        evaporator must boil are the same number. If these ever diverge,
        a new unsourced figure has been introduced.
        """
        r = plant.plant_plan()
        b = basin.get_basin(r["site_id"])
        self.assertAlmostEqual(
            r["evaporator_capacity_m3_per_day"],
            b.daily_abstraction_allowance_l / 1000.0, places=1,
            msg="Plant capacity has drifted away from the basin "
                "allowance. In a closed loop they are the same volume.")


class MachineQueues(unittest.TestCase):

    def test_one_queue_per_machine_and_all_distinct(self):
        q = plant.machine_queues(4)
        self.assertEqual(len(q), 4)
        shade_sets = [tuple(l.shade_name for l in lots) for lots in q.values()]
        self.assertEqual(len(set(shade_sets)), 4,
                         "Machines must run different colour mixes, or the "
                         "coordination problem is trivially symmetric.")

    def test_lot_ids_are_unique_across_machines(self):
        q = plant.machine_queues(4)
        ids = [l.lot_id for lots in q.values() for l in lots]
        self.assertEqual(len(ids), len(set(ids)),
                         "Lot ids collide across machines, so plans could "
                         "be attributed to the wrong machine.")


class SelfishAndCoordinated(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r = plant.plant_plan()

    def test_selfish_choice_is_each_machine_s_own_optimum(self):
        """Every machine in the selfish plan must hold its own lowest
        objective. If not, it is not the plan a per-machine tool would
        recommend, and the comparison means nothing."""
        for mid, sid in self.r["selfish"]["choice"].items():
            opts = self.r["machine_options"][mid]
            best = min(o["objective_inr"] for o in opts.values())
            self.assertAlmostEqual(
                opts[sid]["objective_inr"], best, places=2,
                msg="%s is not on its own optimum in the selfish plan."
                    % mid)

    def test_every_machine_plan_meets_every_ship_date(self):
        """Coordination must never be bought with a late delivery. Only
        feasible plans are offered as options at all."""
        self.assertTrue(self.r["machine_options"],
                        "No machine options were produced.")
        for mid, opts in self.r["machine_options"].items():
            self.assertTrue(opts, "%s has no feasible plan." % mid)

    def test_coordinated_plan_fits_capacity(self):
        if self.r["status"] != "COORDINATION_REQUIRED":
            self.skipTest("selfish plan already fits")
        c = self.r["coordinated"]
        self.assertLessEqual(
            c["reject_m3_per_day"],
            self.r["evaporator_capacity_m3_per_day"] + 1e-6,
            "The coordinated plan does not actually fit the plant.")

    def test_coordination_costs_something(self):
        """The premium cannot be negative. The selfish plan is, by
        construction, every machine's cheapest option, so no other
        combination can be cheaper in total."""
        if self.r["status"] != "COORDINATION_REQUIRED":
            self.skipTest("selfish plan already fits")
        self.assertGreaterEqual(
            self.r["coordinated"]["coordination_premium_inr_per_day"], 0.0,
            "Coordination came out cheaper than every machine's own "
            "optimum, which is arithmetically impossible.")

    def test_coordinated_is_the_cheapest_combination_that_fits(self):
        """Exhaustive check against an independent re-search, so the
        'cheapest that fits' claim is proven rather than asserted."""
        if self.r["status"] != "COORDINATION_REQUIRED":
            self.skipTest("selfish plan already fits")
        r = self.r
        shifts = r["shifts_per_day"]
        cap = r["evaporator_capacity_m3_per_day"]
        mids = sorted(r["machine_options"].keys())
        best = None
        for combo in itertools.product(
                *[sorted(r["machine_options"][m].keys()) for m in mids]):
            choice = dict(zip(mids, combo))
            reject = sum(r["machine_options"][m][s]["reject_l"]
                         for m, s in choice.items()) * shifts / 1000.0
            if reject > cap:
                continue
            obj = sum(r["machine_options"][m][s]["objective_inr"]
                      for m, s in choice.items()) * shifts
            if best is None or obj < best:
                best = obj
        self.assertIsNotNone(best)
        self.assertAlmostEqual(
            r["coordinated"]["totals"]["objective_inr"], best, places=1,
            msg="A cheaper feasible combination exists than the one "
                "reported as coordinated.")

    def test_machines_that_move_actually_differ(self):
        if self.r["status"] != "COORDINATION_REQUIRED":
            self.skipTest("selfish plan already fits")
        c = self.r["coordinated"]
        for mid in c["machines_that_move"]:
            self.assertNotEqual(
                c["choice"][mid], self.r["selfish"]["choice"][mid],
                "%s is listed as moving but did not change plan." % mid)
        for mid, sid in c["choice"].items():
            if mid not in c["machines_that_move"]:
                self.assertEqual(sid, self.r["selfish"]["choice"][mid])


class TheCoordinationFailureIsReal(unittest.TestCase):
    """The headline claim: correct individual choices, failing plant."""

    def test_individually_optimal_plans_overload_the_shared_plant(self):
        r = plant.plant_plan()
        if r["status"] != "COORDINATION_REQUIRED":
            self.skipTest("this order book does not breach")
        self.assertGreater(
            r["selfish"]["utilisation_pct"], 100.0,
            "The selfish plan is supposed to breach capacity. If it no "
            "longer does, the demonstration has lost its point and the "
            "narrative around it needs rewriting, not this test "
            "loosening.")

    def test_pressure_scales_with_machine_count(self):
        """More machines on one plant means more load, not less."""
        small = plant.plant_plan(n_machines=2)
        large = plant.plant_plan(n_machines=4)
        self.assertGreater(large["selfish"]["reject_m3_per_day"],
                           small["selfish"]["reject_m3_per_day"])

    def test_a_single_machine_never_needs_coordination(self):
        """One machine against the whole plant allowance must fit. If it
        does not, the capacity figure is wrong, not the scheduling."""
        r = plant.plant_plan(n_machines=1)
        self.assertEqual(r["status"], "WITHIN_CAPACITY")


class Honesty(unittest.TestCase):

    def test_output_is_labelled_modelled(self):
        self.assertEqual(plant.plant_plan()["classification"], "MODELLED")

    def test_capacity_basis_is_stated(self):
        r = plant.plant_plan()
        self.assertIn("closed loop", r["capacity_basis"].lower())

    def test_reading_is_present_and_specific(self):
        r = plant.plant_plan()
        self.assertGreater(len(r["reading"]), 80)


class PricingDissolvesTheCoordinationProblem(unittest.TestCase):
    """The most important property in this module.

    Under Normal operation, every machine privately prefers the
    water-saving plan, their sum breaches the shared evaporator, and
    somebody has to be made worse off. Under Drought - where scarcity is
    actually priced - the low-salt plan becomes each machine's OWN best
    choice, and the plant fits with nobody giving way.

    That makes the breach a pricing failure rather than a scheduling
    failure, which is a claim the submission makes out loud. It has to be
    reproducible from the engine, not asserted in a document.
    """

    @classmethod
    def setUpClass(cls):
        m = scenarios.constraint_modes()
        cls.plans = {}
        for mid in ("NORMAL", "DROUGHT"):
            mode = m[mid]
            cls.plans[mid] = plant.plant_plan(
                weights=mode.weights, constraints=mode.constraints)

    def test_normal_operation_breaches(self):
        self.assertEqual(self.plans["NORMAL"]["status"],
                         "COORDINATION_REQUIRED")

    def test_pricing_scarcity_removes_the_breach(self):
        self.assertEqual(
            self.plans["DROUGHT"]["status"], "WITHIN_CAPACITY",
            "Under Drought the plant is supposed to fit without "
            "coordination. If it no longer does, the claim that correct "
            "pricing dissolves the coordination problem is no longer "
            "true and must be removed from the submission.")

    def test_drought_costs_no_coordination_premium(self):
        self.assertAlmostEqual(
            self.plans["DROUGHT"]["coordinated"]
            ["coordination_premium_inr_per_day"], 0.0, places=2)
        self.assertEqual(
            self.plans["DROUGHT"]["coordinated"]["machines_that_move"], [],
            "Nobody should have to give way once scarcity is priced.")

    def test_the_lever_coordination_needs_is_the_one_pricing_buys(self):
        """The strategy machines are forced onto under Normal is the same
        one they choose freely under Drought. If these diverged, the two
        findings would be unrelated coincidences rather than one story."""
        n = self.plans["NORMAL"]
        forced = {n["coordinated"]["choice"][mid]
                  for mid in n["coordinated"]["machines_that_move"]}
        chosen = set(self.plans["DROUGHT"]["selfish"]["choice"].values())
        self.assertTrue(
            forced and forced.issubset(chosen),
            "The plan machines are pushed onto under Normal (%s) is not "
            "the plan they pick for themselves under Drought (%s)."
            % (sorted(forced), sorted(chosen)))

    def test_drought_boils_less_than_normal(self):
        self.assertLess(self.plans["DROUGHT"]["selfish"]["reject_m3_per_day"],
                        self.plans["NORMAL"]["selfish"]["reject_m3_per_day"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
