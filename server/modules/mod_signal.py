"""
MOD-N: Signal bus
Emit signals, attach handlers, query log.
Every module that does something important emits a signal.
"""

import json
from datetime import datetime
from . import mod_db as db

# ── Signal group constants ─────────────────────────────────────────────────
SIG_SYSTEM   = "SYS"   # health, locks, restarts
SIG_DATA     = "DAT"   # file read/write/delete
SIG_SCHEDULE = "SCH"   # script start/end/reschedule
SIG_UI       = "UI"    # button clicks, form submits
SIG_PATTERN  = "PAT"   # demon catcher caught something
SIG_LUCK     = "LCK"   # luck mode changed
SIG_EXTERNAL = "EXT"   # container process events

_handlers: dict[str, list] = {}   # signal_id → [callable, ...]


def register_handler(signal_id: str, fn):
    """Attach a callable to a signal. Called whenever that signal is emitted."""
    _handlers.setdefault(signal_id, []).append(fn)


def emit(signal_id: str, source: str = None, target: str = None, payload: dict = None) -> int:
    """
    Log + dispatch a signal.
    Returns the new signal_log row id.
    """
    payload_str = json.dumps(payload) if payload else None
    row_id = db.execute(
        "INSERT INTO signal_log (signal_id, source, target, payload) VALUES (?,?,?,?)",
        (signal_id, source, target, payload_str)
    )
    # fire handlers
    for fn in _handlers.get(signal_id, []):
        try:
            fn(signal_id=signal_id, source=source, target=target, payload=payload)
        except Exception as e:
            # don't let a bad handler kill the bus
            db.execute(
                "INSERT INTO signal_log (signal_id, source, target, status, payload) VALUES (?,?,?,?,?)",
                (SIG_SYSTEM, "mod_signal", source, "handler_error", json.dumps({"error": str(e)}))
            )
    return row_id


def get_log(limit: int = 50, filter_source: str = None, filter_signal: str = None) -> list:
    """Query recent signals. Returns list of dicts."""
    if filter_source and filter_signal:
        return db.execute(
            "SELECT * FROM signal_log WHERE source=? AND signal_id=? ORDER BY id DESC LIMIT ?",
            (filter_source, filter_signal, limit), fetch="all"
        )
    if filter_source:
        return db.execute(
            "SELECT * FROM signal_log WHERE source=? ORDER BY id DESC LIMIT ?",
            (filter_source, limit), fetch="all"
        )
    if filter_signal:
        return db.execute(
            "SELECT * FROM signal_log WHERE signal_id=? ORDER BY id DESC LIMIT ?",
            (filter_signal, limit), fetch="all"
        )
    return db.execute(
        "SELECT * FROM signal_log ORDER BY id DESC LIMIT ?",
        (limit,), fetch="all"
    )
