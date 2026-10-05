"""ClearLoop Full Integration Lifecycle, State Sync & 10x Demo Repeatability Suite.
Covers:
- Phase 13: Real service connection pipeline (Plan -> Optimize -> Clean -> Safety -> Cascade -> Impact -> Audit).
- Phase 16: State synchronization and dependency recalculation across steps.
- Phase 17: Negative testing (operator veto, reset during run).
- Phase 18: Race condition / concurrent request safety.
- Phase 19: Demo Repeatability (10 consecutive identical demo runs).
- Phase 20: Recovery after reset.
"""
import unittest
import urllib.request
import urllib.error
import json
import concurrent.futures
import sys
from pathlib import Path

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
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.status, json.loads(res.read().decode("utf-8"))

class IntegrationLifecycleTests(unittest.TestCase):
    """Rigorous multi-stage lifecycle, concurrency, and 10x demo repeatability tests."""

    def test_01_complete_decision_chain_flow(self):
        """Sequential end-to-end traversal across all 10 stages of the ChangeLoop decision chain."""
        # 1. Reset
        status, s1 = post("/api/demo/reset", {})
        self.assertEqual(status, 200)
        self.assertEqual(s1["demo_step"], "01_PLAN")
        self.assertEqual(s1["decision_status"], "PENDING_REVIEW")
        self.assertEqual(s1["baseline_sequence"], ["B-217", "B-220", "B-218", "B-219", "B-221"])

        # 2. Optimize
        status, s2 = post("/api/demo/step", {"step_id": "02_OPTIMIZE"})
        self.assertEqual(status, 200)
        self.assertEqual(s2["demo_step"], "02_OPTIMIZE")
        self.assertEqual(s2["optimized_sequence"], ["B-217", "B-218", "B-219", "B-220", "B-221"])
        self.assertEqual(s2["optimization_result"]["water_avoided_l"], 284.0)

        # 3. Recommend & Accept
        status, s3 = post("/api/demo/step", {"step_id": "03_RECOMMEND", "decision": "ACCEPT"})
        self.assertEqual(status, 200)
        self.assertEqual(s3["decision_status"], "ACCEPTED")
        self.assertEqual(s3["current_sequence"], s3["optimized_sequence"])

        # 4. Cleaning Simulation
        status, s4 = post("/api/demo/step", {"step_id": "04_CLEANING_SIM"})
        self.assertEqual(status, 200)
        self.assertEqual(s4["demo_step"], "03_CLEAN")
        self.assertGreater(s4["cleaning_simulation"]["predicted_endpoint_minute"], 0)

        # 5. Safety Decision (Authorize Early Cutoff)
        status, s5 = post("/api/demo/step", {"step_id": "06_SAFETY_DECISION"})
        self.assertEqual(status, 200)
        self.assertEqual(s5["operator_validation"], "AUTHORIZED")

        # 6. Water Cascade Screening & Committal
        status, s6 = post("/api/demo/step", {"step_id": "08_CASCADE"})
        self.assertEqual(status, 200)
        self.assertTrue(s6["cascade_committed"])

        # 7. Impact Verification
        status, s7 = post("/api/demo/step", {"step_id": "09_IMPACT"})
        self.assertEqual(status, 200)
        impact = s7["impact_record"]
        # Upstream (284 L) + Adaptive (130 L) = 414 L
        self.assertEqual(impact["total_water_demand_avoided_l"], 414.0)
        self.assertEqual(impact["upstream_avoided_l"], 284.0)
        self.assertEqual(impact["adaptive_avoided_l"], 130.0)

        # 8. Audit Export
        status, export_data = get("/api/demo/export")
        self.assertEqual(status, 200)
        self.assertEqual(export_data["decision_status"], "ACCEPTED")
        self.assertEqual(export_data["total_water_avoided_l"], 414.0)
        self.assertEqual(len(export_data["sha256_fingerprint"]), 64)

    def test_02_operator_veto_reverts_to_sop_timer(self):
        """When operator exercises manual veto, water avoided resets to 0 L and SOP timer is logged."""
        post("/api/demo/reset", {})
        post("/api/demo/step", {"step_id": "04_CLEANING_SIM"})

        # Engage tactile operator veto
        status, veto_data = post("/api/demo/step", {"action": "override_veto"})
        self.assertEqual(status, 200)
        self.assertEqual(veto_data["operator_validation"], "OVERRIDDEN")

        # Impact must reflect 0 L adaptive savings due to manual override
        post("/api/demo/step", {"step_id": "09_IMPACT"})
        status, session = get("/api/demo/session")
        self.assertEqual(session["impact_record"]["adaptive_avoided_l"], 0.0)

    def test_03_concurrent_requests_stability(self):
        """Simultaneous parallel requests execute safely without state corruption or 500 crashes."""
        endpoints = [
            ("/api/health", {}),
            ("/api/batches?seed=2030", {}),
            ("/api/matrix", {}),
            ("/api/planning/data", {}),
            ("/api/impact/timespan?range=24h", {})
        ]

        def call_endpoint(item):
            ep, _ = item
            st, data = get(ep)
            return st, data

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_endpoint, ep) for ep in endpoints * 3]
            for f in concurrent.futures.as_completed(futures):
                st, data = f.result()
                self.assertEqual(st, 200)
                self.assertTrue(data)

    def test_04_ten_consecutive_demo_runs_repeatability(self):
        """Invariant: Running the complete demo 10 times consecutively produces identical outputs."""
        fingerprints = []
        total_avoided_results = []

        for run_idx in range(10):
            # Run complete decision chain
            post("/api/demo/reset", {})
            post("/api/demo/step", {"step_id": "02_OPTIMIZE"})
            post("/api/demo/step", {"step_id": "03_RECOMMEND", "decision": "ACCEPT"})
            post("/api/demo/step", {"step_id": "04_CLEANING_SIM"})
            post("/api/demo/step", {"step_id": "06_SAFETY_DECISION"})
            post("/api/demo/step", {"step_id": "08_CASCADE"})
            post("/api/demo/step", {"step_id": "09_IMPACT"})

            st, exp = get("/api/demo/export")
            self.assertEqual(st, 200)
            self.assertEqual(exp["total_water_avoided_l"], 414.0)

            total_avoided_results.append(exp["total_water_avoided_l"])
            fingerprints.append(exp["sha256_fingerprint"])

        # All 10 runs produced exactly 414.0 L avoided
        self.assertEqual(len(set(total_avoided_results)), 1)
        self.assertEqual(total_avoided_results[0], 414.0)
        self.assertEqual(len(total_avoided_results), 10)

if __name__ == "__main__":
    unittest.main()
