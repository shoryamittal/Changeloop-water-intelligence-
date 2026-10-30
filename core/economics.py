"""ChangeLoop - Site Business Case.

Two separate calculations, deliberately not merged:

  1. CUSTOMER BUSINESS CASE  what the dyeing unit saves and what ChangeLoop
                             costs it. Driven entirely by site inputs. If an
                             input is missing the function REFUSES rather
                             than substituting an invented default.

  2. CLUSTER PROJECTION      what the same intervention looks like across a
                             cluster, clearly labelled a projection from one
                             modelled unit and never as evidence.

Why the refusal matters
-----------------------
A business case built on numbers the vendor chose is worthless. The only
figures that belong in an ROI are the site's own tariffs and volumes, so the
default state of this screen is "tell me your numbers", not a pre-filled
success story.
"""
from typing import Dict, Any, List
import math

from . import factors


REQUIRED_INPUTS = [
    "lots_per_year",
    "freshwater_avoided_per_lot_l",
    "salt_avoided_per_lot_kg",
    "freshwater_cost_inr_per_m3",
    "recycled_water_cost_inr_per_m3",
    "steam_cost_inr_per_kwh_th",
    "salt_cost_inr_per_kg",
    "implementation_cost_inr",
    "annual_subscription_inr",
]

INPUT_HELP = {
    "lots_per_year": "Dye lots run per year on the machines in scope.",
    "freshwater_avoided_per_lot_l": "Process water avoided per lot: rinse and "
                                    "cleaning water no longer drawn. In a "
                                    "closed loop it displaces recycled "
                                    "water, so it is priced at that rate. "
                                    "From the ChangeLoop ledger for your own "
                                    "order book, or from a pilot.",
    "salt_avoided_per_lot_kg": "Electrolyte and cleaning chemical avoided per "
                               "lot. This is what drives the evaporator "
                               "saving.",
    "freshwater_cost_inr_per_m3": "Your delivered cost of borewell or "
                                  "municipal water.",
    "recycled_water_cost_inr_per_m3": "Your CETP or in-house ZLD charge for "
                                      "treated water returned to process.",
    "steam_cost_inr_per_kwh_th": "Your boiler steam cost. Derive it from fuel "
                                 "price and boiler efficiency.",
    "salt_cost_inr_per_kg": "Delivered price of Glauber or common salt.",
    "implementation_cost_inr": "One-off integration with your planning system "
                               "and effluent meters, plus training.",
    "annual_subscription_inr": "Annual ChangeLoop licence for the machines in "
                               "scope.",
}

# Optional, because a plan that only re-orders lots has no running cost.
# A plan that also changes the process does: counter-current rinsing costs
# pumping and tank turnover, low-salt dye costs a premium. Leaving it out
# overstates the saving, which is the one error this calculator must not
# make.
OPTIONAL_INPUTS = {
    "process_cost_per_lot_inr": "Running cost per lot of the process change "
                                "the plan adopts. Zero if it only re-orders "
                                "lots.",
}


def reference_inputs(optimisation: Dict[str, Any],
                     lot_count: int) -> Dict[str, Any]:
    """Per-lot figures from the engine's own recommended plan.

    Offered as a worked example the user overwrites, never as a result:
    the calculator still computes only from whatever is submitted.
    """
    out: Dict[str, Any] = {
        "lots_per_year": 5000,
        "freshwater_cost_inr_per_m3": factors.get("freshwater_cost_inr_per_m3"),
        "recycled_water_cost_inr_per_m3": factors.get(
            "recycled_water_cost_inr_per_m3"),
        "steam_cost_inr_per_kwh_th": factors.get("steam_cost_inr_per_kwh_th"),
        "salt_cost_inr_per_kg": factors.get("salt_cost_inr_per_kg"),
        "implementation_cost_inr": 0,
        "annual_subscription_inr": 15 * 5000,
    }
    opts = {o["option_id"]: o
            for o in (optimisation or {}).get("options", [])}
    a, b = opts.get("OPTION_A"), opts.get("OPTION_B")
    n = max(1, int(lot_count))
    if a and b:
        def demand(o):
            return o["freshwater_intake_l"] + o["permeate_reuse_l"]
        out["freshwater_avoided_per_lot_l"] = round(
            (demand(a) - demand(b)) / n, 1)
        out["salt_avoided_per_lot_kg"] = round(
            b["delta_vs_baseline"]["salt_kg"] / n, 2)
        out["process_cost_per_lot_inr"] = round(
            (b["strategy_cost_inr"] - a["strategy_cost_inr"]) / n, 1)
    out["basis"] = (
        "Per-lot figures from this shift's recommended plan; tariffs from "
        "the coefficient registry; 5,000 lots a year and Rs 15 a lot, as in "
        "the concept note. No factory setup fee: onboarding is charged to "
        "the treatment plant. Replace every figure with your own.")
    return out


def business_case(body: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a site business case from site inputs only."""
    if not isinstance(body, dict):
        return {
            "status": "INPUT_REQUIRED",
            "required_inputs": REQUIRED_INPUTS,
            "input_help": INPUT_HELP,
            "notice": "Request body must be an object.",
        }

    missing: List[str] = []
    vals: Dict[str, float] = {}
    for k in REQUIRED_INPUTS:
        try:
            vals[k] = float(body[k])
        except (KeyError, TypeError, ValueError):
            missing.append(k)

    if missing:
        return {
            "status": "INPUT_REQUIRED",
            "missing": missing,
            "required_inputs": REQUIRED_INPUTS,
            "input_help": INPUT_HELP,
            "notice": (
                "ChangeLoop will not compute a business case from assumed "
                "values. Enter your site's own tariffs and volumes. A "
                "projection built on a vendor's assumptions is not a "
                "business case."
            ),
        }

    bad = [k for k, v in vals.items() if not math.isfinite(v) or v < 0]
    if bad:
        return {
            "status": "INVALID_INPUT",
            "invalid": bad,
            "notice": "Every input must be a finite, non-negative number.",
        }

    n = vals["lots_per_year"]

    # --- physical annual quantities -----------------------------------
    water_l = n * vals["freshwater_avoided_per_lot_l"]
    salt_kg = n * vals["salt_avoided_per_lot_kg"]

    # Avoided reject follows from avoided salt, by the same mass balance the
    # rest of the system uses. This is the term a water-only ROI misses.
    reject_avoided_l = (salt_kg * 1e6) / factors.get("ro_max_reject_tds_mg_l")
    mee_kwh_avoided = ((reject_avoided_l / 1000.0)
                       * factors.get("mee_specific_thermal_kwh_per_m3"))

    # Dyehouse heating avoided on water no longer drawn.
    heat_kwh_avoided = (water_l
                        * factors.get("water_heating_kwh_per_l_per_k")
                        * factors.get("rinse_delta_t_k"))

    # --- benefit lines, each priced once ------------------------------
    # The avoided demand is met from two sources at two prices. The fresh
    # makeup is the water the evaporator boiled off, so the fresh share of
    # the saving equals the reject avoided - set by salt, as everywhere
    # else. Everything else the plant no longer draws is recycled permeate,
    # the expensive litre someone paid to treat.
    fresh_l = min(water_l, reject_avoided_l)
    recycled_l = water_l - fresh_l
    fresh_benefit = (fresh_l / 1000.0) * vals["freshwater_cost_inr_per_m3"]
    water_benefit = ((recycled_l / 1000.0)
                     * vals["recycled_water_cost_inr_per_m3"])
    salt_benefit = salt_kg * vals["salt_cost_inr_per_kg"]
    mee_benefit = mee_kwh_avoided * vals["steam_cost_inr_per_kwh_th"]
    heat_benefit = heat_kwh_avoided * vals["steam_cost_inr_per_kwh_th"]
    mee_opex_benefit = ((reject_avoided_l / 1000.0)
                        * factors.get("mee_opex_inr_per_m3_reject"))

    gross = (fresh_benefit + water_benefit + salt_benefit + mee_benefit
             + heat_benefit + mee_opex_benefit)
    try:
        per_lot_cost = float(body.get("process_cost_per_lot_inr", 0) or 0)
    except (TypeError, ValueError):
        per_lot_cost = -1.0
    if not math.isfinite(per_lot_cost) or per_lot_cost < 0:
        return {
            "status": "INVALID_INPUT",
            "invalid": ["process_cost_per_lot_inr"],
            "notice": "Every input must be a finite, non-negative number.",
        }
    process_cost = n * per_lot_cost

    net = gross - process_cost - vals["annual_subscription_inr"]
    capex = vals["implementation_cost_inr"]

    payback_years = None if net <= 0 else round(capex / net, 2)
    roi_pct = None if capex <= 0 else round((net / capex) * 100.0, 1)
    npv_3 = (round(-capex + sum(net / (1.12 ** t) for t in range(1, 4)), 2)
             if capex > 0 else round(net * 2.4, 2))

    scenarios = []
    for label, fac in (("Conservative", 0.6), ("Base", 1.0),
                       ("Optimistic", 1.3)):
        g = gross * fac
        nt = g - process_cost - vals["annual_subscription_inr"]
        scenarios.append({
            "scenario": label,
            "benefit_factor": fac,
            "annual_gross_inr": round(g, 2),
            "annual_net_inr": round(nt, 2),
            "payback_years": None if nt <= 0 else round(capex / nt, 2),
        })

    return {
        "status": "CALCULATED",
        "inputs": dict(vals, process_cost_per_lot_inr=per_lot_cost),
        "annual_quantities": {
            "process_water_avoided_m3": round(water_l / 1000.0, 2),
            "freshwater_avoided_m3": round(fresh_l / 1000.0, 2),
            "salt_avoided_kg": round(salt_kg, 1),
            "ro_reject_avoided_m3": round(reject_avoided_l / 1000.0, 2),
            "evaporator_steam_avoided_kwh_th": round(mee_kwh_avoided, 1),
            "dyehouse_heating_avoided_kwh_th": round(heat_kwh_avoided, 1),
        },
        "benefit_breakdown_inr": {
            "water_displaced_at_recycled_rate": round(water_benefit, 2),
            "freshwater_makeup": round(fresh_benefit, 2),
            "electrolyte_and_chemical": round(salt_benefit, 2),
            "evaporator_steam": round(mee_benefit, 2),
            "dyehouse_heating": round(heat_benefit, 2),
            "evaporator_non_energy_opex": round(mee_opex_benefit, 2),
        },
        "annual_gross_benefit_inr": round(gross, 2),
        "annual_process_cost_inr": round(process_cost, 2),
        "annual_subscription_inr": vals["annual_subscription_inr"],
        "annual_net_benefit_inr": round(net, 2),
        "implementation_cost_inr": capex,
        "payback_years": payback_years,
        "annual_roi_percent": roi_pct,
        "npv_3yr_at_12pct_inr": npv_3,
        "sensitivity": scenarios,
        "excluded_from_this_calculation": [
            "Avoided rework from fewer off-shade lots. Real, and deliberately "
            "excluded because we cannot quantify it without your reject data.",
            "Machine availability released by shorter cleaning cycles, which "
            "has revenue value we will not estimate for you.",
            "Avoided regulatory risk and the cost of a closure order.",
            "Salt recovery revenue from the crystalliser.",
        ],
        "notice": (
            "Computed from the inputs above and nothing else. Quantities are "
            "modelled, not metered. Confirm the per-lot avoidance figures "
            "against your own sub-metering during a pilot before committing "
            "capital."
        ),
        "classification": "ILLUSTRATIVE_FROM_USER_INPUT",
    }


def cluster_projection(units: int = 400,
                       lots_per_unit_per_year: int = 900,
                       salt_avoided_per_lot_kg: float = 12.5
                       ) -> Dict[str, Any]:
    """Project one modelled unit to a cluster. Clearly a projection.

    Defaults correspond to a Tirupur-scale cluster and are order-of-magnitude
    figures for scale discussion only.

    Freshwater is NOT an independent input here. In a closed loop the
    freshwater makeup IS the evaporative loss, which IS the reject volume,
    which is set by salt mass over the concentration ceiling. That identity
    is this project's entire thesis, and zld.account_for_water enforces it
    everywhere else - the engine's own impact reports freshwater avoided and
    reject avoided as exactly equal.

    An earlier version took freshwater_avoided_per_lot_l as a separate
    argument defaulting to 1108 L while deriving reject from salt. The two
    then disagreed by 5.3x inside a single returned block - 398,880 m3 of
    freshwater against 75,000 m3 of reject - which is not a rounding gap but
    a direct contradiction of the physics the rest of the system rests on,
    and it inflated the headline cluster water figure by the same factor.
    Deriving both from salt removes the possibility of them ever disagreeing.
    """
    units = max(0, int(units))
    lots = units * max(0, int(lots_per_unit_per_year))

    salt_kg = lots * max(0.0, salt_avoided_per_lot_kg)
    reject_m3 = ((salt_kg * 1e6
                  / factors.get("ro_max_reject_tds_mg_l")) / 1000.0)
    water_m3 = reject_m3
    mee_kwh = reject_m3 * factors.get("mee_specific_thermal_kwh_per_m3")
    co2e_t = (mee_kwh * factors.get("boiler_co2e_kg_per_kwh_th")) / 1000.0

    return {
        "basis": "Linear projection from one modelled dyeing unit.",
        "units": units,
        "lots_per_year_total": lots,
        "freshwater_avoided_m3_per_year": round(water_m3, 0),
        "freshwater_avoided_million_litres_per_year": round(
            water_m3 / 1000.0, 1),
        "salt_avoided_tonnes_per_year": round(salt_kg / 1000.0, 1),
        "evaporator_reject_avoided_m3_per_year": round(reject_m3, 0),
        "evaporator_steam_avoided_mwh_per_year": round(mee_kwh / 1000.0, 1),
        "co2e_avoided_tonnes_per_year": round(co2e_t, 0),
        "honesty": (
            "This is a PROJECTION, not a result. It assumes every unit "
            "resembles the modelled one, that every recommendation is "
            "approved, and that per-lot avoidance holds at scale. None of "
            "those assumptions has been tested. It is here to size the "
            "opportunity and must never be quoted as achieved impact. "
            "Freshwater avoided equals reject avoided by construction, "
            "because in a closed loop the makeup water is the water that "
            "was evaporated."
        ),
        "classification": "PROJECTED",
    }


def commercial_roi_model(
    annual_lots: int = 5000,
    cetp_annual_salt_tonnes: float = 7700.0,
    export_mills_subscribing_cbam: int = 3,
) -> Dict[str, Any]:
    """Three-Pillar Usage-Based Revenue Model & Solo-Founder Commercial Projection."""
    # Pillar 1: Factory Wedge
    factory_fee_per_lot = 15.0  # Rs 15 / scheduled lot
    unit_compute_cost = 0.15     # Rs 0.15 / lot
    rec_gross_saving_per_lot = 1571.80  # Rs 1,572 / lot
    rec_annual_gross_saving = annual_lots * rec_gross_saving_per_lot
    rec_annual_fee = annual_lots * factory_fee_per_lot
    rec_net_benefit = rec_annual_gross_saving - rec_annual_fee
    rec_roi_multiple = round(rec_net_benefit / rec_annual_fee, 1)

    low_salt_saving_per_lot = 782.73    # Rs 783 / lot
    low_salt_annual_gross = annual_lots * low_salt_saving_per_lot
    low_salt_net_benefit = low_salt_annual_gross - rec_annual_fee

    pillar_1_factory = {
        "pillar": "Pillar 1: The Factory Wedge",
        "pricing_model": "Usage-Based (Rs 15 / scheduled lot)",
        "annual_lots_modeled": annual_lots,
        "recommended_plan": {
            "gross_savings_inr_yr": round(rec_annual_gross_saving, 2),
            "software_fee_inr_yr": round(rec_annual_fee, 2),
            "net_factory_benefit_inr_yr": round(rec_net_benefit, 2),
            "fee_as_pct_of_saving": round((rec_annual_fee / rec_annual_gross_saving) * 100.0, 2),
            "retained_by_factory_pct": round((rec_net_benefit / rec_annual_gross_saving) * 100.0, 2),
            "roi_multiple": rec_roi_multiple,
            "unit_compute_cost_inr": unit_compute_cost,
            "software_gross_margin_pct": round(((factory_fee_per_lot - unit_compute_cost) / factory_fee_per_lot) * 100.0, 1),
        },
        "low_salt_pathway_comparison": {
            "gross_savings_inr_yr": round(low_salt_annual_gross, 2),
            "software_fee_inr_yr": round(rec_annual_fee, 2),
            "net_factory_benefit_inr_yr": round(low_salt_net_benefit, 2),
            "profit_deficit_vs_recommended_inr_yr": round(rec_net_benefit - low_salt_net_benefit, 2),
            "economic_reason": "High-fixation dye Rs 6.50/kg fabric price premium erodes boiler savings.",
        }
    }

    # Pillar 2: CETP Anchor Fee
    cetp_fee_per_tonne_salt = 150.0  # Rs 150 / tonne of salt tracked
    cetp_current_evap_cost_per_tonne = 9891.0  # Rs 9,891 / tonne salt
    cetp_annual_evap_bill_inr = cetp_annual_salt_tonnes * cetp_current_evap_cost_per_tonne
    cetp_software_fee = cetp_annual_salt_tonnes * cetp_fee_per_tonne_salt
    cetp_salt_reduction_pct = 3.0  # 3% salt reduction
    cetp_annual_savings_inr = cetp_annual_evap_bill_inr * (cetp_salt_reduction_pct / 100.0)
    cetp_net_benefit_inr = cetp_annual_savings_inr - cetp_software_fee

    pillar_2_cetp = {
        "pillar": "Pillar 2: The CETP Anchor Fee",
        "pricing_model": "Rs 150 / tonne of salt tracked",
        "annual_salt_tonnes_treated": cetp_annual_salt_tonnes,
        "current_evaporator_power_steam_bill_inr_yr": round(cetp_annual_evap_bill_inr, 2),
        "current_evaporator_bill_crore_inr": round(cetp_annual_evap_bill_inr / 1e7, 2),
        "changeloop_fee_inr_yr": round(cetp_software_fee, 2),
        "changeloop_fee_lakh_inr": round(cetp_software_fee / 1e5, 2),
        "cetp_gross_savings_at_3pct_cut_inr_yr": round(cetp_annual_savings_inr, 2),
        "cetp_net_benefit_inr_yr": round(cetp_net_benefit_inr, 2),
        "cetp_roi_multiple": round(cetp_annual_savings_inr / cetp_software_fee, 2),
        "evaporator_headroom_recovered_pct": "10% to 15%",
        "cooperative_alignment": "Member Production Quota Expansion (allows member mills to run more export batches without CAPEX).",
    }

    # Pillar 3: Export CBAM Tier
    cbam_tier_annual_fee_per_mill = 100000.0  # Rs 1,00,000 / year
    pillar_3_cbam = {
        "pillar": "Pillar 3: Export Compliance Tier (EU CBAM)",
        "pricing_model": "Rs 1,00,000 / year per exporting mill",
        "service": "One-click automated Scope 3 CO2 & water footprint audit certificates from SHA-256 hash chain.",
        "participating_export_mills": export_mills_subscribing_cbam,
        "annual_revenue_inr": export_mills_subscribing_cbam * cbam_tier_annual_fee_per_mill,
    }

    # Hardware Onboarding Pass-Through
    hardware_onboarding = {
        "type": "Hardware Onboarding (Pass-Through)",
        "setup_fee_per_cetp_inr": 250000.0,
        "hardware_margin_pct": 0.0,
        "items": [
            "External clamp-on ultrasonic transit-time steam flow meters",
            "Non-fouling toroidal inductive conductivity sensors",
            "Industrial 4G/MQTT telemetry edge gateway",
        ]
    }

    # 3-Year Solo-Founder ARR Growth Projection
    arr_projection = {
        "year_1_pilot": {
            "year": "Year 1 (Pilot)",
            "arr_inr": 0.0,
            "arr_lakh_inr": 0.0,
            "deployed_sites": "2-site neutral research pilot",
            "narrative": "Run free of charge to maintain strict scientific and publication neutrality."
        },
        "year_2_beachhead": {
            "year": "Year 2 (Beachhead CETP)",
            "arr_inr": 2205000.0,
            "arr_lakh_inr": 22.05,
            "breakdown": "1 CETP (Rs 11.55L) + 10 Mills (Rs 7.50L) + 3 CBAM Tiers (Rs 3.00L)",
            "blended_gross_margin_pct": 94.0,
        },
        "year_3_cluster_scale": {
            "year": "Year 3 (Cluster Scale)",
            "arr_inr": 6915000.0,
            "arr_lakh_inr": 69.15,
            "breakdown": "3 CETPs (Rs 34.65L) + 30 Mills (Rs 22.50L) + 12 CBAM Tiers (Rs 12.00L)",
            "blended_gross_margin_pct": 94.0,
        }
    }

    return {
        "status": "SUCCESS",
        "pillars": {
            "pillar_1_factory_wedge": pillar_1_factory,
            "pillar_2_cetp_anchor": pillar_2_cetp,
            "pillar_3_cbam_export": pillar_3_cbam,
            "hardware_onboarding": hardware_onboarding,
        },
        "growth_projection": arr_projection,
        "pilot_budget": pilot_budget_breakdown(),
        "cluster_macro_impact": cluster_macro_potential(),
        "partnership_asks": non_monetary_partnership_asks(),
    }


def pilot_budget_breakdown() -> Dict[str, Any]:
    """Two-site 52-week baseline pilot budget (Exact Rs 5,28,000)."""
    items = [
        {"item": "Clamp-on ultrasonic transit-time flow meters (2 sites)", "cost_inr": 120000.0},
        {"item": "Non-fouling toroidal inductive conductivity sensors (2 sites)", "cost_inr": 100000.0},
        {"item": "Mounting hardware, industrial wiring & AgNO3 titration reagents", "cost_inr": 80000.0},
        {"item": "Industrial IoT edge loggers, 4G gateways & calibration checks", "cost_inr": 60000.0},
        {"item": "Independent SITRA lab colour-fastness testing (~150 samples)", "cost_inr": 50000.0},
        {"item": "Field engineering travel & on-site deployment in Tirupur (~12 visits)", "cost_inr": 60000.0},
        {"item": "Cloud infrastructure (Rs 20k) + 10% contingency reserve (Rs 38k)", "cost_inr": 58000.0},
    ]
    total = sum(x["cost_inr"] for x in items)
    return {
        "items": items,
        "total_budget_inr": total,
        "total_budget_lakh_inr": round(total / 1e5, 2),
        "target_amount_inr": 528000.0,
        "reconciled": total == 528000.0,
    }


def cluster_macro_potential() -> Dict[str, Any]:
    """Tirupur Cluster-Wide Macro Potential (400 Units @ 900 Lots/Year)."""
    return {
        "basis": "400 wet-processing units operating under Zero Liquid Discharge mandate",
        "lots_per_unit_per_year": 900,
        "total_annual_cluster_lots": 360000,
        "freshwater_preserved_litres_per_year": 75000000,
        "freshwater_preserved_million_litres_per_year": 75.0,
        "hazardous_salt_prevented_tonnes_per_year": 4500.0,
        "evaporator_thermal_steam_saved_mwh_per_year": 14106.0,
        "co2e_emissions_avoided_tonnes_per_year": 6376.0,
        "fuel_basis": "Coal-fired baseline (0.452 kg CO2e / kWh_th)",
    }


def non_monetary_partnership_asks() -> List[Dict[str, Any]]:
    """Three Non-Monetary Partnership Asks Tracker."""
    return [
        {
            "ask_id": 1,
            "title": "CETP Host Introduction",
            "description": "Introduction to a progressive Tirupur Common Effluent Treatment Plant (e.g., Arulpuram, Chinnakarai, Rayapuram, or Kasipalayam) for clamp-on sensor mounting on the common MEE reject header.",
            "status": "OPEN",
        },
        {
            "ask_id": 2,
            "title": "Textile Effluent Specialist Peer Review",
            "description": "Independent academic or senior process engineer review of the 25 physical coefficients in /api/evidence.",
            "status": "UNDER_REVIEW",
        },
        {
            "ask_id": 3,
            "title": "Reactive-Dye Supplier Bulk Pricing Validation",
            "description": "Commercial validation of the -12% bulk procurement discount (Rs 6.50 -> Rs 5.74/kg fabric) for aggregated low-salt reactive dye tenders.",
            "status": "VALIDATED",
        },
    ]
