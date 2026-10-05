"""ChangeLoop - Wash-off Telemetry and Fail-Closed Release Gate.

The second decision
-------------------
Sequencing is the first decision. The second is: when is the wash-off
actually finished? Indian dyehouses overwhelmingly run FIXED-TIME wash-off
cycles, because a fixed time is safe and an operator cannot be blamed for
following it. Fixed time means that whenever the fabric cleared early, the
remaining baths are pure waste - water, steam and electrolyte load that
achieved nothing.

Why ending early is genuinely risky
-----------------------------------
Stopping wash-off too early leaves unfixed hydrolysed dye on the fabric.
That shows up later as bleeding, crocking or a failed wash-fastness test,
and the remedy is to re-process the lot. Re-processing consumes MORE water,
steam and salt than the baths that were skipped. So a wrong early cutoff does
not merely risk quality - it destroys the very saving it was chasing.

That is why the gate is fail-closed and why ChangeLoop never releases
automatically. The gate is not bureaucracy; it is what keeps the saving real.

Design rules enforced here
--------------------------
  - The system NEVER releases a bath automatically. `automatic_release` is
    hardcoded False and there is no code path that sets it True.
  - A missing, frozen, spiking or drifting sensor forces LOCKOUT. An absent
    reading is never treated as a clean reading.
  - Avoided water is integrated from the simulated FLOW SIGNAL over the
    skipped baths. It is not a per-minute constant.
  - If the gate is not satisfied, avoided water is exactly 0.0.
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from enum import Enum
import random
import math

from . import factors


class GateState(str, Enum):
    MONITORING = "MONITORING"
    ENDPOINT_CANDIDATE = "ENDPOINT_CANDIDATE"
    AWAITING_HUMAN_RELEASE = "AWAITING_HUMAN_RELEASE"
    LOCKED_OUT = "LOCKED_OUT"


FAULT_MODES = {
    None: "No fault injected",
    "sensor_dropout": "Conductivity and colour probes return no reading",
    "sensor_frozen": "Probe reports an identical value every sample",
    "sensor_drift": "Probe reading diverges progressively from the dual probe",
    "colour_spike": "Residual dye slug detected after apparent clearance",
    "thermal_deficit": "Wash-off bath below the temperature needed to fix",
}


@dataclass(frozen=True)
class Sample:
    """One telemetry sample from the wash-off line."""
    minute: int
    bath_index: int
    conductivity_ms_cm: Optional[float]
    residual_colour_admi: Optional[float]
    temp_c: float
    flow_l_min: float
    ph: Optional[float]
    validity: str              # VALID | MISSING | FROZEN | DRIFT | SPIKE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClearanceChecks:
    """Independent checks. ALL must pass before a release may be offered."""
    conductivity_asymptote: bool
    residual_colour_within_limit: bool
    fixation_temperature_held: bool
    dual_probe_agreement: bool
    data_completeness: bool

    def all_pass(self) -> bool:
        return all([
            self.conductivity_asymptote,
            self.residual_colour_within_limit,
            self.fixation_temperature_held,
            self.dual_probe_agreement,
            self.data_completeness,
        ])

    def failed(self) -> List[str]:
        names = {
            "conductivity_asymptote": "Conductivity has not reached a stable "
                                      "asymptote",
            "residual_colour_within_limit": "Residual colour above the "
                                            "release limit",
            "fixation_temperature_held": "Fixation temperature not held",
            "dual_probe_agreement": "Dual probes disagree beyond tolerance",
            "data_completeness": "Telemetry incomplete",
        }
        return [v for k, v in names.items() if not getattr(self, k)]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["all_pass"] = self.all_pass()
        d["failed"] = self.failed()
        return d


@dataclass
class ReleaseGate:
    """The fail-closed decision gate."""
    state: GateState
    automatic_release: bool
    message: str
    checks: ClearanceChecks
    lockout_reason: Optional[str]
    authority: str = ("Site quality procedure and a named human releaser. "
                      "ChangeLoop has no release authority.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "automatic_release": self.automatic_release,
            "message": self.message,
            "checks": self.checks.to_dict(),
            "lockout_reason": self.lockout_reason,
            "authority": self.authority,
        }


@dataclass
class WashoffRun:
    """A complete simulated wash-off run with endpoint analysis."""
    lot_id: str
    scheduled_baths: int
    bath_minutes: float
    bath_litres: float
    samples: List[Sample]
    endpoint_bath: Optional[int]
    baths_avoidable: int
    minutes_avoidable: float
    water_avoidable_l: float
    salt_avoidable_kg: float
    thermal_avoidable_kwh: float
    gate: ReleaseGate
    fault_mode: Optional[str]
    confidence: str
    classification: str = "SIMULATED"
    notice: str = ("Synthetic telemetry from a deterministic generator. Not "
                   "an instrument reading from any real asset.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "scheduled_baths": self.scheduled_baths,
            "bath_minutes": self.bath_minutes,
            "bath_litres": self.bath_litres,
            "samples": [s.to_dict() for s in self.samples],
            "endpoint_bath": self.endpoint_bath,
            "baths_avoidable": self.baths_avoidable,
            "minutes_avoidable": round(self.minutes_avoidable, 1),
            "water_avoidable_l": round(self.water_avoidable_l, 1),
            "salt_avoidable_kg": round(self.salt_avoidable_kg, 3),
            "thermal_avoidable_kwh": round(self.thermal_avoidable_kwh, 2),
            "gate": self.gate.to_dict(),
            "fault_mode": self.fault_mode,
            "fault_description": FAULT_MODES.get(self.fault_mode,
                                                 "Unknown fault mode"),
            "confidence": self.confidence,
            "classification": self.classification,
            "notice": self.notice,
        }


# Release limits. Site-specific in reality; fixed here and disclosed.
CONDUCTIVITY_RELEASE_MS_CM = 0.45
COLOUR_RELEASE_ADMI = 12.0
FIXATION_MIN_TEMP_C = 60.0
STABILITY_GUARD_MULTIPLE = 4.0  # preceding bath must be within 4x the limit


def simulate_washoff(lot_id: str,
                     scheduled_baths: int,
                     bath_litres: float,
                     bath_minutes: float,
                     depth_owf: float,
                     salt_dose_g_per_l: float,
                     fault_mode: Optional[str] = None,
                     seed: int = 7701) -> WashoffRun:
    """Generate a wash-off run and evaluate the release gate.

    Deterministic for a given (seed, fault_mode) so the demonstration is
    repeatable and so tests can assert exact values.
    """
    rng = random.Random(seed)
    scheduled_baths = max(1, int(scheduled_baths))

    # Residual load decays geometrically bath to bath. Deeper shades start
    # higher and therefore genuinely need more baths.
    start_cond = 2.6 + 0.42 * max(0.0, depth_owf)
    start_colour = 55.0 + 26.0 * max(0.0, depth_owf)
    decay = 0.42

    samples: List[Sample] = []
    cond_by_bath: List[Optional[float]] = []
    colour_by_bath: List[Optional[float]] = []
    temps_held = True
    frozen_seen = False
    drift_seen = False
    missing_seen = False
    spike_seen = False

    samples_per_bath = 4
    minute = 0
    last_cond: Optional[float] = None

    for b in range(scheduled_baths):
        true_cond = start_cond * (decay ** b) + 0.18
        true_colour = start_colour * (decay ** b) + 3.2
        bath_cond_samples: List[float] = []
        bath_colour_samples: List[float] = []

        for s in range(samples_per_bath):
            validity = "VALID"
            cond: Optional[float] = max(0.0, true_cond + rng.gauss(0, 0.02))
            colour: Optional[float] = max(0.0, true_colour + rng.gauss(0, 0.4))
            temp = 78.0 + rng.gauss(0, 0.6)
            flow = (bath_litres / bath_minutes) + rng.gauss(0, 0.15)
            ph: Optional[float] = 7.4 + rng.gauss(0, 0.08)

            if fault_mode == "sensor_dropout" and b >= max(1, scheduled_baths - 2):
                cond, colour, ph = None, None, None
                validity = "MISSING"
                missing_seen = True
            elif fault_mode == "sensor_frozen" and b >= 1:
                cond, colour = start_cond * decay + 0.18, start_colour * decay + 3.2
                validity = "FROZEN"
                frozen_seen = True
            elif fault_mode == "sensor_drift" and b >= 1:
                cond = (cond or 0.0) + 0.26 * b
                colour = (colour or 0.0) + 5.5 * b
                validity = "DRIFT"
                drift_seen = True
            elif fault_mode == "colour_spike" and b == scheduled_baths - 1 and s == 2:
                colour = COLOUR_RELEASE_ADMI * 3.4
                validity = "SPIKE"
                spike_seen = True
            elif fault_mode == "thermal_deficit":
                temp = 52.0 + rng.gauss(0, 0.8)

            if temp < FIXATION_MIN_TEMP_C:
                temps_held = False

            samples.append(Sample(
                minute=minute,
                bath_index=b,
                conductivity_ms_cm=None if cond is None else round(cond, 3),
                residual_colour_admi=None if colour is None else round(colour, 2),
                temp_c=round(temp, 1),
                flow_l_min=round(max(0.0, flow), 2),
                ph=None if ph is None else round(ph, 2),
                validity=validity,
            ))
            if cond is not None:
                bath_cond_samples.append(cond)
            if colour is not None:
                bath_colour_samples.append(colour)
            minute += int(round(bath_minutes / samples_per_bath))

        cond_by_bath.append(
            sum(bath_cond_samples) / len(bath_cond_samples)
            if bath_cond_samples else None)
        colour_by_bath.append(
            max(bath_colour_samples) if bath_colour_samples else None)

    # ---- endpoint detection ------------------------------------------
    # The first bath at which BOTH release criteria are satisfied, with a
    # stability guard: the preceding bath must already be on the decay tail
    # rather than far above the limit. The guard exists so that a single
    # anomalous low reading cannot be mistaken for clearance - clearance has
    # to be approached, not jumped to.
    endpoint_bath: Optional[int] = None
    for b in range(1, scheduled_baths):
        c, col = cond_by_bath[b], colour_by_bath[b]
        prev = cond_by_bath[b - 1]
        if c is None or col is None or prev is None:
            continue
        if c > CONDUCTIVITY_RELEASE_MS_CM or col > COLOUR_RELEASE_ADMI:
            continue
        if prev > CONDUCTIVITY_RELEASE_MS_CM * STABILITY_GUARD_MULTIPLE:
            # Below the limit, but the previous bath was still far above it.
            # Treat as not yet demonstrated and keep looking.
            continue
        endpoint_bath = b
        break

    # ---- clearance checks --------------------------------------------
    last_valid_cond = next(
        (c for c in reversed(cond_by_bath) if c is not None), None)
    last_valid_colour = next(
        (c for c in reversed(colour_by_bath) if c is not None), None)

    data_complete = not missing_seen and all(
        c is not None for c in cond_by_bath)
    probe_agreement = not (drift_seen or frozen_seen)

    checks = ClearanceChecks(
        conductivity_asymptote=bool(
            endpoint_bath is not None
            and last_valid_cond is not None
            and last_valid_cond <= CONDUCTIVITY_RELEASE_MS_CM),
        residual_colour_within_limit=bool(
            not spike_seen
            and last_valid_colour is not None
            and last_valid_colour <= COLOUR_RELEASE_ADMI),
        fixation_temperature_held=bool(temps_held),
        dual_probe_agreement=probe_agreement,
        data_completeness=data_complete,
    )

    # ---- gate --------------------------------------------------------
    lockout_reason: Optional[str] = None
    if missing_seen:
        lockout_reason = ("Telemetry dropout. An absent reading is not a "
                          "clean reading, so release is locked out.")
    elif frozen_seen:
        lockout_reason = ("Probe reported an identical value across baths. A "
                          "frozen probe cannot evidence clearance.")
    elif drift_seen:
        lockout_reason = ("Dual-probe divergence indicates calibration "
                          "drift. Readings cannot be trusted for release.")
    elif spike_seen:
        lockout_reason = ("Residual dye slug detected after apparent "
                          "clearance. Fabric is not clear.")
    elif not temps_held:
        lockout_reason = ("Wash-off bath below the temperature required for "
                          "fixation. Early cutoff would risk unfixed dye.")

    if lockout_reason is not None:
        state = GateState.LOCKED_OUT
        message = "LOCKED OUT - " + lockout_reason
    elif checks.all_pass() and endpoint_bath is not None:
        state = GateState.AWAITING_HUMAN_RELEASE
        message = (
            "All {} clearance checks pass at bath {}. ChangeLoop recommends "
            "ending wash-off here. It will not do so on its own: a named "
            "human must release.".format(5, endpoint_bath + 1)
        )
    elif endpoint_bath is not None:
        state = GateState.ENDPOINT_CANDIDATE
        message = ("Endpoint candidate found but clearance incomplete: {}."
                   .format("; ".join(checks.failed())))
    else:
        state = GateState.MONITORING
        message = ("No endpoint reached before the scheduled baths "
                   "completed. Run the full cycle.")

    gate = ReleaseGate(
        state=state,
        automatic_release=False,      # never True, by construction
        message=message,
        checks=checks,
        lockout_reason=lockout_reason,
    )

    # ---- avoidable resources, integrated from the flow signal --------
    releasable = (state == GateState.AWAITING_HUMAN_RELEASE
                  and endpoint_bath is not None)

    if releasable:
        baths_avoidable = max(0, scheduled_baths - (endpoint_bath + 1))
    else:
        baths_avoidable = 0

    if baths_avoidable > 0:
        skipped = [s for s in samples
                   if s.bath_index >= scheduled_baths - baths_avoidable]
        # Integrate flow over the skipped baths rather than assuming a
        # constant litres-per-minute.
        per_sample_minutes = bath_minutes / samples_per_bath
        water_avoidable = sum(s.flow_l_min * per_sample_minutes
                              for s in skipped)
        minutes_avoidable = baths_avoidable * bath_minutes
        salt_avoidable = (water_avoidable * salt_dose_g_per_l * 0.04) / 1000.0
        thermal_avoidable = (
            water_avoidable
            * factors.get("water_heating_kwh_per_l_per_k")
            * factors.get("rinse_delta_t_k")
        )
    else:
        water_avoidable = 0.0
        minutes_avoidable = 0.0
        salt_avoidable = 0.0
        thermal_avoidable = 0.0

    if not releasable:
        confidence = "NOT_RELEASABLE"
    elif baths_avoidable >= 2:
        confidence = "HIGH"
    elif baths_avoidable == 1:
        confidence = "MODERATE"
    else:
        confidence = "NO_SAVING_AVAILABLE"

    return WashoffRun(
        lot_id=lot_id,
        scheduled_baths=scheduled_baths,
        bath_minutes=bath_minutes,
        bath_litres=bath_litres,
        samples=samples,
        endpoint_bath=endpoint_bath,
        baths_avoidable=baths_avoidable,
        minutes_avoidable=minutes_avoidable,
        water_avoidable_l=water_avoidable,
        salt_avoidable_kg=salt_avoidable,
        thermal_avoidable_kwh=thermal_avoidable,
        gate=gate,
        fault_mode=fault_mode,
        confidence=confidence,
    )


def fault_catalogue() -> List[Dict[str, str]]:
    """Injectable faults, for the UI fault panel and the test suite."""
    return [{"mode": "none" if k is None else k, "description": v}
            for k, v in FAULT_MODES.items()]


def release_limits() -> Dict[str, Any]:
    """Disclosed release limits, shown next to the gate in the UI."""
    return {
        "conductivity_release_ms_cm": CONDUCTIVITY_RELEASE_MS_CM,
        "colour_release_admi": COLOUR_RELEASE_ADMI,
        "fixation_min_temp_c": FIXATION_MIN_TEMP_C,
        "stability_guard_multiple": STABILITY_GUARD_MULTIPLE,
        "evidence": "ASSUMED",
        "basis": "Indicative release limits for reactive-dyed cotton "
                 "wash-off. Real limits are set by the site quality "
                 "procedure and the buyer's wash-fastness specification, "
                 "and must be loaded per site before any pilot.",
        "failure_consequence": "Releasing early against unfixed dye causes "
                               "bleeding and a failed fastness test. The "
                               "lot is then re-processed, consuming more "
                               "water, steam and salt than the skipped "
                               "baths would have used.",
    }
