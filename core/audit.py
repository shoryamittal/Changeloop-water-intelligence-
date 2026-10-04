"""ClearLoop Persistent Audit Trail & GAMP 5 Event Logging.
Durable SQLite storage with automatic table initialization and in-memory fallback.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlite3
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "clearloop_demo.db"

_IN_MEMORY_AUDIT: List[Dict[str, Any]] = []

def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL,
            classification TEXT NOT NULL
        )""")
        conn.commit()
    finally:
        conn.close()

def record_audit_event(action: str, detail: str, db_path: Optional[Path] = None) -> Dict[str, Any]:
    path = db_path or DEFAULT_DB_PATH
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "detail": detail,
        "classification": "SIMULATED"
    }
    _IN_MEMORY_AUDIT.append(event)
    try:
        init_db(path)
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                "INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?)",
                (event["event_id"], event["timestamp"], event["action"], event["detail"], event["classification"])
            )
            conn.commit()
            event["persistence"] = "sqlite"
        finally:
            conn.close()
    except sqlite3.Error:
        event["persistence"] = "memory_fallback"
    return event

def get_audit_events(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    path = db_path or DEFAULT_DB_PATH
    try:
        init_db(path)
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute(
                "SELECT event_id, timestamp, action, detail, classification FROM audit_logs ORDER BY timestamp DESC"
            ).fetchall()
            return [dict(zip(["event_id", "timestamp", "action", "detail", "classification"], row)) for row in rows]
        finally:
            conn.close()
    except sqlite3.Error:
        return list(reversed(_IN_MEMORY_AUDIT))
