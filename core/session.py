"""ChangeLoop - Golden Path Session Orchestrator.

Holds the one authoritative state object every screen reads from. There is no
per-screen calculation and no second copy of any quantity: screens are views
over this state.

The golden path
---------------
    RESET -> OBSERVE -> OPTIMISE -> EXPLAIN -> HUMAN DECISION
          -> WASH-OFF TELEMETRY -> RELEASE GATE -> HUMAN RELEASE
          -> ZLD CONSEQUENCE -> LEDGER -> VERIFY -> EXPORT

Every transition is recorded to the tamper-evident ledger, including
rejections and lockouts, so the record shows what a human actually decided
rather than only what the system proposed.
"""
from typing import Dict, Any, List, Optional
import time
import json
import hashlib
import uuid

from . import factors, provenance, zld, telemetry
from .basin import get_basin, all_basins, methodology, DEFAULT_SITE
from .process import (
    reference_lots, arrival_order, evaluate_sequence, changeover_matrix,
    MACHINES, salt_dose_g_per_l, washoff_baths,
)
from .optimizer import optimise, ObjectiveWeights, HardConstraints
from .ledger import new_decision_event, build_ledger, trace


class Stage:
    READY = "READY"
    OPTIMISED = "OPTIMISED"
    DECIDED = "DECIDED"
    WASHOFF_RUN = "WASHOFF_RUN"
    RELEASED = "RELEASED"
    CLOSED = "CLOSED"


class Session:
    """Deterministic single-source-of-truth session."""

    def __init__(self, site_id: str = DEFAULT_SITE) -> None:
        self.reset(site_id)

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def reset(self, site_id: Optional[str] = None) -> Dict[str, Any]:
        self.session_id = str(uuid.uuid4())
        self.site_id = site_id or getattr(self, "site_id", DEFAULT_SITE)
        self.stage = Stage.READY

        self.lots = reference_lots()
        self.arrival = arrival_order()
        self.current_order: List[str] = list(self.arrival)

        self.optimisation: Optional[Dict[str, Any]] = None
        self.decision_event: Optional[Dict[str, Any]] = None
        self.sequencing_status = "PENDING"      # PENDING|APPROVED|REJECTED
        self.sequencing_actor: Optional[str] = None

        self.fault_mode: Optional[str] = None
        self.washoff: Optional[Dict[str, Any]] = None
        self.washoff_status = "NOT_RUN"         # NOT_RUN|AWAITING|RELEASED|
        self.washoff_actor: Optional[str] = None  # LOCKED_OUT|FULL_CYCLE

        provenance.reset()
        provenance.append(
            "SESSION_RESET",
            "New session opened at {}".format(self.site_id),
            {"session_id": self.session_id, "site_id": self.site_id},
            actor="system",
        )
        return self.state()

    def set_site(self, site_id: str) -> Dict[str, Any]:
        """Change site. Invalidates downstream decisions, as it must.

        A different basin has a different stress weight and different costs,
        so a decision approved for one site cannot carry over to another.
        """
        basin = get_basin(site_id)
        self.site_id = basin.site_id
        self.stage = Stage.READY
        self.optimisation = None
        self.decision_event = None
        self.sequencing_status = "PENDING"
        self.sequencing_actor = None
        self.washoff = None
        self.washoff_status = "NOT_RUN"
        self.washoff_actor = None
        self.current_order = list(self.arrival)
        provenance.append(
            "SITE_CHANGED",
            "Site set to {}. Downstream decisions invalidated because the "
            "basin stress weight and cost basis differ.".format(
                basin.site_id),
            {"site_id": basin.site_id,
             "stress_weight": basin.stress_weight},
            actor="system",
        )
        return self.state()

    # ------------------------------------------------------------------
    # step 1 - optimise
    # ------------------------------------------------------------------

    def run_optimisation(self,
                         weights: Optional[Dict[str, float]] = None
                         ) -> Dict[str, Any]:
        w = ObjectiveWeights(**weights) if weights else ObjectiveWeights()
        self.optimisation = optimise(
            self.lots, self.arrival, self.site_id, w, HardConstraints())

        if self.optimisation.get("status") != "FEASIBLE":
            provenance.append(
                "OPTIMISATION_NO_FEASIBLE_OPTION",
                self.optimisation.get("reason", "No feasible option."),
                {"site_id": self.site_id},
                actor="optimiser",
            )
            return self.state()

        ev = new_decision_event(
            site_id=self.site_id,
            asset_id="JET-01",
            decision_type="DYE_LOT_SEQUENCE",
            optimisation=self.optimisation,
            context={"machine": MACHINES["JET-01"].to_dict(),
                     "lot_count": len(self.lots)},
        )
        rec = provenance.append(
            "OPTIMISATION_RUN",
            "Evaluated {} candidate orders by {}. Recommending {}.".format(
                self.optimisation["candidates_evaluated"],
                self.optimisation["method"],
                self.optimisation["recommended_option_id"]),
            {"event_id": ev.event_id,
             "method": self.optimisation["method"],
             "optimality": self.optimisation["optimality"],
             "expected": ev.expected},
            actor="optimiser",
        )
        ev.ledger_seq = rec["seq"]
        ev.record_hash = rec["record_hash"]
        self.decision_event = ev.to_dict()
        self.stage = Stage.OPTIMISED
        return self.state()

    # ------------------------------------------------------------------
    # step 2 - human decision on the sequence
    # ------------------------------------------------------------------

    def decide_sequence(self, approve: bool,
                        actor: str = "Shift planner",
                        note: Optional[str] = None) -> Dict[str, Any]:
        """Approve or reject the sequencing recommendation.

        A rejection is a first-class outcome. It is recorded, it keeps the
        arrival order, and it yields exactly zero saving. It is never
        silently converted into an approval.
        """
        if self.optimisation is None or self.decision_event is None:
            return {"error": "Run the optimisation before deciding.",
                    "state": self.state()}

        rec_id = self.optimisation["recommended_option_id"]
        rec = next((o for o in self.optimisation["options"]
                    if o["option_id"] == rec_id), None)

        if approve:
            if rec is None or not rec.get("feasible", False):
                provenance.append(
                    "SEQUENCE_APPROVAL_BLOCKED",
                    "Approval refused: the recommended option does not "
                    "satisfy the hard constraints.",
                    {"violations": (rec or {}).get("violations", [])},
                    actor=actor,
                )
                return {"error": "Recommended option is not feasible; "
                                 "approval blocked.",
                        "state": self.state()}
            self.sequencing_status = "APPROVED"
            self.current_order = list(rec["order"])
            detail = "Planner approved the recommended order {}.".format(
                " -> ".join(self.current_order))
        else:
            self.sequencing_status = "REJECTED"
            self.current_order = list(self.arrival)
            detail = ("Planner rejected the recommendation and retained the "
                      "arrival order. No saving is credited.")

        self.sequencing_actor = actor
        self.decision_event["human_status"] = (
            "APPROVED" if approve else "REJECTED")
        self.decision_event["human_actor"] = actor
        self.decision_event["human_note"] = note
        self.decision_event["selected_option_id"] = (
            rec_id if approve else "OPTION_A")

        provenance.append(
            "SEQUENCE_DECISION",
            detail,
            {"event_id": self.decision_event["event_id"],
             "decision": "APPROVED" if approve else "REJECTED",
             "order": self.current_order,
             "note": note},
            actor=actor,
        )
        self.stage = Stage.DECIDED
        return self.state()

    # ------------------------------------------------------------------
    # step 3 - wash-off telemetry
    # ------------------------------------------------------------------

    def run_washoff(self, fault_mode: Optional[str] = None,
                    lot_id: Optional[str] = None) -> Dict[str, Any]:
        if fault_mode in ("none", "", "null"):
            fault_mode = None
        if fault_mode is not None and fault_mode not in telemetry.FAULT_MODES:
            return {"error": "Unknown fault mode: {}".format(fault_mode),
                    "state": self.state()}

        # Default to the lot with the longest scheduled wash-off. Fixed-time
        # schedules are padded for the deepest shade, so that is where the
        # slack - and therefore the opportunity - actually is. Pale lots on
        # short schedules have no slack and the system says so rather than
        # manufacturing a saving.
        if lot_id:
            lot = next((l for l in self.lots if l.lot_id == lot_id),
                       self.lots[0])
        else:
            lot = max(self.lots, key=lambda l: washoff_baths(l.depth_owf))
        machine = lot.machine

        self.fault_mode = fault_mode
        self.washoff = telemetry.simulate_washoff(
            lot_id=lot.lot_id,
            scheduled_baths=washoff_baths(lot.depth_owf),
            bath_litres=lot.bath_litres,
            bath_minutes=machine.bath_minutes,
            depth_owf=lot.depth_owf,
            salt_dose_g_per_l=salt_dose_g_per_l(lot.depth_owf),
            fault_mode=fault_mode,
        ).to_dict()

        gate_state = self.washoff["gate"]["state"]
        if gate_state == telemetry.GateState.LOCKED_OUT.value:
            self.washoff_status = "LOCKED_OUT"
        elif gate_state == telemetry.GateState.AWAITING_HUMAN_RELEASE.value:
            self.washoff_status = "AWAITING"
        else:
            self.washoff_status = "FULL_CYCLE"

        provenance.append(
            "WASHOFF_RUN",
            "Wash-off telemetry for {} ({} baths scheduled). Gate: {}. {}"
            .format(lot.lot_id, self.washoff["scheduled_baths"],
                    gate_state, self.washoff["gate"]["message"]),
            {"lot_id": lot.lot_id,
             "fault_mode": fault_mode,
             "gate_state": gate_state,
             "checks": self.washoff["gate"]["checks"],
             "baths_avoidable": self.washoff["baths_avoidable"]},
            actor="telemetry",
        )
        self.stage = Stage.WASHOFF_RUN
        return self.state()

    def release_washoff(self, approve: bool,
                        actor: str = "Quality supervisor",
                        note: Optional[str] = None) -> Dict[str, Any]:
        """Human release decision on ending wash-off early.

        Fail-closed: if the gate is locked out, release is refused here as
        well as in the gate, so there is no path in which a client request
        can produce a saving the gate did not authorise.
        """
        if self.washoff is None:
            return {"error": "Run the wash-off before releasing.",
                    "state": self.state()}

        gate = self.washoff["gate"]
        if approve:
            if gate["state"] != telemetry.GateState.AWAITING_HUMAN_RELEASE.value:
                provenance.append(
                    "WASHOFF_RELEASE_BLOCKED",
                    "Release refused. Gate state is {} and the clearance "
                    "checks that failed were: {}.".format(
                        gate["state"],
                        "; ".join(gate["checks"]["failed"]) or "none"),
                    {"gate_state": gate["state"],
                     "lockout_reason": gate["lockout_reason"],
                     "failed_checks": gate["checks"]["failed"]},
                    actor=actor,
                )
                return {
                    "error": "Release blocked. {}".format(
                        gate["lockout_reason"] or gate["message"]),
                    "state": self.state(),
                }
            self.washoff_status = "RELEASED"
            detail = ("Supervisor released wash-off after bath {}, skipping "
                      "{} bath(s). All five clearance checks passed."
                      .format((self.washoff["endpoint_bath"] or 0) + 1,
                              self.washoff["baths_avoidable"]))
        else:
            self.washoff_status = "FULL_CYCLE"
            detail = ("Supervisor declined early release. Full scheduled "
                      "cycle will run and no saving is credited.")

        self.washoff_actor = actor
        provenance.append(
            "WASHOFF_RELEASE_DECISION",
            detail,
            {"lot_id": self.washoff["lot_id"],
             "decision": "RELEASED" if approve else "FULL_CYCLE",
             "water_avoidable_l": self.washoff["water_avoidable_l"],
             "note": note},
            actor=actor,
        )
        self.stage = Stage.RELEASED
        return self.state()

    # ------------------------------------------------------------------
    # consequence + ledger
    # ------------------------------------------------------------------

    def _scenario(self, order: List[str],
                  washoff_credit: bool) -> Dict[str, Any]:
        """Evaluate one running order, optionally crediting the release."""
        seq = evaluate_sequence(self.lots, order)
        pw = seq["process_water_l"]
        ps = seq["process_salt_kg"]

        if washoff_credit and self.washoff:
            pw = max(0.0, pw - self.washoff["water_avoidable_l"])
            ps = max(0.0, ps - self.washoff["salt_avoidable_kg"])

        out = zld.evaluate_scenario(
            process_water_l=pw,
            process_salt_kg=ps,
            changeover_water_l=seq["changeover_water_l"],
            changeover_salt_kg=seq["changeover_salt_kg"],
            site_id=self.site_id,
        )
        out["_changeover_water_l"] = seq["changeover_water_l"]
        out["_sequence"] = seq
        return out

    def impact(self) -> Dict[str, Any]:
        """The one impact ledger. Every screen reads this."""
        baseline = self._scenario(self.arrival, washoff_credit=False)
        released = (self.washoff_status == "RELEASED")
        achieved = self._scenario(self.current_order, washoff_credit=released)

        base_seq = baseline["_sequence"]
        ach_seq = achieved["_sequence"]

        seq_water_avoided = (
            base_seq["changeover_water_l"] - ach_seq["changeover_water_l"]
            if self.sequencing_status == "APPROVED" else 0.0)
        seq_salt_avoided = (
            base_seq["changeover_salt_kg"] - ach_seq["changeover_salt_kg"]
            if self.sequencing_status == "APPROVED" else 0.0)

        wash_water = (self.washoff["water_avoidable_l"]
                      if released and self.washoff else 0.0)
        wash_salt = (self.washoff["salt_avoidable_kg"]
                     if released and self.washoff else 0.0)
        wash_thermal = (self.washoff["thermal_avoidable_kwh"]
                        if released and self.washoff else 0.0)

        led = build_ledger(
            site_id=self.site_id,
            baseline=baseline,
            achieved=achieved,
            sequencing_status=self.sequencing_status,
            sequencing_water_avoided_l=seq_water_avoided,
            sequencing_salt_avoided_kg=seq_salt_avoided,
            washoff_status=self.washoff_status,
            washoff_water_avoided_l=wash_water,
            washoff_salt_avoided_kg=wash_salt,
            washoff_thermal_avoided_kwh=wash_thermal,
        )
        out = led.to_dict()
        out["baseline_scenario"] = {
            k: v for k, v in baseline.items() if not k.startswith("_")}
        out["achieved_scenario"] = {
            k: v for k, v in achieved.items() if not k.startswith("_")}
        return out

    # ------------------------------------------------------------------
    # state + export
    # ------------------------------------------------------------------

    def state(self) -> Dict[str, Any]:
        basin = get_basin(self.site_id)
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "site_id": self.site_id,
            "basin": basin.to_dict(),
            "basin_methodology": methodology(),

            "machine": MACHINES["JET-01"].to_dict(),
            "lots": [l.to_dict() for l in self.lots],
            "arrival_order": self.arrival,
            "current_order": self.current_order,

            "optimisation": self.optimisation,
            "decision_event": self.decision_event,
            "sequencing_status": self.sequencing_status,
            "sequencing_actor": self.sequencing_actor,

            "fault_mode": self.fault_mode,
            "washoff": self.washoff,
            "washoff_status": self.washoff_status,
            "washoff_actor": self.washoff_actor,
            "release_limits": telemetry.release_limits(),

            "impact": self.impact(),
            "ledger_integrity": provenance.verify_chain(),
            "ledger_records": provenance.records(limit=60),

            "classification": "MODELLED",
            "advisory_notice": (
                "ChangeLoop is advisory. It has no control authority, issues "
                "no setpoints, and cannot release a bath. Every action "
                "requires a named human decision."
            ),
        }

    def export(self) -> Dict[str, Any]:
        """Auditable export. Figures come from the same ledger the UI shows."""
        imp = self.impact()
        basin = get_basin(self.site_id)
        payload = {
            "export_id": str(uuid.uuid4()),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "session_id": self.session_id,
            "product": "ChangeLoop",
            "calculation_version": "changeloop-3.0",
            "site": {
                "site_id": basin.site_id,
                "cluster": basin.cluster,
                "basin": basin.basin_name,
                "stress_weight": basin.stress_weight,
                "stress_band": basin.band(),
                "zld_mandated": basin.zld_mandated,
            },
            "decisions": {
                "sequencing": {
                    "status": self.sequencing_status,
                    "actor": self.sequencing_actor,
                    "arrival_order": self.arrival,
                    "executed_order": self.current_order,
                },
                "washoff_release": {
                    "status": self.washoff_status,
                    "actor": self.washoff_actor,
                    "fault_injected": self.fault_mode,
                },
            },
            "impact": {
                k: v for k, v in imp.items()
                if k not in ("baseline_scenario", "achieved_scenario")
            },
            "evidence": {
                "classification": "MODELLED",
                "coefficients": factors.audit_trail(),
                "evidence_summary": factors.evidence_summary(),
                "basin_methodology": methodology(),
                "disclaimer": (
                    "No figure in this export is a metered value from a real "
                    "asset. All quantities are modelled from the declared "
                    "coefficients. Option RANKING is robust because every "
                    "option is scored identically; ABSOLUTE savings carry "
                    "the uncertainty of the coefficients and require site "
                    "sub-metering to confirm."
                ),
            },
            "ledger_integrity": provenance.verify_chain(),
        }
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        payload["export_sha256"] = hashlib.sha256(raw).hexdigest()
        return payload


# Single process-wide session for the demonstration server.
_SESSION: Optional[Session] = None


def get_session() -> Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = Session()
    return _SESSION
