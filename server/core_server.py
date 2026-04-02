"""
FRACTAL CORE — core_server.py
Flask hub on port 5331 (5330 = EME, runs in parallel).
Every route is a window into the fractal.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from modules import mod_db as db
from modules import mod_signal as sig
from modules import mod_patterns as pat
from modules import mod_numbers as num
from modules import mod_cache as cache
from modules import mod_scheduler as sched
from modules import mod_runner as runner
from modules import mod_file as mfile
from modules import mod_lock as lock

app = Flask(__name__, template_folder="templates")

# ── Boot ───────────────────────────────────────────────────────────────────

def boot():
    db.init_db()
    sched.start()
    sig.emit(sig.SIG_SYSTEM, source="core_server", payload={"action": "boot", "port": 5331})
    print("[FRACTAL] booted on port 5331")

# ── HTML pages ─────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    luck = num.current_mode()
    return render_template("dashboard.html", luck=luck)

@app.route("/signals")
def signals_page():
    return render_template("signals.html")

@app.route("/scheduler")
def scheduler_page():
    return render_template("scheduler.html")

@app.route("/patterns")
def patterns_page():
    return render_template("patterns.html")

@app.route("/db")
def database_page():
    stats = db.table_stats()
    return render_template("database.html", stats=stats)

@app.route("/numbers")
def numbers_page():
    luck = num.current_mode()
    return render_template("numbers.html", luck=luck)

# ── API — signals ──────────────────────────────────────────────────────────

@app.route("/api/signals")
def api_signals():
    limit  = int(request.args.get("limit", 50))
    source = request.args.get("source")
    filt   = request.args.get("signal")
    data   = sig.get_log(limit=limit, filter_source=source, filter_signal=filt)
    return jsonify(data)

@app.route("/api/signal/emit", methods=["POST"])
def api_emit():
    body = request.get_json(force=True) or {}
    pat.catch(str(body), source="api:signal_emit", content_type="json")
    row_id = sig.emit(
        body.get("signal_id", sig.SIG_UI),
        source=body.get("source", "user"),
        target=body.get("target"),
        payload=body.get("payload")
    )
    return jsonify({"ok": True, "id": row_id})

# ── API — patterns (demon catcher) ────────────────────────────────────────

@app.route("/api/patterns")
def api_patterns():
    limit  = int(request.args.get("limit", 50))
    since  = request.args.get("since")
    source = request.args.get("source")
    return jsonify(pat.get_patterns(limit=limit, since=since, source=source))

@app.route("/api/patterns/catch", methods=["POST"])
def api_catch():
    body = request.get_json(force=True) or {}
    content = body.get("content", "")
    source  = body.get("source", "user_input")
    ctype   = body.get("type", "text")
    pat.catch(content, source=source, content_type=ctype)
    result = num.log_calculation(content, notes=f"caught from {source}")
    return jsonify({"ok": True, "luck": result})

@app.route("/api/patterns/hours")
def api_active_hours():
    return jsonify({
        "active": pat.active_hours(),
        "lucky":  pat.lucky_hours()
    })

# ── API — numbers / luck ───────────────────────────────────────────────────

@app.route("/api/numbers/calculate", methods=["POST"])
def api_calculate():
    body = request.get_json(force=True) or {}
    text = body.get("text", "")
    result = num.log_calculation(text)
    return jsonify(result)

@app.route("/api/numbers/current")
def api_current_luck():
    return jsonify(num.current_mode())

@app.route("/api/numbers/log")
def api_numbers_log():
    limit = int(request.args.get("limit", 50))
    return jsonify(num.get_log(limit=limit))

# ── API — scheduler ────────────────────────────────────────────────────────

@app.route("/api/scheduler/jobs")
def api_jobs():
    return jsonify(sched.list_jobs())

@app.route("/api/scheduler/add", methods=["POST"])
def api_add_job():
    body = request.get_json(force=True) or {}
    job_id = sched.add_job(
        script_path=body["script_path"],
        trigger=body.get("trigger", "interval"),
        interval_sec=int(body.get("interval_sec", 3600)),
        label=body.get("label"),
        cron_expr=body.get("cron_expr")
    )
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/api/scheduler/run/<job_id>", methods=["POST"])
def api_run_now(job_id):
    result = sched.run_now(job_id)
    return jsonify(result)

@app.route("/api/scheduler/remove/<job_id>", methods=["DELETE"])
def api_remove_job(job_id):
    sched.remove_job(job_id)
    return jsonify({"ok": True})

# ── API — script runner ────────────────────────────────────────────────────

@app.route("/api/runner/run", methods=["POST"])
def api_run_script():
    body = request.get_json(force=True) or {}
    path = body.get("path", "")
    args = body.get("args", [])
    result = runner.run_script(path, args=args, caller="api:runner")
    return jsonify(result)

@app.route("/api/runner/history")
def api_runner_history():
    script = request.args.get("script")
    limit  = int(request.args.get("limit", 50))
    return jsonify(runner.get_history(script_id=script, limit=limit))

# ── API — database ─────────────────────────────────────────────────────────

@app.route("/api/db/stats")
def api_db_stats():
    return jsonify(db.table_stats())

@app.route("/api/db/query", methods=["POST"])
def api_db_query():
    body = request.get_json(force=True) or {}
    sql  = body.get("sql", "")
    # safety: read-only queries only
    first = sql.strip().upper().split()[0] if sql.strip() else ""
    if first not in ("SELECT",):
        return jsonify({"error": "only SELECT allowed here"}), 400
    rows = db.execute(sql, fetch="all")
    return jsonify(rows)

# ── API — file access ──────────────────────────────────────────────────────

@app.route("/api/files/history")
def api_file_history():
    path  = request.args.get("path")
    limit = int(request.args.get("limit", 50))
    return jsonify(mfile.get_history(file_path=path, limit=limit))

@app.route("/api/files/locks")
def api_locks():
    return jsonify(lock.list_locks())

# ── API — cache ────────────────────────────────────────────────────────────

@app.route("/api/cache")
def api_cache():
    scope = request.args.get("scope")
    return jsonify(cache.list_all(scope=scope))

@app.route("/api/cache/set", methods=["POST"])
def api_cache_set():
    body = request.get_json(force=True) or {}
    cache.set(body["key"], body["value"], scope=body.get("scope", "global"),
              ttl_sec=body.get("ttl_sec"))
    return jsonify({"ok": True})

@app.route("/api/cache/get/<key>")
def api_cache_get(key):
    scope = request.args.get("scope", "global")
    val   = cache.get(key, scope=scope)
    return jsonify({"key": key, "scope": scope, "value": val})

# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    boot()
    app.run(host="0.0.0.0", port=5331, debug=False, use_reloader=False)
