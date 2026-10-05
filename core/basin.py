"""ChangeLoop - Basin Water-Stress Weighting.

Why this module exists
----------------------
One litre is not environmentally equal to another litre. A litre abstracted
from a seasonal river in a water-short district during the dry months carries
a different consequence from a litre abstracted from a perennial alpine-fed
river. Life-cycle practice handles this with a scarcity characterisation
factor (AWARE) or a baseline-water-stress band (WRI Aqueduct), producing
"stress-equivalent litres".

Honesty boundary - read this before quoting any number from this module
----------------------------------------------------------------------
We do NOT ship licensed AWARE characterisation factors or Aqueduct raster
values, and we do not claim to. What we ship is an explicit, arithmetically
transparent *placeholder* index, documented below, that occupies the exact
slot a site-licensed factor would occupy. `methodology()` renders this
disclosure into the UI next to every stress-equivalent figure.

The placeholder index
---------------------
    stress_weight = (1 - renewable_availability_index)
                    x seasonality_penalty
                    x abstraction_pressure

  renewable_availability_index  0..1, higher = more reliable renewable supply
  seasonality_penalty          1.0 perennial .. 2.0 strongly seasonal / no
                               dry-weather dilution flow
  abstraction_pressure         1.0 .. 2.0, groundwater development stage and
                               competing municipal/agricultural demand

The result is normalised so a notional unstressed perennial basin scores 1.0.
It is an ordering device for comparing sites inside this prototype, not a
published characterisation factor, and it must be replaced with a licensed
factor before any external impact claim is made.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass(frozen=True)
class Basin:
    """A production site and the water body it depends on."""
    site_id: str
    site_name: str
    cluster: str
    basin_name: str
    state: str
    regulatory_regime: str
    renewable_availability_index: float   # 0..1
    seasonality_penalty: float            # 1.0 .. 2.0
    abstraction_pressure: float           # 1.0 .. 2.0
    zld_mandated: bool
    context: str
    evidence: str = "ASSUMED"

    @property
    def stress_weight(self) -> float:
        """Stress-equivalence multiplier. 1.0 = notional unstressed basin."""
        raw = (
            (1.0 - self.renewable_availability_index)
            * self.seasonality_penalty
            * self.abstraction_pressure
        )
        # Normalise so a well-supplied perennial basin lands at ~1.0 rather
        # than near zero, keeping the multiplier interpretable.
        return round(1.0 + raw * 4.0, 2)

    def stress_equivalent_litres(self, litres: float) -> float:
        """Convert physical litres into stress-equivalent litres (L-eq)."""
        if litres <= 0:
            return 0.0
        return round(litres * self.stress_weight, 1)

    def band(self) -> str:
        w = self.stress_weight
        if w >= 3.0:
            return "Extreme"
        if w >= 2.2:
            return "High"
        if w >= 1.6:
            return "Moderate"
        return "Low"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stress_weight"] = self.stress_weight
        d["band"] = self.band()
        return d


BASINS: Dict[str, Basin] = {
    "IN-TN-TIRUPUR-01": Basin(
        site_id="IN-TN-TIRUPUR-01",
        site_name="Dyeing Unit 01 (reference site)",
        cluster="Tirupur knitwear cluster, Tamil Nadu",
        basin_name="Noyyal sub-basin (Cauvery system)",
        state="Tamil Nadu",
        regulatory_regime="Zero Liquid Discharge - court mandated, CPCB ZLD "
                          "guidelines, OCEMS online effluent monitoring",
        renewable_availability_index=0.22,
        seasonality_penalty=1.9,
        abstraction_pressure=1.7,
        zld_mandated=True,
        context="The Noyyal is a seasonal river with no assured dry-weather "
                "dilution flow, which is the reason discharge of treated "
                "effluent was ruled out and Zero Liquid Discharge was "
                "imposed on the cluster. The cluster now treats and recycles "
                "on the order of 130 million litres per day. Water recovery "
                "is therefore largely solved here; what remains unsolved is "
                "the energy and salt burden of achieving it.",
    ),
    "IN-TN-ERODE-02": Basin(
        site_id="IN-TN-ERODE-02",
        site_name="Dyeing Unit 02",
        cluster="Erode processing cluster, Tamil Nadu",
        basin_name="Cauvery main stem (Bhavani confluence)",
        state="Tamil Nadu",
        regulatory_regime="Zero Liquid Discharge, CPCB consent conditions",
        renewable_availability_index=0.38,
        seasonality_penalty=1.5,
        abstraction_pressure=1.5,
        zld_mandated=True,
        context="Closer to a perennial main stem than Tirupur, so the same "
                "litre carries a lower scarcity consequence. Useful as the "
                "internal contrast case: identical process decisions produce "
                "a different environmental ranking here.",
    ),
    "IN-RJ-PALI-03": Basin(
        site_id="IN-RJ-PALI-03",
        site_name="Dyeing Unit 03",
        cluster="Pali textile cluster, Rajasthan",
        basin_name="Bandi / Luni basin",
        state="Rajasthan",
        regulatory_regime="Zero Liquid Discharge, critically polluted area "
                          "directions",
        renewable_availability_index=0.10,
        seasonality_penalty=2.0,
        abstraction_pressure=1.9,
        zld_mandated=True,
        context="Arid, ephemeral drainage with heavy groundwater dependence. "
                "The highest stress weighting in the reference set: here the "
                "water term dominates the objective and the optimiser "
                "selects a different option than it does in Erode.",
    ),
    "IN-MH-ICHALKARANJI-04": Basin(
        site_id="IN-MH-ICHALKARANJI-04",
        site_name="Dyeing Unit 04",
        cluster="Ichalkaranji processing cluster, Maharashtra",
        basin_name="Panchganga / Krishna basin",
        state="Maharashtra",
        regulatory_regime="CETP with partial recovery, ZLD directions pending",
        renewable_availability_index=0.45,
        seasonality_penalty=1.3,
        abstraction_pressure=1.4,
        zld_mandated=False,
        context="Not yet under a full ZLD obligation, which is why it is "
                "included: it lets the system show the avoided-compliance "
                "value of cutting salt load before a mandate arrives.",
    ),
}

DEFAULT_SITE = "IN-TN-TIRUPUR-01"


def get_basin(site_id: str) -> Basin:
    """Look up a basin, falling back to the reference site."""
    return BASINS.get(site_id, BASINS[DEFAULT_SITE])


def all_basins() -> List[Dict[str, Any]]:
    return [b.to_dict() for b in BASINS.values()]


def methodology() -> Dict[str, Any]:
    """Disclosure block shown beside every stress-equivalent figure."""
    return {
        "metric": "Stress-equivalent litres (L-eq)",
        "evidence": "ASSUMED",
        "formula": "stress_weight = 1 + 4 x (1 - renewable_availability_index)"
                   " x seasonality_penalty x abstraction_pressure",
        "normalisation": "A notional well-supplied perennial basin scores "
                         "1.00, so L-eq equals physical litres there.",
        "what_this_is": "A transparent ordering index that occupies the slot "
                        "a licensed scarcity characterisation factor would "
                        "occupy, so that site comparison and multi-site "
                        "optimisation can be demonstrated end to end.",
        "what_this_is_not": "It is not an AWARE characterisation factor and "
                            "not a WRI Aqueduct baseline-water-stress value. "
                            "We do not ship or claim either dataset.",
        "before_external_use": "Replace stress_weight with a site-licensed "
                               "AWARE factor or Aqueduct band before making "
                               "any disclosed or audited impact claim. The "
                               "interface is a single scalar per site, so "
                               "this is a data swap, not a code change.",
    }
