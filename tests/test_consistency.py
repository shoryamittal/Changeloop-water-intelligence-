# -*- coding: utf-8 -*-
"""One plan, one set of numbers, on every screen.

Each test here pins a disagreement that once existed between two parts of
the product: the impact ledger reported a larger saving than the decision
workbench for the same plan, the recommendation put the dyehouse's rinse
heating carbon on the evaporator, and the claim register quoted water
prices that contradicted the coefficient registry. A judge who reads two
screens side by side finds these in a minute, so they are tests now.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import economics, factors                         # noqa: E402
from core.session import Session                            # noqa: E402


def _approved_session():
    s = Session()
    s.run_optimisation()
    s.decide_sequence(approve=True, actor="Shift planner", note="test")
    return s


def _options(s):
    return {o["option_id"]: o for o in s.optimisation["options"]}


class LedgerAgreesWithTheWorkbench(unittest.TestCase):

    def test_cost_avoided_is_net_of_the_process_strategy(self):
        """The ledger once left out the counter-current rinse's own running
        cost and reported Rs 8,322 against the workbench's Rs 7,860."""
        s = _approved_session()
        imp = s.impact()
        rec = _options(s)["OPTION_B"]
        self.assertAlmostEqual(imp["cost_avoided_inr"],
                               rec["delta_vs_baseline"]["cost_inr"], places=0)
        self.assertAlmostEqual(imp["achieved_cost_inr"], rec["cost_inr"],
                               places=0)

    def test_unapproved_plan_still_credits_zero_cost(self):
        s = Session()
        s.run_optimisation()
        self.assertEqual(s.impact()["cost_avoided_inr"], 0.0)


class CarbonIsAttributedToWhereItComesFrom(unittest.TestCase):

    def test_split_reconciles_to_the_total(self):
        d = _options(_approved_session())["OPTION_B"]["delta_vs_baseline"]
        parts = d["mee_co2e_kg"] + d["dyehouse_co2e_kg"]
        # the remainder is RO pumping on grid power, which is small
        self.assertLess(parts, d["co2e_kg"] + 0.01)
        self.assertGreater(parts, 0.9 * d["co2e_kg"])

    def test_evaporator_carbon_follows_salt_not_total(self):
        d = _options(_approved_session())["OPTION_B"]["delta_vs_baseline"]
        self.assertAlmostEqual(
            d["mee_co2e_kg"],
            d["mee_thermal_kwh"] * factors.get("boiler_co2e_kg_per_kwh_th"),
            delta=0.5)

    def test_reason_never_puts_rinse_carbon_on_the_evaporator(self):
        s = _approved_session()
        why = " ".join(s.optimisation["rationale"]["why"])
        d = _options(s)["OPTION_B"]["delta_vs_baseline"]
        self.assertNotIn("avoiding {:,.0f} kg CO2e at the boiler"
                         .format(d["co2e_kg"]), why)
        self.assertIn("{:,.0f} kg CO2e. This part follows the salt"
                      .format(d["mee_co2e_kg"]), why)


class CalculatorNetsTheRunningCost(unittest.TestCase):

    BASE = {
        "lots_per_year": 5000, "freshwater_avoided_per_lot_l": 4685.2,
        "salt_avoided_per_lot_kg": 8.64, "freshwater_cost_inr_per_m3": 45,
        "recycled_water_cost_inr_per_m3": 185, "steam_cost_inr_per_kwh_th":
        2.03, "salt_cost_inr_per_kg": 9, "implementation_cost_inr": 0,
        "annual_subscription_inr": 75000,
    }

    def test_process_cost_comes_off_the_net(self):
        a = economics.business_case(dict(self.BASE))
        b = economics.business_case(dict(self.BASE,
                                         process_cost_per_lot_inr=92.4))
        self.assertAlmostEqual(a["annual_net_benefit_inr"]
                               - b["annual_net_benefit_inr"], 5000 * 92.4,
                               places=0)
        self.assertEqual(b["annual_process_cost_inr"], 462000.0)

    def test_fresh_share_is_the_reject_and_is_priced_fresh(self):
        """Freshwater cost was a required input that changed nothing."""
        r = economics.business_case(dict(self.BASE))
        q = r["annual_quantities"]
        self.assertAlmostEqual(q["freshwater_avoided_m3"],
                               q["ro_reject_avoided_m3"], places=1)
        dearer = economics.business_case(
            dict(self.BASE, freshwater_cost_inr_per_m3=90))
        self.assertAlmostEqual(
            dearer["annual_gross_benefit_inr"] - r["annual_gross_benefit_inr"],
            q["freshwater_avoided_m3"] * 45, delta=1.0)

    def test_negative_process_cost_is_refused(self):
        r = economics.business_case(dict(self.BASE,
                                         process_cost_per_lot_inr=-5))
        self.assertEqual(r["status"], "INVALID_INPUT")

    def test_reference_inputs_come_from_the_engine(self):
        s = Session()
        s.run_optimisation()
        ref = economics.reference_inputs(s.optimisation, len(s.lots))
        rec = _options(s)["OPTION_B"]["delta_vs_baseline"]
        self.assertAlmostEqual(ref["salt_avoided_per_lot_kg"],
                               rec["salt_kg"] / len(s.lots), places=2)
        self.assertEqual(ref["recycled_water_cost_inr_per_m3"],
                         factors.get("recycled_water_cost_inr_per_m3"))
        self.assertEqual(ref["annual_subscription_inr"], 75000)
        # every required input is offered, so Calculate works first time
        for k in economics.REQUIRED_INPUTS:
            self.assertIn(k, ref)


class DisplayedPricesStillFlipTheDecision(unittest.TestCase):
    """5.748 was shown as 5.75 and 3.125 as 3.12: both on the side of the
    crossing where the optimiser does NOT change its mind."""

    def test_display_is_rounded_past_the_crossing(self):
        from core import policy
        self.assertEqual(policy._display(5.748, "down"), 5.74)
        self.assertEqual(policy._display(3.125, "up"), 3.13)
        self.assertEqual(policy._display(250.795, "up"), 251)
        for v, d in ((5.748, "down"), (3.1201, "up"), (0.051, "down")):
            shown = policy._display(v, d)
            self.assertTrue(shown <= v if d == "down" else shown >= v)


class ClaimsMatchTheRegistry(unittest.TestCase):

    def test_water_price_claim_matches_registered_coefficients(self):
        from backend.server import claim_register
        text = " ".join(c["claim"] for c in claim_register()["claims"])
        self.assertNotIn("120-150", text)
        lo_hi = "150-220"
        self.assertIn(lo_hi, text)
        self.assertIn("INR %.0f" % factors.get("freshwater_cost_inr_per_m3"),
                      text)


if __name__ == "__main__":
    unittest.main()
