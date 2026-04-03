"""
daily_seed.py — runs once a day via scheduler.
Logs today's date luck. Sweeps expired cache. Emits a DAT signal.
Type: scheduled / daily
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules import mod_db as db
from modules import mod_signal as sig
from modules import mod_numbers as num
from modules import mod_cache as cache

db.init_db()

from datetime import date
today = str(date.today())

# log today only if not already there
existing = db.execute(
    "SELECT id FROM numbers_log WHERE input=? AND notes='daily_seed'",
    (today,), fetch="one"
)
if not existing:
    result = num.log_calculation(today, notes="daily_seed")
    print(f"[daily_seed] {today} = {result['value']} {result['mode']} — {result.get('vibe','')}")
else:
    print(f"[daily_seed] {today} already seeded")

# sweep cache
swept = cache.sweep_expired()
print(f"[daily_seed] cache swept: {swept} entries removed")

# emit
sig.emit(sig.SIG_DATA, source="daily_seed", payload={"date": today, "swept": swept})
print("[daily_seed] done")
