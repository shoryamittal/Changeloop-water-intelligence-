"""ClearLoop Zero-Waste Changeover Engine — Core Domain & Calculation Package.
"""
from .domain import (
    Batch, TransitionBurden, ScheduleEvaluation, OptimizationResult,
    SensorReading, ThreePointClearance, SafetyGate, SafetyLevel,
    CleaningSimulation, WaterStream, CascadeResult,
    SustainabilityLedger, ImpactRecord, AuditEvent,
    WatershedStressProfile, KNOWN_WATERSHEDS, DecisionOption,
    ResourceDecisionEvent, DataCenterWorkloadProfile
)
from .cleanability import (
    RULES, COSMETIC_PRODUCTS, generate_batches, validate_queue,
    calculate_burden, get_transition_matrix,
    PLANNING_BATCHES, PLANNING_MATRIX_SPEC, get_planning_data
)
from .optimizer import (
    evaluate_order, score_order_greedy, score_order_two_opt, optimize_schedule
)
from .safety import SafetyStateMachine
from .simulator import simulate_cleaning_cycle
from .cascade import analyze_cascade
from .impact import calculate_impact, calculate_impact_timespan_ledger
from .economics import calculate_business_case
from .audit import init_db, record_audit_event, get_audit_events
from .demo import DemoSession, get_demo_session, DEMO_STEPS
from .decision_engine import (
    evaluate_changeover_tradeoffs, create_resource_decision_event,
    evaluate_datacenter_workload
)

__all__ = [
    "Batch", "TransitionBurden", "ScheduleEvaluation", "OptimizationResult",
    "SensorReading", "ThreePointClearance", "SafetyGate", "SafetyLevel",
    "CleaningSimulation", "WaterStream", "CascadeResult",
    "SustainabilityLedger", "ImpactRecord", "AuditEvent",
    "WatershedStressProfile", "KNOWN_WATERSHEDS", "DecisionOption",
    "ResourceDecisionEvent", "DataCenterWorkloadProfile",
    "RULES", "COSMETIC_PRODUCTS", "generate_batches", "validate_queue",
    "calculate_burden", "get_transition_matrix",
    "evaluate_order", "score_order_greedy", "score_order_two_opt", "optimize_schedule",
    "SafetyStateMachine", "simulate_cleaning_cycle", "analyze_cascade",
    "calculate_impact", "calculate_impact_timespan_ledger",
    "calculate_business_case",
    "init_db", "record_audit_event", "get_audit_events",
    "DemoSession", "get_demo_session", "DEMO_STEPS",
    "evaluate_changeover_tradeoffs", "create_resource_decision_event",
    "evaluate_datacenter_workload"
]
