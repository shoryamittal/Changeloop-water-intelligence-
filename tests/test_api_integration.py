"""ClearLoop HTTP API Integration & Contract Test Suite.
Validates HTTP endpoints, payload responses, error boundaries,
and durable audit logging over live HTTP requests.
"""
import unittest
import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def get(route):
    req = urllib.request.Request(f"{BASE_URL}{route}")
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.status, json.loads(res.read().decode("utf-8"))

def post(route, body):
    raw = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{route}",
        data=raw,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

class ApiIntegrationTests(unittest.TestCase):
    def test_01_health_check(self):
        status, data = get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")

    def test_02_batches_endpoint(self):
        status, data = get("/api/batches?seed=2030")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 12)
        self.assertEqual(data["items"][0]["id"], "B-01")

    def test_03_planning_data_endpoint(self):
        status, data = get("/api/planning/data")
        self.assertEqual(status, 200)
        self.assertIn("batches", data)
        self.assertIn("B-217", data["batches"])
        self.assertEqual(len(data["optimal_sequence"]), 5)

    def test_04_optimize_endpoint(self):
        status, data = post("/api/optimize", {"seed": 2030, "algorithm": "two_opt"})
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "FEASIBLE")
        self.assertTrue(data["optimization_id"])
        self.assertLessEqual(data["optimized"]["objective"], data["baseline"]["objective"])

    def test_05_cleaning_simulation_endpoint(self):
        status, data = post("/api/cleaning/start", {"seed": 2026, "failure": None})
        self.assertEqual(status, 200)
        self.assertEqual(data["baseline_minutes"], 42)
        self.assertFalse(data["safety_gate"]["automatic_release"])
        self.assertEqual(len(data["readings"]), 42)

    def test_06_water_analyze_and_authorize(self):
        status, data = post("/api/water/analyze", {"volume_l": 210, "quality": "screened"})
        self.assertEqual(status, 200)
        self.assertEqual(len(data["streams"]), 3)
        self.assertEqual(data["available_volume_l"], 210)

        # Authorize valid stream
        auth_status, auth_data = post("/api/water/authorize", {"volume_l": 145, "quality": "screened"})
        self.assertEqual(auth_status, 200)
        self.assertEqual(auth_data["status"], "AUTHORIZED")

        # Block unvalidated stream
        block_status, block_data = post("/api/water/authorize", {"volume_l": 145, "quality": "unknown"})
        self.assertEqual(block_status, 400)
        self.assertEqual(block_data["status"], "BLOCKED")

    def test_07_durable_audit_record(self):
        test_action = f"TEST_AUDIT_{int(time.time())}"
        status, data = post("/api/audit/record", {"action": test_action, "detail": "API integration verification"})
        self.assertEqual(status, 200)
        self.assertEqual(data["event"]["action"], test_action)

        # Verify event appears in audit log query
        log_status, log_data = get("/api/audit-log")
        self.assertEqual(log_status, 200)
        self.assertTrue(any(e["action"] == test_action for e in log_data["items"]))

    def test_08_timespan_impact_ledger(self):
        for span in ["24h", "7d", "30d", "90d"]:
            status, data = get(f"/api/impact/timespan?range={span}")
            self.assertEqual(status, 200)
            self.assertEqual(data["range"], span)
            self.assertGreater(data["savedL"], 0)
            # Verify mass-balance invariant
            self.assertAlmostEqual(
                data["grossConsumedL"],
                data["baselineDemandL"] + data["upstreamDeltaL"] + data["adaptiveDeltaL"],
                delta=0.2
            )

if __name__ == "__main__":
    unittest.main()
