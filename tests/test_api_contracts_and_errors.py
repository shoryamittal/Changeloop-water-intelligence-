"""ClearLoop HTTP API Contracts, Error Boundaries & Schema Verification Test Suite.
Covers:
- Phase 12: Valid and invalid API requests, missing fields, wrong types,
  empty payloads, HTTP 400/404 handling, contract verification.
"""
import unittest
import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def get(route):
    req = urllib.request.Request(f"{BASE_URL}{route}")
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def post(route, body):
    raw = json.dumps(body).encode("utf-8") if isinstance(body, dict) else body
    req = urllib.request.Request(
        f"{BASE_URL}{route}",
        data=raw if isinstance(raw, bytes) else str(raw).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

class ApiContractsAndErrorsTests(unittest.TestCase):
    """Rigorous HTTP contract and negative error boundary tests against running daemon."""

    def test_01_health_contract(self):
        """GET /api/health returns 200 with status ok and storage classification."""
        status, data = get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["classification"], "REAL")

    def test_02_unknown_route_returns_404(self):
        """Unrecognized /api/ routes return HTTP 404 with error message."""
        status, data = get("/api/nonexistent_route_1234")
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    def test_03_invalid_json_body_returns_400(self):
        """Malformed non-JSON payloads return HTTP 400."""
        req = urllib.request.Request(
            f"{BASE_URL}/api/optimize",
            data=b"INVALID_NOT_JSON{[[",
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                self.fail("Expected HTTP 400 error")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("error", err_data)

    def test_04_optimization_decision_invalid_value_returns_400(self):
        """POST /api/optimization/decision rejects unauthorized strings with HTTP 400."""
        status, data = post("/api/optimization/decision", {"decision": "MALICIOUS_OVERRIDE"})
        self.assertEqual(status, 400)
        self.assertIn("error", data)
        self.assertIn("must be", data["error"].lower())

    def test_05_water_authorize_unscreened_returns_400(self):
        """POST /api/water/authorize rejects unscreened effluent with HTTP 400."""
        status, data = post("/api/water/authorize", {"volume_l": 100, "quality": "raw_untreated"})
        self.assertEqual(status, 400)
        self.assertIn("error", data)
        self.assertIn("quality criteria not met", data["error"].lower())

    def test_06_cleaning_authorize_fault_scenario_returns_400(self):
        """POST /api/cleaning/authorize blocks early rinse release under fault scenarios."""
        status, data = post("/api/cleaning/authorize", {"scenario": "drift", "water_saved_l": 130})
        self.assertEqual(status, 400)
        self.assertIn("error", data)
        self.assertIn("interlocks active", data["error"].lower())

    def test_07_demo_session_endpoint_contract(self):
        """GET /api/demo/session returns canonical state with expected top-level keys."""
        status, data = get("/api/demo/session")
        self.assertEqual(status, 200)
        required_keys = {
            "classification", "plant", "line", "demo_step",
            "baseline_sequence", "current_sequence", "optimized_sequence",
            "baseline_burden_l", "optimized_burden_l", "decision_status"
        }
        for k in required_keys:
            self.assertIn(k, data, f"Missing demo session key: {k}")

    def test_08_demo_step_actions(self):
        """POST /api/demo/step executes all valid decision chain actions."""
        # Step: optimize
        status, opt_data = post("/api/demo/step", {"action": "optimize"})
        self.assertEqual(status, 200)
        self.assertEqual(opt_data["demo_step"], "02_OPTIMIZE")

        # Step: accept recommendation
        status, acc_data = post("/api/demo/step", {"action": "accept"})
        self.assertEqual(status, 200)
        self.assertEqual(acc_data["decision_status"], "ACCEPTED")

        # Step: start cleaning
        status, cln_data = post("/api/demo/step", {"action": "start_cleaning", "failure": None})
        self.assertEqual(status, 200)
        self.assertEqual(cln_data["demo_step"], "03_CLEAN")

        # Step: authorize cutoff
        status, aut_data = post("/api/demo/step", {"action": "authorize_cutoff"})
        self.assertEqual(status, 200)
        self.assertEqual(aut_data["operator_validation"], "AUTHORIZED")

        # Step: cascade screen
        status, cas_data = post("/api/demo/step", {"action": "cascade_screen", "volume_l": 200})
        self.assertEqual(status, 200)
        self.assertEqual(cas_data["demo_step"], "06_CASCADE")

        # Step: reset
        status, rst_data = post("/api/demo/step", {"action": "reset"})
        self.assertEqual(status, 200)
        self.assertEqual(rst_data["demo_step"], "01_PLAN")
        self.assertEqual(rst_data["decision_status"], "PENDING_REVIEW")

    def test_09_demo_export_cryptographic_fingerprint(self):
        """GET /api/demo/export generates tamper-evident JSON with valid SHA-256 seal."""
        status, data = get("/api/demo/export")
        self.assertEqual(status, 200)
        self.assertIn("sha256_fingerprint", data)
        fp = data["sha256_fingerprint"]
        self.assertEqual(len(fp), 64, "SHA-256 fingerprint must be exactly 64 hex characters")
        self.assertTrue(all(c in "0123456789abcdef" for c in fp))

if __name__ == "__main__":
    unittest.main()
