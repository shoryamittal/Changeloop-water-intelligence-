# -*- coding: utf-8 -*-
"""ChangeLoop - Strict Schema Validation & Sanitization Engine.

Zero external dependencies: Python standard library only (re, html, typing).
Validates types, ranges, whitelist enums, and lengths. Sanitizes user input against XSS.
"""
import html
import re
from typing import Any, Dict, List, Optional, Tuple, Union

# Whitelist patterns
ALPHANUMERIC_IDENTIFIER = re.compile(r"^[A-Za-z0-9_\-]+$")
SAFE_TEXT_PATTERN = re.compile(r"^[\w\s\.,;:!?@#%&*()_\-+/=\[\]{}<>'\"]+$")

# HTML tag stripping pattern for user text
HTML_TAG_RE = re.compile(r"<[^>]*>")
DANGEROUS_ATTRIBUTES_RE = re.compile(r"(?i)\b(on\w+|javascript:|data:text/html)\b")


def sanitize_string(val: str) -> str:
    """Sanitize string by stripping unsafe HTML/script tokens and escaping special chars."""
    if not isinstance(val, str):
        return str(val)
    # Remove HTML tags
    cleaned = HTML_TAG_RE.sub("", val)
    # Remove script handlers
    cleaned = DANGEROUS_ATTRIBUTES_RE.sub("", cleaned)
    # HTML escape remaining characters
    return html.escape(cleaned.strip())


def sanitize_payload(obj: Any) -> Any:
    """Recursively sanitize all string leaves in a JSON-compatible object."""
    if isinstance(obj, str):
        return sanitize_string(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_payload(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_payload(v) for v in obj]
    return obj


class ValidationError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]


def validate_dict(data: Any, name: str = "request body") -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError(f"Invalid {name}: must be a JSON object.")
    return data


def validate_string(
    val: Any,
    field_name: str,
    min_len: int = 1,
    max_len: int = 256,
    pattern: Optional[re.Pattern] = None,
    allowed: Optional[List[str]] = None,
) -> str:
    if not isinstance(val, str):
        raise ValidationError(f"Field '{field_name}' must be a string.")
    s = val.strip()
    if len(s) < min_len:
        raise ValidationError(f"Field '{field_name}' must be at least {min_len} characters.")
    if len(s) > max_len:
        raise ValidationError(f"Field '{field_name}' exceeds maximum length of {max_len} characters.")
    if pattern and not pattern.match(s):
        raise ValidationError(f"Field '{field_name}' contains invalid characters.")
    if allowed is not None and s not in allowed:
        raise ValidationError(f"Field '{field_name}' must be one of: {', '.join(allowed)}")
    return s


def validate_number(
    val: Any,
    field_name: str,
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    must_be_int: bool = False,
) -> Union[int, float]:
    if must_be_int and not isinstance(val, int):
        raise ValidationError(f"Field '{field_name}' must be an integer.")
    if not isinstance(val, (int, float)):
        raise ValidationError(f"Field '{field_name}' must be a number.")
    if min_val is not None and val < min_val:
        raise ValidationError(f"Field '{field_name}' must be >= {min_val}.")
    if max_val is not None and val > max_val:
        raise ValidationError(f"Field '{field_name}' must be <= {max_val}.")
    return val


def validate_bool(val: Any, field_name: str) -> bool:
    if not isinstance(val, bool):
        raise ValidationError(f"Field '{field_name}' must be a boolean.")
    return val


# Specialized Endpoint Validators

def validate_auth_login(data: Any) -> Dict[str, Any]:
    body = validate_dict(data)
    username = validate_string(body.get("username"), "username", min_len=3, max_len=64, pattern=ALPHANUMERIC_IDENTIFIER)
    password = validate_string(body.get("password"), "password", min_len=8, max_len=128)
    return {"username": username, "password": password}


def validate_auth_register(data: Any) -> Dict[str, Any]:
    body = validate_dict(data)
    username = validate_string(body.get("username"), "username", min_len=3, max_len=64, pattern=ALPHANUMERIC_IDENTIFIER)
    password = validate_string(body.get("password"), "password", min_len=8, max_len=128)
    role = validate_string(body.get("role"), "role", allowed=["ADMIN", "OPERATOR", "AUDITOR", "VIEWER"])
    full_name = validate_string(body.get("full_name", username), "full_name", min_len=1, max_len=128)
    site_id = validate_string(body.get("site_id", "tirupur_mill_04"), "site_id", min_len=1, max_len=64, pattern=ALPHANUMERIC_IDENTIFIER)
    return {
        "username": username,
        "password": password,
        "role": role,
        "full_name": full_name,
        "site_id": site_id,
    }


def validate_optimise_request(data: Any) -> Dict[str, Any]:
    body = validate_dict(data)
    out = {}
    if "weights" in body:
        weights = validate_dict(body["weights"], "weights")
        for k, v in weights.items():
            validate_number(v, f"weights.{k}", min_val=0.0, max_val=10.0)
        out["weights"] = weights
    if "max_tds_mg_l" in body:
        out["max_tds_mg_l"] = validate_number(body["max_tds_mg_l"], "max_tds_mg_l", min_val=10000, max_val=150000)
    if "enforce_delivery_dates" in body:
        out["enforce_delivery_dates"] = validate_bool(body["enforce_delivery_dates"], "enforce_delivery_dates")
    if "fuel_type" in body:
        out["fuel_type"] = validate_string(
            body["fuel_type"], "fuel_type", allowed=["coal", "seasoned_wood", "wet_wood"]
        )
    return out


def validate_release_propose(data: Any) -> Dict[str, Any]:
    body = validate_dict(data)
    bath_id = validate_string(body.get("bath_id"), "bath_id", min_len=1, max_len=64)
    reason = validate_string(body.get("reason", "Operator wash-off check passed"), "reason", min_len=3, max_len=256)
    return {"bath_id": sanitize_string(bath_id), "reason": sanitize_string(reason)}


def validate_release_confirm(data: Any) -> Dict[str, Any]:
    body = validate_dict(data)
    release_id = validate_string(body.get("release_id"), "release_id", min_len=1, max_len=128)
    authorized_by = validate_string(body.get("authorized_by", "Shift Supervisor"), "authorized_by", min_len=2, max_len=64)
    return {"release_id": sanitize_string(release_id), "authorized_by": sanitize_string(authorized_by)}
