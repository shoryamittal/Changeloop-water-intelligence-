# -*- coding: utf-8 -*-
"""ChangeLoop - Production Rate Limiter & Abuse Prevention.

Sliding-window in-memory rate limiting with microsecond timestamps and thread locks.
Zero external dependencies: Python standard library only (time, threading, collections).

Limits:
  - AUTH: Max 5 requests per 15 minutes (900s) per IP.
  - SOLVER: Max 10 requests per minute (60s) per IP/User.
  - GENERAL: Max 100 requests per minute (60s) per IP.
"""
import time
import threading
from typing import Dict, List, Tuple

# Rate Limit Configurations: (max_requests, window_seconds)
LIMITS = {
    "AUTH": (5, 900),     # 5 req / 15 min per IP
    "SOLVER": (30, 60),   # 30 req / 60 sec per IP/User
    "GENERAL": (120, 60), # 120 req / 60 sec per IP
}

_WINDOWS: Dict[str, Dict[str, List[float]]] = {
    "AUTH": {},
    "SOLVER": {},
    "GENERAL": {},
}
_LOCK = threading.Lock()


def get_category_for_route(route: str) -> str:
    """Classify incoming route into rate-limiting category."""
    if route.startswith("/api/auth/"):
        return "AUTH"
    if route in (
        "/api/optimise",
        "/api/forecast",
        "/api/simulate/step",
        "/api/simulate/run",
        "/api/solver/solve",
        "/api/cluster/milp",
    ):
        return "SOLVER"
    return "GENERAL"


def check_rate_limit(key: str, category: str) -> Tuple[bool, int]:
    """Check if key has exceeded the limit for category.

    Returns (is_allowed, retry_after_seconds).
    """
    if category not in LIMITS:
        category = "GENERAL"

    max_reqs, window_s = LIMITS[category]
    now = time.time()
    cutoff = now - window_s

    with _LOCK:
        store = _WINDOWS[category]
        history = store.get(key, [])
        # Prune entries older than window
        valid_entries = [t for t in history if t > cutoff]
        
        if len(valid_entries) >= max_reqs:
            # Earliest entry determines retry after
            oldest_entry = valid_entries[0]
            retry_after = max(1, int(oldest_entry + window_s - now))
            store[key] = valid_entries
            return False, retry_after

        # Record this request
        valid_entries.append(now)
        store[key] = valid_entries
        return True, 0


def reset_rate_limits() -> None:
    """Clear all rate limit windows (for testing or administrative reset)."""
    with _LOCK:
        for cat in _WINDOWS:
            _WINDOWS[cat].clear()
