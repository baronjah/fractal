"""
MOD-F: Subprocess runner + log catcher.
Runs any Python script, captures stdout/stderr line by line.
token_cost = line_count x module_call_count (simple proxy for complexity).
"""

import subprocess
import sys
import time
import os
from . import mod_db as db
from . import mod_signal as sig


def run_script(path: str, args: list = None, caller: str = "unknown",
               sandbox: bool = False, timeout: int = 300) -> dict:
    """
    Run a Python script via subprocess.
    Returns {ok, lines, token_cost, duration_ms, error}
    """
    args = args or []
    cmd = [sys.executable, path] + [str(a) for a in args]

    if not os.path.exists(path):
        result = {"ok": False, "lines": [], "token_cost": 0, "error": f"not found: {path}"}
        _log(path, caller, result, 0)
        return result

    start = time.time()
    lines = []
    error = None
    ok = True

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        try:
            stdout, _ = proc.communicate(timeout=timeout)
            lines = stdout.splitlines()
            if proc.returncode != 0:
                ok = False
                error = f"exit code {proc.returncode}"
        except subprocess.TimeoutExpired:
            proc.kill()
            ok = False
            error = f"timeout after {timeout}s"
    except Exception as e:
        ok = False
        error = str(e)

    duration_ms = int((time.time() - start) * 1000)
    # simple token cost: lines × any line that looks like a module call
    module_calls = sum(1 for l in lines if "mod_" in l)
    token_cost = len(lines) * max(module_calls, 1)

    result = {
        "ok": ok,
        "lines": lines,
        "token_cost": token_cost,
        "duration_ms": duration_ms,
        "error": error
    }
    _log(path, caller, result, duration_ms)

    sig.emit(
        sig.SIG_SCHEDULE, source="mod_runner", target=path,
        payload={"ok": ok, "lines": len(lines), "token_cost": token_cost, "caller": caller}
    )
    return result


def _log(path: str, caller: str, result: dict, duration_ms: int):
    log_text = "\n".join(result.get("lines", []))[:8000]
    db.execute(
        """INSERT INTO script_history (script_id, duration_ms, tokens_used, result, log)
           VALUES (?,?,?,?,?)""",
        (
            path, duration_ms, result.get("token_cost", 0),
            "ok" if result.get("ok") else result.get("error", "fail"),
            log_text
        )
    )


def get_history(script_id: str = None, limit: int = 50) -> list:
    if script_id:
        return db.execute(
            "SELECT * FROM script_history WHERE script_id=? ORDER BY id DESC LIMIT ?",
            (script_id, limit), fetch="all"
        )
    return db.execute(
        "SELECT * FROM script_history ORDER BY id DESC LIMIT ?",
        (limit,), fetch="all"
    )
