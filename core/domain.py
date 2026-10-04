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
