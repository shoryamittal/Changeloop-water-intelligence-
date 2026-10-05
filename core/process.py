"""ChangeLoop - Dyehouse Process Model.

Models reactive dyeing of cotton knitwear on soft-flow jet machines, which is
the dominant wet-processing route in Indian knitwear clusters.

Everything in this module is COMPUTED from the lot attributes and the
coefficient registry. There is no lookup table of pre-baked answers and no
planted bottleneck: the expensive dark-to-light changeover emerges from the
shade-tolerance arithmetic, which is exactly why it can be optimised away.

Two distinct quantities are kept rigorously separate throughout:

  PROCESS DEMAND     water and salt a lot needs regardless of sequence.
                     Not optimisable by scheduling.
  CHANGEOVER BURDEN  additional water, salt and time caused purely by the
                     ORDER in which lots are run. This is the decision
                     variable ChangeLoop acts on.

Only the changeover burden may ever be claimed as a scheduling saving.
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple
import math

from . import factors


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Machine:
    """A soft-flow jet dyeing machine."""
    machine_id: str
    name: str
    capacity_kg: float
    liquor_ratio: float          # L of bath per kg of fabric
    bath_minutes: float          # minutes for one fill/drain/treat bath

    @property
    def nominal_bath_litres(self) -> float:
        return round(self.capacity_kg * self.liquor_ratio, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["nominal_bath_litres"] = self.nominal_bath_litres
        return d


MACHINES: Dict[str, Machine] = {
    "JET-01": Machine("JET-01", "Soft-flow jet 01", 300.0, 8.0, 22.0),
    "JET-02": Machine("JET-02", "Soft-flow jet 02", 500.0, 8.5, 26.0),
}

DEFAULT_MACHINE = "JET-01"


# ---------------------------------------------------------------------------
# Shade depth -> salt and tolerance relationships
# ---------------------------------------------------------------------------

# Reactive dyeing needs electrolyte to drive dye exhaustion onto cotton, and
# the requirement rises with depth of shade. Standard dyehouse practice runs
# roughly 30 g/L for pale shades up to 80-100 g/L for navy and black.
_SALT_BASE_G_PER_L = 25.0
_SALT_PER_DEPTH_G_PER_L = 13.0

# Shade tolerance: how much carried-over colour a target shade can absorb
# before it is off-shade. A pale shade tolerates almost nothing; a black
# tolerates a great deal. Expressed in the same depth units as depth_owf.
_TOLERANCE_FLOOR = 0.04
_TOLERANCE_SLOPE = 0.11


def salt_dose_g_per_l(depth_owf: float) -> float:
    """Electrolyte dose required for a given depth of shade."""
    d = max(0.0, float(depth_owf))
    return round(_SALT_BASE_G_PER_L + _SALT_PER_DEPTH_G_PER_L * d, 1)


def shade_tolerance(depth_owf: float) -> float:
    """Carry-over colour a target shade can absorb before going off-shade."""
    d = max(0.0, float(depth_owf))
    return round(_TOLERANCE_FLOOR + _TOLERANCE_SLOPE * d, 4)


def washoff_baths(depth_owf: float) -> int:
    """Rinse/soaping baths needed to remove hydrolysed dye after dyeing.

    Deeper shades leave more unfixed hydrolysed dye and need more wash-off.
    This is PROCESS DEMAND, not changeover burden - it is not optimisable by
    resequencing and is therefore never counted as a scheduling saving.
    """
    d = max(0.0, float(depth_owf))
    return int(min(7, max(2, round(2.0 + 0.95 * d))))


# ---------------------------------------------------------------------------
# Dye lots
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DyeLot:
    """One production lot queued on a dyeing machine."""
    lot_id: str
    buyer_ref: str
    article: str
    shade_name: str
    shade_hex: str
    depth_owf: float             # % dye on weight of fabric
    dye_class: str               # reactive | disperse | vat
    fabric_kg: float
    machine_id: str
    due_h: float                 # hours from shift start
    priority: int                # 1 = firm ship date, 3 = flexible

    def validate(self) -> Optional[str]:
        if not self.lot_id:
            return "Lot id must not be empty"
        if self.dye_class not in {"reactive", "disperse", "vat"}:
            return "Unknown dye class: {}".format(self.dye_class)
        if not math.isfinite(self.depth_owf) or self.depth_owf < 0:
            return "Depth on weight of fabric must be finite and non-negative"
        if not math.isfinite(self.fabric_kg) or self.fabric_kg <= 0:
            return "Fabric weight must be finite and positive"
        if not math.isfinite(self.due_h) or self.due_h < 0:
            return "Due hour must be finite and non-negative"
        if self.machine_id not in MACHINES:
            return "Unknown machine: {}".format(self.machine_id)
        return None

    @property
    def machine(self) -> Machine:
        return MACHINES.get(self.machine_id, MACHINES[DEFAULT_MACHINE])

    @property
    def bath_litres(self) -> float:
        """Liquor volume for one bath at this lot's weight."""
        return round(self.fabric_kg * self.machine.liquor_ratio, 1)

    def process_demand(self) -> Dict[str, Any]:
        """Sequence-independent water, salt and time demand for this lot."""
        bath = self.bath_litres
        rinses = washoff_baths(self.depth_owf)
        dose = salt_dose_g_per_l(self.depth_owf)

        # One dyebath carrying the electrolyte, plus wash-off baths.
        dye_water_l = bath
        rinse_water_l = bath * rinses
        total_water_l = dye_water_l + rinse_water_l

        # All electrolyte added to the dyebath ends up in the effluent; none
        # of it is consumed by the reaction.
        salt_kg = (bath * dose) / 1000.0

        minutes = self.machine.bath_minutes * (1 + rinses)

        return {
            "lot_id": self.lot_id,
            "bath_litres": bath,
            "washoff_baths": rinses,
            "salt_dose_g_per_l": dose,
            "dye_water_l": round(dye_water_l, 1),
            "rinse_water_l": round(rinse_water_l, 1),
            "process_water_l": round(total_water_l, 1),
            "process_salt_kg": round(salt_kg, 2),
            "process_minutes": round(minutes, 1),
            "classification": "MODELLED",
        }

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["bath_litres"] = self.bath_litres
        d["salt_dose_g_per_l"] = salt_dose_g_per_l(self.depth_owf)
        d["shade_tolerance"] = shade_tolerance(self.depth_owf)
        d["washoff_baths"] = washoff_baths(self.depth_owf)
        return d


# ---------------------------------------------------------------------------
# Changeover burden - the decision variable
# ---------------------------------------------------------------------------

# Caustic / reducing agent charged into each machine-cleaning bath, which
# adds dissolved solids to the effluent and therefore evaporator load.
_CLEAN_CHEM_G_PER_L = 6.0

# A change of dye class leaves chemistry the next class cannot tolerate and
# costs one additional stripping bath regardless of shade direction.
_CLASS_CHANGE_BATHS = 1


@dataclass(frozen=True)
class Changeover:
    """Cost of running `to_lot` immediately after `from_lot`."""
    from_lot: str
    to_lot: str
    cleaning_baths: int
    water_l: float
    salt_kg: float
    minutes: float
    depth_delta: float
    tolerance: float
    direction: str               # DARK_TO_LIGHT | LIGHT_TO_DARK | LATERAL
    class_change: bool
    severity: str                # NONE | LOW | MODERATE | SEVERE
    drivers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["water_l"] = round(self.water_l, 1)
        d["salt_kg"] = round(self.salt_kg, 3)
        d["minutes"] = round(self.minutes, 1)
        return d


def changeover_burden(from_lot: DyeLot, to_lot: DyeLot) -> Changeover:
    """Compute the machine-cleaning burden between two consecutive lots.

    Physical reasoning
    ------------------
    Residual colour left in the machine after a deep shade will contaminate
    the next shade. Whether that matters depends entirely on the TARGET:

      going darker or lateral  the next shade masks the residue, so no
                               cleaning bath is required beyond the normal
                               drain. Burden is zero.
      going lighter            residue must be reduced below the target
                               shade's tolerance. Each cleaning bath removes
                               a fixed fraction of what remains, so the
                               number of baths needed grows logarithmically
                               with the ratio of carried-over depth to
                               tolerance.

    This is why the arithmetic, not a hand-authored table, produces the
    expensive dark-to-light transitions the optimiser then reorders away.
    """
    machine = to_lot.machine
    bath = machine.nominal_bath_litres

    depth_delta = round(from_lot.depth_owf - to_lot.depth_owf, 3)
    tolerance = shade_tolerance(to_lot.depth_owf)
    class_change = from_lot.dye_class != to_lot.dye_class

    drivers: List[str] = []
    baths = 0

    if depth_delta > 0:
        # Carried-over colour, as a fraction of the previous shade depth that
        # remains in the machine after a plain drain.
        carryover = from_lot.depth_owf * 0.18
        if carryover > tolerance:
            # Each cleaning bath removes ~70% of remaining residue.
            baths = int(math.ceil(math.log(carryover / tolerance) / math.log(1 / 0.30)))
            baths = max(1, min(6, baths))
            drivers.append(
                "Shade reversal: {:.2f}% -> {:.2f}% owf. Carry-over {:.3f} "
                "exceeds target tolerance {:.3f}, requiring {} cleaning "
                "bath(s).".format(
                    from_lot.depth_owf, to_lot.depth_owf, carryover,
                    tolerance, baths)
            )
        else:
            drivers.append(
                "Shade reversal within tolerance: carry-over {:.3f} is below "
                "the {:.3f} tolerance of the target shade. No cleaning bath "
                "required.".format(carryover, tolerance)
            )
        direction = "DARK_TO_LIGHT"
    elif depth_delta < 0:
        direction = "LIGHT_TO_DARK"
        drivers.append(
            "Shade progression {:.2f}% -> {:.2f}% owf. The deeper target "
            "shade masks residual colour, so no cleaning bath is "
            "required.".format(from_lot.depth_owf, to_lot.depth_owf)
        )
    else:
        direction = "LATERAL"
        drivers.append("Equal shade depth; no colour-driven cleaning required.")

    if class_change:
        baths += _CLASS_CHANGE_BATHS
        drivers.append(
            "Dye class change {} -> {} adds one stripping bath to clear "
            "incompatible auxiliary chemistry.".format(
                from_lot.dye_class, to_lot.dye_class)
        )

    water_l = baths * bath
    salt_kg = (water_l * _CLEAN_CHEM_G_PER_L) / 1000.0
    minutes = baths * machine.bath_minutes

    if baths == 0:
        severity = "NONE"
    elif baths == 1:
        severity = "LOW"
    elif baths <= 3:
        severity = "MODERATE"
    else:
        severity = "SEVERE"

    return Changeover(
        from_lot=from_lot.lot_id,
        to_lot=to_lot.lot_id,
        cleaning_baths=baths,
        water_l=water_l,
        salt_kg=salt_kg,
        minutes=minutes,
        depth_delta=depth_delta,
        tolerance=tolerance,
        direction=direction,
        class_change=class_change,
        severity=severity,
        drivers=drivers,
    )


def changeover_matrix(lots: List[DyeLot]) -> Dict[str, Dict[str, Any]]:
    """Full pairwise changeover matrix, computed on demand."""
    out: Dict[str, Dict[str, Any]] = {}
    for a in lots:
        row: Dict[str, Any] = {}
        for b in lots:
            if a.lot_id == b.lot_id:
                row[b.lot_id] = None
                continue
            row[b.lot_id] = changeover_burden(a, b).to_dict()
        out[a.lot_id] = row
    return out


# ---------------------------------------------------------------------------
# Sequence evaluation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Process strategy - the second decision dimension
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RinseStrategy:
    """A choice about HOW the wash-off is run, independent of lot ORDER.

    This dimension exists because the two available levers do NOT move
    together through the ZLD chain:

      counter-current reuse  cuts rinse WATER, leaves SALT MASS unchanged.
                             Saves freshwater, barely touches evaporator duty.
      low-salt chemistry     cuts SALT MASS, leaves rinse WATER unchanged.
                             Barely touches freshwater, cuts evaporator duty
                             substantially - because reject volume is set by
                             salt mass.

    A water-only optimiser will always choose counter-current and will
    believe it has solved the energy problem. It has not. That divergence is
    the whole reason this product needs a joint objective.
    """
    strategy_id: str
    name: str
    description: str
    water_multiplier: float
    salt_multiplier: float
    cost_inr_per_kg_fabric: float
    maturity: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def strategies() -> Dict[str, RinseStrategy]:
    cc_w = factors.get("counter_current_water_multiplier")
    cc_c = factors.get("counter_current_cost_inr_per_kg_fabric")
    ls_s = factors.get("low_salt_chemistry_salt_multiplier")
    ls_c = factors.get("low_salt_chemistry_cost_inr_per_kg_fabric")
    return {
        "CONVENTIONAL": RinseStrategy(
            strategy_id="CONVENTIONAL",
            name="Conventional single-stage rinse",
            description="Fresh water to each wash-off bath, conventional "
                        "reactive dye range. Current practice and the "
                        "baseline for every comparison.",
            water_multiplier=1.0,
            salt_multiplier=1.0,
            cost_inr_per_kg_fabric=0.0,
            maturity="Current practice",
        ),
        "COUNTER_CURRENT": RinseStrategy(
            strategy_id="COUNTER_CURRENT",
            name="Counter-current rinse cascade",
            description="Cleaner late-stage rinse liquor cascaded back to "
                        "earlier stages. Cuts rinse water. Does NOT cut the "
                        "salt mass discharged, so the evaporator sees almost "
                        "the same duty.",
            water_multiplier=cc_w,
            salt_multiplier=1.0,
            cost_inr_per_kg_fabric=cc_c,
            maturity="Established best available technique",
        ),
        "LOW_SALT": RinseStrategy(
            strategy_id="LOW_SALT",
            name="Low-electrolyte dye chemistry",
            description="Low-salt, high-fixation reactive range. Cuts the "
                        "electrolyte that sets RO reject volume, so it cuts "
                        "evaporator steam. Does NOT cut rinse water, and "
                        "carries a dye price premium.",
            water_multiplier=1.0,
            salt_multiplier=ls_s,
            cost_inr_per_kg_fabric=ls_c,
            maturity="Commercially available",
        ),
        "COMBINED": RinseStrategy(
            strategy_id="COMBINED",
            name="Counter-current cascade with low-salt chemistry",
            description="Both levers. Largest total reduction and the "
                        "highest process cost. Whether it is worth paying "
                        "for depends on the basin stress weight and the "
                        "site's steam price.",
            water_multiplier=cc_w,
            salt_multiplier=ls_s,
            cost_inr_per_kg_fabric=cc_c + ls_c,
            maturity="Both components proven; combination site-specific",
        ),
    }


DEFAULT_STRATEGY = "CONVENTIONAL"


def get_strategy(strategy_id: Optional[str]) -> RinseStrategy:
    s = strategies()
    return s.get(strategy_id or DEFAULT_STRATEGY, s[DEFAULT_STRATEGY])


def evaluate_sequence(lots: List[DyeLot], order: List[str],
                      strategy_id: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate one candidate running order on one machine.

    Returns the changeover burden (the optimisable part), the process demand
    (the non-optimisable part), and schedule lateness, all explicitly
    separated so they are never conflated in a saving claim.
    """
    index = {lot.lot_id: lot for lot in lots}
    missing = [lid for lid in order if lid not in index]
    if missing:
        raise KeyError("Unknown lot id(s) in order: {}".format(missing))

    seq = [index[lid] for lid in order]
    strategy = get_strategy(strategy_id)

    # The strategy multipliers apply to the RINSE portion of process demand
    # and to the electrolyte, not to the dyebath fill itself - a cascade
    # cannot reduce the bath the fabric has to be dyed in.
    process_water = 0.0
    process_salt = 0.0
    process_minutes = 0.0
    fabric_kg = 0.0
    for lot in seq:
        pd = lot.process_demand()
        process_water += (pd["dye_water_l"]
                          + pd["rinse_water_l"] * strategy.water_multiplier)
        process_salt += pd["process_salt_kg"] * strategy.salt_multiplier
        process_minutes += pd["process_minutes"]
        fabric_kg += lot.fabric_kg

    strategy_cost_inr = fabric_kg * strategy.cost_inr_per_kg_fabric

    transitions: List[Dict[str, Any]] = []
    changeover_water = 0.0
    changeover_salt = 0.0
    changeover_minutes = 0.0
    for i in range(len(seq) - 1):
        co = changeover_burden(seq[i], seq[i + 1])
        transitions.append(co.to_dict())
        changeover_water += co.water_l
        changeover_salt += co.salt_kg
        changeover_minutes += co.minutes

    # Lateness: walk the schedule and compare completion against due hour.
    elapsed_min = 0.0
    lateness: List[Dict[str, Any]] = []
    total_late_h = 0.0
    firm_breaches = 0
    for i, lot in enumerate(seq):
        if i > 0:
            elapsed_min += changeover_burden(seq[i - 1], lot).minutes
        elapsed_min += lot.process_demand()["process_minutes"]
        completion_h = elapsed_min / 60.0
        late_h = max(0.0, completion_h - lot.due_h)
        if late_h > 0:
            total_late_h += late_h
            if lot.priority == 1:
                firm_breaches += 1
        lateness.append({
            "lot_id": lot.lot_id,
            "completion_h": round(completion_h, 2),
            "due_h": lot.due_h,
            "late_h": round(late_h, 2),
            "priority": lot.priority,
            "breaches_firm_date": bool(late_h > 0 and lot.priority == 1),
        })

    return {
        "order": list(order),
        "strategy": strategy.to_dict(),
        "strategy_cost_inr": round(strategy_cost_inr, 2),
        "fabric_kg": round(fabric_kg, 1),
        "process_water_l": round(process_water, 1),
        "process_salt_kg": round(process_salt, 2),
        "process_minutes": round(process_minutes, 1),
        "changeover_water_l": round(changeover_water, 1),
        "changeover_salt_kg": round(changeover_salt, 3),
        "changeover_minutes": round(changeover_minutes, 1),
        "total_water_l": round(process_water + changeover_water, 1),
        "total_salt_kg": round(process_salt + changeover_salt, 2),
        "total_minutes": round(process_minutes + changeover_minutes, 1),
        "transitions": transitions,
        "lateness": lateness,
        "total_late_h": round(total_late_h, 2),
        "firm_date_breaches": firm_breaches,
        "classification": "MODELLED",
    }


# ---------------------------------------------------------------------------
# Reference order book
# ---------------------------------------------------------------------------

def reference_lots() -> List[DyeLot]:
    """The deterministic five-lot order book used by the demonstration.

    Arrival order is the sequence a planner gets from an ERP sorted by
    order-entry date, i.e. what happens with no intervention.

    Scope note (stated so the water figures are not over-read): this models
    the DYEING and WASH-OFF stages only. Pretreatment - singeing, desizing,
    scouring and bleaching - is excluded, so the litres-per-kilogram figure
    here is lower than a whole-mill specific water consumption.

    The due dates below are deliberately tight. Ascending shade sequencing
    (palest first) is standard dyehouse practice and would drive changeover
    water to zero, but here it breaches a firm ship date. That tension is
    the entire point: the real decision is constrained, and the optimiser
    has to refuse the water-minimal answer.
    """
    return [
        DyeLot(
            lot_id="L-4412",
            buyer_ref="PO-88213",
            article="Single jersey 180 gsm, combed cotton",
            shade_name="Deep Indigo",
            shade_hex="#1b2a52",
            depth_owf=4.6,
            dye_class="reactive",
            fabric_kg=285.0,
            machine_id="JET-01",
            due_h=4.0,
            priority=1,
        ),
        DyeLot(
            lot_id="L-4413",
            buyer_ref="PO-88240",
            article="Interlock 220 gsm, cotton/elastane",
            shade_name="Pale Mint",
            shade_hex="#cfe8d8",
            depth_owf=0.35,
            dye_class="reactive",
            fabric_kg=240.0,
            machine_id="JET-01",
            due_h=7.5,
            priority=2,
        ),
        DyeLot(
            lot_id="L-4414",
            buyer_ref="PO-88251",
            article="Pique 200 gsm, combed cotton",
            shade_name="Dusty Rose",
            shade_hex="#c98a95",
            depth_owf=1.6,
            dye_class="reactive",
            fabric_kg=270.0,
            machine_id="JET-01",
            due_h=10.0,
            priority=3,
        ),
        DyeLot(
            lot_id="L-4415",
            buyer_ref="PO-88262",
            article="Rib 240 gsm, combed cotton",
            shade_name="Carbon Black",
            shade_hex="#17181c",
            depth_owf=6.0,
            dye_class="reactive",
            fabric_kg=295.0,
            machine_id="JET-01",
            due_h=12.5,
            priority=3,
        ),
        DyeLot(
            lot_id="L-4416",
            buyer_ref="PO-88275",
            article="Single jersey 160 gsm, cotton",
            shade_name="Ecru Natural",
            shade_hex="#e8dfcc",
            depth_owf=0.18,
            dye_class="reactive",
            fabric_kg=230.0,
            machine_id="JET-01",
            due_h=13.0,
            priority=2,
        ),
    ]


def arrival_order() -> List[str]:
    """ERP order-entry sequence, i.e. what happens with no intervention."""
    return [lot.lot_id for lot in reference_lots()]
