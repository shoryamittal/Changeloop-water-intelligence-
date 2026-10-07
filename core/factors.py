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
import threading


# ---------------------------------------------------------------------------
# Registry lock.
#
# The sensitivity and ablation studies in core/scenarios.py temporarily
# replace coefficients in FACTORS to see what moves. Those studies hold
# this lock while they do it. READERS MUST HOLD IT TOO.
#
# Without that, a request served concurrently with a study can read a
# coefficient mid-patch and return a number computed against a value the
# caller never asked for - silently, with no error and no way to tell from
# the response. A concurrency test caught exactly that: the "cut salt 20%"
# proof intermittently came back as something other than -20.0% because an
# ablation run was patching the registry underneath it.
#
# For a system whose entire claim is that every number is traceable, a
# reader that can observe a torn registry is the most serious defect
# available. An RLock is re-entrant, so get() inside a study that already
# holds it does not deadlock.
#
# Owned here rather than in scenarios.py because the registry lives here;
# a lock that does not live with the data it guards gets forgotten.
# ---------------------------------------------------------------------------
REGISTRY_LOCK = threading.RLock()


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
# kg of water evaporated per kg of live steam supplied.
#
# Anchored on PUBLISHED specific steam consumption for MEE trains on
# textile RO reject: 0.25-0.35 kg steam per kg of water evaporated
# (CPCB Tirupur ZLD assessment; Indian ZLD vendor design data). Steam
# economy is the reciprocal of that figure, so the published band is
# 1/0.35 = 2.86 to 1/0.25 = 4.00 kg/kg. We take the MIDPOINT of the
# published specific-steam range, 0.30 kg/kg, giving 1/0.30 = 3.333.
#
# We deliberately do NOT use the 5-6 kg/kg reachable by optimised trains
# with thermocompression and condensate flashing: a better evaporator
# would make the steam saved per kg of salt avoided look smaller, so
# assuming a poor evaporator would inflate our claim. 3.333 is the
# published middle, not our choice of a flattering end.
_MEE_STEAM_ECONOMY = 1.0 / 0.30

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
        label="MEE steam economy (multiple-effect train on textile reject)",
        value=_MEE_STEAM_ECONOMY,
        unit="kg water evaporated / kg live steam",
        evidence="PUBLISHED",
        basis="Specific steam consumption of multiple-effect evaporators on "
              "textile RO reject is reported at 0.25-0.35 kg steam per kg of "
              "water evaporated. Steam economy is the reciprocal: "
              "1/0.30 = 3.33 kg/kg at the midpoint (range 2.86-4.00). "
              "Sources: CPCB assessment of textile dyeing units and ZLD at "
              "Tirupur; Indian ZLD design data for falling-film and "
              "forced-circulation MEE trains.",
    ),
    "mee_specific_thermal_kwh_per_m3": Factor(
        key="mee_specific_thermal_kwh_per_m3",
        label="MEE specific thermal energy per m3 of reject evaporated",
        value=round((_H_VAP_KWH_PER_KG * 1000.0) / _MEE_STEAM_ECONOMY, 2),
        unit="kWh_th/m3",
        evidence="DERIVED",
        basis="h_vap x 1000 kg/m3 / steam_economy = 0.62694 x 1000 / 3.333 "
              "= 188.08 kWh_th per m3 evaporated. Both inputs are "
              "PUBLISHED: latent heat from steam tables, steam economy from "
              "the reported 0.25-0.35 kg steam per kg evaporation for "
              "textile MEE trains. The result sits inside the "
              "150-250 kWh_th/m3 band quoted for the evaporator section of "
              "textile ZLD plants, which is an independent check: two "
              "unrelated published figures, multiplied, land inside a third "
              "published band.",
        tunable=False,
    ),

    # --- Reverse osmosis -------------------------------------------------
    "ro_max_recovery_frac": Factor(
        key="ro_max_recovery_frac",
        label="RO hydraulic recovery ceiling (multi-stage train)",
        value=0.90,
        unit="fraction of feed recovered as permeate",
        evidence="PUBLISHED",
        basis="Indian textile ZLD operators report RO reject at 20-30% of "
              "inlet volume for a single pass, i.e. 70-80% recovery, rising "
              "to about 90% on multi-stage trains with interstage boosting - "
              "which is what Tirupur CETPs run to reach the 95-98% water "
              "reuse they report. We set the ceiling at 0.90. NOTE: in this "
              "model recovery is a CEILING that is normally NOT the binding "
              "constraint - the salt balance binds first (see "
              "ro_max_reject_tds_mg_l). tests/test_published_validation.py "
              "checks our computed reject fraction against the published "
              "20-30% band as an external cross-check on the engine.",
    ),
    "ro_max_reject_tds_mg_l": Factor(
        key="ro_max_reject_tds_mg_l",
        label="Maximum concentrate (reject) TDS before evaporator feed",
        value=60000.0,
        unit="mg/L",
        evidence="PUBLISHED",
        basis="RO reject from Indian textile effluent is reported at "
              "15,000-80,000 mg/L TDS entering thermal evaporation, with "
              "multi-stage RO concentrating dissolved solids 3-5x. We take "
              "60,000 mg/L, the upper-middle of that operating band, as the "
              "ceiling set by osmotic pressure and sparingly-soluble salt "
              "scaling in the final stage. This number, with salt mass "
              "conservation, is what fixes reject volume: "
              "V_reject = M_salt / C_reject_max. Sources: CPCB Tirupur ZLD "
              "assessment; Indian ZLD process design data.",
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
        label="Indian grid CO2 emission factor (combined margin)",
        value=0.705,
        unit="kg CO2e/kWh_e",
        evidence="PUBLISHED",
        basis="Combined margin (CM) of the Indian grid = 0.705 tCO2/MWh for "
              "FY 2025-26, adjusted for cross-border electricity transfers "
              "and including renewable and captive injection into the grid. "
              "Source: CO2 Baseline Database for the Indian Power Sector, "
              "User Guide Version 22.0, August 2026, Central Electricity "
              "Authority, Ministry of Power, Government of India, Table S. "
              "Same table: weighted-average grid factor 0.675, simple "
              "operating margin 0.963, build margin 0.446; CM is the 50:50 "
              "weighting of OM and BM. We use CM rather than the average "
              "because avoided dyehouse load displaces marginal, not "
              "average, generation.",
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
        label="Freshwater cost delivered to a Tirupur wet-processing unit",
        value=45.0,
        unit="INR/m3",
        evidence="PUBLISHED",
        basis="Bhavani river water supplied to Tirupur dyeing units is "
              "reported at INR 45 per kilolitre. Tanker water runs "
              "INR 10-20/kL for small dyers in the monsoon and about "
              "INR 90/kL at summer rates (INR 1,000 per 11 kL load); Tirupur "
              "wet-processing units collectively spend roughly INR 115 crore "
              "a year on groundwater. We use the INR 45/kL piped-supply "
              "figure as the reference abstraction cost. Source: Down To "
              "Earth reporting on the Tirupur cluster; India Environment "
              "Portal.",
    ),
    "recycled_water_cost_inr_per_m3": Factor(
        key="recycled_water_cost_inr_per_m3",
        label="Marginal cost of a litre of water from the ZLD recycle loop",
        value=185.0,
        unit="INR/m3",
        evidence="PUBLISHED",
        basis="ZLD treatment charges levied on member units by Tirupur "
              "CETPs, from Tamil Nadu pollution board plant-level data: "
              "INR 150-220 per kilolitre at plants running at or above 30% "
              "of design capacity. We take INR 185/kL, the midpoint of that "
              "well-utilised band. THIS IS THE SINGLE MOST IMPORTANT "
              "ECONOMIC FACT IN THE DOMAIN: recycled water costs about four "
              "times the INR 45/kL freshwater it replaces, because adding "
              "the evaporator and crystalliser roughly doubles the cost of a "
              "plant that stops at reverse osmosis. Once a site is "
              "closed-loop the marginal litre comes from the recycle train, "
              "not the borewell - so avoiding a litre of DEMAND is worth far "
              "more than recovering a litre of effluent. That is why "
              "ChangeLoop intervenes upstream of the demand rather than "
              "downstream of the waste. Source: TNPCB plant-level charge "
              "data as compiled in published analysis of ZLD compliance-cost "
              "incidence in Indian textile and tannery clusters.",
    ),
    "steam_cost_inr_per_kwh_th": Factor(
        key="steam_cost_inr_per_kwh_th",
        label="Delivered boiler steam cost (fuel component)",
        value=2.03,
        unit="INR/kWh_th",
        evidence="DERIVED",
        basis="Derived from published coal pricing. Imported sub-bituminous "
              "thermal coal landed in India at about INR 9,180 per tonne = "
              "INR 9.18/kg. At 5,000 kcal/kg gross calorific value: "
              "5,000 x 4.184 = 20,920 kJ/kg = 5.811 kWh/kg of fuel energy. "
              "Fuel cost = 9.18 / 5.811 = INR 1.580 per kWh_fuel. At 78% "
              "boiler efficiency: 1.580 / 0.78 = INR 2.03 per kWh of thermal "
              "energy actually delivered to the evaporator. Boiler non-fuel "
              "operating cost (DM water, ash handling, labour, maintenance - "
              "typically +8-12%) is EXCLUDED, which understates the true "
              "steam cost and therefore understates the energy saving we "
              "report. Domestic coal is cheaper at source (INR 5,200-6,600 "
              "per tonne for 4,500-5,000 GCV, April 2026) but Tamil Nadu is "
              "far from the coalfields and the delivered price converges on "
              "the imported figure. Tunable per site fuel contract.",
    ),
    "electricity_cost_inr_per_kwh": Factor(
        key="electricity_cost_inr_per_kwh",
        label="Effective HT industrial electricity tariff, Tamil Nadu",
        value=9.04,
        unit="INR/kWh_e",
        evidence="DERIVED",
        basis="Derived from two published tariff components. TNERC tariff "
              "order of 27 March 2025, effective 1 July 2025 (FY 2026): HT "
              "industrial energy charge INR 7.50/kWh (up 3.4% from "
              "INR 7.25/kWh) and demand charge INR 608 per kVA per month (up "
              "from INR 589). Amortising the demand charge: at 0.90 power "
              "factor and 60% load factor one kVA of contracted demand "
              "delivers 0.90 x 0.60 x 730 = 394 kWh per month, so the demand "
              "charge adds 608 / 394 = INR 1.54/kWh. Effective tariff = "
              "7.50 + 1.54 = INR 9.04/kWh. Tamil Nadu runs a multi-year "
              "tariff framework with inflation-indexed annual revision "
              "capped at 6%.",
    ),
    "salt_cost_inr_per_kg": Factor(
        key="salt_cost_inr_per_kg",
        label="Dyebath electrolyte (Glauber salt / common salt) cost",
        value=9.0,
        unit="INR/kg",
        evidence="PUBLISHED",
        basis="Textile and detergent grade Glauber salt (sodium sulphate) is "
              "quoted at about INR 9/kg in bulk on Indian industrial "
              "marketplaces at 10-tonne minimum order quantity. "
              "Higher-purity grades range INR 22-58/kg, and Indian sodium "
              "sulphate prices rose 7-8% in Q2 2026. We use the bulk "
              "textile-grade figure because that is what a dyehouse actually "
              "buys. Salt avoided upstream is both a chemical saving and an "
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
        evidence="PUBLISHED",
        basis="Counter-current rinsing - cascading cleaner late-stage rinse "
              "liquor back to earlier dirtier stages - is established Best "
              "Available Technique in the EU IPPC BAT Reference Document for "
              "the Textiles Industry and is NOT claimed here as an "
              "invention. Published water savings run from 50% with two wash "
              "tanks to 80% with five tanks; whole-mill studies report about "
              "30% reduction in total specific water consumption from "
              "in-process BAT packages including counter-current washing. WE "
              "USE A 35% REDUCTION, below the published single-technique "
              "range, so our reported water saving deliberately under-claims "
              "against the literature. Critically, counter-current rinsing "
              "does NOT reduce the salt mass discharged - the same "
              "electrolyte simply leaves in less water - so it barely moves "
              "evaporator duty.",
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
        evidence="PUBLISHED",
        basis="Conventional exhaust dyeing of cellulose with reactive dyes "
              "uses 50-80 g/L of common salt or sodium sulphate; the full "
              "reported envelope across shade depths is 5-120 g/L. "
              "Low-electrolyte reactive ranges are documented at 5-40 g/L "
              "for the same exhaustion and levelness. Midpoint to midpoint "
              "that is 65 -> 22.5 g/L, a multiplier of 0.35. WE USE 0.55, a "
              "45% reduction, which under-claims the published benefit by a "
              "wide margin. Low-salt chemistry is commercially available and "
              "is NOT our invention. It does NOT reduce rinse water volume, "
              "but it cuts the salt mass that sets RO reject volume, so it "
              "is the lever that actually reduces evaporator steam.",
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
        evidence="PUBLISHED",
        basis="Antiscalant, cleaning, crystalliser handling, salt handling "
              "and maintenance, EXCLUDING steam - steam is costed separately "
              "via steam_cost_inr_per_kwh_th so the energy term is never "
              "double counted. Indian ZLD operating cost is reported at "
              "INR 180-350 per kilolitre treated, driven mainly by the "
              "thermal stages. We take the bottom of that band, INR 180, for "
              "the non-energy share so that our two components together stay "
              "inside the published envelope rather than exceeding it.",
    ),
    # --- published operating envelopes: VALIDATION ONLY -------------------
    # Nothing below is read by the optimiser. These are independently
    # published observations of real Indian ZLD plants, registered here so
    # tests/test_published_validation.py can assert that what our engine
    # computes lands inside the band real plants actually operate in. This
    # is the closest thing this prototype has to external ground truth and
    # it is labelled as such rather than dressed up as a measurement.
    "mee_specific_electrical_kwh_per_m3": Factor(
        key="mee_specific_electrical_kwh_per_m3",
        label="MEE parasitic electrical load per m3 evaporated",
        value=3.5,
        unit="kWh_e/m3",
        evidence="PUBLISHED",
        basis="Circulation pumps, vacuum system and condensate handling on a "
              "textile MEE train are reported at 2-5 kWh per kilolitre of "
              "evaporation; we take the midpoint, 3.5. Small against the "
              "thermal duty but real, and it is charged at the HT electrical "
              "tariff rather than the steam cost.",
    ),
    "reactive_dye_fixation_frac": Factor(
        key="reactive_dye_fixation_frac",
        label="Reactive dye fixation on cotton in exhaust dyeing",
        value=0.675,
        unit="fraction of applied dye fixed to fibre",
        evidence="PUBLISHED",
        basis="Even at the full conventional salt dose only 65-70% of "
              "reactive dye is exhausted onto the fibre; the remaining "
              "25-30% leaves as coloured effluent. Midpoint 0.675. This is "
              "why a rinse load exists at all, and why the hydrolysed-dye "
              "fraction cannot be scheduled away. Source: published "
              "reactive-dyeing exhaustion data for cellulose; reported "
              "consistently across the reactive-dye literature and in "
              "salt-free / low-salt dyeing studies that cite it as the "
              "baseline they improve on.",
        tunable=False,
    ),
    "cetp_reject_volume_frac_published": Factor(
        key="cetp_reject_volume_frac_published",
        label="Observed RO reject volume as a fraction of inlet (published)",
        value=0.25,
        unit="fraction of RO inlet volume",
        evidence="PUBLISHED",
        basis="Indian textile ZLD operators report RO reject at 20-30% of "
              "inlet volume; midpoint 0.25. VALIDATION ONLY - never read by "
              "the optimiser. tests/test_published_validation.py asserts "
              "that the reject fraction our salt-mass model computes for a "
              "realistic dyehouse lot sits inside this independently "
              "observed band.",
        tunable=False,
    ),
    "cetp_charge_inr_per_m3_distressed": Factor(
        key="cetp_charge_inr_per_m3_distressed",
        label="ZLD charge at a CETP stuck below viable utilisation",
        value=412.5,
        unit="INR/m3",
        evidence="PUBLISHED",
        basis="Tamil Nadu pollution board plant-level data: CETPs running at "
              "15% and 24% of design capacity charged members INR 450 and "
              "INR 375 per kilolitre respectively, against INR 150-220 at "
              "30% utilisation and above. Midpoint of the distressed pair = "
              "412.5. This is the UTILISATION TRAP: charges rise on an "
              "underused plant, members default or withdraw, throughput "
              "falls, charges rise again, until the plant drops below the "
              "load it needs to hold its own standards. VALIDATION AND "
              "CONTEXT ONLY - not an optimiser input. It matters because it "
              "sets the upper bound on what the downstream consequence can "
              "cost, and because a cluster in the trap is exactly the "
              "cluster where upstream demand reduction is worth the most per "
              "litre.",
        tunable=False,
    ),
    "tds_after_evaporation_mg_l_published": Factor(
        key="tds_after_evaporation_mg_l_published",
        label="Observed TDS of MEE concentrate leaving the evaporator",
        value=212384.0,
        unit="mg/L",
        evidence="PUBLISHED",
        basis="A CPCB-assessed textile unit reported 18,340 mg/L TDS "
              "entering the multiple-effect evaporator and 212,384 mg/L "
              "leaving it - an 11.6x concentration, approaching the "
              "solubility wall where the crystalliser takes over. VALIDATION "
              "AND CONTEXT ONLY. Registered because it is the clearest "
              "published demonstration that the evaporator's job is to "
              "concentrate SALT, and that its duty is therefore set by salt "
              "mass rather than by water volume.",
        tunable=False,
    ),
}


def get(key: str) -> float:
    """Return a registered coefficient value. Raises if unregistered.

    Takes REGISTRY_LOCK so a concurrent sensitivity study cannot be
    observed mid-patch.
    """
    with REGISTRY_LOCK:
        return _get_unlocked(key)


def _get_unlocked(key: str) -> float:
    if key not in FACTORS:
        raise KeyError(
            "Coefficient '{}' is not registered in core.factors. Every "
            "number used in a calculation must be registered with a unit, a "
            "basis and an evidence class.".format(key)
        )
    return FACTORS[key].value


def factor(key: str) -> Factor:
    with REGISTRY_LOCK:
        if key not in FACTORS:
            raise KeyError(
                "Coefficient '{}' is not registered in "
                "core.factors.".format(key)
            )
        return FACTORS[key]


def audit_trail() -> List[Dict[str, Any]]:
    """Full registry, for the Evidence / Data Trust screen and exports.

    Snapshotted under the lock so the screen can never render half of a
    patched registry.
    """
    with REGISTRY_LOCK:
        return [f.to_dict() for f in FACTORS.values()]


def evidence_summary() -> Dict[str, int]:
    """Count of coefficients per evidence class."""
    out: Dict[str, int] = {}
    with REGISTRY_LOCK:
        for f in FACTORS.values():
            out[f.evidence] = out.get(f.evidence, 0) + 1
    return out
