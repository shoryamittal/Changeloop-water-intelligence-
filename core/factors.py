"""ChangeLoop - Coefficient & Evidence Registry.

SINGLE SOURCE OF TRUTH for every physical, thermodynamic, economic and
emissions coefficient used anywhere in the system.

Design rule enforced here:
  No number may be used in a calculation unless it is registered in this
  module with (a) an explicit unit, (b) a derivation or source, and
  (c) an evidence class. `audit_trail()` renders this registry to the UI so
  a reviewer can trace any displayed figure back to its origin.

Evidence classes (strict, never mixed):
  MEASURED   - instrument reading from a real asset. NOTHING in this
               prototype is MEASURED. The class exists so a pilot
               deployment can promote values into it.
  DERIVED    - computed from first principles (thermodynamics, mass
               balance) inside this repository. Derivation string given.
  PUBLISHED  - value reported in public literature / regulation. Source given.
  ASSUMED    - engineering assumption chosen by us. Rationale given and the
               value is exposed as a tunable input.
  SIMULATED  - produced by our own synthetic generators.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass(frozen=True)
class Factor:
    """One traceable coefficient."""
    key: str
    label: str
    value: float
    unit: str
    evidence: str          # MEASURED | DERIVED | PUBLISHED | ASSUMED | SIMULATED
    basis: str             # derivation or source - must be non-empty
    tunable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Thermodynamics of evaporation - the core of the ZLD energy coupling
# ---------------------------------------------------------------------------

# Latent heat of vaporisation of water at ~100 degC, 1 atm = 2257 kJ/kg.
# 2257 kJ/kg / 3600 kJ/kWh = 0.62694 kWh/kg
_H_VAP_KWH_PER_KG = 2257.0 / 3600.0

# Steam economy of a forced-circulation multiple-effect evaporator:
# kg of water evaporated per kg of live steam supplied. A well-run 4-effect
# train sits around 3.2-3.6; optimised trains with thermocompression and
# condensate flashing reach 5-6. We take the conservative mid-range value.
_MEE_STEAM_ECONOMY = 3.5

FACTORS: Dict[str, Factor] = {

    # --- Evaporation / ZLD energy ---------------------------------------
    "h_vap_kwh_per_kg": Factor(
        key="h_vap_kwh_per_kg",
        label="Latent heat of vaporisation of water",
        value=round(_H_VAP_KWH_PER_KG, 6),
        unit="kWh_th/kg",
        evidence="PUBLISHED",
        basis="2257 kJ/kg at 100 degC and 1 atm (standard steam tables), "
              "converted: 2257 / 3600 = 0.62694 kWh/kg.",
        tunable=False,
    ),
    "mee_steam_economy": Factor(
        key="mee_steam_economy",
        label="MEE steam economy (4-effect train)",
        value=_MEE_STEAM_ECONOMY,
        unit="kg water evaporated / kg live steam",
        evidence="ASSUMED",
        basis="Conservative mid-range for a 4-effect forced-circulation "
              "evaporator on textile RO reject. Literature places optimised "
              "multiple-effect trains at up to 5-6 kg/kg; we deliberately "
              "under-claim so the energy saving we report is not inflated.",
    ),
    "mee_specific_thermal_kwh_per_m3": Factor(
        key="mee_specific_thermal_kwh_per_m3",
        label="MEE specific thermal energy per m3 of reject evaporated",
        value=round((_H_VAP_KWH_PER_KG * 1000.0) / _MEE_STEAM_ECONOMY, 2),
        unit="kWh_th/m3",
        evidence="DERIVED",
        basis="h_vap x 1000 kg/m3 / steam_economy = 0.62694 x 1000 / 3.5 "
              "= 179.13 kWh_th per m3 evaporated. Sits inside the "
              "150-250 kWh_th/m3 band commonly quoted for the evaporator "
              "section of textile ZLD plants.",
        tunable=False,
    ),

    # --- Reverse osmosis -------------------------------------------------
    "ro_max_recovery_frac": Factor(
        key="ro_max_recovery_frac",
        label="RO hydraulic recovery ceiling",
        value=0.90,
        unit="fraction of feed recovered as permeate",
        evidence="ASSUMED",
        basis="Hydraulic limit of a multi-stage brackish RO train on "
              "biologically pretreated textile effluent. Caps permeate even "
              "when the salt balance alone would allow more.",
    ),
    "ro_max_reject_tds_mg_l": Factor(
        key="ro_max_reject_tds_mg_l",
        label="Maximum concentrate (reject) TDS before evaporator feed",
        value=60000.0,
        unit="mg/L",
        evidence="ASSUMED",
        basis="Concentration ceiling set by osmotic pressure and sparingly "
              "soluble salt scaling in the final RO stage. This number, with "
              "salt mass conservation, is what fixes reject volume: "
              "V_reject = M_salt / C_reject_max.",
    ),
    "ro_specific_electrical_kwh_per_m3": Factor(
        key="ro_specific_electrical_kwh_per_m3",
        label="RO high-pressure pumping energy per m3 of feed",
        value=1.2,
        unit="kWh_e/m3 feed",
        evidence="ASSUMED",
        basis="Specific energy consumption of brackish-water RO on high-TDS "
              "textile effluent at elevated feed pressure.",
    ),

    # --- Emissions -------------------------------------------------------
    "boiler_co2e_kg_per_kwh_th": Factor(
        key="boiler_co2e_kg_per_kwh_th",
        label="Boiler CO2e per kWh of delivered thermal energy",
        value=0.452,
        unit="kg CO2e/kWh_th",
        evidence="DERIVED",
        basis="Indian industrial coal-fired steam boiler. Coal combustion "
              "~0.353 kg CO2e per kWh of fuel energy; boiler efficiency "
              "assumed 0.78, so 0.353 / 0.78 = 0.452 kg CO2e per kWh of "
              "thermal energy actually delivered to the evaporator.",
    ),
    "grid_co2e_kg_per_kwh_e": Factor(
        key="grid_co2e_kg_per_kwh_e",
        label="Indian grid electricity emission factor",
        value=0.71,
        unit="kg CO2e/kWh_e",
        evidence="PUBLISHED",
        basis="Central Electricity Authority CO2 baseline database for the "
              "Indian grid; combined-margin factor of approximately 0.71 kg "
              "CO2 per kWh. Applied to RO pumping and dyehouse electrical "
              "loads.",
    ),

    # --- Dyehouse thermal ------------------------------------------------
    "water_heating_kwh_per_l_per_k": Factor(
        key="water_heating_kwh_per_l_per_k",
        label="Sensible heat to raise 1 L of water by 1 K",
        value=round(4.186 / 3600.0, 8),
        unit="kWh_th/(L.K)",
        evidence="PUBLISHED",
        basis="Specific heat capacity of water 4.186 kJ/(kg.K); 1 L ~ 1 kg; "
              "4.186 / 3600 = 0.00116278 kWh per litre per kelvin.",
        tunable=False,
    ),
    "rinse_delta_t_k": Factor(
        key="rinse_delta_t_k",
        label="Hot rinse temperature rise over ambient",
        value=55.0,
        unit="K",
        evidence="ASSUMED",
        basis="Soaping and hot-wash stages in reactive dyeing run near "
              "80 degC against a 25 degC ambient intake in Tamil Nadu.",
    ),

    # --- Economics (INR) -------------------------------------------------
    "freshwater_cost_inr_per_m3": Factor(
        key="freshwater_cost_inr_per_m3",
        label="Freshwater cost (groundwater / municipal abstraction)",
        value=45.0,
        unit="INR/m3",
        evidence="PUBLISHED",
        basis="Reported cost of water extraction from ground or municipal "
              "supply for Indian textile units is in the range of "
              "INR 30-60 per kilolitre. We take the midpoint, 45.",
    ),
    "recycled_water_cost_inr_per_m3": Factor(
        key="recycled_water_cost_inr_per_m3",
        label="Cost of treated and recycled water from the ZLD loop",
        value=135.0,
        unit="INR/m3",
        evidence="PUBLISHED",
        basis="Treated and recycled water in Indian textile ZLD operation is "
              "reported at INR 120-150 per kilolitre; midpoint 135. This is "
              "2 to 5 times the cost of the freshwater it replaces, which is "
              "the single most important economic fact in this domain: once a "
              "plant is closed-loop, the marginal litre comes from the "
              "recycle train, not from the borewell. Avoiding a litre of "
              "DEMAND is therefore worth far more than recovering a litre of "
              "effluent - which is precisely why ChangeLoop intervenes "
              "upstream of the demand rather than downstream of the waste.",
    ),
    "steam_cost_inr_per_kwh_th": Factor(
        key="steam_cost_inr_per_kwh_th",
        label="Delivered boiler steam cost",
        value=2.40,
        unit="INR/kWh_th",
        evidence="ASSUMED",
        basis="Derived from Indian industrial coal/biomass pricing at about "
              "78% boiler efficiency. Tunable per site fuel contract.",
    ),
    "electricity_cost_inr_per_kwh": Factor(
        key="electricity_cost_inr_per_kwh",
        label="Industrial electricity tariff",
        value=8.50,
        unit="INR/kWh_e",
        evidence="ASSUMED",
        basis="Tamil Nadu HT industrial tariff band including demand charges.",
    ),
    "salt_cost_inr_per_kg": Factor(
        key="salt_cost_inr_per_kg",
        label="Dyebath electrolyte (Glauber salt / common salt) cost",
        value=9.0,
        unit="INR/kg",
        evidence="ASSUMED",
        basis="Bulk industrial sodium sulphate / sodium chloride delivered "
              "price. Salt avoided upstream is both a chemical saving and an "
              "evaporator-load saving; each is reported on its own ledger "
              "line and never summed into the water line.",
    ),
    # --- process strategy levers ----------------------------------------
    # These two levers are the reason the product needs a multi-objective
    # optimiser rather than a water dashboard: ONE SAVES WATER WITHOUT
    # SAVING SALT, THE OTHER SAVES SALT WITHOUT SAVING WATER. They pull in
    # different directions through the ZLD chain.
    "counter_current_water_multiplier": Factor(
        key="counter_current_water_multiplier",
        label="Rinse water multiplier under counter-current reuse",
        value=0.65,
        unit="fraction of single-stage rinse water",
        evidence="ASSUMED",
        basis="Counter-current rinsing, in which later and cleaner rinse "
              "liquor is cascaded back to earlier dirtier stages, is "
              "established best available technique in textile wet "
              "processing and is not claimed here as an invention. A 30-40% "
              "reduction in rinse water is the commonly cited range; we take "
              "35%. Critically it does NOT reduce the salt mass discharged - "
              "the same electrolyte simply leaves in less water - so it "
              "barely moves evaporator duty.",
    ),
    "counter_current_cost_inr_per_kg_fabric": Factor(
        key="counter_current_cost_inr_per_kg_fabric",
        label="Counter-current rinse operating cost per kg fabric",
        value=0.35,
        unit="INR/kg fabric",
        evidence="ASSUMED",
        basis="Additional transfer pumping, holding-tank turnover and "
              "cycle-time cost of running a cascaded rinse.",
    ),
    "low_salt_chemistry_salt_multiplier": Factor(
        key="low_salt_chemistry_salt_multiplier",
        label="Electrolyte multiplier under low-salt dye chemistry",
        value=0.55,
        unit="fraction of conventional electrolyte dose",
        evidence="ASSUMED",
        basis="Low-electrolyte and high-fixation reactive dye ranges are "
              "commercially available and reduce the salt required for dye "
              "exhaustion. Not our invention. We assume a 45% reduction in "
              "electrolyte. It does NOT reduce rinse water volume, but it "
              "cuts the salt mass that sets RO reject volume, so it is the "
              "lever that actually reduces evaporator steam.",
    ),
    "low_salt_chemistry_cost_inr_per_kg_fabric": Factor(
        key="low_salt_chemistry_cost_inr_per_kg_fabric",
        label="Low-salt dye chemistry premium per kg fabric",
        value=6.50,
        unit="INR/kg fabric",
        evidence="ASSUMED",
        basis="Low-electrolyte reactive dye ranges carry a price premium "
              "over conventional ranges. Sized against dye cost: a deep "
              "shade at 6% on weight of fabric with dye around "
              "INR 600/kg is roughly INR 36/kg fabric of dye, so an 18% "
              "range premium is about INR 6.5/kg fabric. This premium is "
              "what makes the choice a genuine trade-off rather than a free "
              "win, and it is the reason a site will not pay for the "
              "chemistry until the evaporator saving is quantified for it. "
              "It is also the single most decision-relevant uncertainty in "
              "the model - see the sensitivity sweep.",
    ),

    "mee_opex_inr_per_m3_reject": Factor(
        key="mee_opex_inr_per_m3_reject",
        label="MEE non-energy operating cost per m3 of reject",
        value=180.0,
        unit="INR/m3",
        evidence="ASSUMED",
        basis="Antiscalant, cleaning, crystalliser handling, salt disposal "
              "and maintenance, excluding steam. Steam is costed separately "
              "so the energy term is never double counted.",
    ),
}


def get(key: str) -> float:
    """Return a registered coefficient value. Raises if unregistered."""
    if key not in FACTORS:
        raise KeyError(
            "Coefficient '{}' is not registered in core.factors. Every "
            "number used in a calculation must be registered with a unit, a "
            "basis and an evidence class.".format(key)
        )
    return FACTORS[key].value


def factor(key: str) -> Factor:
    if key not in FACTORS:
        raise KeyError(
            "Coefficient '{}' is not registered in core.factors.".format(key)
        )
    return FACTORS[key]


def audit_trail() -> List[Dict[str, Any]]:
    """Full registry, for the Evidence / Data Trust screen and exports."""
    return [f.to_dict() for f in FACTORS.values()]


def evidence_summary() -> Dict[str, int]:
    """Count of coefficients per evidence class."""
    out: Dict[str, int] = {}
    for f in FACTORS.values():
        out[f.evidence] = out.get(f.evidence, 0) + 1
    return out
