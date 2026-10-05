"""ClearLoop Canonical Domain Models & Data Specifications.
Defines strongly-typed, immutable dataclasses with explicit engineering units
for all manufacturing, chemical, fluidic, and financial entities.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import math
import uuid
import time

class SafetyLevel(str, Enum):
    NORMAL = "NORMAL_OPERATION"
    ADVISORY = "ADVISORY_MONITORING"
    ATTENTION = "ATTENTION_REQUIRED"
    INTERLOCK = "SAFETY_INTERLOCK_HOLD"
    FAULT = "FAULT_LOCKOUT"

class StreamClassification(str, Enum):
    ENERGY_RECOVERY = "Energy Recovery Segregation"
    CHEMICAL_LOOP = "Internal Chemical Loop"
    UTILITY_REUSE = "Non-Product Utility Loop"
    WWTP_TREATMENT = "Biological Treatment Required"

@dataclass(frozen=True)
class Batch:
    """Canonical cosmetic batch formulation profile."""
    id: str
    family: str           # 'care', 'colour', 'styling'
    shade: str            # 'light', 'medium', 'dark'
    viscosity: str        # 'low', 'high'
    residue: str          # 'low', 'medium', 'high'
    special: bool         # allergen / high-adhesion flag
    priority: int         # 1 (high) to 3 (normal)
    deadline_h: float     # scheduling deadline in hours
    product_name: str = ""
    formulation_type: str = ""
    cleanability_tier: str = "Standard"
    allergen_flag: bool = False

    def validate(self) -> Optional[str]:
        if not self.id:
            return "Batch ID must not be empty"
        if self.family not in {"care", "colour", "styling"}:
            return f"Invalid family: {self.family}"
        if self.shade not in {"light", "medium", "dark"}:
            return f"Invalid shade: {self.shade}"
        if self.viscosity not in {"low", "high"}:
            return f"Invalid viscosity: {self.viscosity}"
        if self.residue not in {"low", "medium", "high"}:
            return f"Invalid residue: {self.residue}"
        if not math.isfinite(self.deadline_h) or self.deadline_h < 0:
            return f"Invalid deadline: {self.deadline_h}"
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class TransitionBurden:
    """Authoritative cleaning requirement between two sequenced batches."""
    from_id: str
    to_id: str
    litres: float
    minutes: float
    reasons: List[str]
    classification: str = "ENGINEERING_ASSUMPTION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "litres": round(self.litres, 1),
            "minutes": round(self.minutes, 1),
            "reasons": list(self.reasons),
            "classification": self.classification
        }

@dataclass
class ScheduleEvaluation:
    """Quantitative performance score of a sequenced batch tour."""
    order: List[str]
    water_demand_l: float
    objective: float
    duration_min: float
    transitions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "water_demand_l": round(self.water_demand_l, 1),
            "objective": round(self.objective, 1),
            "duration_min": round(self.duration_min, 1),
            "transitions": self.transitions
        }

@dataclass
class OptimizationResult:
    """Comprehensive output of an optimization execution."""
    status: str
    optimization_id: str
    baseline: ScheduleEvaluation
    optimized: ScheduleEvaluation
    algorithm_used: str
    algorithm_comparison: Dict[str, Any]
    baseline_retained: bool
    classification: str = "SYNTHETIC_DATA"
    notice: str = "Simulation — not L'Oréal production data."
    method: str = "2-Opt local search refinement with baseline safeguard"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "optimization_id": self.optimization_id,
            "classification": self.classification,
            "notice": self.notice,
            "baseline": self.baseline.to_dict(),
            "optimized": self.optimized.to_dict(),
            "algorithm_used": self.algorithm_used,
            "algorithm_comparison": self.algorithm_comparison,
            "method": self.method,
            "baseline_retained": self.baseline_retained
        }

@dataclass(frozen=True)
class SensorReading:
    """In-line telemetry observation from optical & fluidic sensors."""
    minute: int
    conductivity_ms_cm: Optional[float]
    turbidity_ntu: Optional[float]
    temp_c: float
    flow_l_min: float
    ph: float
    stage: str
    quality: str = "valid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "minute": self.minute,
            "conductivity": self.conductivity_ms_cm,
            "turbidity": self.turbidity_ntu,
            "temperature": self.temp_c,
            "flow": self.flow_l_min,
            "ph": self.ph,
            "stage": self.stage,
            "quality": self.quality
        }

@dataclass
class ThreePointClearance:
    """Quality clearance criteria before allowing early rinse termination."""
    asymptotic_conductivity: bool
    turbidity_below_threshold: bool
    thermal_contact_satisfied: bool

    def all_satisfied(self) -> bool:
        return (
            self.asymptotic_conductivity and
            self.turbidity_below_threshold and
            self.thermal_contact_satisfied
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asymptotic_conductivity": self.asymptotic_conductivity,
            "turbidity_below_threshold": self.turbidity_below_threshold,
            "thermal_contact_satisfied": self.thermal_contact_satisfied
        }

@dataclass
class SafetyGate:
    """Decision-support gatekeeper governing CIP cycle authorization."""
    state: SafetyLevel
    model_message: str
    automatic_release: bool
    required: str
    three_point_clearance: ThreePointClearance
    lockout_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safety_state": self.state.value,
            "model_message": self.model_message,
            "automatic_release": self.automatic_release,
            "required": self.required,
            "three_point_clearance": self.three_point_clearance.to_dict(),
            "lockout_reason": self.lockout_reason
        }

@dataclass
class CleaningSimulation:
    """Dynamic 4-phase physical CIP run with telemetry and endpoint prediction."""
    classification: str
    notice: str
    baseline_minutes: int
    predicted_endpoint_minute: Optional[int]
    endpoint_probability: float
    confidence: str
    minutes_avoided: int
    water_avoided_l: float
    phases: List[Dict[str, Any]]
    safety_gate: SafetyGate
    readings: List[SensorReading]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "notice": self.notice,
            "baseline_minutes": self.baseline_minutes,
            "predicted_endpoint_minute": self.predicted_endpoint_minute,
            "endpoint_probability": self.endpoint_probability,
            "confidence": self.confidence,
            "minutes_avoided": self.minutes_avoided,
            "water_avoided_l": self.water_avoided_l,
            "phases": self.phases,
            "safety_gate": self.safety_gate.to_dict(),
            "readings": [r.to_dict() for r in self.readings]
        }

@dataclass(frozen=True)
class WaterStream:
    """Segregated effluent stream in the circular cascade manifold."""
    stream_name: str
    volume_l: float
    cod_mg_l: float
    disposition: str
    status: str
    tds_ppm: Optional[float] = None
    ph: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "stream_name": self.stream_name,
            "volume_l": round(self.volume_l, 1),
            "cod_mg_l": round(self.cod_mg_l, 1),
            "disposition": self.disposition,
            "status": self.status
        }
        if self.tds_ppm is not None:
            d["tds_ppm"] = round(self.tds_ppm, 1)
        if self.ph is not None:
            d["ph"] = round(self.ph, 2)
        return d

@dataclass
class CascadeResult:
    """Circular cascade segregation assessment with quality screening."""
    classification: str
    notice: str
    available_volume_l: float
    screening: str
    recommended_destination: Optional[str]
    required_checks: List[str]
    streams: List[WaterStream]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "notice": self.notice,
            "available_volume_l": round(self.available_volume_l, 1),
            "screening": self.screening,
            "recommended_destination": self.recommended_destination,
            "required_checks": self.required_checks,
            "streams": [s.to_dict() for s in self.streams]
        }

@dataclass(frozen=True)
class SustainabilityLedger:
    """CSRD & ISO 14046 compliant environmental impact ledger."""
    water_avoided_m3: float
    thermal_energy_avoided_kwh: float
    thermal_energy_avoided_mwh: float
    scope1_ghg_avoided_kg_co2e: float
    caustic_detergent_avoided_kg: float
    turnaround_downtime_avoided_min: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "water_avoided_m3": round(self.water_avoided_m3, 3),
            "thermal_energy_avoided_kwh": round(self.thermal_energy_avoided_kwh, 2),
            "thermal_energy_avoided_mwh": round(self.thermal_energy_avoided_mwh, 4),
            "scope1_ghg_avoided_kg_co2e": round(self.scope1_ghg_avoided_kg_co2e, 2),
            "caustic_detergent_avoided_kg": round(self.caustic_detergent_avoided_kg, 2),
            "turnaround_downtime_avoided_min": round(self.turnaround_downtime_avoided_min, 1)
        }

@dataclass
class ImpactRecord:
    """Authoritative multi-dimensional resource impact accounting with strict mass-balance lock."""
    common_baseline_l: float
    prevent_incremental_l: float
    adapt_incremental_l: float
    adapt_requested_l: float
    cascade_potential_l: float
    water_demand_after_prevent_adapt_l: float
    total_water_demand_avoided_l: float
    sustainability_ledger: SustainabilityLedger
    classification: str = "MODEL_OUTPUT"
    notice: str = "Modeled synthetic scenario, not L'Oréal production data."
    accounting_note: str = "Cascade is reported separately as potential reuse and is not added to water-demand avoidance."

    def validate_mass_balance(self) -> bool:
        """Enforce strict invariant: gross consumed minus cascade reclaim equals net fresh intake."""
        gross = self.common_baseline_l - self.prevent_incremental_l - self.adapt_incremental_l
        return math.isclose(gross, self.water_demand_after_prevent_adapt_l, abs_tol=0.1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "notice": self.notice,
            "common_baseline_l": round(self.common_baseline_l, 1),
            "prevent_incremental_l": round(self.prevent_incremental_l, 1),
            "adapt_incremental_l": round(self.adapt_incremental_l, 1),
            "adapt_requested_l": round(self.adapt_requested_l, 1),
            "cascade_potential_l": round(self.cascade_potential_l, 1),
            "water_demand_after_prevent_adapt_l": round(self.water_demand_after_prevent_adapt_l, 1),
            "total_water_demand_avoided_l": round(self.total_water_demand_avoided_l, 1),
            "sustainability_ledger": self.sustainability_ledger.to_dict(),
            "accounting_note": self.accounting_note
        }

@dataclass
class AuditEvent:
    """GAMP 5 & 21 CFR Part 11 compliant durable audit record."""
    event_id: str
    timestamp: str
    action: str
    detail: str
    classification: str = "SIMULATED"
    persistence: str = "sqlite"

    @classmethod
    def create(cls, action: str, detail: str) -> "AuditEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            action=action,
            detail=detail,
            classification="SIMULATED"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ======================================================================
# SANKALP CLIMATE EDITION — RESOURCE DECISION ARCHITECTURE EXTENSIONS
# ======================================================================

@dataclass(frozen=True)
class WatershedStressProfile:
    """Local basin hydrological scarcity index (WRI Aqueduct 4.0 / AWARE)."""
    site_id: str
    site_name: str
    basin_name: str
    wri_category: str                  # e.g., "Low", "Low-Medium", "High", "Extremely High"
    aware_factor: float                # 1.0 (baseline) to 42.0+ (extreme scarcity)
    water_cost_eur_per_m3: float
    municipal_quota_m3_day: float
    description: str

    def calculate_stress_equated_litres(self, litres: float) -> float:
        """Convert physical consumption litres into watershed-scarcity-equated litres (L-eq)."""
        return round(litres * self.aware_factor, 1)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


KNOWN_WATERSHEDS: Dict[str, WatershedStressProfile] = {
    "FR-AULNAY-04": WatershedStressProfile(
        site_id="FR-AULNAY-04",
        site_name="L'Oréal Aulnay Excellence Hub",
        basin_name="Seine-Normandie Basin",
        wri_category="Low-Medium Stress",
        aware_factor=1.2,
        water_cost_eur_per_m3=3.85,
        municipal_quota_m3_day=85.0,
        description="Temperate catchment; moderate seasonal drought pressure during July-August."
    ),
    "ES-BURGOS-01": WatershedStressProfile(
        site_id="ES-BURGOS-01",
        site_name="L'Oréal Burgos Dry Factory",
        basin_name="Duero River Basin",
        wri_category="High Water Stress",
        aware_factor=3.4,
        water_cost_eur_per_m3=5.40,
        municipal_quota_m3_day=45.0,
        description="Mediterranean dry catchment; strict regional quotas; 100% industrial water loop required."
    ),
    "IT-SETTIMO-02": WatershedStressProfile(
        site_id="IT-SETTIMO-02",
        site_name="L'Oréal Settimo Torinese Plant",
        basin_name="Po River Catchment",
        wri_category="Low Stress (Alpine Feed)",
        aware_factor=1.0,
        water_cost_eur_per_m3=2.90,
        municipal_quota_m3_day=110.0,
        description="Alpine glacial recharge; low baseline scarcity; primary focus on chemical COD segregation."
    ),
    "BE-VORSELAAR-01": WatershedStressProfile(
        site_id="BE-VORSELAAR-01",
        site_name="L'Oréal Vorselaar Plant",
        basin_name="Scheldt River Basin",
        wri_category="High Water Stress",
        aware_factor=3.1,
        water_cost_eur_per_m3=6.10,
        municipal_quota_m3_day=40.0,
        description="High population density and low groundwater recharge rate; high effluent discharge tariffs."
    ),
    "US-PHOENIX-DC01": WatershedStressProfile(
        site_id="US-PHOENIX-DC01",
        site_name="Hyperscale AI Data Center West-1",
        basin_name="Lower Colorado River Basin",
        wri_category="Extremely High Stress",
        aware_factor=8.5,
        water_cost_eur_per_m3=8.20,
        municipal_quota_m3_day=120.0,
        description="Severe arid watershed; Tier-1 Colorado River shortage declaration; evaporative cooling strictly constrained."
    )
}


@dataclass
class DecisionOption:
    """Rigorous multi-resource trade-off option presented to human supervisor."""
    option_id: str                      # "OPTION_A" | "OPTION_B" | "OPTION_C"
    title: str
    description: str
    water_l: float
    freshwater_l: float
    water_stress_l_eq: float
    energy_kwh: float
    carbon_kg_co2e: float
    cost_eur: float
    schedule_delay_min: float
    operational_risk: str               # "LOW" | "BALANCED" | "TIGHT_SLA" | "HIGH_BURDEN"
    is_recommended: bool
    tradeoff_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceDecisionEvent:
    """Canonical Resource Decision Event answering:
    'Which operational decision caused this environmental outcome,
    what alternatives existed, and how was it verified?'
    """
    event_id: str
    timestamp: str
    site: str
    asset: str
    context: Dict[str, Any]
    decision_type: str                  # e.g., "BATCH_SEQUENCE_OPTIMIZATION", "CIP_OPTICAL_CUTOFF", "CASCADE_SEGREGATION"
    selected_option_id: str
    alternatives: List[DecisionOption]
    hard_constraints_satisfied: bool
    expected_water_l: float
    expected_freshwater_l: float
    watershed_stress_multiplier: float
    expected_water_stress_impact_l_eq: float
    expected_energy_kwh: float
    expected_carbon_kg_co2e: float
    expected_cost_eur: float
    operational_risk: str
    recommendation: str
    rationale: str
    confidence_score: float
    human_validation_status: str        # "PENDING" | "VALIDATED" | "OVERRIDDEN" | "REJECTED"
    operator_id: str
    water_recovered_l: float
    water_reused_l: float
    final_net_impact: Dict[str, Any]
    provenance_hash: str
    provenance_signature: str
    calculation_version: str = "v2.6-Sankalp"
    classification: str = "MODEL_OUTPUT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "site": self.site,
            "asset": self.asset,
            "context": self.context,
            "decision_type": self.decision_type,
            "selected_option_id": self.selected_option_id,
            "alternatives": [a.to_dict() for a in self.alternatives],
            "hard_constraints_satisfied": self.hard_constraints_satisfied,
            "expected_water_l": round(self.expected_water_l, 1),
            "expected_freshwater_l": round(self.expected_freshwater_l, 1),
            "watershed_stress_multiplier": round(self.watershed_stress_multiplier, 2),
            "expected_water_stress_impact_l_eq": round(self.expected_water_stress_impact_l_eq, 1),
            "expected_energy_kwh": round(self.expected_energy_kwh, 2),
            "expected_carbon_kg_co2e": round(self.expected_carbon_kg_co2e, 2),
            "expected_cost_eur": round(self.expected_cost_eur, 2),
            "operational_risk": self.operational_risk,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "confidence_score": round(self.confidence_score, 3),
            "human_validation_status": self.human_validation_status,
            "operator_id": self.operator_id,
            "water_recovered_l": round(self.water_recovered_l, 1),
            "water_reused_l": round(self.water_reused_l, 1),
            "final_net_impact": self.final_net_impact,
            "provenance_hash": self.provenance_hash,
            "provenance_signature": self.provenance_signature,
            "calculation_version": self.calculation_version,
            "classification": self.classification
        }


@dataclass(frozen=True)
class DataCenterWorkloadProfile:
    """Secondary vertical: AI Data Center thermal & cooling workload dispatch."""
    workload_id: str
    model_type: str                     # "LLM Pre-training", "Inference Batch", "Embedding Indexing", "Fine-Tuning"
    gpu_cluster: str                    # "8x H100 SXM5", "64x H100 SXM5"
    duration_h: float
    power_draw_kw: float
    thermal_load_kwh: float
    cooling_mode: str                   # "Direct Evaporative", "Dry Hybrid Closed-Loop", "Direct-to-Chip Liquid"
    wue_l_per_kwh: float                # Water Usage Effectiveness
    pue: float                          # Power Usage Effectiveness
    direct_water_l: float
    indirect_water_l: float
    total_water_l: float
    carbon_kg_co2e: float
    cost_eur: float
    flexible_deferral_h: float
    dispatch_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

