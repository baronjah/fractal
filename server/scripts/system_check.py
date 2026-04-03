"""
system_check.py — health check for all fractal modules.
Reports which modules import OK, which tables exist, counts rows.
Type: single_use / check
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

MODULES = [
    "modules.mod_db",
    "modules.mod_signal",
    "modules.mod_patterns",
    "modules.mod_numbers",
    "modules.mod_cache",
    "modules.mod_lock",
    "modules.mod_file",
    "modules.mod_scheduler",
    "modules.mod_runner",
    "modules.mod_containers",
]

print("[system_check] === FRACTAL HEALTH CHECK ===")
ok = 0
fail = 0
for mod in MODULES:
    try:
        __import__(mod)
        print(f"  OK  {mod}")
        ok += 1
    except Exception as e:
        print(f"  ERR {mod}: {e}")
        fail += 1

print(f"\n[system_check] modules: {ok} ok, {fail} failed")

# check DB tables
try:
    from modules import mod_db as db
    db.init_db()
    stats = db.table_stats()
    print("\n[system_check] DB tables:")
    for table, count in stats.items():
        print(f"  {table:<30} {count} rows")

    from modules import mod_signal as sig
    sig.emit(sig.SIG_SYSTEM, source="system_check", payload={
        "modules_ok": ok, "modules_failed": fail, "tables": len(stats)
    })
except Exception as e:
    print(f"[system_check] DB error: {e}")

print("\n[system_check] done")
