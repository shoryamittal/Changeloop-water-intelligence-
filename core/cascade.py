"""ClearLoop Circular Water Cascade & Segregation Engine.
Models 3-stream circular separation (L'Oréal Waterloop plant standard):
Pre-rinse biogas energy recovery, caustic buffer loop, and final permeate utility reuse.
"""
from typing import Dict, Any, List
from .domain import CascadeResult, WaterStream

def analyze_cascade(body: Dict[str, Any]) -> Dict[str, Any]:
    """Segregate and screen industrial wash effluent into 3 closed-loop circular streams."""
    try:
        volume = float(body.get("volume_l", 120))
    except (TypeError, ValueError):
        volume = -1.0
    quality_flag = body.get("quality", "unknown")

    if volume < 0:
        return {
            "classification": "ILLUSTRATIVE_SCENARIO",
            "notice": "Simulation — not L'Oréal production data.",
            "screening": "INSUFFICIENT INFORMATION",
            "available_volume_l": 0.0,
            "recommended_destination": None,
            "required_checks": ["Correct invalid negative volume before screening"],
            "streams": []
        }

    if quality_flag == "unknown":
        status = "INSUFFICIENT INFORMATION"
    elif quality_flag == "screened":
        status = "POTENTIALLY REUSABLE SUBJECT TO VALIDATION"
    else:
        status = "TREATMENT REQUIRED"

    # 3-Stream Circular Segregation Architecture
    s1 = WaterStream(
        stream_name="Stream 1: Pre-Rinse First-Flush",
        volume_l=round(volume * 0.35, 1),
        cod_mg_l=12500.0,
        disposition="Diverted to Biogas Anaerobic Digestion (Methane Energy Recovery)",
        status="Energy Recovery Segregation"
    )
    s2 = WaterStream(
        stream_name="Stream 2: Caustic Wash Recovery",
        volume_l=round(volume * 0.45, 1),
        cod_mg_l=2800.0,
        disposition="CIP Skid Caustic Buffer Tank (Filtered & Re-dosed for next cycle)",
        status="Internal Chemical Loop"
    )
    s3 = WaterStream(
        stream_name="Stream 3: Final Rinse Permeate",
        volume_l=volume,
        cod_mg_l=28.0,
        tds_ppm=160.0,
        ph=7.1,
        disposition="Non-product-contact utility use (Cooling Towers / Scrubbers / Boiler Pre-feed)",
        status=status
    )

    result = CascadeResult(
        classification="ILLUSTRATIVE_SCENARIO",
        notice="Simulation — not L'Oréal production data. No reuse is approved.",
        available_volume_l=volume,
        screening=status,
        recommended_destination="Non-product-contact utility use — illustrative only" if status.startswith("POTENTIALLY") else None,
        required_checks=[
            "site water-quality criteria (COD < 50 mg/L, TDS < 200 ppm)",
            "regulatory review & ATEX compliance",
            "microbiological barrier & cross-contamination review",
            "human approval & quality release authorization"
        ],
        streams=[s1, s2, s3]
    )
    return result.to_dict()
