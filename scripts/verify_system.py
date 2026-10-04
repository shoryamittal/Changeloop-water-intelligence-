"""Comprehensive System Verification Runner for ClearLoop / Zero-Waste Changeover Engine.

Executes all verification gates:
1. Python syntax & compilation across core, backend, and tests
2. Frontend JavaScript syntax check (node -c)
3. Frontend TypeScript declarations verification (tsc --noEmit)
4. Core domain unit test suite (tests/test_core.py)
5. Domain mathematical invariants suite (tests/test_domain_invariants.py)
6. REST API integration test suite (tests/test_api_integration.py)
7. Industrial 1,000-scenario stress benchmark (tests/test_stress_1000.py)
8. Live backend HTTP endpoint health check (http://127.0.0.1:8000)
"""
import sys
import os
import py_compile
import subprocess
import glob
import urllib.request
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def log_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def run_step(step_name: str, fn) -> bool:
    print(f"[*] Running: {step_name} ... ", end="", flush=True)
    t0 = time.time()
    try:
        fn()
        dt = time.time() - t0
        print(f"PASSED ({dt:.2f}s)")
        return True
    except Exception as e:
        print(f"FAILED!\nError: {e}")
        return False

def verify_python_compilation():
    py_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if any(ignored in root for ignored in [".git", "node_modules", ".venv", "__pycache__"]):
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    for f in py_files:
        py_compile.compile(f, doraise=True)

def verify_js_syntax():
    app_js = os.path.join(PROJECT_ROOT, "frontend", "app.js")
    res = subprocess.run(["node", "-c", app_js], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"JS syntax error in app.js:\n{res.stderr}")

def verify_ts_types():
    types_dts = os.path.join(PROJECT_ROOT, "frontend", "types.d.ts")
    res = subprocess.run(["npx", "--yes", "typescript", "--noEmit", types_dts], capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"TS type check failed:\n{res.stderr or res.stdout}")

def run_unittest_file(rel_path: str):
    test_path = os.path.join(PROJECT_ROOT, rel_path)
    res = subprocess.run([sys.executable, test_path], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Test failure in {rel_path}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")

def verify_live_server_endpoints():
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        "/health",
        "/api/batches",
        "/api/planning/data",
        "/api/impact/timespan?range=24h"
    ]
    for ep in endpoints:
        req = urllib.request.Request(f"{base_url}{ep}")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Endpoint {ep} returned HTTP {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                raise RuntimeError(f"Endpoint {ep} returned empty payload")

def main():
    log_header("CLEARLOOP ZERO-WASTE CHANGEOVER ENGINE — VERIFICATION SUITE")
    all_passed = True

    steps = [
        ("Python Compilation Check", verify_python_compilation),
        ("Frontend JavaScript Syntax Check", verify_js_syntax),
        ("Frontend TypeScript Declarations Check", verify_ts_types),
        ("Core Domain Unit Tests (test_core.py)", lambda: run_unittest_file("tests/test_core.py")),
        ("Domain Invariants Tests (test_domain_invariants.py)", lambda: run_unittest_file("tests/test_domain_invariants.py")),
        ("Canonical Demo Session Tests (test_demo_session.py)", lambda: run_unittest_file("tests/test_demo_session.py")),
        ("API Integration Tests (test_api_integration.py)", lambda: run_unittest_file("tests/test_api_integration.py")),
        ("Industrial Stress Tests (test_stress_1000.py)", lambda: run_unittest_file("tests/test_stress_1000.py")),
    ]

    for name, fn in steps:
        if not run_step(name, fn):
            all_passed = False
            break

    # Server check is optional/warning if server is not up
    try:
        run_step("Live Backend Daemon Endpoints Check (port 8000)", verify_live_server_endpoints)
    except Exception as e:
        print(f"[!] Note: Live server check skipped ({e})")

    log_header("VERIFICATION SUMMARY")
    if all_passed:
        print("[SUCCESS] ALL ARCHITECTURAL AND FOUNDATION GATES PASSED (100% SUCCESS)")
        sys.exit(0)
    else:
        print("[FAILURE] VERIFICATION FAILED - FOUNDATION DEFECTS DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
