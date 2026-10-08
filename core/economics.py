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
    "freshwater_avoided_per_lot_l": "From the ChangeLoop ledger for your own "
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
    # In a closed-loop plant the avoided litre displaces the RECYCLED litre,
    # which is the expensive one. Pricing it at the freshwater rate would
    # understate the saving roughly threefold.
    water_benefit = (water_l / 1000.0) * vals["recycled_water_cost_inr_per_m3"]
    salt_benefit = salt_kg * vals["salt_cost_inr_per_kg"]
    mee_benefit = mee_kwh_avoided * vals["steam_cost_inr_per_kwh_th"]
    heat_benefit = heat_kwh_avoided * vals["steam_cost_inr_per_kwh_th"]
    mee_opex_benefit = ((reject_avoided_l / 1000.0)
                        * factors.get("mee_opex_inr_per_m3_reject"))

    gross = (water_benefit + salt_benefit + mee_benefit + heat_benefit
             + mee_opex_benefit)
    net = gross - vals["annual_subscription_inr"]
    capex = vals["implementation_cost_inr"]

    payback_years = None if net <= 0 else round(capex / net, 2)
    roi_pct = None if capex <= 0 else round((net / capex) * 100.0, 1)
    npv_3 = (round(-capex + sum(net / (1.12 ** t) for t in range(1, 4)), 2)
             if capex > 0 else round(net * 2.4, 2))

    scenarios = []
    for label, fac in (("Conservative", 0.6), ("Base", 1.0),
                       ("Optimistic", 1.3)):
        g = gross * fac
        nt = g - vals["annual_subscription_inr"]
        scenarios.append({
            "scenario": label,
            "benefit_factor": fac,
            "annual_gross_inr": round(g, 2),
            "annual_net_inr": round(nt, 2),
            "payback_years": None if nt <= 0 else round(capex / nt, 2),
        })

    return {
        "status": "CALCULATED",
        "inputs": vals,
        "annual_quantities": {
            "freshwater_avoided_m3": round(water_l / 1000.0, 2),
            "salt_avoided_kg": round(salt_kg, 1),
            "ro_reject_avoided_m3": round(reject_avoided_l / 1000.0, 2),
            "evaporator_steam_avoided_kwh_th": round(mee_kwh_avoided, 1),
            "dyehouse_heating_avoided_kwh_th": round(heat_kwh_avoided, 1),
        },
        "benefit_breakdown_inr": {
            "water_displaced_at_recycled_rate": round(water_benefit, 2),
            "electrolyte_and_chemical": round(salt_benefit, 2),
            "evaporator_steam": round(mee_benefit, 2),
            "dyehouse_heating": round(heat_benefit, 2),
            "evaporator_non_energy_opex": round(mee_opex_benefit, 2),
        },
        "annual_gross_benefit_inr": round(gross, 2),
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
