"""
MOD-M: Monitor external Python processes.
Simple container list — add a process path, check if it's running,
auto-restart at configured times, view its stdout tail.
"""

import subprocess
import sys
import os
import psutil
from datetime import datetime
from . import mod_db as db
from . import mod_signal as sig

# In-memory registry: {name: {pid, proc, path, auto_restart}}
_containers: dict = {}


def add(name: str, script_path: str, auto_restart: bool = True, args: list = None):
    """Register an external script as a container."""
    _containers[name] = {
        "name": name,
        "path": script_path,
        "args": args or [],
        "auto_restart": auto_restart,
        "pid": None,
        "proc": None,
        "started_at": None,
        "status": "idle"
    }


def start(name: str) -> bool:
    c = _containers.get(name)
    if not c:
        return False
    if _is_alive(name):
        return True   # already running
    cmd = [sys.executable, c["path"]] + c["args"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        c["proc"] = proc
        c["pid"] = proc.pid
        c["started_at"] = datetime.now().isoformat()
        c["status"] = "running"
        sig.emit(sig.SIG_EXTERNAL, source="mod_containers", payload={"action": "start", "name": name, "pid": proc.pid})
        return True
    except Exception as e:
        c["status"] = f"error: {e}"
        return False


def stop(name: str) -> bool:
    c = _containers.get(name)
    if not c or not c.get("proc"):
        return False
    try:
        c["proc"].terminate()
        c["proc"].wait(timeout=5)
    except Exception:
        try:
            c["proc"].kill()
        except Exception:
            pass
    c["status"] = "stopped"
    c["pid"] = None
    sig.emit(sig.SIG_EXTERNAL, source="mod_containers", payload={"action": "stop", "name": name})
    return True


def restart(name: str) -> bool:
    stop(name)
    return start(name)


def status(name: str = None) -> list:
    """Return status of all containers (or one)."""
    targets = [_containers[name]] if name and name in _containers else list(_containers.values())
    result = []
    for c in targets:
        alive = _is_alive(c["name"])
        result.append({
            "name": c["name"],
            "path": c["path"],
            "pid": c["pid"],
            "status": "running" if alive else c["status"],
            "started_at": c["started_at"],
            "auto_restart": c["auto_restart"]
        })
    return result


def tail(name: str, lines: int = 20) -> list:
    """Read last N lines of stdout from a running container."""
    c = _containers.get(name)
    if not c or not c.get("proc") or not c["proc"].stdout:
        return []
    collected = []
    try:
        for line in c["proc"].stdout:
            collected.append(line.rstrip())
            if len(collected) > lines:
                collected.pop(0)
    except Exception:
        pass
    return collected


def _is_alive(name: str) -> bool:
    c = _containers.get(name)
    if not c or not c.get("pid"):
        return False
    try:
        return psutil.pid_exists(c["pid"])
    except Exception:
        return False
