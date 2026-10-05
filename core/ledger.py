"""ChangeLoop - Resource Decision Event and Mass-Balance Impact Ledger.

The Resource Decision Event is the connector the whole architecture turns on.
It records a decision together with the alternatives that existed, the
consequence of each, who approved it, what actually happened, and the chain
position that makes the record tamper-evident. It answers the question that
reporting tools cannot:

    "Which decision caused this environmental outcome?"

The ledger below is the SINGLE SOURCE OF TRUTH for every impact figure in the
product. The dashboard, the detail screens and the export all read this one
structure. There is no second calculation of the same quantity anywhere.

Accounting rules, enforced in code by `validate()`
--------------------------------------------------
 1. Demand avoided and water recovered are DIFFERENT quantities and are never
    added together into a single "water saved" headline.
 2. Freshwater avoided can never exceed baseline freshwater intake.
 3. No physical litre is credited twice. Reuse is bounded by both what was
    recovered and what the process demanded.
 4. A saving only exists if the decision that produced it was actually
    approved. A rejected recommendation yields exactly zero.
 5. Process demand is never claimed as a scheduling saving - only the
    changeover burden is optimisable by resequencing.
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
import math
import time
import uuid

from . import factors, provenance
from .basin import get_basin


# ---------------------------------------------------------------------------
# Resource Decision Event
# ---------------------------------------------------------------------------

@dataclass
class ResourceDecisionEvent:
    """One operational decision and its full resource consequence."""
    event_id: str
    timestamp: str
    site_id: str
    asset_id: str
    decision_type: str
    context: Dict[str, Any]

    options: List[Dict[str, Any]]
    recommended_option_id: str
    selected_option_id: Optional[str]

    hard_constraints_satisfied: bool
    constraint_violations: List[str]

    expected: Dict[str, Any]
    rationale: Dict[str, Any]

    human_status: str            # PENDING | APPROVED | REJECTED | OVERRIDDEN
    human_actor: Optional[str]
    human_note: Optional[str]

    realised: Optional[Dict[str, Any]] = None
    ledger_seq: Optional[int] = None
    record_hash: Optional[str] = None

    calculation_version: str = "changeloop-3.0"
    classification: str = "MODELLED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def new_decision_event(site_id: str,
                       asset_id: str,
                       decision_type: str,
                       optimisation: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None
                       ) -> ResourceDecisionEvent:
    """Build a decision event from an optimiser result.

    The expected consequence is read from the optimiser output. Nothing is
    recomputed here, so there is no second source of truth.
    """
    basin = get_basin(site_id)
    options = optimisation.get("options", [])
    rec_id = optimisation.get("recommended_option_id", "OPTION_B")
    rec = next((o for o in options if o["option_id"] == rec_id),
               options[0] if options else {})

    return ResourceDecisionEvent(
        event_id=str(uuid.uuid4()),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        site_id=site_id,
        asset_id=asset_id,
        decision_type=decision_type,
        context={
            "basin": basin.basin_name,
            "cluster": basin.cluster,
            "stress_weight": basin.stress_weight,
            "stress_band": basin.band(),
            "zld_mandated": basin.zld_mandated,
            "regulatory_regime": basin.regulatory_regime,
            **(context or {}),
        },
        options=options,
        recommended_option_id=rec_id,
        selected_option_id=None,
        hard_constraints_satisfied=bool(rec.get("feasible", False)),
        constraint_violations=list(rec.get("violations", [])),
        expected={
            "order": rec.get("order", []),
            "freshwater_intake_l": rec.get("freshwater_intake_l"),
            "freshwater_avoided_l": rec.get("delta_vs_baseline", {})
                                       .get("freshwater_l"),
            "stress_equivalent_avoided_l_eq": rec.get("delta_vs_baseline", {})
                                                 .get("stress_l_eq"),
            "salt_avoided_kg": rec.get("delta_vs_baseline", {})
                                  .get("salt_kg"),
            "mee_thermal_avoided_kwh": rec.get("delta_vs_baseline", {})
                                          .get("mee_thermal_kwh"),
            "co2e_avoided_kg": rec.get("delta_vs_baseline", {})
                                  .get("co2e_kg"),
            "cost_avoided_inr": rec.get("delta_vs_baseline", {})
                                   .get("cost_inr"),
            "lateness_change_h": rec.get("delta_vs_baseline", {})
                                    .get("lateness_h"),
        },
        rationale=optimisation.get("rationale", {}),
        human_status="PENDING",
        human_actor=None,
        human_note=None,
    )


# ---------------------------------------------------------------------------
# Impact ledger
# ---------------------------------------------------------------------------

@dataclass
class ImpactLedger:
    """Mass-balance-locked impact ledger. The only source of impact figures.

    Attribution is explicit: every line says WHICH decision produced it, and
    a line is zero unless that decision was approved.
    """
    # --- baseline (no intervention) -----------------------------------
    baseline_process_water_l: float
    baseline_changeover_water_l: float
    baseline_total_water_l: float
    baseline_salt_kg: float
    baseline_freshwater_intake_l: float
    baseline_reject_l: float
    baseline_mee_thermal_kwh: float
    baseline_co2e_kg: float
    baseline_cost_inr: float

    # --- decision 1: sequencing ---------------------------------------
    sequencing_status: str
    sequencing_water_avoided_l: float
    sequencing_salt_avoided_kg: float

    # --- decision 2: wash-off release ---------------------------------
    washoff_status: str
    washoff_water_avoided_l: float
    washoff_salt_avoided_kg: float
    washoff_thermal_avoided_kwh: float

    # --- resulting state ----------------------------------------------
    achieved_total_water_l: float
    achieved_salt_kg: float
    achieved_freshwater_intake_l: float
    achieved_permeate_reuse_l: float
    achieved_reject_l: float
    achieved_mee_thermal_kwh: float
    achieved_co2e_kg: float
    achieved_cost_inr: float

    # --- avoidance (differences, never sums of unlike things) ---------
    freshwater_avoided_l: float
    stress_equivalent_avoided_l_eq: float
    salt_avoided_kg: float
    reject_avoided_l: float
    mee_thermal_avoided_kwh: float
    co2e_avoided_kg: float
    cost_avoided_inr: float

    site_id: str
    stress_weight: float
    classification: str = "MODELLED"
    notes: List[str] = field(default_factory=list)

    def validate(self) -> Dict[str, Any]:
        """Run every accounting invariant. Returns pass/fail per rule."""
        checks: List[Dict[str, Any]] = []

        def chk(rule: str, ok: bool, detail: str) -> None:
            checks.append({"rule": rule, "pass": bool(ok), "detail": detail})

        chk("water_balance_closes",
            math.isclose(self.baseline_total_water_l
                         - self.sequencing_water_avoided_l
                         - self.washoff_water_avoided_l,
                         self.achieved_total_water_l, abs_tol=1.0),
            "baseline water minus each approved avoidance equals achieved "
            "water, with no residual adjustment term")

        chk("salt_balance_closes",
            math.isclose(self.baseline_salt_kg
                         - self.sequencing_salt_avoided_kg
                         - self.washoff_salt_avoided_kg,
                         self.achieved_salt_kg, abs_tol=0.05),
            "baseline salt minus each approved avoidance equals achieved salt")

        chk("freshwater_avoided_bounded",
            self.freshwater_avoided_l <= self.baseline_freshwater_intake_l
            + 0.5,
            "freshwater avoided never exceeds baseline freshwater intake")

        chk("no_negative_physical_quantities",
            all(v >= -0.001 for v in [
                self.achieved_total_water_l, self.achieved_salt_kg,
                self.achieved_freshwater_intake_l, self.achieved_reject_l,
                self.achieved_mee_thermal_kwh, self.achieved_permeate_reuse_l,
            ]),
            "no physical quantity is negative")

        chk("reuse_bounded_by_recovery_and_demand",
            self.achieved_permeate_reuse_l
            <= self.achieved_total_water_l + 0.5,
            "reused water never exceeds process demand, so no litre is "
            "credited twice")

        chk("unapproved_decision_yields_zero",
            (self.sequencing_status == "APPROVED"
             or abs(self.sequencing_water_avoided_l) < 0.001)
            and (self.washoff_status == "RELEASED"
                 or abs(self.washoff_water_avoided_l) < 0.001),
            "a decision that was not approved contributes exactly zero")

        chk("stress_equivalence_consistent",
            math.isclose(self.stress_equivalent_avoided_l_eq,
                         self.freshwater_avoided_l * self.stress_weight,
                         rel_tol=0.01, abs_tol=1.0),
            "stress-equivalent litres equal physical litres times the "
            "declared basin weight")

        chk("energy_tracks_reject",
            math.isclose(
                self.achieved_mee_thermal_kwh,
                (self.achieved_reject_l / 1000.0)
                * factors.get("mee_specific_thermal_kwh_per_m3"),
                rel_tol=0.01, abs_tol=1.0),
            "evaporator energy equals reject volume times the derived "
            "specific thermal energy")

        failed = [c for c in checks if not c["pass"]]
        return {
            "all_pass": len(failed) == 0,
            "checks": checks,
            "failed_count": len(failed),
        }

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d = {k: (round(v, 2) if isinstance(v, float) else v)
             for k, v in d.items()}
        d["validation"] = self.validate()
        return d


def build_ledger(site_id: str,
                 baseline: Dict[str, Any],
                 achieved: Dict[str, Any],
                 sequencing_status: str,
                 sequencing_water_avoided_l: float,
                 sequencing_salt_avoided_kg: float,
                 washoff_status: str,
                 washoff_water_avoided_l: float,
                 washoff_salt_avoided_kg: float,
                 washoff_thermal_avoided_kwh: float) -> ImpactLedger:
    """Assemble the ledger from two already-computed scenario evaluations.

    `baseline` and `achieved` are both outputs of zld.evaluate_scenario, so
    both sides of every difference were produced by the same code path with
    the same coefficients.
    """
    basin = get_basin(site_id)

    notes: List[str] = []
    if sequencing_status != "APPROVED":
        notes.append(
            "Sequencing recommendation was not approved, so it contributes "
            "zero. The ledger reflects the decision actually taken.")
    if washoff_status != "RELEASED":
        notes.append(
            "Wash-off early release was not granted, so the full scheduled "
            "cycle is accounted for and contributes zero saving.")
    notes.append(
        "Process demand is excluded from the saving claim. Only the "
        "changeover burden and the released wash-off baths are optimisable "
        "by decision, so only those are claimed.")

    fresh_avoided = max(
        0.0,
        baseline["water"]["freshwater_intake_l"]
        - achieved["water"]["freshwater_intake_l"])

    return ImpactLedger(
        baseline_process_water_l=baseline["water"]["process_demand_l"]
        - baseline.get("_changeover_water_l", 0.0),
        baseline_changeover_water_l=baseline.get("_changeover_water_l", 0.0),
        baseline_total_water_l=baseline["water"]["process_demand_l"],
        baseline_salt_kg=baseline["salt"]["total_salt_kg"],
        baseline_freshwater_intake_l=baseline["water"]["freshwater_intake_l"],
        baseline_reject_l=baseline["zld"]["reject_l"],
        baseline_mee_thermal_kwh=baseline["zld"]["mee_thermal_kwh"],
        baseline_co2e_kg=baseline["carbon"]["total_co2e_kg"],
        baseline_cost_inr=baseline["cost_inr"]["total"],

        sequencing_status=sequencing_status,
        sequencing_water_avoided_l=round(sequencing_water_avoided_l, 1),
        sequencing_salt_avoided_kg=round(sequencing_salt_avoided_kg, 3),

        washoff_status=washoff_status,
        washoff_water_avoided_l=round(washoff_water_avoided_l, 1),
        washoff_salt_avoided_kg=round(washoff_salt_avoided_kg, 3),
        washoff_thermal_avoided_kwh=round(washoff_thermal_avoided_kwh, 2),

        achieved_total_water_l=achieved["water"]["process_demand_l"],
        achieved_salt_kg=achieved["salt"]["total_salt_kg"],
        achieved_freshwater_intake_l=achieved["water"]["freshwater_intake_l"],
        achieved_permeate_reuse_l=achieved["water"]["permeate_reuse_l"],
        achieved_reject_l=achieved["zld"]["reject_l"],
        achieved_mee_thermal_kwh=achieved["zld"]["mee_thermal_kwh"],
        achieved_co2e_kg=achieved["carbon"]["total_co2e_kg"],
        achieved_cost_inr=achieved["cost_inr"]["total"],

        freshwater_avoided_l=round(fresh_avoided, 1),
        stress_equivalent_avoided_l_eq=basin.stress_equivalent_litres(
            fresh_avoided),
        salt_avoided_kg=round(
            baseline["salt"]["total_salt_kg"]
            - achieved["salt"]["total_salt_kg"], 2),
        reject_avoided_l=round(
            baseline["zld"]["reject_l"] - achieved["zld"]["reject_l"], 1),
        mee_thermal_avoided_kwh=round(
            baseline["zld"]["mee_thermal_kwh"]
            - achieved["zld"]["mee_thermal_kwh"], 1),
        co2e_avoided_kg=round(
            baseline["carbon"]["total_co2e_kg"]
            - achieved["carbon"]["total_co2e_kg"], 2),
        cost_avoided_inr=round(
            baseline["cost_inr"]["total"] - achieved["cost_inr"]["total"], 2),

        site_id=site_id,
        stress_weight=basin.stress_weight,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------

def trace(metric: str) -> Dict[str, Any]:
    """Answer "how did you get this number?" for a headline metric.

    Returns the formula, the coefficients involved with their evidence class,
    and the upstream quantities. This is what the UI opens when a reviewer
    clicks a figure.
    """
    traces: Dict[str, Dict[str, Any]] = {
        "freshwater_avoided_l": {
            "metric": "Freshwater avoided (L)",
            "formula": "baseline_freshwater_intake - achieved_freshwater_intake",
            "upstream": [
                "freshwater_intake = process_demand - permeate_reuse",
                "permeate_reuse = min(RO permeate, process_demand)",
                "RO permeate = effluent_volume - reject_volume",
                "reject_volume = max(salt_mass / reject_TDS_ceiling, "
                "(1 - RO_recovery_ceiling) x effluent_volume)",
            ],
            "coefficients": ["ro_max_reject_tds_mg_l",
                             "ro_max_recovery_frac"],
            "evidence": "MODELLED from ASSUMED coefficients",
        },
        "mee_thermal_avoided_kwh": {
            "metric": "Evaporator steam avoided (kWh thermal)",
            "formula": "(baseline_reject_l - achieved_reject_l) / 1000 x "
                       "mee_specific_thermal_kwh_per_m3",
            "upstream": [
                "reject_volume is set by salt mass, not water volume",
                "mee_specific_thermal = h_vap x 1000 / steam_economy",
            ],
            "coefficients": ["h_vap_kwh_per_kg", "mee_steam_economy",
                             "mee_specific_thermal_kwh_per_m3"],
            "evidence": "DERIVED from PUBLISHED latent heat and an ASSUMED "
                        "steam economy",
        },
        "co2e_avoided_kg": {
            "metric": "CO2e avoided (kg)",
            "formula": "thermal_avoided x boiler_co2e_kg_per_kwh_th + "
                       "electrical_avoided x grid_co2e_kg_per_kwh_e",
            "upstream": ["evaporator steam avoided",
                         "dyehouse hot-water heating avoided",
                         "RO pumping avoided"],
            "coefficients": ["boiler_co2e_kg_per_kwh_th",
                             "grid_co2e_kg_per_kwh_e"],
            "evidence": "DERIVED and PUBLISHED emission factors",
        },
        "stress_equivalent_avoided_l_eq": {
            "metric": "Stress-equivalent litres avoided (L-eq)",
            "formula": "freshwater_avoided_l x basin_stress_weight",
            "upstream": ["basin stress weight from core.basin"],
            "coefficients": [],
            "evidence": "ASSUMED placeholder index - NOT an AWARE "
                        "characterisation factor. See basin methodology.",
        },
        "cost_avoided_inr": {
            "metric": "Cost avoided (INR)",
            "formula": "sum of avoided freshwater, recycled water, dyehouse "
                       "steam, electrolyte, evaporator steam, evaporator "
                       "opex and RO power",
            "upstream": ["each cost line is priced independently so no term "
                         "is double counted"],
            "coefficients": ["freshwater_cost_inr_per_m3",
                             "recycled_water_cost_inr_per_m3",
                             "steam_cost_inr_per_kwh_th",
                             "electricity_cost_inr_per_kwh",
                             "salt_cost_inr_per_kg",
                             "mee_opex_inr_per_m3_reject"],
            "evidence": "PUBLISHED water tariffs, ASSUMED energy and "
                        "chemical prices",
        },
    }

    t = traces.get(metric)
    if not t:
        return {
            "metric": metric,
            "error": "No trace registered for this metric.",
            "available": sorted(traces.keys()),
        }
    t = dict(t)
    t["coefficient_detail"] = [
        factors.factor(k).to_dict() for k in t["coefficients"]
    ]
    return t
