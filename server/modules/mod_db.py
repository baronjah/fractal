"""
MOD-D + MOD-P: SQLite database core
All internal tables live in one fractal.db file.
Every module calls db.execute() — never touches sqlite3 directly.
"""

import sqlite3
import os
import threading
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "databases", "fractal.db")
_lock = threading.Lock()


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    with _lock:
        conn = _conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db():
    """Create all tables if they don't exist. Safe to call on every startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS signal_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now')),
                signal_id   TEXT    NOT NULL,
                source      TEXT,
                target      TEXT,
                status      TEXT    DEFAULT 'emitted',
                payload     TEXT
            );

            CREATE TABLE IF NOT EXISTS script_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id   TEXT    NOT NULL,
                run_time    TEXT    DEFAULT (datetime('now')),
                duration_ms INTEGER,
                tokens_used INTEGER DEFAULT 0,
                result      TEXT,
                log         TEXT
            );

            CREATE TABLE IF NOT EXISTS file_access_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path   TEXT    NOT NULL,
                script_id   TEXT,
                action      TEXT,
                lock_state  TEXT    DEFAULT 'unlocked',
                timestamp   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS schedule_list (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id   TEXT    NOT NULL UNIQUE,
                type        TEXT,
                interval_sec INTEGER,
                last_run    TEXT,
                next_run    TEXT,
                token_cost  INTEGER DEFAULT 0,
                enabled     INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS module_calls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id   TEXT    NOT NULL,
                caller      TEXT,
                call_count  INTEGER DEFAULT 1,
                timestamp   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cache_store (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT    NOT NULL,
                value       TEXT,
                scope       TEXT    DEFAULT 'global',
                expires_at  TEXT,
                UNIQUE(key, scope)
            );

            CREATE TABLE IF NOT EXISTS patterns_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT    DEFAULT (datetime('now')),
                source        TEXT,
                content       TEXT,
                content_type  TEXT,
                char_count    INTEGER DEFAULT 0,
                word_count    INTEGER DEFAULT 0,
                numbers_found TEXT,
                luck_score    INTEGER
            );

            CREATE TABLE IF NOT EXISTS lock_registry (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path   TEXT    NOT NULL UNIQUE,
                lock_type   TEXT    DEFAULT 'write',
                locked_by   TEXT,
                locked_at   TEXT    DEFAULT (datetime('now')),
                expires_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS numbers_log (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp        TEXT    DEFAULT (datetime('now')),
                input            TEXT,
                calculated_value INTEGER,
                luck_mode        TEXT,
                notes            TEXT
            );

            CREATE TABLE IF NOT EXISTS signal_routes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id   TEXT    NOT NULL,
                script_path TEXT    NOT NULL,
                label       TEXT,
                enabled     INTEGER DEFAULT 1,
                created_at  TEXT    DEFAULT (datetime('now')),
                UNIQUE(signal_id, script_path)
            );
        """)
    return True


def execute(sql: str, params: tuple = (), fetch: str = None):
    """
    Universal query runner.
    fetch=None    → execute only (INSERT/UPDATE/DELETE)
    fetch='one'   → fetchone() → dict or None
    fetch='all'   → fetchall() → list of dicts
    fetch='count' → rowcount
    """
    with get_db() as conn:
        cur = conn.execute(sql, params)
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        if fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        if fetch == "count":
            return cur.rowcount
        return cur.lastrowid


def table_stats():
    """Return {table_name: row_count} for all tables."""
    tables = [
        "signal_log", "script_history", "file_access_log",
        "schedule_list", "module_calls", "cache_store",
        "patterns_log", "lock_registry", "numbers_log", "signal_routes"
    ]
    stats = {}
    for t in tables:
        row = execute(f"SELECT COUNT(*) AS cnt FROM {t}", fetch="one")
        stats[t] = row["cnt"] if row else 0
    return stats
