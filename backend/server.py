"""ChangeLoop - demonstration HTTP server and REST API.

Dependency-free: Python standard library only. No build step, no install.

Design rules
------------
  - Every impact figure is computed server side from the session. The client
    cannot supply a saving, a volume or a release. Requests carry INTENT
    ("approve this"), never OUTCOMES ("I saved 130 L").
  - Mutating endpoints accept an optional Idempotency-Key. A repeated key
    returns the first response instead of applying the action twice, so a
    double-click or a retry cannot double-count an approval.
  - Errors return a machine-readable code plus a human sentence, and never
    leak a stack trace.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Optional, Tuple
import json
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core
from core import (
    factors, basin, process, zld, telemetry, provenance, economics,
    scenarios, ledger, forecast,
)
from core.session import get_session

API_VERSION = "3.0"

# --- idempotency cache -----------------------------------------------------
_IDEMPOTENCY: Dict[str, Tuple[float, Any]] = {}
_IDEMPOTENCY_TTL_S = 900
_LOCK = threading.Lock()


def _idem_get(key: Optional[str]):
    if not key:
        return None
    with _LOCK:
        entry = _IDEMPOTENCY.get(key)
        if not entry:
            return None
        ts, value = entry
        if time.time() - ts > _IDEMPOTENCY_TTL_S:
            _IDEMPOTENCY.pop(key, None)
            return None
        return value


def _idem_put(key: Optional[str], value: Any) -> None:
    if not key:
        return
    with _LOCK:
        _IDEMPOTENCY[key] = (time.time(), value)
        if len(_IDEMPOTENCY) > 500:
            cutoff = time.time() - _IDEMPOTENCY_TTL_S
            for k, (ts, _) in list(_IDEMPOTENCY.items()):
                if ts < cutoff:
                    _IDEMPOTENCY.pop(k, None)


# --- reference payloads ----------------------------------------------------

def pilot_plan() -> Dict[str, Any]:
    return {
        "classification": "PLANNED",
        "mode": "Advisory only. The existing planning procedure stays "
                "authoritative throughout. ChangeLoop issues no setpoints.",
        "question_the_pilot_answers": (
            "Did ChangeLoop cause the reduction, or would it have happened "
            "anyway? Everything below exists to make that answerable."
        ),
        "phases": [
            {
                "phase": 1, "name": "Baseline metering", "weeks": "1-4",
                "objective": "Establish a measured baseline before the "
                             "system influences anything.",
                "exit_criteria": [
                    "28 days of continuous data at over 95% completeness",
                    "Measured litres and kg-salt per kg fabric per shade band",
                    "Measured evaporator steam per m3 of reject, replacing "
                    "our assumed 179 kWh/m3",
                ],
            },
            {
                "phase": 2, "name": "Shadow mode", "weeks": "5-8",
                "objective": "ChangeLoop recommends, nobody acts. Compare "
                             "what it would have advised against what the "
                             "planner actually did.",
                "exit_criteria": [
                    "Planner agrees with over 60% of recommendations "
                    "unprompted",
                    "Zero recommendations that would have breached a ship "
                    "date",
                ],
            },
            {
                "phase": 3, "name": "Advisory with approval", "weeks": "9-16",
                "objective": "Planner may approve recommendations. "
                             "Resequencing only, no chemistry change yet.",
                "exit_criteria": [
                    "Alternate weeks on and off, so the comparison is against "
                    "the same season, order mix and crew",
                    "Measured changeover water reduction with a confidence "
                    "interval",
                    "Zero off-shade lots attributable to an approved sequence",
                ],
            },
            {
                "phase": 4, "name": "Wash-off release trial", "weeks": "17-24",
                "objective": "Quality supervisor may grant early wash-off "
                             "release on deep shades.",
                "guardrail": "Every released lot goes to an independent "
                             "wash-fastness test. A single failure stops the "
                             "trial, because a re-processed lot costs more "
                             "water than was saved.",
                "exit_criteria": [
                    "Wash-fastness pass rate equal to the baseline period",
                    "Measured water and steam reduction per released lot",
                ],
            },
            {
                "phase": 5, "name": "Chemistry decision", "weeks": "25-32",
                "objective": "With a measured steam cost per m3 of reject, "
                             "decide whether low-electrolyte chemistry pays.",
                "note": "Deliberately last. Our sensitivity sweep shows this "
                        "is the coefficient-sensitive decision, and by now "
                        "the site has measured the two numbers it turns on.",
            },
            {
                "phase": 6, "name": "Cluster rollout", "weeks": "33+",
                "objective": "Second and third unit on the same common "
                             "effluent plant, reusing the shared model.",
            },
        ],
        "stop_conditions": [
            "Any off-shade lot or wash-fastness failure attributable to a "
            "ChangeLoop recommendation",
            "Any firm ship date missed on an approved sequence",
            "Effluent data completeness below 90% for 72 hours",
            "Mass-balance validation failing on any committed ledger entry",
        ],
        "what_we_will_not_claim": (
            "Until Phase 3 completes, every figure the product shows is "
            "MODELLED. We will not describe a modelled number as a result, "
            "and the interface labels it on every screen."
        ),
    }


def model_governance() -> Dict[str, Any]:
    return {
        "models": [
            {
                "name": "Changeover burden model",
                "purpose": "Compute machine-cleaning water, salt and time "
                           "between two consecutive lots.",
                "type": "Deterministic physical rule model. Not machine "
                        "learning.",
                "limitations": [
                    "Carry-over fraction and per-bath removal efficiency are "
                    "assumed, not measured",
                    "Does not model machine-specific dead volume",
                    "Excludes pretreatment (desizing, scouring, bleaching)",
                ],
                "failure_mode": "Mis-states the number of cleaning baths.",
                "fallback": "A lot with missing attributes is rejected at "
                            "validation; no default is invented.",
                "validation_plan": "Compare predicted cleaning baths against "
                                   "logged cleaning cycles in Phase 1.",
            },
            {
                "name": "ZLD consequence model",
                "purpose": "Convert effluent volume and salt mass into the RO "
                           "split, evaporator duty, carbon and cost.",
                "type": "Mass and energy balance. Closed form, no fitting.",
                "limitations": [
                    "Permeate salt passage neglected",
                    "Assumes a single blended effluent stream",
                    "Crystalliser performance not modelled",
                ],
                "failure_mode": "Over- or under-states evaporator duty in "
                                "proportion to the reject TDS ceiling.",
                "fallback": "Reports which constraint binds, so a reviewer "
                            "can see whether the result is salt-limited or "
                            "hydraulically limited.",
                "validation_plan": "Meter evaporator steam against reject "
                                   "flow in Phase 1 and replace the assumed "
                                   "specific energy with the measured value.",
            },
            {
                "name": "Wash-off endpoint detector",
                "purpose": "Identify the first bath at which both release "
                           "criteria are met.",
                "type": "Threshold rule with a stability guard, on synthetic "
                        "telemetry. Explicitly NOT a trained model.",
                "limitations": [
                    "Operates on simulated telemetry in this prototype",
                    "Release limits are indicative, not from a site quality "
                    "procedure",
                ],
                "failure_mode": "A false endpoint would risk unfixed dye.",
                "fallback": "Fail closed. Missing, frozen, drifting or "
                            "spiking data forces lockout, and the system "
                            "never releases without a named human.",
                "validation_plan": "Shadow against logged conductivity and "
                                   "residual colour, scored for false "
                                   "endpoints, before any release is "
                                   "permitted in Phase 4.",
            },
            {
                "name": "Decision optimiser",
                "purpose": "Select the lot order and process strategy with "
                           "the lowest total consequence, subject to hard "
                           "constraints.",
                "type": "Exhaustive enumeration at this queue size, so the "
                        "optimum is proven rather than approximated.",
                "limitations": [
                    "Single machine queue",
                    "Scalarised objective, so the weights encode a value "
                    "judgement - which is shown to the user, not hidden",
                ],
                "failure_mode": "A wrong weight produces a plan the planner "
                                "rejects.",
                "fallback": "Infeasible candidates can never be recommended, "
                            "and rejection is a recorded first-class outcome.",
                "validation_plan": "Shadow-mode agreement rate in Phase 2.",
            },
        ],
        "no_machine_learning_claim": (
            "ChangeLoop contains no trained machine-learning model and does "
            "not claim one. At this problem size a transparent deterministic "
            "optimiser is both correct and auditable, and it cannot "
            "hallucinate. If a learned component is added later it would be "
            "for forecasting effluent load, and it would be labelled and "
            "governed separately."
        ),
        "versioning": {
            "application_version": core.__version__,
            "calculation_version": core.CALCULATION_VERSION,
            "note": "Every exported record carries the calculation version, "
                    "so a historical figure can be reproduced with the logic "
                    "that generated it.",
        },
    }


def claim_register() -> Dict[str, Any]:
    """Every externally stated claim, with evidence level and safe wording."""
    return {
        "evidence_levels": {
            "L1": "Measured at a real asset",
            "L2": "Validated pilot data",
            "L3": "External authoritative source (regulation, court order)",
            "L4": "Published research or industry reporting",
            "L5": "Our model or simulation",
            "L6": "Our assumption",
        },
        "claims": [
            {
                "claim": "Tirupur operates under a court-mandated Zero "
                         "Liquid Discharge regime, because the Noyyal is "
                         "seasonal and cannot dilute treated effluent.",
                "level": "L3",
                "safe_wording": "State as regulatory and judicial fact.",
            },
            {
                "claim": "ZLD raised operating costs for Tirupur units by "
                         "about 25-30%, and dyed fabric cost by 12-15%, "
                         "reducible to around 5% with salt and water "
                         "recovery.",
                "level": "L4",
                "safe_wording": "Attribute to industry reporting. Give the "
                                "range, never a single figure.",
            },
            {
                "claim": "Recycled water costs roughly INR 120-150 per "
                         "kilolitre against INR 30-60 for fresh abstraction.",
                "level": "L4",
                "safe_wording": "Quote as a reported range, and state that it "
                                "is why avoiding demand beats recovering "
                                "water.",
            },
            {
                "claim": "RO reject volume equals salt mass divided by the "
                         "reject TDS ceiling, so saving water without saving "
                         "salt does not save evaporator energy.",
                "level": "L5",
                "safe_wording": "Present as a conclusion from salt mass "
                                "conservation, shown live in the product. The "
                                "ARITHMETIC is exact; the TDS ceiling is an "
                                "assumption and must be stated as such.",
            },
            {
                "claim": "Evaporating one cubic metre of reject needs about "
                         "179 kWh of thermal energy.",
                "level": "L5",
                "safe_wording": "Derived: latent heat 0.627 kWh/kg divided by "
                                "an assumed 4-effect steam economy of 3.5. "
                                "State both inputs whenever the figure is "
                                "used.",
            },
            {
                "claim": "On the reference order book ChangeLoop reduces "
                         "freshwater intake, evaporator steam and CO2e.",
                "level": "L5",
                "safe_wording": "Always say 'modelled, on a five-lot "
                                "reference order book'. Never 'achieves' or "
                                "'delivers'. Never imply a real plant. Quote "
                                "the figure the product returns, not a "
                                "remembered one.",
            },
            {
                "claim": "A scheduler that optimises dyehouse water alone "
                         "captures only a fraction of the available benefit.",
                "level": "L5",
                "safe_wording": "Attribute to our own ablation study, "
                                "reproducible at /api/ablation.",
            },
            {
                "claim": "CPCB has mandated online effluent monitoring for 17 "
                         "categories of highly polluting industry, so the "
                         "effluent data this product needs already exists.",
                "level": "L3",
                "safe_wording": "State as regulatory fact. It answers the "
                                "data-availability objection directly.",
            },
            {
                "claim": "Court-ordered closure of the Tirupur dyeing units "
                         "was reported to have cost around INR 11 billion in "
                         "exports and about 100,000 jobs.",
                "level": "L4",
                "safe_wording": "Attribute to the industry association's "
                                "representation. Use it to size the stake, "
                                "not as our own estimate.",
            },
        ],
        "forbidden_wordings": [
            "Any sentence implying a deployment, a customer or a measured "
            "result.",
            "'AI-powered' - there is no trained model in this system.",
            "'Blockchain' - the ledger is a hash chain and says so.",
            "Any named company's internal standard or charter.",
            "Any single-point figure where the source gives a range.",
        ],
    }


# ---------------------------------------------------------------------------

class App(SimpleHTTPRequestHandler):
    server_version = "ChangeLoop/" + API_VERSION

    # Speak HTTP/1.1. Every JSON response below sets an explicit
    # Content-Length, and SimpleHTTPRequestHandler does the same for static
    # files, so persistent connections are safe. Left at the HTTP/1.0 default
    # the server closes the socket after each response, which well-behaved
    # keep-alive clients mishandle.
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def handle_one_request(self):
        """Serve one request, treating a peer disconnect as normal.

        Every response path eventually writes to the socket - including the
        parent class's static-file serving, which this class does not wrap.
        A client that closes early (a refreshed browser tab, an aborted
        fetch) therefore raised out of several different places and printed
        a traceback each time. Catching it here covers all of them.
        """
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError,
                BrokenPipeError, TimeoutError):
            self.close_connection = True

    # -- helpers ----------------------------------------------------------

    def send_json(self, value: Any, code: int = 200) -> None:
        """Write a JSON response.

        A client that has gone away makes every socket write raise, and
        end_headers() writes too - guarding only the body left the header
        write to escape the handler and print a traceback. A disconnected
        peer is normal, not an error, so the whole write is guarded.
        """
        raw = json.dumps(value, default=str).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type",
                             "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-API-Version", API_VERSION)
            self.send_header("X-Request-ID", str(uuid.uuid4()))
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(raw)
        except (ConnectionResetError, ConnectionAbortedError,
                BrokenPipeError, OSError):
            self.close_connection = True

    def send_error_json(self, code: int, err_code: str, message: str,
                        extra: Optional[Dict[str, Any]] = None) -> None:
        payload = {"error": {"code": err_code, "message": message}}
        if extra:
            payload["error"].update(extra)
        self.send_json(payload, code)

    def read_body(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            return None, "Content-Length is not a number."
        if length < 0 or length > 1000000:
            return None, "Request body too large."
        if length == 0:
            return {}, None
        try:
            raw = self.rfile.read(length)
            body = json.loads(raw or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None, "Request body is not valid JSON."
        except OSError:
            return None, "Could not read the request body."
        if not isinstance(body, dict):
            return None, "Request body must be a JSON object."
        return body, None

    def _bool(self, body: Dict[str, Any], field: str) -> Optional[bool]:
        v = body.get(field)
        if isinstance(v, bool):
            return v
        if isinstance(v, str) and v.lower() in ("true", "false"):
            return v.lower() == "true"
        return None

    def _actor(self, body: Dict[str, Any], default: str) -> str:
        a = body.get("actor")
        if isinstance(a, str) and a.strip():
            return a.strip()[:120]
        return default

    # -- routing ----------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, HEAD, OPTIONS")
        self.end_headers()

    def do_HEAD(self):
        route = urlparse(self.path).path
        if route.startswith("/api/") or route == "/health":
            return self.send_json({"ok": True})
        self.path = "/frontend/index.html" if route == "/" else route
        return super().do_HEAD()

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        q = parse_qs(parsed.query)
        s = get_session()

        def one(name: str, default=None):
            return q.get(name, [default])[0]

        try:
            if route in ("/health", "/api/health"):
                return self.send_json({
                    "status": "ok",
                    "api_version": API_VERSION,
                    "application_version": core.__version__,
                    "calculation_version": core.CALCULATION_VERSION,
                    "ledger": provenance.verify_chain(),
                })

            if route == "/api/state":
                return self.send_json(s.state())

            if route == "/api/sites":
                return self.send_json({
                    "sites": basin.all_basins(),
                    "methodology": basin.methodology(),
                    "default": basin.DEFAULT_SITE,
                })

            if route == "/api/lots":
                return self.send_json({
                    "lots": [l.to_dict() for l in s.lots],
                    "arrival_order": s.arrival,
                    "machine": process.MACHINES["JET-01"].to_dict(),
                    "classification": "SIMULATED",
                })

            if route == "/api/changeover-matrix":
                return self.send_json({
                    "matrix": process.changeover_matrix(s.lots),
                    "note": "Computed on request from shade depth and shade "
                            "tolerance. This is not a stored lookup table.",
                })

            if route == "/api/strategies":
                return self.send_json({
                    "strategies": {k: v.to_dict()
                                   for k, v in process.strategies().items()},
                    "why_two_levers": (
                        "Counter-current reuse cuts water but not salt. "
                        "Low-electrolyte chemistry cuts salt but not water. "
                        "Because reject volume - and so evaporator steam - is "
                        "set by salt mass, these two levers have very "
                        "different climate consequences for a similar water "
                        "headline. That divergence is why a joint objective "
                        "is required."
                    ),
                })

            if route == "/api/insight/salt-is-water":
                return self.send_json(zld.sensitivity_salt_vs_water())

            if route == "/api/modes":
                return self.send_json({
                    "modes": {k: v.to_dict() for k, v
                              in scenarios.constraint_modes().items()}
                })

            if route == "/api/modes/compare":
                return self.send_json(
                    scenarios.compare_modes(one("site", s.site_id)))

            if route == "/api/sensitivity":
                return self.send_json(
                    scenarios.sensitivity(one("site", s.site_id)))

            if route == "/api/ablation":
                mode_id = one("mode", "NORMAL")
                if mode_id not in scenarios.constraint_modes():
                    return self.send_error_json(
                        400, "UNKNOWN_MODE", "Unknown constraint mode.",
                        {"valid": sorted(scenarios.constraint_modes())})
                return self.send_json(
                    scenarios.ablation(one("site", s.site_id), mode_id))

            if route == "/api/forecast":
                return self.send_json(s.forecast())

            if route == "/api/impact":
                return self.send_json(s.impact())

            if route == "/api/trace":
                return self.send_json(
                    ledger.trace(one("metric", "freshwater_avoided_l")))

            if route == "/api/evidence":
                return self.send_json({
                    "coefficients": factors.audit_trail(),
                    "summary": factors.evidence_summary(),
                    "basin_methodology": basin.methodology(),
                    "release_limits": telemetry.release_limits(),
                    "claim_register": claim_register(),
                })

            if route == "/api/ledger":
                try:
                    limit = min(500, max(1, int(one("limit", "80"))))
                except (TypeError, ValueError):
                    limit = 80
                return self.send_json({
                    "records": provenance.records(limit=limit),
                    "integrity": provenance.verify_chain(),
                })

            if route == "/api/ledger/verify":
                return self.send_json(provenance.verify_chain())

            if route == "/api/faults":
                return self.send_json({"faults": telemetry.fault_catalogue()})

            if route == "/api/pilot":
                return self.send_json(pilot_plan())

            if route == "/api/governance":
                return self.send_json(model_governance())

            if route == "/api/claims":
                return self.send_json(claim_register())

            if route == "/api/export":
                return self.send_json(s.export())

            if route == "/api/business-case":
                return self.send_json({
                    "status": "INPUT_REQUIRED",
                    "required_inputs": economics.REQUIRED_INPUTS,
                    "input_help": economics.INPUT_HELP,
                    "notice": "POST your site's own tariffs and volumes. "
                              "ChangeLoop will not compute a business case "
                              "from assumed values.",
                })

            if route == "/api/cluster-projection":
                def num(name, default):
                    try:
                        return float(one(name, str(default)))
                    except (TypeError, ValueError):
                        return default
                return self.send_json(economics.cluster_projection(
                    units=int(num("units", 400)),
                    lots_per_unit_per_year=int(num("lots", 900)),
                    freshwater_avoided_per_lot_l=num("water_per_lot", 1108.0),
                    salt_avoided_per_lot_kg=num("salt_per_lot", 12.5),
                ))

            if route.startswith("/api/"):
                return self.send_error_json(
                    404, "UNKNOWN_ROUTE",
                    "No such endpoint: {}".format(route))

        except Exception as exc:                       # noqa: BLE001
            return self.send_error_json(
                500, "INTERNAL_ERROR",
                "The request failed and no state was changed.",
                {"detail": str(exc)[:300]})

        self.path = "/frontend/index.html" if route == "/" else route
        return super().do_GET()

    def do_POST(self):
        route = urlparse(self.path).path
        body, err = self.read_body()
        if err:
            return self.send_error_json(400, "BAD_REQUEST", err)

        idem = (self.headers.get("Idempotency-Key")
                or body.get("idempotency_key"))
        cached = _idem_get(idem)
        if cached is not None:
            return self.send_json(cached)

        s = get_session()

        try:
            if route == "/api/session/reset":
                out = s.reset(body.get("site_id"))
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/session/site":
                site_id = body.get("site_id")
                if (not isinstance(site_id, str)
                        or site_id not in basin.BASINS):
                    return self.send_error_json(
                        400, "UNKNOWN_SITE",
                        "site_id must be one of the configured sites.",
                        {"valid": sorted(basin.BASINS.keys())})
                out = s.set_site(site_id)
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/optimise":
                weights = body.get("weights")
                mode_id = body.get("mode")
                if mode_id:
                    modes = scenarios.constraint_modes()
                    if mode_id not in modes:
                        return self.send_error_json(
                            400, "UNKNOWN_MODE", "Unknown constraint mode.",
                            {"valid": sorted(modes.keys())})
                    weights = modes[mode_id].weights.to_dict()
                if weights is not None and not isinstance(weights, dict):
                    return self.send_error_json(
                        400, "BAD_WEIGHTS",
                        "weights must be an object of numeric values.")
                out = s.run_optimisation(weights)
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/decision/sequence":
                approve = self._bool(body, "approve")
                if approve is None:
                    return self.send_error_json(
                        400, "MISSING_DECISION",
                        "Send approve as an explicit true or false. "
                        "ChangeLoop will not infer a human decision.")
                out = s.decide_sequence(
                    approve, actor=self._actor(body, "Shift planner"),
                    note=body.get("note"))
                if "error" in out:
                    return self.send_error_json(
                        409, "DECISION_BLOCKED", out["error"],
                        {"state": out.get("state")})
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/washoff/run":
                out = s.run_washoff(body.get("fault_mode"),
                                    body.get("lot_id"))
                if "error" in out:
                    return self.send_error_json(
                        400, "UNKNOWN_FAULT_MODE", out["error"],
                        {"valid": [f["mode"]
                                   for f in telemetry.fault_catalogue()]})
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/washoff/release":
                approve = self._bool(body, "approve")
                if approve is None:
                    return self.send_error_json(
                        400, "MISSING_DECISION",
                        "Send approve as an explicit true or false.")
                out = s.release_washoff(
                    approve, actor=self._actor(body, "Quality supervisor"),
                    note=body.get("note"))
                if "error" in out:
                    return self.send_error_json(
                        409, "RELEASE_BLOCKED", out["error"],
                        {"state": out.get("state")})
                _idem_put(idem, out)
                return self.send_json(out)

            if route == "/api/business-case":
                out = economics.business_case(body)
                code = 200 if out.get("status") == "CALCULATED" else 422
                _idem_put(idem, out)
                return self.send_json(out, code)

            return self.send_error_json(
                404, "UNKNOWN_ROUTE",
                "No such endpoint: {}".format(route))

        except Exception as exc:                       # noqa: BLE001
            return self.send_error_json(
                500, "INTERNAL_ERROR",
                "The request failed. No partial state was committed.",
                {"detail": str(exc)[:300]})


class Server(ThreadingHTTPServer):
    """Threading server with a listen backlog big enough for a real client.

    socketserver defaults request_queue_size to 5. The Scale view alone opens
    five concurrent API calls, and a browser adds static assets on top, so
    the backlog overflowed and the operating system refused connections -
    which surfaced as intermittent "connection refused" rather than as a
    server error. 128 is ample for a single-operator demonstration server.
    """
    request_queue_size = 128
    daemon_threads = True
    allow_reuse_address = True


def main() -> None:
    import os
    os.chdir(ROOT)
    provenance.init_db()
    port = int(os.environ.get("PORT", "8000"))
    print("ChangeLoop {} - http://localhost:{}".format(core.__version__, port))
    print("Hero use case: reactive dyeing under a Zero Liquid Discharge "
          "mandate")
    try:
        Server(("", port), App).serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
