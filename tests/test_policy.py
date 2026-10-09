# -*- coding: utf-8 -*-
"""Switching prices: what would make the right plan the profitable plan.

These tests guard claims the submission makes out loud - a carbon price,
a dye premium, a water tariff. A number in a concept note that the engine
has stopped producing is worse than no number, so each one is pinned to
the mechanism that produces it rather than to its current value alone.
"""
import unittest

from core import factors, policy
from core.optimizer import ObjectiveWeights, HardConstraints


class TheSearchFindsARealCrossing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r = policy.policy_levers()
        cls.by_key = {l["coefficient"]: l for l in cls.r["levers"]}

    def test_every_lever_resolves(self):
        for l in self.r["levers"]:
            self.assertIn(l["status"],
                          ("FOUND", "NOT_FOUND", "ALREADY_CHOSEN"))

    def test_today_does_not_buy_the_salt_lever(self):
        """The premise of this whole module. If the optimiser starts
        recommending a low-salt plan at today's prices, there is no
        switching price to find and the submission's framing is wrong."""
        for l in self.r["levers"]:
            self.assertEqual(
                l["strategy_now"], "COUNTER_CURRENT",
                "At today's prices the recommendation is no longer the "
                "counter-current plan. The 6%-versus-47% framing that "
                "this module exists to quantify needs rechecking.")

    def test_each_crossing_lands_on_a_salt_reducing_plan(self):
        for key, l in self.by_key.items():
            if l["status"] != "FOUND":
                continue
            self.assertIn(
                l["strategy_after"], policy.SALT_LEVER_STRATEGIES,
                "%s crossed to %s, which does not reduce salt."
                % (key, l["strategy_after"]))

    def test_the_crossing_is_the_boundary_not_just_a_point_past_it(self):
        """Just below the reported price the salt lever must NOT be
        chosen, and at it, it must be. Otherwise the figure is somewhere
        inside the region rather than its edge, and quoting it as 'the
        price needed' overstates how much is required."""
        for key, l in self.by_key.items():
            if l["status"] != "FOUND":
                continue
            x = l["switching_value"]
            eps = max(abs(x) * 0.02, 1e-6)
            below = x - eps if l["direction"] == "up" else x + eps
            with factors.REGISTRY_LOCK:
                with policy._patched(key, below):
                    rec_below = policy._recommended_strategy(
                        "IN-TN-TIRUPUR-01", ObjectiveWeights(),
                        HardConstraints(),
                        *_lots())
                with policy._patched(key, x):
                    rec_at = policy._recommended_strategy(
                        "IN-TN-TIRUPUR-01", ObjectiveWeights(),
                        HardConstraints(),
                        *_lots())
            self.assertFalse(
                policy._buys_the_salt_lever(rec_below),
                "%s: 2%% short of the reported price the salt lever is "
                "already chosen, so the real crossing is lower." % key)
            self.assertTrue(
                policy._buys_the_salt_lever(rec_at),
                "%s: at the reported price the salt lever is still not "
                "chosen." % key)

    def test_a_patched_coefficient_is_always_restored(self):
        """A sweep that leaked would corrupt every later request on the
        running server. This is the failure mode that already happened
        once in this project, under concurrency."""
        before = {k: factors.get(k) for k in policy.LEVERS}
        policy.policy_levers()
        for k, v in before.items():
            self.assertAlmostEqual(factors.get(k), v, places=9)

    def test_directions_are_the_ones_that_help(self):
        """Raising a cost of harm, or lowering the cost of the fix. A
        lever pointing the other way would be arithmetic, not policy."""
        for key, l in self.by_key.items():
            if l["status"] != "FOUND":
                continue
            if l["direction"] == "up":
                self.assertGreater(l["switching_value"], l["current_value"])
            else:
                self.assertLess(l["switching_value"], l["current_value"])


class TheCacheIsSafe(unittest.TestCase):
    """The sweep is cached because it is slow. A cache that served a
    stale answer after a coefficient moved would be worse than the wait,
    so the key has to notice."""

    def test_repeated_calls_agree(self):
        a = policy.policy_levers()
        b = policy.policy_levers()
        self.assertEqual(a["implied_carbon_price"]["inr_per_tonne_co2e"],
                         b["implied_carbon_price"]["inr_per_tonne_co2e"])

    def test_a_changed_coefficient_invalidates_it(self):
        before = policy.policy_levers()
        base = before["implied_carbon_price"]["inr_per_tonne_co2e"]
        with factors.REGISTRY_LOCK:
            with policy._patched("boiler_co2e_kg_per_kwh_th",
                                 factors.get("boiler_co2e_kg_per_kwh_th") * 2):
                during = policy.policy_levers()
        self.assertNotAlmostEqual(
            during["implied_carbon_price"]["inr_per_tonne_co2e"], base,
            places=0,
            msg="Doubling the boiler emission factor did not change the "
                "implied carbon price, so the cache returned a stale "
                "answer.")
        after = policy.policy_levers()
        self.assertAlmostEqual(
            after["implied_carbon_price"]["inr_per_tonne_co2e"], base,
            places=0)


class TheCarbonPrice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.steam = policy.switching_point("steam_cost_inr_per_kwh_th")
        cls.c = policy.implied_carbon_price(cls.steam)

    def test_the_arithmetic_is_exactly_what_it_says(self):
        delta = self.steam["absolute_change"]
        e = factors.get("boiler_co2e_kg_per_kwh_th")
        self.assertAlmostEqual(self.c["inr_per_tonne_co2e"],
                               round(delta / e * 1000.0, 0), places=0)

    def test_it_uses_the_boiler_factor_not_the_grid_one(self):
        """Steam comes from a boiler. Using the grid factor would be a
        quiet 56% error in a headline policy number."""
        self.assertAlmostEqual(self.c["boiler_co2e_kg_per_kwh_th"],
                               factors.get("boiler_co2e_kg_per_kwh_th"),
                               places=6)
        self.assertNotAlmostEqual(self.c["boiler_co2e_kg_per_kwh_th"],
                                  factors.get("grid_co2e_kg_per_kwh_e"),
                                  places=3)

    def test_the_price_is_in_a_sane_range(self):
        """Wide bounds on purpose. This guards against a sign flip or a
        unit slip turning the headline into nonsense, not against the
        number moving with the model."""
        p = self.c["inr_per_tonne_co2e"]
        self.assertGreater(p, 100.0)
        self.assertLess(p, 100000.0)

    def test_the_benchmark_carries_its_date_and_source(self):
        b = self.c["benchmark"]
        self.assertTrue(b["benchmark_as_of"])
        self.assertIn("2026", b["benchmark_as_of"])
        self.assertGreater(len(b["benchmark_source"]), 40)

    def test_the_benchmark_is_not_a_model_coefficient(self):
        """It is a comparison, not an input. If it ever enters the
        registry it would start driving results while looking like
        context."""
        self.assertNotIn("eu_ets", " ".join(factors.FACTORS.keys()).lower())
        self.assertNotIn("carbon_price",
                         " ".join(factors.FACTORS.keys()).lower())


class Honesty(unittest.TestCase):

    def test_output_is_derived_not_measured(self):
        r = policy.policy_levers()
        self.assertEqual(r["classification"], "DERIVED")
        self.assertEqual(r["implied_carbon_price"]["status"], "DERIVED")

    def test_the_pass_through_assumption_is_stated(self):
        c = policy.implied_carbon_price(
            policy.switching_point("steam_cost_inr_per_kwh_th"))
        self.assertIn("steam price", c["what_it_assumes"])
        self.assertIn("higher", c["what_it_assumes"])

    def test_it_does_not_present_itself_as_a_proposal(self):
        c = policy.implied_carbon_price(
            policy.switching_point("steam_cost_inr_per_kwh_th"))
        self.assertIn("not a claim about what a carbon price should be",
                      c["what_it_is_not"])

    def test_method_names_scan_and_bisection(self):
        l = policy.switching_point("steam_cost_inr_per_kwh_th")
        self.assertIn("scan", l["method"].lower())
        self.assertIn("bisect", l["method"].lower())


def _lots():
    from core.process import reference_lots, arrival_order
    return reference_lots(), arrival_order()


if __name__ == "__main__":
    unittest.main(verbosity=2)
