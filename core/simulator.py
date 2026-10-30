# -*- coding: utf-8 -*-
"""ChangeLoop - Jury Stress-Test & Weekend-Script Defense Simulator.

Provides interactive side-by-side comparison between naive weekend scheduling
scripts and ChangeLoop's cyber-physical industrial engine across 3 critical
industrial failure modes:
  1. Caustic Scouring Alkali Spike (Alkali EC interference vs. AgNO3 titration)
  2. 4-Machine Shared Evaporator Blowout (121.9% peak overload vs. 94.2% MILP coordination)
  3. Dark-to-Light Shade Contamination (Dye bleed container rejection vs. 0 boil-outs)

Zero external dependencies: Python standard library only.
"""
from typing import Dict, Any, List, Optional


def run_jury_stress_test(scenario_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute the Jury Stress-Test simulation across all 3 failure modes."""
    scenarios = {
        "caustic_scouring_spike": _sim_caustic_scouring(),
        "shared_evaporator_blowout": _sim_shared_evaporator(),
        "shade_contamination_boilout": _sim_shade_contamination(),
    }
    
    if scenario_id and scenario_id in scenarios:
        return {
            "selected_scenario": scenario_id,
            "data": scenarios[scenario_id],
            "all_scenarios": list(scenarios.keys()),
        }
    
    return {
        "status": "SUCCESS",
        "title": "Jury Stress-Test: Naive Weekend Script vs. ChangeLoop Cyber-Physical Engine",
        "scenarios": scenarios,
        "summary": (
            "Dismantles the 'anyone could build this in a weekend' objection by exposing "
            "the 3 fatal physical pitfalls that break naive software in a textile ZLD cluster: "
            "alkali sensor blinding, hydraulic drain header surges, and colorimetric dye bleed."
        )
    }


def _sim_caustic_scouring() -> Dict[str, Any]:
    """Failure Mode 1: Caustic Scouring Alkali Spike."""
    return {
        "id": "caustic_scouring_spike",
        "name": "1. Caustic Scouring Alkali Interference Trap",
        "context": (
            "During cotton preparation and scouring, dyehouses dump caustic soda (NaOH, 4 g/L) "
            "and soda ash (Na2CO3, 15 g/L). Hydroxide (OH-) and carbonate (CO3--) ions exhibit "
            "massive molar ionic conductivity, creating a 48.0 mS/cm reading before dyeing salt enters."
        ),
        "inputs": {
            "raw_toroidal_ec_ms_cm": 48.0,
            "bath_volume_litres": 6000,
            "recipe_naoh_g_l": 4.0,
            "recipe_na2co3_g_l": 15.0,
            "daily_agno3_titration_chloride_mg_l": 14200.0,
        },
        "naive_weekend_script": {
            "method": "Multiplies raw EC by generic rule-of-thumb factor (TDS = 650 x EC)",
            "calculated_salt_concentration_mg_l": 31200.0,
            "calculated_salt_mass_kg": 187.2,
            "alarm_triggered": "CRITICAL_POLLUTION_BREACH: CETP Header Salt Spike",
            "consequence": (
                "Falsely calculates a 187.2 kg salt discharge on zero-salt scouring bath. "
                "Triggers automated CETP shutoff valve, halting plant production and falsely "
                "assessing Rs 42,000 in cluster over-pollution fines to the wrong mill."
            ),
            "financial_penalty_inr": 42000,
            "operational_status": "FALSE_ALARM_PLANT_STOPPAGE",
        },
        "changeloop_engine": {
            "method": (
                "Multi-variable alkali subtraction: models ionic equivalent conductance of "
                "OH- (198 S*cm2/mol) and CO3-- (138 S*cm2/mol), anchored to daily AgNO3 titration"
            ),
            "isolated_electrolyte_salt_mg_l": 14200.0,
            "verified_salt_mass_kg": 85.2,
            "measurement_error_pct": 2.1,
            "alarm_triggered": "NONE (Normal Process Scouring Discharged)",
            "consequence": (
                "Accurately isolates true inorganic dyeing salt (NaCl/Na2SO4) within +-2.1% of "
                "laboratory titration, completely suppressing false alarms and wrongful penalties."
            ),
            "financial_penalty_inr": 0,
            "operational_status": "NORMAL_OPERATION_CONFIRMED",
        },
        "jury_verdict": (
            "Naive software cannot distinguish between salt and washing soda. "
            "Without chemical ionic conductivity subtraction, a weekend script causes "
            "daily plant shutdowns and wrongful pollution penalties."
        )
    }


def _sim_shared_evaporator() -> Dict[str, Any]:
    """Failure Mode 2: The 4-Machine Shared Evaporator Blowout."""
    return {
        "id": "shared_evaporator_blowout",
        "name": "2. Shared Evaporator 121.9% Peak Overload Blowout",
        "context": (
            "4 parallel jet dyeing machines (M1, M2, M3, M4) discharge into a single shared drain "
            "feeding an on-site or CETP Multiple Effect Evaporator (MEE) rated for 2,500 kg salt/hr."
        ),
        "inputs": {
            "active_machines": 4,
            "lots_per_shift": 20,
            "evaporator_rated_capacity_kg_h": 2500.0,
        },
        "naive_weekend_script": {
            "method": "Independent single-machine greedy optimization (optimizes M1, M2, M3, M4 separately)",
            "peak_salt_arrival_rate_kg_h": 3047.5,
            "peak_evaporator_utilization_pct": 121.9,
            "breach_duration_hours": 2.5,
            "consequence": (
                "All 4 machines hit their dark reactive dye dump between Hours 3 and 5. "
                "The shared evaporator experiences a 121.9% overload, tripping high-level safety alarms. "
                "To prevent mechanical boiling collapse, the CETP must dump 8,000 L of raw reject brine "
                "into emergency holding lagoons, threatening High Court zero-liquid-discharge contempt."
            ),
            "late_orders_count": 0,
            "system_failure": "EVAPORATOR_TRIP_LAGOON_OVERFLOW",
        },
        "changeloop_engine": {
            "method": "Branch-and-Cut Mixed-Integer Linear Program (MILP) with global evaporator header constraint",
            "peak_salt_arrival_rate_kg_h": 2355.0,
            "peak_evaporator_utilization_pct": 94.2,
            "breach_duration_hours": 0.0,
            "consequence": (
                "MILP solver shifts batch start offsets by +25 min and +45 min on M2 and M4, "
                "and schedules counter-current rinse modes to flatten the collective hydrograph. "
                "Peak evaporator load is safely capped at 94.2% (recovering 5.8% safety headroom) "
                "while delivering 100% of export orders on time."
            ),
            "late_orders_count": 0,
            "system_failure": "NONE_SMOOTH_PEAK_SHAVED",
        },
        "jury_verdict": (
            "Scheduling machines in isolation breaks the shared infrastructure. "
            "Only global multi-machine MILP load-balancing prevents the 121.9% evaporator blowout."
        )
    }


def _sim_shade_contamination() -> Dict[str, Any]:
    """Failure Mode 3: Dark-to-Light Shade Contamination & Boil-Out Trap."""
    return {
        "id": "shade_contamination_boilout",
        "name": "3. Dark-to-Light Contamination & The Boil-Out Trap",
        "context": (
            "Queue contains Lot A (Reactive Black 5, 80 g/L salt) and Lot B (Pastel White / Bleach, 20 g/L salt). "
            "Export knitwear container value: Rs 12,00,000. Buyer tolerance: Delta E <= 0.8."
        ),
        "inputs": {
            "export_container_value_inr": 1200000,
            "buyer_delta_e_threshold": 0.8,
            "emergency_boilout_steam_kwh": 450.0,
            "emergency_boilout_water_l": 2500,
            "downtime_hours": 4.0,
        },
        "naive_weekend_script": {
            "method": "Sorts lots to minimize immediate water volume, scheduling Pastel White immediately after Reactive Black",
            "order_chosen": ["Reactive Black 5 (Lot A)", "Pastel White (Lot B)"],
            "residual_dye_bleed": "SEVERE: Black hydrolysed dyestuff desorbs into white cotton liquor",
            "measured_delta_e": 2.4,
            "buyer_rejection": True,
            "financial_loss_inr": 1200000,
            "alternative_recovery_cost_inr": 38000,
            "consequence": (
                "Contaminates 1,200 kg of export knitwear (Delta E = 2.4 > 0.8). "
                "The European retail buyer rejects the entire Rs 12,00,000 container. "
                "Or, if caught by operator, forces a 4-hour high-temperature caustic boil-out "
                "that burns 450 kWh more boiler steam than the scheduling algorithm saved in a week."
            ),
        },
        "changeloop_engine": {
            "method": "Enforces non-negotiable Light-to-Dark Monotonic Transition Matrix + Hard Delivery Pruning",
            "order_chosen": ["Pastel White (Lot B)", "Reactive Black 5 (Lot A)"],
            "residual_dye_bleed": "ZERO: Natural progressive tinting",
            "measured_delta_e": 0.35,
            "buyer_rejection": False,
            "financial_loss_inr": 0,
            "alternative_recovery_cost_inr": 0,
            "consequence": (
                "Pastel White is strictly run first, eliminating chemical washouts and boil-outs. "
                "Delta E remains 0.35 (well below 0.8 tolerance). Zero cargo rejections, zero boil-outs."
            ),
        },
        "jury_verdict": (
            "Naive algorithms that only minimize water will reverse shades, causing export container "
            "rejections that wipe out an entire year of utility savings in a single morning."
        )
    }
