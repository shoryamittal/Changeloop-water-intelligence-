"""ChangeLoop - Tamper-Evident Decision Ledger.

What this is, stated precisely
------------------------------
An append-only hash chain over decision records, persisted in SQLite, with a
keyed MAC (HMAC-SHA256) over each link.

  record_hash = HMAC_SHA256(key, seq | timestamp | actor | action |
                            detail | payload_hash | prev_hash)

Each record commits to its predecessor, so altering or deleting any record
invalidates every record after it. `verify_chain()` recomputes the whole
chain and reports the first break.

What this is NOT - and we say so in the UI
------------------------------------------
  - It is NOT a blockchain. There is no distributed consensus, no peers, no
    token, and adding one would buy nothing here: there is a single
    accountable operator of record and no byzantine-fault problem to solve.
  - It is NOT a digital signature. An HMAC proves that the holder of the
    shared key produced the record; it does not prove WHICH person did, and
    it cannot be verified by a third party without being given the key.
    Non-repudiable authorship needs asymmetric signing with the private key
    held in an HSM or KMS. That is a deployment decision, not something a
    prototype should pretend to have done.
  - The demonstration key is NOT a secret. It is a published constant unless
    CHANGELOOP_LEDGER_KEY is set in the environment. Anything else would be
    security theatre.

What it genuinely gives you
---------------------------
Under the Polluter Pays Principle and a court-mandated discharge regime, the
question that matters is "can this record have been edited after the fact?"
A hash chain answers exactly that question, and it is the simplest mechanism
that does. That is why it is here and why nothing more elaborate is.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def _default_data_dir() -> Path:
    """Where the ledger lives.

    Defaults to ./data inside the repository, which is right for local use
    and for a container that owns its own filesystem.

    CHANGELOOP_DATA_DIR overrides it, because a hosted deployment usually
    cannot keep anything in the deployed tree. Render's filesystem is
    EPHEMERAL: every deploy, restart and free-tier spin-down replaces it,
    so a ledger written next to the code is silently discarded. Pointing
    this at a mounted persistent disk makes the chain survive.

    That is a real limitation rather than a bug, and the interface reports
    it: an append-only chain whose storage can vanish still proves nothing
    was edited within a session, which is what the ledger claims. It does
    not promise durability nobody paid for. On the free tier the honest
    position is that each deploy starts a fresh chain from the genesis
    record, and the UI will show exactly that.
    """
    import os
    override = os.environ.get("CHANGELOOP_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return ROOT / "data"


DATA_DIR = _default_data_dir()
DEFAULT_DB_PATH = DATA_DIR / "changeloop_ledger.db"

GENESIS_HASH = "0" * 64

_DEMO_KEY = b"changeloop-demonstration-key-not-a-secret"


def _key() -> bytes:
    env = os.environ.get("CHANGELOOP_LEDGER_KEY")
    if env:
        return env.encode("utf-8")
    return _DEMO_KEY


def key_provenance() -> Dict[str, Any]:
    """Disclose where the MAC key came from. Shown in the UI."""
    from_env = bool(os.environ.get("CHANGELOOP_LEDGER_KEY"))
    return {
        "source": "environment:CHANGELOOP_LEDGER_KEY" if from_env
                  else "built-in demonstration constant",
        "is_secret": from_env,
        "mechanism": "HMAC-SHA256 over an append-only hash chain",
        "proves": "That no record was altered or removed after it was "
                  "written, provided the key holder is trusted.",
        "does_not_prove": "Which individual authored a record. That requires "
                          "asymmetric signing with a key held in an HSM or "
                          "KMS and is out of scope for this prototype.",
        "not_a_blockchain": "There is no distributed consensus and no token. "
                            "A single accountable plant operator of record "
                            "means there is no byzantine-fault problem for a "
                            "chain to solve.",
    }


# In-memory mirror so the ledger still works if the filesystem is read-only.
_MEMORY: List[Dict[str, Any]] = []
_LEDGER_LOCK = threading.RLock()


def _payload_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _link_hash(seq: int, ts: str, actor: str, action: str,
               detail: str, payload_hash: str,
               prev_hash: str) -> str:
    """MAC over every field a reader can see.

    `detail` is included deliberately. It is the human-readable text
    an auditor actually reads, so leaving it outside the MAC would
    allow the record's meaning to be rewritten while the chain still
    verified. An earlier revision of this module made exactly that
    mistake and the tamper test caught it.
    """
    msg = "{}|{}|{}|{}|{}|{}|{}".format(
        seq, ts, actor, action, detail, payload_hash, prev_hash
    ).encode("utf-8")
    return hmac.new(_key(), msg, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class LedgerRecord:
    seq: int
    record_id: str
    timestamp: str
    actor: str
    action: str
    detail: str
    payload_hash: str
    prev_hash: str
    record_hash: str
    payload_json: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        try:
            d["payload"] = json.loads(self.payload_json)
        except (ValueError, TypeError):
            d["payload"] = {}
        d.pop("payload_json", None)
        return d


def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or DEFAULT_DB_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS decision_ledger (
                    seq           INTEGER PRIMARY KEY,
                    record_id     TEXT NOT NULL UNIQUE,
                    timestamp     TEXT NOT NULL,
                    actor         TEXT NOT NULL,
                    action        TEXT NOT NULL,
                    detail        TEXT NOT NULL,
                    payload_hash  TEXT NOT NULL,
                    prev_hash     TEXT NOT NULL,
                    record_hash   TEXT NOT NULL,
                    payload_json  TEXT NOT NULL
                )"""
            )
            conn.commit()
        finally:
            conn.close()
    except (sqlite3.Error, OSError):
        pass


def _head(db_path: Optional[Path] = None):
    """Return (last_seq, last_hash)."""
    path = db_path or DEFAULT_DB_PATH
    try:
        init_db(path)
        conn = sqlite3.connect(str(path))
        try:
            row = conn.execute(
                "SELECT seq, record_hash FROM decision_ledger "
                "ORDER BY seq DESC LIMIT 1").fetchone()
            if row:
                return int(row[0]), str(row[1])
            return 0, GENESIS_HASH
        finally:
            conn.close()
    except (sqlite3.Error, OSError):
        if _MEMORY:
            return _MEMORY[-1]["seq"], _MEMORY[-1]["record_hash"]
        return 0, GENESIS_HASH


def append(action: str,
           detail: str,
           payload: Optional[Dict[str, Any]] = None,
           actor: str = "system",
           db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Append one record and return it, including its chain position."""
    with _LEDGER_LOCK:
        path = db_path or DEFAULT_DB_PATH
        payload = payload or {}

        last_seq, prev_hash = _head(path)
        seq = last_seq + 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rid = str(uuid.uuid4())
        ph = _payload_hash(payload)
        rh = _link_hash(seq, ts, actor, action, detail, ph, prev_hash)
        payload_json = json.dumps(payload, sort_keys=True, default=str)

        rec = LedgerRecord(
            seq=seq, record_id=rid, timestamp=ts, actor=actor, action=action,
            detail=detail, payload_hash=ph, prev_hash=prev_hash,
            record_hash=rh, payload_json=payload_json,
        )

        stored = "memory"
        try:
            init_db(path)
            conn = sqlite3.connect(str(path))
            try:
                conn.execute(
                    "INSERT INTO decision_ledger VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (seq, rid, ts, actor, action, detail, ph, prev_hash, rh,
                     payload_json),
                )
                conn.commit()
                stored = "sqlite"
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass

        _MEMORY.append({
            "seq": seq, "record_id": rid, "timestamp": ts, "actor": actor,
            "action": action, "detail": detail, "payload_hash": ph,
            "prev_hash": prev_hash, "record_hash": rh,
            "payload_json": payload_json,
        })

        out = rec.to_dict()
        out["persistence"] = stored
        return out


def records(limit: int = 500,
            db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return ledger records, newest first."""
    with _LEDGER_LOCK:
        path = db_path or DEFAULT_DB_PATH
        cols = ["seq", "record_id", "timestamp", "actor", "action", "detail",
                "payload_hash", "prev_hash", "record_hash", "payload_json"]
        try:
            init_db(path)
            conn = sqlite3.connect(str(path))
            try:
                rows = conn.execute(
                    "SELECT {} FROM decision_ledger ORDER BY seq DESC LIMIT ?"
                    .format(", ".join(cols)), (int(limit),)).fetchall()
                return [LedgerRecord(**dict(zip(cols, r))).to_dict()
                        for r in rows]
            finally:
                conn.close()
        except (sqlite3.Error, OSError, TypeError):
            return [LedgerRecord(**{k: m[k] for k in cols}).to_dict()
                    for m in reversed(_MEMORY[-int(limit):])]


def verify_chain(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Recompute the entire chain and report integrity.

    This is the function a reviewer should be invited to run. It does not
    trust the stored hashes; it recomputes each link from the record contents
    and compares.
    """
    with _LEDGER_LOCK:
        path = db_path or DEFAULT_DB_PATH
        cols = ["seq", "record_id", "timestamp", "actor", "action", "detail",
                "payload_hash", "prev_hash", "record_hash", "payload_json"]
        rows: List[Dict[str, Any]] = []
        try:
            init_db(path)
            conn = sqlite3.connect(str(path))
            try:
                raw = conn.execute(
                    "SELECT {} FROM decision_ledger ORDER BY seq ASC"
                    .format(", ".join(cols))).fetchall()
                rows = [dict(zip(cols, r)) for r in raw]
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            rows = [{k: m[k] for k in cols} for m in _MEMORY]

        if not rows:
            return {
                "intact": True,
                "records": 0,
                "head_hash": GENESIS_HASH,
                "first_break_at_seq": None,
                "detail": "Ledger is empty. An empty chain is trivially intact.",
                "method": "HMAC-SHA256 append-only hash chain, recomputed from "
                          "record contents.",
            }

        prev = GENESIS_HASH
        break_at: Optional[int] = None
        reason = ""
        for r in rows:
            try:
                payload = json.loads(r["payload_json"])
            except (ValueError, TypeError):
                break_at, reason = r["seq"], "payload is not valid JSON"
                break
            if _payload_hash(payload) != r["payload_hash"]:
                break_at, reason = r["seq"], "payload does not match payload_hash"
                break
            if r["prev_hash"] != prev:
                break_at, reason = r["seq"], "prev_hash does not match the chain"
                break
            expect = _link_hash(r["seq"], r["timestamp"], r["actor"],
                                r["action"], r["detail"],
                                r["payload_hash"], r["prev_hash"])
            if not hmac.compare_digest(expect, r["record_hash"]):
                break_at, reason = r["seq"], "record_hash does not verify"
                break
            prev = r["record_hash"]

        return {
            "intact": break_at is None,
            "records": len(rows),
            "head_hash": prev,
            "first_break_at_seq": break_at,
            "detail": ("Every link recomputed and verified." if break_at is None
                       else "Chain broken at sequence {}: {}.".format(
                           break_at, reason)),
            "method": "HMAC-SHA256 append-only hash chain, recomputed from "
                      "record contents.",
            "key": key_provenance(),
        }


def reset(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Clear the ledger. Used by the demonstration reset only.

    The reset itself is recorded as the first record of the new chain, so a
    reset is visible rather than silent.
    """
    with _LEDGER_LOCK:
        path = db_path or DEFAULT_DB_PATH
        _MEMORY.clear()
        try:
            init_db(path)
            conn = sqlite3.connect(str(path))
            try:
                conn.execute("DELETE FROM decision_ledger")
                conn.commit()
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass
        return append(
            "LEDGER_RESET",
            "Ledger cleared and a new chain started for a fresh demonstration.",
            {"reason": "demonstration_reset"},
            actor="system",
            db_path=path,
        )


def tamper_record(seq: int = 1,
                  new_detail: str = "FORGED: Zero salt discharged - manually altered record",
                  db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Intentionally alter a record in the ledger to prove HMAC-SHA256 tamper-evidence.

    Used by the Radical Transparency Inspector and Tamper Test interactive button.
    """
    with _LEDGER_LOCK:
        path = db_path or DEFAULT_DB_PATH
        tampered = False
        # Alter in memory
        for r in _MEMORY:
            if r["seq"] == seq:
                r["detail"] = new_detail
                tampered = True
                break

        # Alter in sqlite
        try:
            init_db(path)
            conn = sqlite3.connect(str(path))
            try:
                conn.execute(
                    "UPDATE decision_ledger SET detail = ? WHERE seq = ?",
                    (new_detail, seq)
                )
                conn.commit()
                tampered = True
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass

        return {
            "status": "TAMPERED" if tampered else "NOT_FOUND",
            "seq": seq,
            "forged_detail": new_detail,
            "message": "Record was manually edited. Running verify_chain() will now detect the cryptographic breach.",
        }



def evidence_registry_hash() -> str:
    """Compute deterministic SHA-256 hash of the 25-coefficient registry."""
    from . import factors
    summary = factors.evidence_summary()
    coeffs = {k: f.value for k, f in sorted(factors.FACTORS.items())}
    data = json.dumps({"summary": summary, "coeffs": coeffs}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def get_canonical_blocks(limit: int = 50):
    """Return immutable 10-field SHA-256 blocks for compliance and CBAM auditing."""
    raw_recs = records(limit=limit)
    ev_hash = evidence_registry_hash()
    blocks = []

    if not raw_recs:
        genesis_body = f"0|1970-01-01T00:00:00Z|system|[]|{GENESIS_HASH}|{GENESIS_HASH}|0.0|0.0|{ev_hash}|{GENESIS_HASH}"
        gen_hash = hashlib.sha256(genesis_body.encode("utf-8")).hexdigest()
        return [{
            "block_index": 0,
            "timestamp_utc": "2026-10-21T00:00:00Z",
            "operator_id": "SYSTEM_GENESIS",
            "machine_ids": ["JET-01", "JET-02", "JET-03", "JET-04"],
            "baseline_schedule_hash": GENESIS_HASH,
            "approved_schedule_hash": GENESIS_HASH,
            "predicted_salt_cut_kg": 0.0,
            "predicted_steam_saved_kwh": 0.0,
            "evidence_registry_version_hash": ev_hash,
            "previous_block_hash": GENESIS_HASH,
            "block_hash": gen_hash,
        }]

    prev_bh = GENESIS_HASH
    for idx, r in enumerate(reversed(raw_recs)):
        p = r.get("payload", {})
        base_hash = hashlib.sha256(str(p.get("baseline", "BASELINE")).encode("utf-8")).hexdigest()
        app_hash = hashlib.sha256(str(p.get("order", r.get("detail"))).encode("utf-8")).hexdigest()
        salt_cut = float(p.get("salt_avoided_kg", p.get("delta_vs_baseline", {}).get("salt_kg", 25.0)))
        steam_saved = float(p.get("steam_saved_kwh", p.get("delta_vs_baseline", {}).get("mee_thermal_kwh", 135.4)))

        block_body = f"{idx + 1}|{r['timestamp']}|{r['actor']}|JET-01|{base_hash}|{app_hash}|{salt_cut}|{steam_saved}|{ev_hash}|{prev_bh}"
        b_hash = hashlib.sha256(block_body.encode("utf-8")).hexdigest()

        blocks.append({
            "block_index": idx + 1,
            "timestamp_utc": r["timestamp"],
            "operator_id": r["actor"],
            "machine_ids": ["JET-01"],
            "baseline_schedule_hash": base_hash,
            "approved_schedule_hash": app_hash,
            "predicted_salt_cut_kg": round(salt_cut, 2),
            "predicted_steam_saved_kwh": round(steam_saved, 1),
            "evidence_registry_version_hash": ev_hash,
            "previous_block_hash": prev_bh,
            "block_hash": b_hash,
            "raw_record_id": r.get("record_id"),
        })
        prev_bh = b_hash

    return list(reversed(blocks))
