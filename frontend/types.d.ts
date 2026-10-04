/**
 * ClearLoop / Zero-Waste Changeover Engine — Canonical Frontend Type Definitions
 * 
 * Formal TypeScript declarations matching core domain models:
 * - Domain entities (Batch, TransitionBurden, ScheduleEvaluation, OptimizationResult)
 * - Sensor & telemetry models (SensorReading, SafetyGate, CleaningSimulation)
 * - Cascade & circular recovery models (WaterStream, CascadeResult)
 * - Sustainability & CSRD accounting ledgers (SustainabilityLedger, ImpactRecord, TimespanLedger)
 * - Durable compliance records (AuditEvent)
 */

export type SafetyLevel =
  | 'NORMAL_OPERATION'
  | 'ADVISORY_MONITORING'
  | 'ATTENTION_REQUIRED'
  | 'SAFETY_INTERLOCK_HOLD'
  | 'FAULT_LOCKOUT';

export interface Batch {
  id: string;
  family: 'care' | 'colour' | 'styling';
  shade: 'light' | 'medium' | 'dark';
  viscosity: 'low' | 'high';
  residue: 'low' | 'medium' | 'high';
  special: boolean;
  priority: number;
  deadline_h: number;
  product_name?: string;
  formulation_type?: string;
  cleanability_tier?: string;
  allergen_flag?: boolean;
}

export interface TransitionBurden {
  from: string;
  to: string;
  litres: number;
  minutes: number;
  reasons: string[];
  classification?: string;
}

export interface ScheduleEvaluation {
  order: string[];
  water_demand_l: number;
  objective: number;
  duration_min: number;
  transitions: TransitionBurden[];
}

export interface OptimizationResult {
  status: string;
  optimization_id: string;
  classification: string;
  notice: string;
  baseline: ScheduleEvaluation;
  optimized: ScheduleEvaluation;
  algorithm_used: string;
  algorithm_comparison: Record<string, { water_l: number; duration_min: number }>;
  method: string;
  baseline_retained: boolean;
}

export interface SensorReading {
  minute: number;
  conductivity: number | null;
  turbidity: number | null;
  temperature: number;
  flow: number;
  ph: number;
  stage: string;
  quality: string;
}

export interface ThreePointClearance {
  asymptotic_conductivity: boolean;
  turbidity_below_threshold: boolean;
  thermal_contact_satisfied: boolean;
}

export interface SafetyGate {
  safety_state: SafetyLevel;
  model_message: string;
  automatic_release: boolean;
  required: string;
  three_point_clearance: ThreePointClearance;
  lockout_reason: string | null;
}

export interface CleaningPhase {
  phase_id: number;
  name: string;
  duration_min: number;
  flow_rate_lpm: number;
  temp_c: number;
  purpose: string;
}

export interface CleaningSimulation {
  classification: string;
  notice: string;
  baseline_minutes: number;
  predicted_endpoint_minute: number | null;
  endpoint_probability: number;
  confidence: string;
  minutes_avoided: number;
  water_avoided_l: number;
  phases: CleaningPhase[];
  safety_gate: SafetyGate;
  readings: SensorReading[];
}

export interface WaterStream {
  stream_name: string;
  volume_l: number;
  cod_mg_l: number;
  disposition: string;
  status: string;
  tds_ppm?: number;
  ph?: number;
}

export interface CascadeResult {
  classification: string;
  notice: string;
  available_volume_l: number;
  screening: string;
  recommended_destination: string | null;
  required_checks: string[];
  streams: WaterStream[];
}

export interface SustainabilityLedger {
  water_avoided_m3: number;
  thermal_energy_avoided_kwh: number;
  thermal_energy_avoided_mwh: number;
  scope1_ghg_avoided_kg_co2e: number;
  caustic_detergent_avoided_kg: number;
  turnaround_downtime_avoided_min: number;
}

export interface ImpactRecord {
  classification: string;
  notice: string;
  common_baseline_l: number;
  prevent_incremental_l: number;
  adapt_incremental_l: number;
  adapt_requested_l: number;
  cascade_potential_l: number;
  water_demand_after_prevent_adapt_l: number;
  total_water_demand_avoided_l: number;
  sustainability_ledger: SustainabilityLedger;
  accounting_note: string;
}

export interface TimespanImpactSummary {
  timespan: '24h' | 'shift' | 'weekly' | 'annual';
  batches_processed: number;
  common_baseline_l: number;
  prevent_incremental_l: number;
  adapt_incremental_l: number;
  cascade_potential_l: number;
  water_demand_after_prevent_adapt_l: number;
  net_fresh_water_intake_l: number;
  total_demand_avoided_l: number;
  turnaround_downtime_saved_min: number;
  caustic_detergent_avoided_kg: number;
  thermal_energy_avoided_kwh: number;
  co2e_avoided_kg: number;
  water_bill_savings_eur: number;
  energy_savings_eur: number;
  total_financial_savings_eur: number;
  water_reduction_pct: number;
  avoidance_vs_recovery_isolated: boolean;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  action: string;
  detail: string;
  classification: string;
  persistence?: string;
  standard?: string;
}

export interface AppState {
  view: string;
  batches: Batch[];
  opt: OptimizationResult | null;
  clean: CleaningSimulation | null;
  water: CascadeResult | null;
  impact: ImpactRecord | null;
  impactRangeData: Record<string, TimespanImpactSummary>;
  selectedImpactRange: string;
  audit: AuditEvent[];
  seed: number;
  weight: number;
  algorithm: string;
  cleaningScenario: 'normal' | 'drift' | 'thermal' | 'spike';
  cleaningAuthorized: boolean;
  cleaningOverridden: boolean;
  cascadeAuthorized: boolean;
  cascadeOverridden: boolean;
  cascadeSimulationRunning: boolean;
  selectedCascadeStream: string;
  selectedCascadeRule: string;
  selectedPlanningShift: number | 'stress';
  baselineComparisonActive: boolean;
  activeScheduleLocked: boolean;
  soundEnabled: boolean;
}
