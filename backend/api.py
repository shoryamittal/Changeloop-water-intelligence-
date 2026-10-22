# -*- coding: utf-8 -*-
"""ChangeLoop - High-Performance FastAPI Application & OpenAPI Gateway.

What this is
------------
Enterprise FastAPI application for ChangeLoop: The Operating System for Industrial
Zero Liquid Discharge (ZLD) Clusters.
Exposes fully typed OpenAPI 3.1 endpoints for:
  - Shift Planning & MILP Sequence Optimization
  - Multi-Machine Shared Evaporator Cluster Load Balancing
  - Multi-Variable Ionic Calibration & Non-Invasive IoT Telemetry
  - Three-Pillar SaaS Billing & Scope-3 EU CBAM Carbon Assurance
  - Tamper-Evident HMAC-SHA256 Provenance Ledger & Interactive Tamper Test
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from pydantic import BaseModel, Field
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    BaseModel = object
    Field = lambda *args, **kwargs: None
    FastAPI = None
    HTTPException = Exception
    Request = None
    Response = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core
from core import (
    factors, basin, process, zld, telemetry, provenance, economics,
    scenarios, ledger, forecast, narrative, plant, policy,
    calibration, billing, milp,
)
from core.session import get_session
from core.optimizer import optimise_milp


if HAS_FASTAPI:
    app = FastAPI(
        title="ChangeLoop ZLD Cluster Operating System",
        description="The Operating System for Industrial Zero Liquid Discharge (ZLD) Clusters.",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for Next.js / modern web frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class TitrationInput(BaseModel):
    record_id: Optional[str] = "TITR-NEW"
    timestamp: Optional[str] = ""
    operator_id: str = "LAB-ANAND"
    sample_volume_ml: float = 50.0
    titrant_normality_n: float = 0.1000
    titre_volume_ml: float = 14.1
    blank_volume_ml: float = 0.1
    ph_measured: float = 9.8
    conductivity_us_cm: float = 18500.0
    temperature_c: float = 25.0
    calibration_slope: float = 0.68


class IonicCalibrationRequest(BaseModel):
    raw_conductivity_us_cm: float = Field(default=18500.0, description="Raw inductive conductivity (uS/cm)")
    ph: float = Field(default=9.8, description="Measured liquor pH")
    temperature_c: float = Field(default=25.0, description="Measured temperature (deg C)")
    titration: Optional[TitrationInput] = None


class BillingQuoteRequest(BaseModel):
    lots_processed: int = Field(default=10, description="Number of dye lots processed")
    salt_avoided_kg: float = Field(default=12.5, description="Avoided salt mass (kg)")
    client_total_savings_inr: float = Field(default=5834.0, description="Verified client operational savings (INR)")
    include_cbam: bool = Field(default=True, description="Enable Scope-3 CBAM carbon assurance tier")
    new_skids: int = Field(default=0, description="Count of new hardware onboarding skids")


class CBAMExportRequest(BaseModel):
    site_id: Optional[str] = None
    reporting_period: str = "OCT-2026"
    production_kg: Optional[float] = None
    co2e_avoided_kg: Optional[float] = None
    lot_ids: Optional[List[str]] = None


class MILPOptimizeRequest(BaseModel):
    mode: Optional[str] = None
    weights: Optional[Dict[str, float]] = None


class SequenceDecisionRequest(BaseModel):
    approve: bool
    actor: str = "Shift planner"
    note: Optional[str] = None


class WashoffReleaseRequest(BaseModel):
    approve: bool
    actor: str = "Quality supervisor"
    note: Optional[str] = None


class TamperTestRequest(BaseModel):
    seq: int = Field(default=1, description="Sequence number of ledger record to tamper")
    detail: str = Field(
        default="FORGED: Zero salt discharged - manually altered record",
        description="Forged payload text to inject into ledger"
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "api_version": "3.0",
        "application_version": core.__version__,
        "calculation_version": core.CALCULATION_VERSION,
        "ledger": provenance.verify_chain(),
    }


@app.get("/api/state", tags=["Session"])
def get_state():
    s = get_session()
    return s.state()


@app.get("/api/sites", tags=["Domain & Plant"])
def get_sites():
    return {
        "sites": basin.all_basins(),
        "methodology": basin.methodology(),
        "default": basin.DEFAULT_SITE,
    }


@app.get("/api/lots", tags=["Process & Sequencing"])
def get_lots():
    s = get_session()
    return {
        "lots": [l.to_dict() for l in s.lots],
        "arrival_order": s.arrival,
        "machine": process.MACHINES["JET-01"].to_dict(),
        "classification": "SIMULATED",
    }


@app.get("/api/changeover-matrix", tags=["Process & Sequencing"])
def get_changeover_matrix():
    s = get_session()
    return {
        "matrix": process.changeover_matrix(s.lots),
        "note": "Computed on request from shade depth and shade tolerance.",
    }


@app.get("/api/strategies", tags=["Process & Sequencing"])
def get_strategies():
    return {
        "strategies": {k: v.to_dict() for k, v in process.strategies().items()},
        "governing_law": "Reject volume and evaporator steam are dictated by salt mass, never by water volume.",
    }


@app.get("/api/plant", tags=["Domain & Plant"])
def get_plant_coordination(mode: str = "NORMAL", machines: Optional[int] = None, shifts: Optional[int] = None):
    s = get_session()
    modes = scenarios.constraint_modes()
    if mode not in modes:
        raise HTTPException(status_code=400, detail=f"Unknown constraint mode: {mode}")
    m = modes[mode]
    out = plant.plant_plan(
        site_id=s.site_id,
        n_machines=machines,
        shifts_per_day=shifts,
        weights=m.weights,
        constraints=m.constraints,
    )
    out["mode_id"] = m.mode_id
    out["mode_name"] = m.name
    return out


@app.post("/api/optimizer/milp", tags=["Optimization"])
def run_milp_optimizer(req: MILPOptimizeRequest):
    s = get_session()
    w = None
    c = None
    if req.mode:
        modes = scenarios.constraint_modes()
        if req.mode in modes:
            w = modes[req.mode].weights
            c = modes[req.mode].constraints
    return optimise_milp(s.lots, s.arrival, site_id=s.site_id, weights=w, constraints=c)


@app.get("/api/calibration/ionic", tags=["Ionic Calibration"])
def get_ionic_calibration_status(conductivity: float = 18500.0, ph: float = 9.8, temp: float = 25.0):
    hw = calibration.CALIBRATION_ENGINE.get_hardware_status()
    cal = calibration.CALIBRATION_ENGINE.calibrate_tds(
        raw_conductivity_us_cm=conductivity,
        ph=ph,
        temp_c=temp,
    )
    return {"hardware": hw, "calibration": cal}


@app.post("/api/calibration/ionic", tags=["Ionic Calibration"])
def perform_ionic_calibration(req: IonicCalibrationRequest):
    if req.titration:
        t_dict = req.titration.model_dump()
        rec = calibration.TitrationRecord(**t_dict)
        calibration.CALIBRATION_ENGINE.update_titration(rec)
    return calibration.CALIBRATION_ENGINE.calibrate_tds(
        raw_conductivity_us_cm=req.raw_conductivity_us_cm,
        ph=req.ph,
        temp_c=req.temperature_c,
    )


@app.get("/api/billing", tags=["Billing & CBAM"])
def get_billing_quote():
    s = get_session()
    imp = s.impact()
    salt_avoided = imp.get("avoided_consequence", {}).get("salt", {}).get("total_salt_kg", 12.5)
    cost_saved = imp.get("avoided_consequence", {}).get("cost_inr", {}).get("total", 5834.0)
    quote = billing.calculate_billing(
        lots_processed=len(s.lots),
        salt_avoided_kg=salt_avoided,
        client_total_savings_inr=cost_saved,
        include_cbam=True,
        new_skids=0,
    )
    switching = billing.evaluate_switching_thresholds()
    return {
        "quote": quote.to_dict(),
        "switching_thresholds": switching,
    }


@app.post("/api/billing", tags=["Billing & CBAM"])
def calculate_custom_billing(req: BillingQuoteRequest):
    quote = billing.calculate_billing(
        lots_processed=req.lots_processed,
        salt_avoided_kg=req.salt_avoided_kg,
        client_total_savings_inr=req.client_total_savings_inr,
        include_cbam=req.include_cbam,
        new_skids=req.new_skids,
    )
    return quote.to_dict()


@app.get("/api/cbam/export", tags=["Billing & CBAM"])
@app.post("/api/cbam/export", tags=["Billing & CBAM"])
def export_cbam_certificate(req: Optional[CBAMExportRequest] = None):
    s = get_session()
    imp = s.impact()
    co2e_avoided = imp.get("avoided_consequence", {}).get("carbon", {}).get("total_co2e_kg", 18.5)
    fabric_kg = sum(l.fabric_kg for l in s.lots)
    lot_ids = [l.lot_id for l in s.lots]

    if req:
        if req.co2e_avoided_kg is not None:
            co2e_avoided = req.co2e_avoided_kg
        if req.production_kg is not None:
            fabric_kg = req.production_kg
        if req.lot_ids is not None:
            lot_ids = req.lot_ids

    return billing.generate_cbam_certificate(
        site_id=s.site_id,
        reporting_period="OCT-2026",
        production_kg=fabric_kg,
        co2e_avoided_kg=co2e_avoided,
        lot_ids=lot_ids,
    )


@app.get("/api/ledger", tags=["Provenance Ledger"])
def get_ledger_records(limit: int = 80):
    return {
        "records": provenance.records(limit=limit),
        "integrity": provenance.verify_chain(),
    }


@app.get("/api/ledger/verify", tags=["Provenance Ledger"])
def verify_ledger_integrity():
    return provenance.verify_chain()


@app.post("/api/ledger/tamper-test", tags=["Provenance Ledger"])
def test_ledger_tamper(req: TamperTestRequest):
    res = provenance.tamper_record(seq=req.seq, new_detail=req.detail)
    integrity = provenance.verify_chain()
    return {
        "tamper_action": res,
        "post_tamper_integrity": integrity,
        "detection_confirmed": not integrity["intact"],
    }


@app.get("/api/evidence", tags=["Transparency & Evidence"])
def get_evidence_registry():
    return {
        "coefficients": factors.audit_trail(),
        "summary": factors.evidence_summary(),
        "basin_methodology": basin.methodology(),
        "release_limits": telemetry.release_limits(),
    }


@app.get("/api/policy", tags=["Policy & Scenarios"])
def get_policy(mode: str = "NORMAL"):
    s = get_session()
    modes = scenarios.constraint_modes()
    if mode not in modes:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}")
    m = modes[mode]
    out = policy.policy_levers(
        site_id=s.site_id,
        weights=m.weights,
        constraints=m.constraints,
    )
    out["mode_id"] = m.mode_id
    out["mode_name"] = m.name
    return out


@app.get("/api/forecast", tags=["Session"])
def get_forecast():
    s = get_session()
    return s.forecast()


@app.get("/api/impact", tags=["Session"])
def get_impact():
    s = get_session()
    return s.impact()


@app.post("/api/decision/sequence", tags=["Session"])
def decide_sequence(req: SequenceDecisionRequest):
    s = get_session()
    out = s.decide_sequence(req.approve, actor=req.actor, note=req.note)
    if "error" in out:
        raise HTTPException(status_code=409, detail=out["error"])
    return out


@app.post("/api/washoff/run", tags=["Wash-off Gate"])
def run_washoff(fault_mode: Optional[str] = None, lot_id: Optional[str] = None):
    s = get_session()
    out = s.run_washoff(fault_mode, lot_id)
    if "error" in out:
        raise HTTPException(status_code=400, detail=out["error"])
    return out


@app.post("/api/washoff/release", tags=["Wash-off Gate"])
def release_washoff(req: WashoffReleaseRequest):
    s = get_session()
    out = s.release_washoff(req.approve, actor=req.actor, note=req.note)
    if "error" in out:
        raise HTTPException(status_code=409, detail=out["error"])
    return out


@app.post("/api/session/reset", tags=["Session"])
def reset_session(site_id: Optional[str] = None):
    s = get_session()
    return s.reset(site_id)
