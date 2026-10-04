"""ClearLoop Cleanability & Transition Burden Engine.
Authoritative source of truth for pairwise cosmetic transition burdens,
rheological compatibility matrix, and synthetic cosmetic formulations.
"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union
import json
import random
import math
from .domain import Batch, TransitionBurden

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "changeover_rules.json"

def load_rules() -> Dict[str, Any]:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "classification": "ENGINEERING_ASSUMPTION",
            "base_litres_by_residue": {"low": 120, "medium": 180, "high": 260},
            "transition_multipliers": {
                "same_family": 1.0,
                "dark_to_light": 1.55,
                "viscous_to_low": 1.3,
                "special_clean": 1.7
            },
            "base_minutes_by_residue": {"low": 18, "medium": 27, "high": 40}
        }

RULES = load_rules()

COSMETIC_PRODUCTS: Dict[Tuple[str, str, str], Dict[str, str]] = {
    ("care", "light", "low"): {"name": "Hydra Genius 72H Liquid Moisturizer", "type": "Aqueous Hyaluronic Fluid", "tier": "Standard Clean"},
    ("care", "light", "high"): {"name": "Revitalift Laser X3 Day Cream", "type": "O/W Anti-Aging Emulsion", "tier": "Moderate Emulsion"},
    ("care", "medium", "low"): {"name": "Age Perfect Midnight Serum", "type": "Antioxidant Recovery Serum", "tier": "Standard Clean"},
    ("care", "medium", "high"): {"name": "Nutri-Gold Rich Nourishing Balm", "type": "Lipid-Rich W/O Balm", "tier": "Challenging Lipids"},
    ("care", "dark", "low"): {"name": "Pure Clay Charcoal Cleansing Gel", "type": "Activated Charcoal Fluid", "tier": "Moderate Pigment"},
    ("care", "dark", "high"): {"name": "Pure Clay Black Mineral Purifying Mask", "type": "Heavy Mineral Kaolin Slurry", "tier": "Severe Soil"},
    ("colour", "light", "low"): {"name": "Infaillible 24H Fresh Wear Nude #110", "type": "Light Fluid Foundation", "tier": "Moderate Pigment"},
    ("colour", "light", "high"): {"name": "True Match Super-Blendable Cream #0.5D", "type": "High-Coverage Pigment Cream", "tier": "Challenging Pigment"},
    ("colour", "medium", "low"): {"name": "Lumi Glotion Liquid Illuminator #903", "type": "Pearlescent Mica Dispersion", "tier": "Moderate Pigment"},
    ("colour", "medium", "high"): {"name": "Color Riche Satin Lipstick #120 Nude", "type": "Anhydrous Microcrystalline Wax", "tier": "Severe Wax"},
    ("colour", "dark", "low"): {"name": "Telescopic Lift Liquid Liner Deep Black", "type": "Carbon Black Polymer Dispersion", "tier": "Severe Pigment"},
    ("colour", "dark", "high"): {"name": "Infaillible Matte Resistance #500 Plum", "type": "Ultra-Matte High-Resin Paste", "tier": "Severe Pigment/Wax"},
    ("styling", "light", "low"): {"name": "Micellar Cleansing Water Normal Skin", "type": "Aqueous Micellar Surfactant", "tier": "Rapid Rinse"},
    ("styling", "light", "high"): {"name": "Elvive Dream Lengths Restoring Shampoo", "type": "Viscous Surfactant Gel", "tier": "Standard Surfactant"},
    ("styling", "medium", "low"): {"name": "Elseve Extraordinary Oil Hair Mist", "type": "Light Botanical Lipid Spray", "tier": "Moderate Lipid"},
    ("styling", "medium", "high"): {"name": "Elvive Total Repair 5 Conditioning Balm", "type": "Cationic Conditioning Emulsion", "tier": "Moderate Emulsion"},
    ("styling", "dark", "low"): {"name": "Men Expert Barber Club 3-in-1 Wash", "type": "Charcoal Infused Surfactant Gel", "tier": "Standard Surfactant"},
    ("styling", "dark", "high"): {"name": "Excellence Crème Permanent Color #1.0 Black", "type": "Alkaline Pigment Colorant Cream", "tier": "Severe Dye/Alkaline"}
}

def generate_batches(seed: int = 2030, count: int = 12) -> List[Dict[str, Any]]:
    """Generate deterministic cosmetic batch queue for simulation and demo."""
    r = random.Random(seed)
    families = ["care", "colour", "styling"]
    shades = ["light", "medium", "dark"]
    residues = ["low", "medium", "high"]
    items = []
    for i in range(count):
        fam = r.choice(families)
        shd = r.choice(shades)
        vis = r.choice(["low", "high"])
        res = r.choice(residues)
        spc = r.random() < 0.16
        pri = r.randint(1, 3)
        ddl = r.randint(10, 54)
        meta = COSMETIC_PRODUCTS.get((fam, shd, vis), {
            "name": f"L'Oréal Formula {fam.capitalize()}",
            "type": "Cosmetic Emulsion",
            "tier": "Standard"
        })
        batch_obj = Batch(
            id=f"B-{i+1:02}",
            family=fam,
            shade=shd,
            viscosity=vis,
            residue=res,
            special=spc,
            priority=pri,
            deadline_h=float(ddl),
            product_name=meta["name"],
            formulation_type=meta["type"],
            cleanability_tier=meta["tier"],
            allergen_flag=spc
        )
        items.append(batch_obj.to_dict())
    return items

def validate_queue(queue: Any) -> Optional[str]:
    """Strict structural and physical validation for incoming batch queues."""
    required = {"id", "family", "shade", "viscosity", "residue", "special", "priority", "deadline_h"}
    if not isinstance(queue, list) or not queue:
        return "No batches supplied."
    ids = []
    for batch in queue:
        if not isinstance(batch, dict) or required - set(batch):
            return "A batch is missing required fields."
        if batch["residue"] not in RULES["base_litres_by_residue"]:
            return "Unknown residue class."
        try:
            deadline = float(batch["deadline_h"])
        except (TypeError, ValueError):
            return f"Deadline is invalid for {batch.get('id', 'unknown')}."
        if not math.isfinite(deadline) or deadline < 0:
            return f"Deadline is already infeasible for {batch.get('id', 'unknown')}."
        ids.append(batch["id"])
    if len(ids) != len(set(ids)):
        return "Duplicate batch identifiers are not allowed."
    return None

def calculate_burden(a: Union[Dict[str, Any], Batch], b: Union[Dict[str, Any], Batch], rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate authoritative transition burden between product batch A and B.
    Handles dark-to-light, viscosity disparity, and allergen/special wash flags.
    """
    r = rules or RULES
    m = 1.0
    tags = []

    a_fam = a.family if isinstance(a, Batch) else a["family"]
    b_fam = b.family if isinstance(b, Batch) else b["family"]
    a_shd = a.shade if isinstance(a, Batch) else a["shade"]
    b_shd = b.shade if isinstance(b, Batch) else b["shade"]
    a_vis = a.viscosity if isinstance(a, Batch) else a["viscosity"]
    b_vis = b.viscosity if isinstance(b, Batch) else b["viscosity"]
    b_spc = b.special if isinstance(b, Batch) else b["special"]
    b_res = b.residue if isinstance(b, Batch) else b["residue"]
    from_id = a.id if isinstance(a, Batch) else a.get("id", "")
    to_id = b.id if isinstance(b, Batch) else b.get("id", "")

    if a_fam == b_fam:
        tags.append("same formula family")
    if a_shd == "dark" and b_shd == "light":
        m *= r["transition_multipliers"]["dark_to_light"]
        tags.append("dark-to-light transition")
    if a_vis == "high" and b_vis == "low":
        m *= r["transition_multipliers"]["viscous_to_low"]
        tags.append("high-to-low viscosity")
    if b_spc:
        m *= r["transition_multipliers"]["special_clean"]
        tags.append("special-cleaning flag")

    base_l = r["base_litres_by_residue"][b_res]
    base_m = r["base_minutes_by_residue"][b_res]

    burden_obj = TransitionBurden(
        from_id=from_id,
        to_id=to_id,
        litres=round(base_l * m, 1),
        minutes=round(base_m * m, 1),
        reasons=tags or ["base residue burden"],
        classification="ENGINEERING_ASSUMPTION"
    )
    return burden_obj.to_dict()

def get_transition_matrix(rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pairwise transition burden matrix across all 6 shade x viscosity combinations (36 pairs)."""
    shades = ["light", "medium", "dark"]
    viscosities = ["low", "high"]
    matrix = []
    for s_from in shades:
        for v_from in viscosities:
            for s_to in shades:
                for v_to in viscosities:
                    dummy_a = {"id": f"{s_from}-{v_from}", "family": "care", "shade": s_from, "viscosity": v_from, "residue": "medium", "special": False}
                    dummy_b = {"id": f"{s_to}-{v_to}", "family": "colour", "shade": s_to, "viscosity": v_to, "residue": "medium", "special": False}
                    b = calculate_burden(dummy_a, dummy_b, rules)
                    matrix.append({
                        "from": f"{s_from}-{v_from}",
                        "to": f"{s_to}-{v_to}",
                        "litres": b["litres"],
                        "minutes": b["minutes"],
                        "reasons": b["reasons"]
                    })
    return {"classification": "ENGINEERING_ASSUMPTION", "matrix": matrix}

PLANNING_BATCHES: Dict[str, Dict[str, Any]] = {
    "B-217": {
        "id": "B-217", "swatch": "#b91c1c", "name": "Lancôme Rouge Velvet", "code": "#PR00124 • 3,200 units",
        "family": "colour", "shade": "dark", "viscosity": "high", "residue": "high", "special": False, "priority": 1, "deadline_h": 24.0,
        "label1": "Wax Matrix", "val1": "Candelilla 14%", "label2": "CIP Wash Target", "val2": "Low Shear (Hot)",
        "label3": "Scheduled Window", "val3": "08:00–10:30 CET", "tag1": "CRITICAL COLOR", "tag1Kind": "red", "tag2": "ALLERGEN SAFE", "tag2Kind": "green"
    },
    "B-218": {
        "id": "B-218", "swatch": "#f59e0b", "name": "YSL Loveshine Nude #02", "code": "#PR00125 • 2,800 units",
        "family": "colour", "shade": "light", "viscosity": "low", "residue": "low", "special": False, "priority": 2, "deadline_h": 28.0,
        "label1": "Wax Matrix", "val1": "Ester Polymer 6%", "label2": "CIP Wash Target", "val2": "Rapid Flush",
        "label3": "Scheduled Window", "val3": "10:45–12:30 CET", "tag1": "SHADE SENSITIVE", "tag1Kind": "gold", "tag2": "RECIRC RINSE", "tag2Kind": "green"
    },
    "B-219": {
        "id": "B-219", "swatch": "#ec4899", "name": "Armani Lip Maestro Satin", "code": "#PR00126 • 1,950 units",
        "family": "colour", "shade": "medium", "viscosity": "low", "residue": "medium", "special": False, "priority": 2, "deadline_h": 32.0,
        "label1": "Carrier Matrix", "val1": "Volatile Dimethicone", "label2": "CIP Wash Target", "val2": "Organic Solvent Rinse",
        "label3": "Scheduled Window", "val3": "13:00–14:45 CET", "tag1": "SILICONE CARRIER", "tag1Kind": "purple", "tag2": "SOLVENT PURGE", "tag2Kind": "blue"
    },
    "B-220": {
        "id": "B-220", "swatch": "#18181b", "name": "Kérastase Chronologiste Black", "code": "#PR00127 • 4,500 units",
        "family": "styling", "shade": "dark", "viscosity": "high", "residue": "high", "special": True, "priority": 1, "deadline_h": 18.0,
        "label1": "Pigment System", "val1": "Carbon Black CI 77499", "label2": "CIP Wash Target", "val2": "High Temp Boil-Out",
        "label3": "Scheduled Window", "val3": "15:00–18:00 CET", "tag1": "HEAVY PIGMENT SLUG", "tag1Kind": "dark", "tag2": "STAINING RISK", "tag2Kind": "amber",
        "isAlertCard": True
    },
    "B-221": {
        "id": "B-221", "swatch": "#f472b6", "name": "Biotherm Plumping Rose", "code": "994401L • 4,000 units",
        "family": "care", "shade": "light", "viscosity": "low", "residue": "low", "special": False, "priority": 3, "deadline_h": 36.0,
        "label1": "Phase Sector", "val1": "Aqua/Oil Veil", "label2": "Clean Window", "val2": "Dry-Down Req",
        "label3": "Dispatch Target", "val3": "18:30 CET", "tag1": "POST-OP CLEAN", "tag1Kind": "gray", "tag2": "ECO WASH", "tag2Kind": "mint"
    }
}

PLANNING_MATRIX_SPEC: Dict[str, Dict[str, Dict[str, Any]]] = {
    "B-217": {
        "B-217": {"litres": 0, "minutes": 0, "val": "—", "level": "none"},
        "B-218": {"litres": 38, "minutes": 10, "val": "38 L", "level": "low"},
        "B-219": {"litres": 115, "minutes": 22, "val": "115 L", "level": "mod"},
        "B-220": {"litres": 42, "minutes": 12, "val": "42 L", "level": "low"},
        "B-221": {"litres": 390, "minutes": 52, "val": "390 L", "level": "severe"}
    },
    "B-218": {
        "B-217": {"litres": 35, "minutes": 10, "val": "35 L", "level": "low"},
        "B-218": {"litres": 0, "minutes": 0, "val": "—", "level": "none"},
        "B-219": {"litres": 30, "minutes": 8, "val": "30 L", "level": "low"},
        "B-220": {"litres": 40, "minutes": 12, "val": "40 L", "level": "low"},
        "B-221": {"litres": 370, "minutes": 48, "val": "370 L", "level": "severe"}
    },
    "B-219": {
        "B-217": {"litres": 45, "minutes": 12, "val": "45 L", "level": "low"},
        "B-218": {"litres": 35, "minutes": 10, "val": "35 L", "level": "low"},
        "B-219": {"litres": 0, "minutes": 0, "val": "—", "level": "none"},
        "B-220": {"litres": 50, "minutes": 14, "val": "50 L", "level": "low"},
        "B-221": {"litres": 340, "minutes": 42, "val": "340 L", "level": "mod"}
    },
    "B-220": {
        "B-217": {"litres": 430, "minutes": 62, "val": "430 L", "level": "severe"},
        "B-218": {"litres": 450, "minutes": 68, "val": "450 L !", "level": "severe", "isBottleneck": True},
        "B-219": {"litres": 448, "minutes": 65, "val": "448 L", "level": "severe"},
        "B-220": {"litres": 0, "minutes": 0, "val": "—", "level": "none"},
        "B-221": {"litres": 460, "minutes": 70, "val": "460 L", "level": "severe"}
    },
    "B-221": {
        "B-217": {"litres": 180, "minutes": 28, "val": "180 L", "level": "mod"},
        "B-218": {"litres": 175, "minutes": 26, "val": "175 L", "level": "mod"},
        "B-219": {"litres": 190, "minutes": 30, "val": "190 L", "level": "mod"},
        "B-220": {"litres": 160, "minutes": 24, "val": "160 L", "level": "mod"},
        "B-221": {"litres": 0, "minutes": 0, "val": "—", "level": "none"}
    }
}

def get_planning_data() -> Dict[str, Any]:
    """Expose canonical planning batch definitions and pairwise matrix to frontend."""
    return {
        "classification": "ENGINEERING_ASSUMPTION",
        "batches": PLANNING_BATCHES,
        "matrix": PLANNING_MATRIX_SPEC,
        "optimal_sequence": ["B-217", "B-218", "B-219", "B-220", "B-221"],
        "unoptimized_baseline_sequence": ["B-217", "B-220", "B-218", "B-219", "B-221"]
    }

