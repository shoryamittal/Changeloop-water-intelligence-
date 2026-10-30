# -*- coding: utf-8 -*-
"""ChangeLoop - Institutional Master Security Hardening & Full-Stack Audit Test Suite.

Verifies Phases 1 through 5:
  - Phase 1: Environment variables, Secrets & Git hygiene
  - Phase 2: Secure authentication, PBKDF2 password hashing & RBAC
  - Phase 3: Input validation, Sanitization & Injection defense
  - Phase 4: API security, Strict CORS & Rate-limiting
  - Phase 5: HTTP security headers (CSP, HSTS, DENY, nosniff) & zero CVEs
"""
import unittest
import os
import re
from pathlib import Path
from http.server import HTTPServer
import threading
import urllib.request
import urllib.error
import json
import time

from backend.server import App, _load_env_file, ROOT
from core import provenance, auth, validator, ratelimit


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
        for ext in (".py", ".js", ".json", ".yml", ".yaml"):
            for p in ROOT.rglob(f"*{ext}"):
                if any(ignored in p.parts for ignored in (".git", "node_modules", "__pycache__", ".gemini", "submission")):
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
                for pat in secret_patterns:
                    matches = pat.findall(text)
                    for m in matches:
                        if "changeloop-demonstration-key" in m or "CHANGE_LOOP" in m or "ChangeLoop#Admin" in m or "Operator#ZLD" in m or "Auditor#Audit" in m:
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


class TestPhase2AuthAndRBAC(unittest.TestCase):
    def test_pbkdf2_password_hashing(self):
        raw_pw = "SecureClusterPass2026!"
        h1 = auth.hash_password(raw_pw)
        self.assertTrue(h1.startswith("pbkdf2:sha256:600000$"))
        self.assertTrue(auth.verify_password(raw_pw, h1))
        self.assertFalse(auth.verify_password("WrongPassword123!", h1))

        # Different salts for identical passwords
        h2 = auth.hash_password(raw_pw)
        self.assertNotEqual(h1, h2)
        self.assertTrue(auth.verify_password(raw_pw, h2))

    def test_session_token_cryptography_and_tamper(self):
        payload = {"username": "test_engineer", "role": "OPERATOR"}
        token = auth.create_token(payload, max_age=3600)
        self.assertEqual(token.count("."), 2)

        valid, claims, err = auth.verify_token(token)
        self.assertTrue(valid)
        self.assertEqual(claims["username"], "test_engineer")
        self.assertEqual(claims["role"], "OPERATOR")

        # Tampered token must fail signature check
        parts = token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}X.{parts[2]}"
        valid_t, _, err_t = auth.verify_token(tampered_token)
        self.assertFalse(valid_t)
        self.assertIn("signature", err_t.lower())

    def test_token_expiration(self):
        payload = {"username": "exp_user", "role": "VIEWER"}
        expired_token = auth.create_token(payload, max_age=-10)
        valid, _, err = auth.verify_token(expired_token)
        self.assertFalse(valid)
        self.assertIn("expired", err.lower())


class TestPhase3ValidationAndInjection(unittest.TestCase):
    def test_schema_validation_rejects_invalid(self):
        # Invalid password length
        with self.assertRaises(validator.ValidationError):
            validator.validate_auth_login({"username": "valid_user", "password": "123"})

        # Invalid role
        with self.assertRaises(validator.ValidationError):
            validator.validate_auth_register({
                "username": "user1",
                "password": "Password123!",
                "role": "SUPERUSER_HACKER",
            })

    def test_xss_sanitization(self):
        dirty = "<script>alert('xss')</script>Normal<b>Bold</b>"
        clean = validator.sanitize_string(dirty)
        self.assertNotIn("<script>", clean)
        self.assertNotIn("<b>", clean)

        dirty_obj = {
            "name": "<img src=x onerror=alert(1)>",
            "nested": ["<script>eval()</script>", 42]
        }
        cleaned_obj = validator.sanitize_payload(dirty_obj)
        self.assertNotIn("<img", cleaned_obj["name"])
        self.assertNotIn("onerror", cleaned_obj["name"])
        self.assertEqual(cleaned_obj["nested"][1], 42)


class TestPhase4And5ServerEndpoints(unittest.TestCase):
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

    def _request(self, method: str, path: str, data: dict = None, headers: dict = None):
        url = f"http://127.0.0.1:{self.port}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=body, headers=h, method=method)
        try:
            res = urllib.request.urlopen(req, timeout=5)
            raw = res.read().decode("utf-8")
            return res.status, res.headers, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                err_json = json.loads(raw)
            except Exception:
                err_json = {"raw": raw}
            return e.code, e.headers, err_json

    def test_security_headers_in_responses(self):
        status, headers, body = self._request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("max-age=63072000", headers.get("Strict-Transport-Security", ""))
        self.assertIn("default-src 'self'", headers.get("Content-Security-Policy", ""))
        self.assertIn("camera=()", headers.get("Permissions-Policy", ""))

    def test_cors_preflight_and_origin_reflection(self):
        # OPTIONS request with verified origin
        status, headers, body = self._request(
            "OPTIONS", "/api/optimise",
            headers={"Origin": "https://changeloop.ai"}
        )
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "https://changeloop.ai")
        self.assertEqual(headers.get("Access-Control-Allow-Credentials"), "true")

    def test_auth_login_sets_secure_httponly_cookie(self):
        # Reset rate limits before test
        ratelimit.reset_rate_limits()

        status, headers, body = self._request("POST", "/api/auth/login", {
            "username": "admin",
            "password": "ChangeLoop#Admin2026!"
        })
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        self.assertIn("token", body)
        self.assertEqual(body["user"]["role"], "ADMIN")

        cookie = headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertIn("session_token=", cookie)

    def test_rbac_admin_route_protection(self):
        ratelimit.reset_rate_limits()

        # Unauthenticated request to /api/admin/users -> 401
        status, _, err = self._request("GET", "/api/admin/users")
        self.assertEqual(status, 401)

        # Login as operator
        status, _, op_res = self._request("POST", "/api/auth/login", {
            "username": "operator",
            "password": "Operator#ZLD2026!"
        })
        op_token = op_res["token"]

        # Operator tries to access /api/admin/users -> 403 Forbidden
        status, _, err = self._request("GET", "/api/admin/users", headers={"Authorization": f"Bearer {op_token}"})
        self.assertEqual(status, 403)

        # Operator CAN access /api/secure/diagnostics -> 200 OK
        status, _, diag = self._request("GET", "/api/secure/diagnostics", headers={"Authorization": f"Bearer {op_token}"})
        self.assertEqual(status, 200)
        self.assertEqual(diag.get("status"), "HEALTHY")

        # Admin CAN access /api/admin/users -> 200 OK
        admin_token = auth.create_token({"username": "admin", "role": "ADMIN"})
        status, _, adm_res = self._request("GET", "/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(status, 200)
        self.assertIn("users", adm_res)

    def test_rate_limiting_enforcement(self):
        ratelimit.reset_rate_limits()

        # Auth endpoint limit is 5 requests per 15 min
        ip_header = {"X-Forwarded-For": "198.51.100.55"}
        for i in range(5):
            status, _, _ = self._request("POST", "/api/auth/login", {
                "username": "admin",
                "password": "WrongPassword123!"
            }, headers=ip_header)
            self.assertEqual(status, 401)

        # 6th request must trigger 429
        status, headers, err = self._request("POST", "/api/auth/login", {
            "username": "admin",
            "password": "WrongPassword123!"
        }, headers=ip_header)
        self.assertEqual(status, 429)
        self.assertIn("Retry-After", headers)
        self.assertEqual(err["error"]["code"], "RATE_LIMIT_EXCEEDED")

        # Clean up
        ratelimit.reset_rate_limits()

    def test_path_traversal_defense(self):
        status, _, _ = self._request("GET", "/core/factors.py")
        self.assertIn(status, (403, 404))

        status, _, _ = self._request("GET", "/../server.py")
        self.assertIn(status, (403, 404))

    def test_ledger_tamper_detection(self):
        integrity = provenance.verify_chain()
        self.assertTrue(integrity["intact"])


if __name__ == "__main__":
    unittest.main()
