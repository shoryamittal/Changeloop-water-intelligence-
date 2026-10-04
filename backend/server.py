"""ClearLoop Demonstration HTTP Server & REST API.
Delegates all combinatorial optimization, physical telemetry simulation,
cascade segregation, and ESG ledger accounting to the core domain engine.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, uuid, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core
from core import (
    generate_batches as batches,
    calculate_burden as burden,
    optimize_schedule as sequence_payload,
    simulate_cleaning_cycle as cleaning,
    analyze_cascade as cascade,
    calculate_impact as impact,
    calculate_impact_timespan_ledger,
    calculate_business_case as business_case,
    get_transition_matrix as transition_matrix,
    init_db,
    record_audit_event as record,
    get_audit_events as audit_events,
    RULES
)

def pilot():
    return {
        "classification": "ARCHITECTED",
        "notice": "Target integration architecture — not connected to L'Oréal systems.",
        "mode": "Advisory only; existing validated procedure remains authoritative.",
        "scope": "One line and selected quality-approved transitions.",
        "timeline_weeks": 6,
        "phases": [
            {"week": "Week 01", "name": "Baseline Metering", "objective": "Calibrate sub-meters and establish baseline CIP volumes."},
            {"week": "Week 02-03", "name": "Shadow Optimization", "objective": "Run ClearLoop in shadow mode alongside MES planner."},
            {"week": "Week 04-05", "name": "Controlled Advisory Pilot", "objective": "Execute approved transitions with operator sign-off."},
            {"week": "Week 06", "name": "Validation & Audit", "objective": "Audit water savings, quality release, and operator feedback."}
        ],
        "success_criteria": [
            "Zero quality deviations or microbiological failures",
            "100% deadline compliance and packaging line availability",
            "Measurable reduction relative to metered baseline (>15% modeled)",
            "Operational acceptance by shift supervisors & CIP operators",
            "Adequate data availability (>99.5% sensor telemetry uptime)"
        ],
        "stop_conditions": [
            "Any quality deviation or out-of-spec micro release",
            "Sensor telemetry dropout exceeding 60 seconds",
            "Unvalidated reuse route or cross-contamination risk",
            "Planner manual override without documented rationale",
            "Production line throughput hazard or scheduling conflict"
        ]
    }

def models():
    return {
        "classification": "ARCHITECTED",
        "endpoint_model": {
            "status": "Not trained on plant data",
            "approach": "Physics-informed rules and synthetic signal simulation only",
            "release_authority": "Site-specific validated criteria and human approval"
        },
        "monitoring": {
            "track": ["data availability", "invalid reading rate", "operator override rate", "prediction error after ground truth exists"],
            "action": "Flag model; revert to validated procedure"
        }
    }

class App(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

    def send_json(self, value, code=200):
        raw = json.dumps(value).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        self.send_header("X-Request-ID", str(uuid.uuid4()))
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        self.end_headers()

    def do_HEAD(self):
        route = urlparse(self.path).path
        self.path = "/frontend/index.html" if route == "/" else route
        return super().do_HEAD()

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/api/batches":
            seed = 2030
            if "seed" in query:
                try: seed = int(query["seed"][0])
                except ValueError: pass
            return self.send_json({"classification": "SYNTHETIC_DATA", "items": batches(seed)})

        if route == "/api/cleaning":
            failure = query.get("failure", [None])[0]
            seed = 2026
            if "seed" in query:
                try: seed = int(query["seed"][0])
                except ValueError: pass
            return self.send_json(cleaning(seed=seed, failure=failure))

        if route == "/api/audit-log":
            return self.send_json({"items": audit_events(), "storage": "sqlite with in-memory fallback"})

        if route == "/api/assumptions":
            return self.send_json({"classification": "ENGINEERING_ASSUMPTION", "rules": RULES})

        if route == "/api/pilot":
            return self.send_json(pilot())

        if route == "/api/models":
            return self.send_json(models())

        if route == "/api/matrix":
            return self.send_json(transition_matrix())

        if route == "/api/impact/timespan":
            range_key = query.get("range", ["24h"])[0]
            return self.send_json(calculate_impact_timespan_ledger(range_key))

        if route == "/api/stress-test":
            rf = ROOT / "data" / "stress_test_1000_report.json"
            if rf.exists():
                return self.send_json(json.loads(rf.read_text(encoding="utf-8")))
            return self.send_json({"status": "RUN_REQUIRED"})

        if route == "/api/business-case":
            return self.send_json({
                "classification": "ILLUSTRATIVE_SCENARIO",
                "status": "INPUT REQUIRED",
                "required_fields": ["changeovers_per_year", "water_avoided_per_changeover_l", "water_cost_per_l", "implementation_cost", "annual_software_cost"],
                "notice": "Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions."
            })

        if route == "/api/health":
            return self.send_json({"status": "ok", "classification": "REAL", "storage": "sqlite with in-memory fallback"})

        if route.startswith("/api/"):
            return self.send_json({"error": "Unknown route"}, 404)

        self.path = "/frontend/index.html" if route == "/" else route
        return super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "Invalid JSON request body"}, 400)

        route = urlparse(self.path).path

        if route == "/api/optimize":
            record("OPTIMIZE_RUN", f"Executed schedule optimization (seed={body.get('seed', 2030)})")
            return self.send_json(sequence_payload(body))

        if route == "/api/cleaning/start":
            failure = body.get("failure")
            seed = body.get("seed", 2026)
            record("CLEANING_SIMULATION", f"Started physical CIP simulation (failure={failure or 'none'})")
            return self.send_json(cleaning(seed=seed, failure=failure))

        if route == "/api/water/analyze":
            record("WATER_SCREEN", f"Effluent segregation screen for volume={body.get('volume_l', 120)} L")
            return self.send_json(cascade(body))

        if route == "/api/impact/calculate":
            return self.send_json(impact(body))

        if route == "/api/impact/timespan":
            range_key = body.get("range", "24h")
            return self.send_json(calculate_impact_timespan_ledger(range_key))

        if route == "/api/business-case":
            res = business_case(body)
            if res.get("status") == "CALCULATED":
                record("BUSINESS_CASE", "Calculated facility ROI from user inputs")
            return self.send_json(res)

        if route == "/api/optimization/decision":
            decision = body.get("decision") if isinstance(body, dict) else None
            if decision not in {"accept_recommendation", "retain_baseline"}:
                return self.send_json({"error": "Decision must be accept_recommendation or retain_baseline."}, 400)
            event = record("PLANNER_DECISION", f"{decision} for synthetic optimization {body.get('optimization_id', 'unknown')}")
            return self.send_json({
                "classification": "SIMULATED",
                "notice": "Planner decision recorded in local session audit trail; no plant schedule was changed.",
                "event": event
            })

        return self.send_json({"error": "Unknown route"}, 404)

if __name__ == "__main__":
    import os
    os.chdir(ROOT)
    init_db()
    print("ClearLoop running at http://localhost:8000")
    ThreadingHTTPServer(("", 8000), App).serve_forever()
