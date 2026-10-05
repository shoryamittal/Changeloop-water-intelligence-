"""ChangeLoop - Zero Liquid Discharge Consequence Chain.

This module is the core of the product. It converts an upstream dyehouse
decision into the downstream consequence that nobody currently prices.

The chain
---------
    effluent volume + salt mass
        -> effluent TDS
        -> reverse osmosis split (permeate / reject)
        -> permeate reused as process water      (freshwater avoided)
        -> reject evaporated in the MEE          (steam, fuel, CO2e)
        -> recovered salt / solid reject
        -> cost

The one equation that matters
-----------------------------
Salt is conserved. It is not destroyed by RO, by biology or by evaporation.
The final RO stage can only concentrate up to a ceiling TDS before osmotic
pressure and scaling stop it. So, by salt mass conservation:

    V_reject  =  M_salt / C_reject_max

Reject volume is set by SALT MASS, not by water volume. And evaporator steam
is proportional to reject volume. Therefore:

    *** Saving water without saving salt does not save evaporator energy. ***

A water-only dashboard cannot see this. It is the reason a scheduling change
that cuts rinse volume but leaves electrolyte dosing untouched produces far
less ZLD energy benefit than its water headline suggests - and the reason
cutting machine-cleaning baths, which carry both water AND chemical load,
produces more benefit than its water headline suggests.

A hydraulic floor also applies: the RO array cannot physically recover more
than its hydraulic recovery ceiling, so

    V_reject = max( M_salt / C_reject_max , (1 - r_max) * V )

whichever constraint binds. The system reports WHICH constraint bound, so a
reviewer can see whether a given stream is salt-limited or hydraulically
limited - and therefore whether salt reduction or water reduction is the
lever that will actually help.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import math

from . import factors
from .basin import Basin, get_basin


@dataclass(frozen=True)
class ZLDResult:
    """Full ZLD mass and energy balance for one effluent stream."""
    # Inputs
    effluent_volume_l: float
    salt_mass_kg: float
    effluent_tds_mg_l: float

    # RO split
    permeate_l: float
    reject_l: float
    ro_recovery_frac: float
    reject_tds_mg_l: float
    binding_constraint: str          # SALT_BALANCE | RO_HYDRAULIC

    # Energy
    ro_electrical_kwh: float
    mee_thermal_kwh: float
    total_energy_kwh_equivalent: float

    # Emissions
    ro_co2e_kg: float
    mee_co2e_kg: float
    total_co2e_kg: float

    # Solids
    recovered_solids_kg: float

    # Cost
    mee_steam_cost_inr: float
    mee_opex_cost_inr: float
    ro_power_cost_inr: float
    total_zld_cost_inr: float

    classification: str = "MODELLED"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: (round(v, 3) if isinstance(v, float) else v)
                for k, v in d.items()}

    def check_mass_balance(self, tol: float = 0.01) -> bool:
        """Water in must equal permeate plus reject."""
        return math.isclose(
            self.effluent_volume_l,
            self.permeate_l + self.reject_l,
            rel_tol=tol, abs_tol=0.5,
        )

    def check_salt_balance(self, tol: float = 0.02) -> bool:
        """Salt in must equal salt out in the reject (permeate ~ salt free).

        We allow a small tolerance for the permeate salt passage we neglect.
        """
        salt_out = (self.reject_l * self.reject_tds_mg_l) / 1e6
        if self.salt_mass_kg <= 0:
            return salt_out <= 0.001
        return salt_out <= self.salt_mass_kg * (1.0 + tol) + 0.001


def treat(effluent_volume_l: float,
          salt_mass_kg: float,
          site_id: Optional[str] = None) -> ZLDResult:
    """Run one effluent stream through the ZLD chain.

    Args:
        effluent_volume_l: water sent to the treatment plant, litres.
        salt_mass_kg: dissolved solids carried in that water, kilograms.
        site_id: used only for cost/basin context, not for the physics.
    """
    v = max(0.0, float(effluent_volume_l))
    m_salt = max(0.0, float(salt_mass_kg))

    if not math.isfinite(v) or not math.isfinite(m_salt):
        raise ValueError("Effluent volume and salt mass must be finite.")

    c_rej_max = factors.get("ro_max_reject_tds_mg_l")
    r_max = factors.get("ro_max_recovery_frac")

    tds = (m_salt * 1e6 / v) if v > 0 else 0.0

    # --- the two competing constraints on reject volume ---------------
    reject_from_salt = (m_salt * 1e6) / c_rej_max if c_rej_max > 0 else 0.0
    reject_from_hydraulics = (1.0 - r_max) * v

    if reject_from_salt >= reject_from_hydraulics:
        reject = reject_from_salt
        binding = "SALT_BALANCE"
    else:
        reject = reject_from_hydraulics
        binding = "RO_HYDRAULIC"

    reject = min(reject, v)          # cannot reject more than was fed
    permeate = max(0.0, v - reject)
    recovery = (permeate / v) if v > 0 else 0.0
    reject_tds = (m_salt * 1e6 / reject) if reject > 0 else 0.0

    # --- energy -------------------------------------------------------
    ro_kwh = (v / 1000.0) * factors.get("ro_specific_electrical_kwh_per_m3")
    mee_kwh = (reject / 1000.0) * factors.get(
        "mee_specific_thermal_kwh_per_m3")

    # --- emissions ----------------------------------------------------
    ro_co2 = ro_kwh * factors.get("grid_co2e_kg_per_kwh_e")
    mee_co2 = mee_kwh * factors.get("boiler_co2e_kg_per_kwh_th")

    # --- solids -------------------------------------------------------
    # Everything dissolved ends up as solid once the water is evaporated.
    solids = m_salt

    # --- cost ---------------------------------------------------------
    steam_cost = mee_kwh * factors.get("steam_cost_inr_per_kwh_th")
    mee_opex = (reject / 1000.0) * factors.get("mee_opex_inr_per_m3_reject")
    ro_power_cost = ro_kwh * factors.get("electricity_cost_inr_per_kwh")

    return ZLDResult(
        effluent_volume_l=v,
        salt_mass_kg=m_salt,
        effluent_tds_mg_l=tds,
        permeate_l=permeate,
        reject_l=reject,
        ro_recovery_frac=recovery,
        reject_tds_mg_l=reject_tds,
        binding_constraint=binding,
        ro_electrical_kwh=ro_kwh,
        mee_thermal_kwh=mee_kwh,
        # Reported separately as well as combined, because thermal and
        # electrical kWh are not interchangeable. The combined figure is a
        # site-energy total, clearly labelled as such in the UI.
        total_energy_kwh_equivalent=ro_kwh + mee_kwh,
        ro_co2e_kg=ro_co2,
        mee_co2e_kg=mee_co2,
        total_co2e_kg=ro_co2 + mee_co2,
        recovered_solids_kg=solids,
        mee_steam_cost_inr=steam_cost,
        mee_opex_cost_inr=mee_opex,
        ro_power_cost_inr=ro_power_cost,
        total_zld_cost_inr=steam_cost + mee_opex + ro_power_cost,
    )


# ---------------------------------------------------------------------------
# Freshwater accounting
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WaterAccount:
    """Closed freshwater account for one scenario.

    The six quantities below are DEFINED here once and are never used
    interchangeably anywhere in the codebase:

      process_demand_l     water the process must receive, from any source.
      permeate_reuse_l     recovered water actually fed back. Bounded by both
                           what was recovered and what the process demands.
      freshwater_intake_l  demand that reuse could not cover. The only figure
                           that represents new abstraction from the basin.
      evaporative_loss_l   water destroyed in the evaporator. Leaves the
                           system as vapour; it is not available for reuse.
      demand_avoided_l     reduction in process_demand versus the baseline
                           caused by a decision. NOT a recovery figure.
      freshwater_avoided_l reduction in freshwater_intake versus the
                           baseline. This is the headline climate number and
                           it is always <= baseline freshwater_intake.
    """
    process_demand_l: float
    permeate_reuse_l: float
    freshwater_intake_l: float
    evaporative_loss_l: float
    recovery_frac_of_demand: float

    def to_dict(self) -> Dict[str, Any]:
        return {k: round(v, 1) if isinstance(v, float) else v
                for k, v in asdict(self).items()}

    def check_closes(self, tol: float = 0.5) -> bool:
        """Demand must be met exactly by reuse plus fresh intake."""
        return math.isclose(
            self.process_demand_l,
            self.permeate_reuse_l + self.freshwater_intake_l,
            abs_tol=tol,
        )


def account_for_water(process_demand_l: float,
                      zld: ZLDResult) -> WaterAccount:
    """Close the freshwater account for a scenario.

    Reuse is bounded twice, which is what prevents the classic double count:
      - you cannot reuse more than the RO actually produced, and
      - you cannot reuse more than the process actually needs.
    """
    demand = max(0.0, float(process_demand_l))
    reuse = min(zld.permeate_l, demand)
    intake = max(0.0, demand - reuse)
    return WaterAccount(
        process_demand_l=demand,
        permeate_reuse_l=reuse,
        freshwater_intake_l=intake,
        evaporative_loss_l=zld.reject_l,
        recovery_frac_of_demand=(reuse / demand) if demand > 0 else 0.0,
    )


# ---------------------------------------------------------------------------
# Scenario roll-up
# ---------------------------------------------------------------------------

def evaluate_scenario(process_water_l: float,
                      process_salt_kg: float,
                      changeover_water_l: float,
                      changeover_salt_kg: float,
                      site_id: Optional[str] = None) -> Dict[str, Any]:
    """Full water -> salt -> ZLD -> energy -> carbon -> cost evaluation.

    Takes the process demand and the changeover burden separately so the
    ledger can attribute the result to the decision rather than to the
    process, then treats their sum because the treatment plant sees one
    combined stream.
    """
    basin = get_basin(site_id or "")

    total_water = max(0.0, process_water_l) + max(0.0, changeover_water_l)
    total_salt = max(0.0, process_salt_kg) + max(0.0, changeover_salt_kg)

    zld = treat(total_water, total_salt, site_id)
    account = account_for_water(total_water, zld)

    # Dyehouse-side thermal load: the hot rinse / soaping water itself.
    heat_kwh = (
        total_water
        * factors.get("water_heating_kwh_per_l_per_k")
        * factors.get("rinse_delta_t_k")
    )
    heat_co2 = heat_kwh * factors.get("boiler_co2e_kg_per_kwh_th")
    heat_cost = heat_kwh * factors.get("steam_cost_inr_per_kwh_th")

    # In a closed-loop plant the process is fed from TWO sources at very
    # different prices: recycled permeate (expensive, because someone paid to
    # treat it) and freshwater makeup (cheap by comparison). Costing them at
    # one blended rate hides the central economic fact of ZLD, so they are
    # priced separately.
    fresh_cost = (account.freshwater_intake_l / 1000.0) * factors.get(
        "freshwater_cost_inr_per_m3")
    reuse_cost = (account.permeate_reuse_l / 1000.0) * factors.get(
        "recycled_water_cost_inr_per_m3")
    salt_cost = total_salt * factors.get("salt_cost_inr_per_kg")

    total_cost = (
        zld.total_zld_cost_inr + heat_cost + fresh_cost + reuse_cost
        + salt_cost
    )

    return {
        "site_id": basin.site_id,
        "basin": basin.to_dict(),

        "water": account.to_dict(),
        "stress_equivalent_l_eq": basin.stress_equivalent_litres(
            account.freshwater_intake_l),

        "salt": {
            "process_salt_kg": round(process_salt_kg, 2),
            "changeover_salt_kg": round(changeover_salt_kg, 3),
            "total_salt_kg": round(total_salt, 2),
        },

        "zld": zld.to_dict(),

        "energy": {
            "dyehouse_thermal_kwh": round(heat_kwh, 1),
            "ro_electrical_kwh": round(zld.ro_electrical_kwh, 1),
            "mee_thermal_kwh": round(zld.mee_thermal_kwh, 1),
            "total_site_energy_kwh": round(
                heat_kwh + zld.ro_electrical_kwh + zld.mee_thermal_kwh, 1),
            "note": "Thermal and electrical kWh are reported separately "
                    "because they are not interchangeable. The total is a "
                    "site-energy figure, not a primary-energy figure.",
        },

        "carbon": {
            "dyehouse_thermal_co2e_kg": round(heat_co2, 2),
            "ro_electrical_co2e_kg": round(zld.ro_co2e_kg, 2),
            "mee_thermal_co2e_kg": round(zld.mee_co2e_kg, 2),
            "total_co2e_kg": round(
                heat_co2 + zld.ro_co2e_kg + zld.mee_co2e_kg, 2),
        },

        "cost_inr": {
            "freshwater": round(fresh_cost, 2),
            "recycled_water": round(reuse_cost, 2),
            "dyehouse_steam": round(heat_cost, 2),
            "electrolyte": round(salt_cost, 2),
            "zld_steam": round(zld.mee_steam_cost_inr, 2),
            "zld_opex": round(zld.mee_opex_cost_inr, 2),
            "ro_power": round(zld.ro_power_cost_inr, 2),
            "total": round(total_cost, 2),
        },

        "classification": "MODELLED",
    }


def sensitivity_salt_vs_water() -> Dict[str, Any]:
    """Demonstrate the central insight numerically.

    Takes one stream and cuts 20% of the water alone, then 20% of the salt
    alone, and reports what each does to evaporator energy. This is the proof
    behind the claim and it is computed live, not asserted.
    """
    base_v, base_m = 60000.0, 700.0

    base = treat(base_v, base_m)
    water_only = treat(base_v * 0.8, base_m)
    salt_only = treat(base_v, base_m * 0.8)
    both = treat(base_v * 0.8, base_m * 0.8)

    def delta(r: ZLDResult) -> float:
        if base.mee_thermal_kwh <= 0:
            return 0.0
        return round(
            (r.mee_thermal_kwh - base.mee_thermal_kwh)
            / base.mee_thermal_kwh * 100.0, 1)

    return {
        "baseline": {
            "volume_l": base_v,
            "salt_kg": base_m,
            "reject_l": round(base.reject_l, 1),
            "mee_thermal_kwh": round(base.mee_thermal_kwh, 1),
            "binding_constraint": base.binding_constraint,
        },
        "cut_water_20pct_only": {
            "reject_l": round(water_only.reject_l, 1),
            "mee_thermal_kwh": round(water_only.mee_thermal_kwh, 1),
            "mee_energy_change_pct": delta(water_only),
            "binding_constraint": water_only.binding_constraint,
        },
        "cut_salt_20pct_only": {
            "reject_l": round(salt_only.reject_l, 1),
            "mee_thermal_kwh": round(salt_only.mee_thermal_kwh, 1),
            "mee_energy_change_pct": delta(salt_only),
            "binding_constraint": salt_only.binding_constraint,
        },
        "cut_both_20pct": {
            "reject_l": round(both.reject_l, 1),
            "mee_thermal_kwh": round(both.mee_thermal_kwh, 1),
            "mee_energy_change_pct": delta(both),
            "binding_constraint": both.binding_constraint,
        },
        "interpretation": (
            "While the stream is salt-limited, evaporator energy tracks salt "
            "mass and is almost indifferent to water volume. Cutting water "
            "alone concentrates the same salt into less water and moves the "
            "evaporator load hardly at all. This is why ChangeLoop optimises "
            "the joint water-and-salt objective instead of a water headline."
        ),
        "classification": "DERIVED",
    }
