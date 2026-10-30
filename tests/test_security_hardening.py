# -*- coding: utf-8 -*-
"""ChangeLoop - Institutional Security Hardening & DevSecOps Test Suite."""
import unittest
import os
import re
from pathlib import Path
from http.server import HTTPServer
import threading
import urllib.request
import urllib.error
import json

from backend.server import App, _load_env_file, ROOT
from core import provenance


class TestPhase1SecretsAndGitHygiene(unittest.TestCase):
    def test_gitignore_contains_all_critical_rules(self):
        gitignore_path = ROOT / ".gitignore"
        self.assertTrue(gitignore_path.is_file(), ".gitignore must exist")
        content = gitignore_path.read_text(encoding="utf-8")

        required_patterns = [
            ".env",
            ".env.local",
            "*.key",
            "*.pem",
            "*.db",
            "*.sqlite",
            "*.log",
            "__pycache__",
            ".DS_Store",
            "Thumbs.db",
        ]
        for pat in required_patterns:
            self.assertIn(pat, content, f"Missing {pat} in .gitignore")

    def test_no_hardcoded_credentials_in_source(self):
        secret_patterns = [
            re.compile(r'(?i)(?:api_key|apikey|secret|password|passwd|jwt_secret|private_key)\s*[:=]\s*["\'][^"\']{8,}["\']'),
            re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
        ]
        # Scanned files
        for ext in (".py", ".js", ".json", ".yml", ".yaml"):
            for p in ROOT.rglob(f"*{ext}"):
                if any(ignored in p.parts for ignored in (".git", "node_modules", "__pycache__", ".gemini", "submission")):
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
                for pat in secret_patterns:
                    matches = pat.findall(text)
                    for m in matches:
                        # Exclude published constants or test fixtures
                        if "changeloop-demonstration-key" in m or "CHANGE_LOOP" in m:
                            continue
                        self.fail(f"Potential hardcoded secret detected in {p}: {m}")

    def test_env_example_has_no_active_secrets(self):
        env_example = ROOT / ".env.example"
        self.assertTrue(env_example.is_file())
        content = env_example.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("CHANGELOOP_LEDGER_KEY="):
                val = line.split("=", 1)[1].strip()
                self.assertEqual(val, "", ".env.example must never contain an active ledger signing key")


class TestPhase2HTTPAndNetworkHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), App)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path: str):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url)
        return urllib.request.urlopen(req, timeout=5)

    def test_security_headers_in_responses(self):
        res = self._get("/api/health")
        headers = dict(res.headers)

        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("geolocation=()", headers.get("Permissions-Policy", ""))
        self.assertIn("default-src 'self'", headers.get("Content-Security-Policy", ""))

    def test_path_traversal_and_sensitive_file_blocking(self):
        forbidden_paths = [
            "/core/factors.py",
            "/backend/server.py",
            "/data/changeloop_ledger.db",
            "/.env",
            "/.env.example",
            "/../server.py",
            "/%2e%2e/server.py",
            "/Dockerfile",
        ]
        for path in forbidden_paths:
            url = f"http://127.0.0.1:{self.port}{path}"
            req = urllib.request.Request(url)
            try:
                urllib.request.urlopen(req, timeout=5)
                self.fail(f"Path {path} should have been forbidden (403/404)")
            except urllib.error.HTTPError as e:
                self.assertIn(e.code, (403, 404), f"Path {path} returned unexpected status {e.code}")

    def test_request_body_size_protection(self):
        url = f"http://127.0.0.1:{self.port}/api/optimise"
        # 1.1 MB oversized payload
        huge_data = json.dumps({"weights": {"water": 1.0}, "padding": "X" * 1100000}).encode("utf-8")
        req = urllib.request.Request(url, data=huge_data, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("Oversized payload > 1MB should be rejected")
        except (urllib.error.HTTPError, ConnectionResetError, ConnectionAbortedError) as e:
            if isinstance(e, urllib.error.HTTPError):
                self.assertEqual(e.code, 400)

    def test_tamper_detection(self):
        # Genesis block must be valid
        integrity = provenance.verify_chain()
        self.assertTrue(integrity["intact"])

        # Tampering must fail verification
        tamper_res = provenance.tamper_record(seq=1, new_detail="FORGED: Zero salt discharged")
        try:
            post_tamper = provenance.verify_chain()
            self.assertFalse(post_tamper["intact"], "Chain must detect tampering")
        finally:
            # Restore clean state
            provenance.reset()
            self.assertTrue(provenance.verify_chain()["intact"])


if __name__ == "__main__":
    unittest.main()
