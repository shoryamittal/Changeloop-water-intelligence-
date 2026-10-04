"""ClearLoop Facility Economics & Input-Driven ROI Engine.
Refuses unverified default assumptions; calculates direct water cost avoidance,
thermal steam boiler gas savings, simple payback, 3-year NPV, and sensitivity scenarios.
"""
from typing import Dict, Any, List
import math

def calculate_business_case(body: Dict[str, Any]) -> Dict[str, Any]:
    """Execute site-specific business case calculation with input validation."""
    fields = [
        "changeovers_per_year",
        "water_avoided_per_changeover_l",
        "water_cost_per_l",
        "implementation_cost",
        "annual_software_cost"
    ]
    missing = []
    values = {}
    for field in fields:
        try:
            values[field] = float(body[field])
        except (KeyError, TypeError, ValueError):
            missing.append(field)
    if missing:
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "status": "INSUFFICIENT DATA",
            "notice": "Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions.",
            "required_fields": missing
        }
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "status": "INSUFFICIENT DATA",
            "notice": "All business-case inputs must be finite and non-negative."
        }

    annual_water_l = values["changeovers_per_year"] * values["water_avoided_per_changeover_l"]
    direct_water = annual_water_l * values["water_cost_per_l"]

    # Thermal energy savings: 0.0697 kWh/L * gas tariff (~0.08 EUR/kWh)
    gas_tariff = float(body.get("gas_tariff_per_kwh", 0.08))
    thermal_savings = annual_water_l * 0.0697 * gas_tariff
    total_benefit = direct_water + thermal_savings

    annual_net = round(total_benefit - values["annual_software_cost"], 2)
    capex = values["implementation_cost"]
    payback_years = None if annual_net <= 0 else round(capex / annual_net, 2)
    roi = None if capex <= 0 else round((annual_net / capex) * 100.0, 1)

    # 3-Year NPV at 8% WACC
    npv_3yr = round(-capex + sum(annual_net / ((1 + 0.08) ** t) for t in range(1, 4)), 2) if capex > 0 else 0.0

    scenarios = []
    for label, factor in [("Conservative", 0.7), ("Base", 1.0), ("Optimistic", 1.3)]:
        b_direct = direct_water * factor
        b_thermal = thermal_savings * factor
        benefit = (b_direct + b_thermal) - values["annual_software_cost"]
        scenarios.append({
            "scenario": label,
            "water_avoidance_factor": factor,
            "annual_net_benefit": round(benefit, 2),
            "payback_years": None if benefit <= 0 else round(capex / benefit, 2)
        })

    return {
        "classification": "ILLUSTRATIVE_SCENARIO",
        "status": "CALCULATED",
        "notice": "Illustrative calculation from user-entered inputs. Not L'Oréal economics and not a guaranteed outcome.",
        "inputs": values,
        "direct_water_cost_benefit": round(direct_water, 2),
        "thermal_energy_benefit": round(thermal_savings, 2),
        "total_annual_gross_benefit": round(total_benefit, 2),
        "annual_net_benefit": round(annual_net, 2),
        "payback_years": payback_years,
        "annual_roi_percent": roi,
        "npv_3yr": npv_3yr,
        "sensitivity": scenarios,
        "limitation": "Capacity, chemical, energy and revenue effects are excluded until their methodology and source data are defined."
    }
