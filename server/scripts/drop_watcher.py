"""
drop_watcher.py — runs every 60s via scheduler.
Scans server/scripts/drop/ for new files, parses them, feeds demon catcher.
Moves parsed files to drop/done/ so they don't parse twice.
Type: scheduled / interval
"""
import sys, os, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from modules import mod_signal as sig
from modules import mod_db as db

db.init_db()

DROP_DIR = os.path.join(os.path.dirname(__file__), "drop")
DONE_DIR = os.path.join(DROP_DIR, "done")
os.makedirs(DONE_DIR, exist_ok=True)

PARSEABLE = {".txt", ".md", ".py", ".gd", ".json", ".log", ".csv"}

found = 0
for fname in os.listdir(DROP_DIR):
    fpath = os.path.join(DROP_DIR, fname)
    if not os.path.isfile(fpath):
        continue
    ext = os.path.splitext(fname)[1].lower()
    if ext not in PARSEABLE:
        continue

    try:
        from parsers.parser_core import parse_file
        result = parse_file(fpath, send_to_catcher=True)
        print(f"[drop_watcher] parsed {fname}: {result.get('line_count',0)} lines, luck {result.get('luck_score','?')}")
        shutil.move(fpath, os.path.join(DONE_DIR, fname))
        found += 1
    except Exception as e:
        print(f"[drop_watcher] error on {fname}: {e}")

if found:
    sig.emit(sig.SIG_DATA, source="drop_watcher", payload={"parsed": found})
    print(f"[drop_watcher] done — {found} files processed")
else:
    print("[drop_watcher] drop folder empty")
