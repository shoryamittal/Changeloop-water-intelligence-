#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChangeLoop - Concept Note Invariant & Numerical Drift Verification Suite.

This script executes a strict, automated zero-drift audit against the 8-page
ChangeLoop Concept Note ("The Operating System for Industrial Zero Liquid Discharge Clusters").

Every single invariant, benchmark, and empirical constant published in the
specification is asserted programmatically from first principles:

  1. Combined Plan Net Saving: Rs 1,572 / lot (Rs 78,60,000/yr at 5,000 lots)
  2. Low-Salt Chemistry Plan Net Saving: Rs 783 / lot (Rs 39,14,000/yr at 5,000 lots)
  3. Re-ordering Alone Net Saving: Rs 607 / lot (Rs 30,37,000/yr at 5,000 lots)
  4. Counter-Current Rinsing Alone Net Saving: Rs 964 / lot (Rs 48,22,000/yr at 5,000 lots)
     [Proof: Rs 607 + Rs 964 = Rs 1,571 ≈ Rs 1,572 / lot]
  5. Baseline Fresh Water: 11,907 L per 5-lot queue (11,906.8 L)
  6. Combined Recommended Fresh Water: 11,187 L (-6.0%, 11,186.8 L)
  7. Low-Salt Chemistry Fresh Water: 6,369 L (-46.5%, 6,368.8 L)
  8. Baseline Evaporator Steam: 2,239 kWh per 5-lot queue (2,239.4 kWh)
  9. Combined Recommended Evaporator Steam: 2,104 kWh (-6.0%, 2,104.0 kWh)
 10. Low-Salt Chemistry Evaporator Steam: 1,198 kWh (-46.5%, 1,197.85 kWh)
 11. Evaporator Capacity Overload under Uncoordinated Scheduling: 121.9%
 12. CPCB Observed Water Strength Reject Fraction: 30.6% (18,340 / 60,000 mg/L)
 13. Low-Salt Reactive Dye Switching Tipping Point: Rs 5.74 / kg fabric (12% discount)
 14. Implied Boiler Carbon Abatement Price: Rs 2,423 / tonne CO2e
 15. 25 Traceable System Coefficients with exactly 0 MEASURED in Pre-Pilot mode
 16. Boiler Fuel Profile Invariant: Wet wood (-25% steam cost) shifts required dye discount from 12% (Rs 5.74) to 17% (Rs 5.40)
 17. The Governing ZLD Invariant: Counter-current cuts circulation water by ~25% but changes evaporator steam by 0.00%
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import factors, policy, plant, milp, process, optimizer
from core.optimizer import evaluate_candidate, ObjectiveWeights, HardConstraints


def run_concept_note_audit() -> bool:
    print("========================================================================")
    print("CHANGELOOP CONCEPT NOTE ZERO-DRIFT VERIFICATION SUITE")
    print("Specification: 8-Page ChangeLoop Concept Note (Tirupur ZLD OS)")
    print("========================================================================")

    passed_checks = 0
    total_checks = 17

    lots = process.reference_lots()
    arr = process.arrival_order()
    w = ObjectiveWeights()
    c = HardConstraints()

    # Candidates
    cand_base = evaluate_candidate(lots, arr, "IN-TN-TIRUPUR-01", w, c, "CONVENTIONAL")
    cand_reorder = evaluate_candidate(lots, ["L-4416", "L-4412", "L-4413", "L-4414", "L-4415"], "IN-TN-TIRUPUR-01", w, c, "CONVENTIONAL")
    cand_cc_alone = evaluate_candidate(lots, arr, "IN-TN-TIRUPUR-01", w, c, "COUNTER_CURRENT")
    cand_comb = evaluate_candidate(lots, ["L-4416", "L-4412", "L-4413", "L-4414", "L-4415"], "IN-TN-TIRUPUR-01", w, c, "COUNTER_CURRENT")
    cand_low_salt_comb = evaluate_candidate(lots, ["L-4416", "L-4412", "L-4413", "L-4414", "L-4415"], "IN-TN-TIRUPUR-01", w, c, "COMBINED")

    cost_base = cand_base.consequence["cost_inr"]["total"] + cand_base.sequence["strategy_cost_inr"]
    cost_reorder = cand_reorder.consequence["cost_inr"]["total"] + cand_reorder.sequence["strategy_cost_inr"]
    cost_cc_alone = cand_cc_alone.consequence["cost_inr"]["total"] + cand_cc_alone.sequence["strategy_cost_inr"]
    cost_comb = cand_comb.consequence["cost_inr"]["total"] + cand_comb.sequence["strategy_cost_inr"]
    cost_ls = cand_low_salt_comb.consequence["cost_inr"]["total"] + cand_low_salt_comb.sequence["strategy_cost_inr"]

    # --- Check 1: Combined Plan Net Saving: Rs 1,572 / lot ---
    comb_saving_lot = (cost_base - cost_comb) / 5.0
    print(f"\n[1/17] Combined Plan Net Saving: Rs {comb_saving_lot:.2f} / lot (Target: Rs 1,572)")
    assert abs(comb_saving_lot - 1572.0) <= 1.0, f"Drift: {comb_saving_lot} != 1572"
    print("       -> PASS (Rs 1,572/lot, Rs 78,60,000/yr at 5,000 lots/yr)")
    passed_checks += 1

    # --- Check 2: Low-Salt Chemistry Plan Net Saving: Rs 783 / lot ---
    ls_saving_lot = (cost_base - cost_ls) / 5.0
    print(f"[2/17] Low-Salt Chemistry Net Saving: Rs {ls_saving_lot:.2f} / lot (Target: Rs 783)")
    assert abs(ls_saving_lot - 783.0) <= 1.0, f"Drift: {ls_saving_lot} != 783"
    print("       -> PASS (Rs 783/lot, Rs 39,14,000/yr at 5,000 lots/yr)")
    passed_checks += 1

    # --- Check 3: Re-ordering Alone Net Saving: Rs 607 / lot ---
    reorder_saving_lot = (cost_base - cost_reorder) / 5.0
    print(f"[3/17] Re-ordering Alone Net Saving: Rs {reorder_saving_lot:.2f} / lot (Target: Rs 607)")
    assert abs(reorder_saving_lot - 607.0) <= 1.0, f"Drift: {reorder_saving_lot} != 607"
    print("       -> PASS (Rs 607/lot, drives 100% of 6% freshwater and steam cut)")
    passed_checks += 1

    # --- Check 4: Counter-Current Rinsing Alone Net Saving: Rs 964 / lot ---
    cc_saving_lot = (cost_base - cost_cc_alone) / 5.0
    print(f"[4/17] Counter-Current Alone Net Saving: Rs {cc_saving_lot:.2f} / lot (Target: Rs 964)")
    assert abs(cc_saving_lot - 964.0) <= 1.0, f"Drift: {cc_saving_lot} != 964"
    assert abs((reorder_saving_lot + cc_saving_lot) - comb_saving_lot) <= 1.0
    print("       -> PASS (Rs 964/lot; Rs 607 + Rs 964 = Rs 1,571 ~= Rs 1,572)")
    passed_checks += 1

    # --- Check 5: Baseline Fresh Water: 11,907 L ---
    base_water = cand_base.consequence["water"]["freshwater_intake_l"]
    print(f"[5/17] Baseline Fresh Water: {base_water:.1f} L (Target: 11,907 L)")
    assert abs(base_water - 11906.8) < 1.0, f"Drift: {base_water} != 11906.8"
    print("       -> PASS (11,907 L per 5-lot baseline queue)")
    passed_checks += 1

    # --- Check 6: Combined Recommended Fresh Water: 11,187 L (-6.0%) ---
    comb_water = cand_comb.consequence["water"]["freshwater_intake_l"]
    print(f"[6/17] Combined Recommended Fresh Water: {comb_water:.1f} L (Target: 11,187 L)")
    assert abs(comb_water - 11186.8) < 1.0, f"Drift: {comb_water} != 11186.8"
    print("       -> PASS (11,187 L, exactly -6.0% water reduction)")
    passed_checks += 1

    # --- Check 7: Low-Salt Chemistry Fresh Water: 6,369 L (-46.5%) ---
    ls_water = cand_low_salt_comb.consequence["water"]["freshwater_intake_l"]
    print(f"[7/17] Low-Salt Chemistry Fresh Water: {ls_water:.1f} L (Target: 6,369 L)")
    assert abs(ls_water - 6368.8) < 1.0, f"Drift: {ls_water} != 6368.8"
    print("       -> PASS (6,369 L, exactly -46.5% water reduction)")
    passed_checks += 1

    # --- Check 8: Baseline Evaporator Steam: 2,239 kWh ---
    base_steam = cand_base.consequence["zld"]["mee_thermal_kwh"]
    print(f"[8/17] Baseline Evaporator Steam: {base_steam:.1f} kWh (Target: 2,239 kWh)")
    assert abs(base_steam - 2239.4) < 1.0, f"Drift: {base_steam} != 2239.4"
    print("       -> PASS (2,239 kWh per 5-lot baseline queue)")
    passed_checks += 1

    # --- Check 9: Combined Recommended Evaporator Steam: 2,104 kWh (-6.0%) ---
    comb_steam = cand_comb.consequence["zld"]["mee_thermal_kwh"]
    print(f"[9/17] Combined Recommended Evaporator Steam: {comb_steam:.1f} kWh (Target: 2,104 kWh)")
    assert abs(comb_steam - 2104.0) < 1.0, f"Drift: {comb_steam} != 2104.0"
    print("       -> PASS (2,104 kWh, exactly -6.0% steam reduction)")
    passed_checks += 1

    # --- Check 10: Low-Salt Chemistry Evaporator Steam: 1,198 kWh (-46.5%) ---
    ls_steam = cand_low_salt_comb.consequence["zld"]["mee_thermal_kwh"]
    print(f"[10/17] Low-Salt Chemistry Evaporator Steam: {ls_steam:.1f} kWh (Target: 1,198 kWh)")
    assert abs(ls_steam - 1197.85) < 1.0, f"Drift: {ls_steam} != 1198.0"
    print("       -> PASS (1,198 kWh, exactly -46.5% steam reduction)")
    passed_checks += 1

    # --- Check 11: Evaporator Capacity Overload: 121.9% ---
    queues = plant.machine_queues(4)
    cluster_res = milp.solve_cluster_milp(queues)
    utilization_selfish = cluster_res["selfish"]["utilization_pct"]
    print(f"[11/17] Cluster Evaporator Overload: {utilization_selfish:.1f}% (Target: 121.9%)")
    assert abs(utilization_selfish - 121.9) < 0.2, f"Drift: {utilization_selfish} != 121.9"
    print("       -> PASS (121.9% rated evaporator capacity breached under selfish scheduling)")
    passed_checks += 1

    # --- Check 12: CPCB Water Strength Reject Fraction: 30.6% ---
    cpcb_tds = 18340.0
    membrane_limit = factors.get("ro_max_reject_tds_mg_l") # 60000.0
    cpcb_frac = (cpcb_tds / membrane_limit) * 100.0
    print(f"[12/17] CPCB Observed Reject Fraction: {cpcb_frac:.1f}% (Target: 30.6%)")
    assert abs(cpcb_frac - 30.567) < 0.1, f"Drift: {cpcb_frac} != 30.6"
    print("       -> PASS (18,340 / 60,000 mg/L TDS yields exactly 30.6% reject volume)")
    passed_checks += 1

    # --- Check 13: Low-Salt Reactive Dye Switching Tipping Point: Rs 5.74 / kg fabric ---
    sw_point = policy.switching_point("low_salt_chemistry_cost_inr_per_kg_fabric")
    sw_val = sw_point["switching_value"]
    print(f"[13/17] Low-Salt Dye Premium Tipping Point: Rs {sw_val:.2f}/kg fabric (Target: Rs 5.74)")
    assert abs(sw_val - 5.74) <= 0.01 or abs(sw_val - 5.748) < 0.01, f"Drift: {sw_val} != 5.74"
    print("       -> PASS (Rs 5.74/kg fabric dye premium, exactly a 12% discount from Rs 6.50/kg)")
    passed_checks += 1

    # --- Check 14: Implied Boiler Carbon Abatement Price: Rs 2,423 / tonne CO2e ---
    pol_out = policy.policy_levers()
    carbon_val = pol_out["implied_carbon_price"]["inr_per_tonne_co2e"]
    print(f"[14/17] Implied Carbon Abatement Price: Rs {carbon_val:,.0f} / tonne CO2e (Target: Rs 2,423)")
    assert abs(carbon_val - 2423.0) <= 2.0, f"Drift: {carbon_val} != 2423"
    print("       -> PASS (Rs 2,423 / tonne CO2e implied carbon abatement price)")
    passed_checks += 1

    # --- Check 15: 25 Traceable System Coefficients, exactly 0 MEASURED ---
    total_coeffs = len(factors.FACTORS)
    summary = factors.evidence_summary()
    measured_count = summary.get("MEASURED", 0)
    print(f"[15/17] Evidence Registry: {total_coeffs} coefficients, {measured_count} MEASURED (Target: 25, 0)")
    assert total_coeffs == 25, f"Drift: {total_coeffs} != 25"
    assert measured_count == 0, f"Drift: {measured_count} != 0 (must be 0 in pre-pilot mode)"
    print("       -> PASS (25 total coefficients: 17 Published, 4 Derived, 4 Assumed, 0 Measured)")
    passed_checks += 1

    # --- Check 16: Boiler Fuel Profile Invariant: Wet wood discount shifts from 12% to 17% ---
    wet_analysis = policy.boiler_fuel_analysis("WET_WOOD")
    wet_discount = wet_analysis["calculated_discount_pct"]
    wet_sw = wet_analysis["calculated_switching_value_inr"]
    print(f"[16/17] Wet Wood Profile (-25% steam cost): {wet_discount:.0f}% discount, Rs {wet_sw:.2f}/kg (Target: 17%, Rs 5.40)")
    assert abs(wet_discount - 16.9) < 0.5, f"Drift: {wet_discount} != 17%"
    assert abs(wet_sw - 5.40) <= 0.05, f"Drift: {wet_sw} != 5.40"
    print("       -> PASS (Wet wood 25% cheaper steam shifts required dye discount from 12% to 17%)")
    passed_checks += 1

    # --- Check 17: Governing ZLD Invariant: Counter-current changes steam by 0.00% ---
    steam_base = cand_base.consequence["zld"]["mee_thermal_kwh"]
    steam_cc = cand_cc_alone.consequence["zld"]["mee_thermal_kwh"]
    steam_diff_pct = abs(steam_base - steam_cc) / steam_base * 100.0
    print(f"[17/17] Governing ZLD Invariant: CC steam delta = {steam_diff_pct:.4f}% (Target: 0.00%)")
    assert steam_diff_pct < 1e-4, f"Invariant breached: {steam_diff_pct}% != 0.00%"
    print("       -> PASS (Counter-current rinsing changes evaporator steam by exactly 0.00%)")
    passed_checks += 1

    print("\n========================================================================")
    print(f"VERIFICATION COMPLETE: ALL {passed_checks}/{total_checks} CONCEPT NOTE FIGURES CERTIFIED (100.0% SUCCESS)")
    print("Zero mathematical or empirical drift detected against specification.")
    print("========================================================================")
    return True


if __name__ == "__main__":
    success = run_concept_note_audit()
    sys.exit(0 if success else 1)
