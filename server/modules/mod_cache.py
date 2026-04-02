"""
MOD-B: Scoped key-value cache with expiry.
Cache lives in SQLite (persistent) and in-memory dict (fast).
scope='global' | 'session' | any string label
"""

import json
from datetime import datetime, timedelta
from . import mod_db as db

_mem: dict = {}   # {(scope, key): value} — in-memory fast layer


def set(key: str, value, scope: str = "global", ttl_sec: int = None):
    """
    Store a value. ttl_sec=None = no expiry.
    value can be any JSON-serializable type.
    """
    expires_at = None
    if ttl_sec:
        expires_at = (datetime.now() + timedelta(seconds=ttl_sec)).isoformat()
    val_str = json.dumps(value)
    _mem[(scope, key)] = value
    db.execute(
        """INSERT INTO cache_store (key, value, scope, expires_at)
           VALUES (?,?,?,?)
           ON CONFLICT(key, scope) DO UPDATE SET value=excluded.value, expires_at=excluded.expires_at""",
        (key, val_str, scope, expires_at)
    )


def get(key: str, scope: str = "global", default=None):
    """Return cached value or default. Respects expiry."""
    mem_val = _mem.get((scope, key))
    if mem_val is not None:
        return mem_val

    row = db.execute(
        "SELECT value, expires_at FROM cache_store WHERE key=? AND scope=?",
        (key, scope), fetch="one"
    )
    if not row:
        return default
    if row["expires_at"]:
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            delete(key, scope)
            return default
    try:
        val = json.loads(row["value"])
        _mem[(scope, key)] = val
        return val
    except Exception:
        return row["value"]


def delete(key: str, scope: str = "global"):
    _mem.pop((scope, key), None)
    db.execute(
        "DELETE FROM cache_store WHERE key=? AND scope=?",
        (key, scope)
    )


def clear_scope(scope: str):
    """Delete everything in a scope."""
    keys = [k for (s, k) in _mem if s == scope]
    for k in keys:
        _mem.pop((scope, k), None)
    db.execute("DELETE FROM cache_store WHERE scope=?", (scope,))


def sweep_expired():
    """Remove all expired cache entries. Call periodically."""
    now = datetime.now().isoformat()
    db.execute(
        "DELETE FROM cache_store WHERE expires_at IS NOT NULL AND expires_at < ?",
        (now,)
    )
    # also clear stale mem entries
    for k in list(_mem.keys()):
        scope, key = k
        row = db.execute(
            "SELECT id FROM cache_store WHERE key=? AND scope=?",
            (key, scope), fetch="one"
        )
        if not row:
            _mem.pop(k, None)


def list_all(scope: str = None) -> list:
    if scope:
        return db.execute(
            "SELECT key, scope, expires_at FROM cache_store WHERE scope=? ORDER BY key",
            (scope,), fetch="all"
        )
    return db.execute(
        "SELECT key, scope, expires_at FROM cache_store ORDER BY scope, key",
        fetch="all"
    )
