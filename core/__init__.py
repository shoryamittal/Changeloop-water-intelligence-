"""ChangeLoop - Resource Decision Intelligence for water-stressed industry.

Hero use case: reactive dyeing in an Indian textile cluster operating under a
Zero Liquid Discharge mandate.

Thesis
------
Water waste is not a reporting problem. It is a decision problem. A lot
sequencing decision taken in the dyehouse in the morning determines how much
boiler steam the zero-liquid-discharge evaporator burns that night, and no
existing system connects those two facts.

The one equation it turns on
----------------------------
Salt is conserved. RO, biology and evaporation do not destroy it, and the
final RO stage can only concentrate to a ceiling. So:

    V_reject = M_salt / C_reject_max

Reject volume - and therefore evaporator steam - is set by SALT MASS, not by
water volume. Saving water without saving salt does not save energy.

Module map
----------
  factors     every coefficient, with unit, derivation and evidence class
  basin       basin stress weighting, with an explicit honesty boundary
  process     dye lot model, COMPUTED changeover burden, process strategies
  zld         the consequence chain: salt -> reject -> steam -> carbon -> cost
  optimizer   constrained multi-objective optimiser over order x strategy
  telemetry   wash-off telemetry and the fail-closed release gate
  ledger      resource decision event and mass-balance impact ledger
  provenance  tamper-evident HMAC hash-chained decision ledger
  economics   site business case and cluster projection
  scenarios   constraint modes, sensitivity sweep, ablation study
  session     golden-path orchestrator and single source of truth
"""

from . import factors
from . import basin
from . import process
from . import zld
from . import optimizer
from . import telemetry
from . import ledger
from . import provenance
from . import economics
from . import scenarios
from . import session

from .basin import Basin, BASINS, get_basin, all_basins, DEFAULT_SITE
from .process import (
    DyeLot, Machine, MACHINES, reference_lots, arrival_order,
    changeover_burden, changeover_matrix, evaluate_sequence,
    salt_dose_g_per_l, shade_tolerance, washoff_baths,
    RinseStrategy, strategies, get_strategy, DEFAULT_STRATEGY,
)
from .zld import (
    treat, evaluate_scenario, account_for_water,
    sensitivity_salt_vs_water, ZLDResult, WaterAccount,
)
from .optimizer import (
    optimise, ObjectiveWeights, HardConstraints, evaluate_candidate,
    check_constraints,
)
from .telemetry import (
    simulate_washoff, release_limits, fault_catalogue, GateState,
    FAULT_MODES,
)
from .ledger import (
    ResourceDecisionEvent, new_decision_event, ImpactLedger, build_ledger,
    trace,
)
from .economics import (
    business_case, cluster_projection, REQUIRED_INPUTS, INPUT_HELP,
)
from .scenarios import (
    constraint_modes, run_mode, compare_modes, sensitivity, ablation,
)
from .session import Session, get_session, Stage

__version__ = "3.0.0"
CALCULATION_VERSION = "changeloop-3.0"

__all__ = [
    "factors", "basin", "process", "zld", "optimizer", "telemetry",
    "ledger", "provenance", "economics", "scenarios", "session",
    "Basin", "BASINS", "get_basin", "all_basins", "DEFAULT_SITE",
    "DyeLot", "Machine", "MACHINES", "reference_lots", "arrival_order",
    "changeover_burden", "changeover_matrix", "evaluate_sequence",
    "salt_dose_g_per_l", "shade_tolerance", "washoff_baths",
    "RinseStrategy", "strategies", "get_strategy", "DEFAULT_STRATEGY",
    "treat", "evaluate_scenario", "account_for_water",
    "sensitivity_salt_vs_water", "ZLDResult", "WaterAccount",
    "optimise", "ObjectiveWeights", "HardConstraints", "evaluate_candidate",
    "check_constraints",
    "simulate_washoff", "release_limits", "fault_catalogue", "GateState",
    "FAULT_MODES",
    "ResourceDecisionEvent", "new_decision_event", "ImpactLedger",
    "build_ledger", "trace",
    "business_case", "cluster_projection", "REQUIRED_INPUTS", "INPUT_HELP",
    "constraint_modes", "run_mode", "compare_modes", "sensitivity",
    "ablation",
    "Session", "get_session", "Stage",
    "__version__", "CALCULATION_VERSION",
]
