"""
MOD-G: File access with lock + log.
Every file read/write goes through here so we have a full history.
Direct os/open calls in scripts are bad manners — use this.
"""

import os
from . import mod_db as db
from . import mod_lock as lock
from . import mod_signal as sig
from . import mod_patterns as pat


def read(file_path: str, caller: str = "unknown") -> str:
    """Read file contents as string. Logs the access."""
    _log(file_path, caller, "read")
    sig.emit(sig.SIG_DATA, source=caller, target=file_path, payload={"action": "read"})
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"mod_file.read: not found: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(file_path: str, content: str, caller: str = "unknown", catch_pattern: bool = True) -> bool:
    """
    Write string to file. Acquires lock, writes, releases.
    catch_pattern=True → runs content through demon catcher.
    Returns True on success.
    """
    if not lock.acquire(file_path, caller):
        raise PermissionError(f"mod_file.write: locked: {file_path} (caller={caller})")
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        _log(file_path, caller, "write")
        sig.emit(sig.SIG_DATA, source=caller, target=file_path, payload={"action": "write"})
        if catch_pattern:
            pat.catch(content, source=f"file:{file_path}", content_type="file")
        return True
    finally:
        lock.release(file_path, caller)


def append(file_path: str, content: str, caller: str = "unknown") -> bool:
    """Append to file. Acquires lock."""
    if not lock.acquire(file_path, caller):
        raise PermissionError(f"mod_file.append: locked: {file_path}")
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)
        _log(file_path, caller, "append")
        return True
    finally:
        lock.release(file_path, caller)


def delete(file_path: str, caller: str = "unknown") -> bool:
    """Delete a file. Logs it."""
    _log(file_path, caller, "delete")
    sig.emit(sig.SIG_DATA, source=caller, target=file_path, payload={"action": "delete"})
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def exists(file_path: str) -> bool:
    return os.path.exists(file_path)


def get_history(file_path: str = None, limit: int = 50) -> list:
    """Query file_access_log. If file_path given, filter to that file."""
    if file_path:
        return db.execute(
            "SELECT * FROM file_access_log WHERE file_path=? ORDER BY id DESC LIMIT ?",
            (file_path, limit), fetch="all"
        )
    return db.execute(
        "SELECT * FROM file_access_log ORDER BY id DESC LIMIT ?",
        (limit,), fetch="all"
    )


def _log(file_path: str, script_id: str, action: str):
    locked = "locked" if lock.is_locked(file_path) else "unlocked"
    db.execute(
        "INSERT INTO file_access_log (file_path, script_id, action, lock_state) VALUES (?,?,?,?)",
        (file_path, script_id, action, locked)
    )
