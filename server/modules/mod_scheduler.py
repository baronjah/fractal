"""
MOD-C: APScheduler wrapper.
Add scripts, trigger manually, list all jobs, log every run.
"""

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from . import mod_db as db
from . import mod_signal as sig
from . import mod_runner as runner

_scheduler = BackgroundScheduler(timezone="UTC")
_started = False


def start():
    global _started
    if not _started:
        _scheduler.start()
        _started = True
        sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", payload={"action": "started"})


def stop():
    if _started:
        _scheduler.shutdown(wait=False)
        sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", payload={"action": "stopped"})


def add_job(script_path: str, trigger: str = "interval", interval_sec: int = 3600,
            label: str = None, cron_expr: str = None) -> str:
    """
    Register a script with the scheduler.
    trigger = 'interval' | 'cron' | 'once'
    cron_expr = '*/5 * * * *' style string (only for trigger='cron')
    Returns job_id.
    """
    job_id = label or script_path.replace("\\", "/").split("/")[-1]

    if trigger == "interval":
        apstrigger = IntervalTrigger(seconds=interval_sec)
    elif trigger == "cron" and cron_expr:
        parts = cron_expr.strip().split()
        apstrigger = CronTrigger(
            minute=parts[0] if len(parts) > 0 else "*",
            hour=parts[1] if len(parts) > 1 else "*",
            day=parts[2] if len(parts) > 2 else "*",
            month=parts[3] if len(parts) > 3 else "*",
            day_of_week=parts[4] if len(parts) > 4 else "*"
        )
    else:
        # once — run at next scheduler tick
        apstrigger = IntervalTrigger(seconds=max(interval_sec, 1), end_date=datetime.utcnow())

    def _job_fn():
        _run_job(script_path, job_id)

    _scheduler.add_job(_job_fn, apstrigger, id=job_id, replace_existing=True)

    db.execute(
        """INSERT INTO schedule_list (script_id, type, interval_sec, enabled)
           VALUES (?,?,?,1)
           ON CONFLICT(script_id) DO UPDATE SET
           type=excluded.type, interval_sec=excluded.interval_sec, enabled=1""",
        (job_id, trigger, interval_sec)
    )
    sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", payload={"action": "job_added", "id": job_id})
    return job_id


def remove_job(job_id: str):
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
    db.execute("UPDATE schedule_list SET enabled=0 WHERE script_id=?", (job_id,))
    sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", payload={"action": "job_removed", "id": job_id})


def run_now(job_id: str) -> dict:
    """Manual trigger. Finds script path from DB and runs immediately."""
    row = db.execute(
        "SELECT script_id FROM schedule_list WHERE script_id=?",
        (job_id,), fetch="one"
    )
    if not row:
        return {"error": "job not found"}
    return _run_job(row["script_id"], job_id)


def list_jobs() -> list:
    rows = db.execute("SELECT * FROM schedule_list ORDER BY id", fetch="all")
    # merge in live APScheduler next_run info
    for row in rows:
        job = _scheduler.get_job(row["script_id"])
        if job and job.next_run_time:
            row["next_run_live"] = job.next_run_time.isoformat()
        else:
            row["next_run_live"] = None
    return rows


def _run_job(script_path: str, job_id: str) -> dict:
    start_ts = datetime.now()
    db.execute(
        "UPDATE schedule_list SET last_run=? WHERE script_id=?",
        (start_ts.isoformat(), job_id)
    )
    sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", target=job_id,
             payload={"action": "job_start"})

    result = runner.run_script(script_path, caller=f"scheduler:{job_id}")
    duration = int((datetime.now() - start_ts).total_seconds() * 1000)
    result["duration_ms"] = duration

    sig.emit(sig.SIG_SCHEDULE, source="mod_scheduler", target=job_id,
             payload={"action": "job_end", "duration_ms": duration, "ok": result.get("ok")})
    return result
