"""
MOD-H: Zone lock manager.
Before any script touches a file, it acquires a lock.
Other scripts that try to lock the same file wait or fail.
Locks auto-expire to prevent deadlocks.
"""

from datetime import datetime, timedelta
from . import mod_db as db
from . import mod_signal as sig


DEFAULT_TTL_SEC = 60


def acquire(file_path: str, locked_by: str, lock_type: str = "write", ttl_sec: int = DEFAULT_TTL_SEC) -> bool:
    """
    Try to lock file_path for locked_by.
    Returns True if lock acquired, False if already locked by someone else.
    """
    # clear expired locks first
    _sweep()
    existing = db.execute(
        "SELECT locked_by FROM lock_registry WHERE file_path=?",
        (file_path,), fetch="one"
    )
    if existing:
        return False   # locked
    expires_at = (datetime.now() + timedelta(seconds=ttl_sec)).isoformat()
    try:
        db.execute(
            """INSERT INTO lock_registry (file_path, lock_type, locked_by, expires_at)
               VALUES (?,?,?,?)""",
            (file_path, lock_type, locked_by, expires_at)
        )
        sig.emit(sig.SIG_DATA, source="mod_lock", target=file_path,
                 payload={"action": "lock_acquired", "by": locked_by})
        return True
    except Exception:
        return False


def release(file_path: str, locked_by: str) -> bool:
    """
    Release a lock. Only the original locker can release it.
    Returns True if released.
    """
    existing = db.execute(
        "SELECT locked_by FROM lock_registry WHERE file_path=?",
        (file_path,), fetch="one"
    )
    if not existing:
        return False
    if existing["locked_by"] != locked_by:
        return False
    db.execute("DELETE FROM lock_registry WHERE file_path=?", (file_path,))
    sig.emit(sig.SIG_DATA, source="mod_lock", target=file_path,
             payload={"action": "lock_released", "by": locked_by})
    return True


def force_release(file_path: str):
    """Admin force-unlock. Use carefully."""
    db.execute("DELETE FROM lock_registry WHERE file_path=?", (file_path,))


def is_locked(file_path: str) -> bool:
    _sweep()
    row = db.execute(
        "SELECT id FROM lock_registry WHERE file_path=?",
        (file_path,), fetch="one"
    )
    return row is not None


def get_lock_info(file_path: str) -> dict:
    _sweep()
    return db.execute(
        "SELECT * FROM lock_registry WHERE file_path=?",
        (file_path,), fetch="one"
    )


def list_locks() -> list:
    _sweep()
    return db.execute(
        "SELECT * FROM lock_registry ORDER BY locked_at DESC",
        fetch="all"
    )


def _sweep():
    """Remove expired locks."""
    now = datetime.now().isoformat()
    db.execute(
        "DELETE FROM lock_registry WHERE expires_at IS NOT NULL AND expires_at < ?",
        (now,)
    )
