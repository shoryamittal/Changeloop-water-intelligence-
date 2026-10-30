# -*- coding: utf-8 -*-
"""ChangeLoop - Institutional Authentication, Password Security & RBAC Engine.

Implements OWASP 2024 password hashing standards (PBKDF2-HMAC-SHA256 with 600,000
iterations and cryptographically secure random salts), tamper-proof signed session
tokens (HMAC-SHA256), and Role-Based Access Control (RBAC).

Zero external dependencies: Python standard library only (hashlib, hmac, secrets, time).
"""
import hashlib
import hmac
import base64
import json
import os
import secrets
import time
from typing import Dict, Any, Optional, Tuple, List

# Roles defined in the system
ROLES = ("ADMIN", "PLANNER", "SUPERVISOR", "CETP_OPERATOR", "AUDITOR", "OPERATOR", "VIEWER")

# PBKDF2 parameters per OWASP Password Storage Guidelines (2023/2024)
PBKDF2_ITERATIONS = 600000
PBKDF2_ALGORITHM = "sha256"
SALT_BYTES = 16

# Session validity: 8 hours (28800 seconds)
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60

# HMAC secret key for signing tokens
_SECRET_KEY = os.environ.get(
    "CHANGELOOP_LEDGER_KEY",
    "changeloop-auth-production-master-secret-seed-2026-tirupur"
).encode("utf-8")

# In-memory user store (can be populated at boot or via registration)
# Pre-seeded with default demo users for secure cluster operation
_USERS: Dict[str, Dict[str, Any]] = {}
_USER_LOCK = secrets.token_hex(4)


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    dk_b64 = base64.b64encode(dk).decode("ascii")
    return f"pbkdf2:{PBKDF2_ALGORITHM}:{PBKDF2_ITERATIONS}${salt_b64}${dk_b64}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison."""
    if not password or not hashed or "$" not in hashed:
        return False
    try:
        header, salt_b64, dk_b64 = hashed.split("$")
        parts = header.split(":")
        algo = parts[1]
        iterations = int(parts[2])
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_dk = base64.b64decode(dk_b64.encode("ascii"))
        actual_dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, iterations)
        return secrets.compare_digest(actual_dk, expected_dk)
    except Exception:
        return False


def create_token(payload: Dict[str, Any], max_age: int = SESSION_MAX_AGE_SECONDS) -> str:
    """Create a tamper-proof HMAC-SHA256 signed session token (JWT-style claims)."""
    now = int(time.time())
    claims = dict(payload)
    claims["iat"] = now
    claims["exp"] = now + max_age
    claims["jti"] = secrets.token_hex(16)

    # Encode header & claims in URL-safe base64
    header_json = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
    claims_json = json.dumps(claims, sort_keys=True).encode("utf-8")

    h_b64 = base64.urlsafe_b64encode(header_json).decode("ascii").rstrip("=")
    c_b64 = base64.urlsafe_b64encode(claims_json).decode("ascii").rstrip("=")

    message = f"{h_b64}.{c_b64}".encode("ascii")
    signature = hmac.new(_SECRET_KEY, message, hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    return f"{h_b64}.{c_b64}.{s_b64}"


def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Verify an HMAC-SHA256 signed session token.

    Returns (is_valid, claims, error_message).
    """
    if not token or token.count(".") != 2:
        return False, None, "Invalid token format."

    parts = token.split(".")
    h_b64, c_b64, s_b64 = parts

    try:
        # Recompute signature
        message = f"{h_b64}.{c_b64}".encode("ascii")
        expected_sig = hmac.new(_SECRET_KEY, message, hashlib.sha256).digest()
        
        # Add back padding
        pad = len(s_b64) % 4
        s_b64_padded = s_b64 + ("=" * (4 - pad) if pad else "")
        actual_sig = base64.urlsafe_b64decode(s_b64_padded.encode("ascii"))

        if not secrets.compare_digest(actual_sig, expected_sig):
            return False, None, "Invalid token signature."

        pad_c = len(c_b64) % 4
        c_b64_padded = c_b64 + ("=" * (4 - pad_c) if pad_c else "")
        claims_bytes = base64.urlsafe_b64decode(c_b64_padded.encode("ascii"))
        claims = json.loads(claims_bytes.decode("utf-8"))

        # Check expiration
        now = int(time.time())
        if claims.get("exp", 0) < now:
            return False, None, "Session token has expired."

        return True, claims, None
    except Exception as exc:
        return False, None, f"Token validation error: {str(exc)[:100]}"


def seed_default_users() -> None:
    """Seed baseline cluster accounts if not already initialized."""
    if _USERS:
        return
    # 1. Administrator / Chief Engineer
    _USERS["admin"] = {
        "username": "admin",
        "password_hash": hash_password("ChangeLoop#Admin2026!"),
        "role": "ADMIN",
        "full_name": "Cluster Chief Engineer",
        "site_id": "tirupur_central_cetp",
    }
    # 2. Dyehouse Shift Planner
    _USERS["planner"] = {
        "username": "planner",
        "password_hash": hash_password("Planner#2026!"),
        "role": "PLANNER",
        "full_name": "Shift Production Planner",
        "site_id": "tirupur_mill_04",
    }
    # 3. Quality & Wash-Off Supervisor
    _USERS["supervisor"] = {
        "username": "supervisor",
        "password_hash": hash_password("Supervisor#2026!"),
        "role": "SUPERVISOR",
        "full_name": "Quality & Wash-Off Supervisor",
        "site_id": "tirupur_mill_04",
    }
    # 4. Shared CETP Operations Engineer
    _USERS["cetp_operator"] = {
        "username": "cetp_operator",
        "password_hash": hash_password("CETPOp#2026!"),
        "role": "CETP_OPERATOR",
        "full_name": "CETP Evaporator Shift Engineer",
        "site_id": "tirupur_central_cetp",
    }
    # 5. Regulatory Compliance Auditor
    _USERS["auditor"] = {
        "username": "auditor",
        "password_hash": hash_password("Auditor#Audit2026!"),
        "role": "AUDITOR",
        "full_name": "TNPCB / CPCB Compliance Inspector",
        "site_id": "cpcb_south_zone",
    }
    # 6. Dyeing Machine Operator
    _USERS["operator"] = {
        "username": "operator",
        "password_hash": hash_password("Operator#ZLD2026!"),
        "role": "OPERATOR",
        "full_name": "Shift Plant Operator",
        "site_id": "tirupur_mill_04",
    }


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Authenticate credentials and return user record if valid."""
    seed_default_users()
    user = _USERS.get(username.strip().lower())
    if not user:
        return False, None, "Invalid credentials."
    if not verify_password(password, user["password_hash"]):
        return False, None, "Invalid credentials."
    
    # Return user record without password hash
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return True, safe_user, None


def register_user(username: str, password: str, role: str, full_name: str, site_id: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Register a new user account with hashed password and assigned RBAC role."""
    seed_default_users()
    uname = username.strip().lower()
    if uname in _USERS:
        return False, None, "Username already exists."
    if role not in ROLES:
        return False, None, f"Invalid role. Must be one of: {', '.join(ROLES)}"
    
    try:
        p_hash = hash_password(password)
    except ValueError as e:
        return False, None, str(e)

    record = {
        "username": uname,
        "password_hash": p_hash,
        "role": role,
        "full_name": full_name.strip(),
        "site_id": site_id.strip(),
    }
    _USERS[uname] = record
    return True, {k: v for k, v in record.items() if k != "password_hash"}, None


def get_cookie_header(token: str, max_age: int = SESSION_MAX_AGE_SECONDS, is_secure: bool = True) -> str:
    """Format Set-Cookie header with strict security flags."""
    secure_flag = "; Secure" if is_secure else ""
    return (
        f"session_token={token}; "
        f"Max-Age={max_age}; "
        f"Path=/; "
        f"HttpOnly"
        f"{secure_flag}; "
        f"SameSite=Strict"
    )


def get_logout_cookie_header() -> str:
    """Format Set-Cookie header to immediately invalidate the session cookie."""
    return "session_token=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict"


# Initialize default users
seed_default_users()

def demo_switch_role(role: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Instantly generate a signed token and cookie for one of the verified demo roles."""
    seed_default_users()
    r = role.strip().upper()
    role_to_uname = {
        "ADMIN": "admin",
        "PLANNER": "planner",
        "SUPERVISOR": "supervisor",
        "CETP_OPERATOR": "cetp_operator",
        "AUDITOR": "auditor",
        "OPERATOR": "operator",
    }
    uname = role_to_uname.get(r)
    if not uname or uname not in _USERS:
        return False, None, None, f"Unknown demo role '{role}'. Valid roles: {list(role_to_uname.keys())}"
    
    user = {k: v for k, v in _USERS[uname].items() if k != "password_hash"}
    token = create_token(user)
    is_secure = os.environ.get("CHANGELOOP_ENV") == "production"
    cookie_hdr = get_cookie_header(token, is_secure=is_secure)
    return True, user, token, cookie_hdr
