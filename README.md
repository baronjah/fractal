# fractal

Self-managing Python/Flask server. Every action passes through a module. Every module logs. Every log feeds the visualizer.

**Port:** 5331
**Start:** `run.bat` (Windows) or `cd server && python core_server.py`

## Architecture

```
server/
  core_server.py          Flask hub — all routes
  modules/
    mod_db.py             SQLite core, 9 tables
    mod_signal.py         Signal bus — emit, listen, log
    mod_patterns.py       Demon catcher — watches everything, scores luck
    mod_numbers.py        L=Luck — numerology engine (FLOW/BALANCE/BUILD/CHAOS/AMPLIFIED)
    mod_cache.py          Scoped KV cache with TTL
    mod_lock.py           Zone lock manager — file locking, auto-expire
    mod_file.py           File access through lock + demon catcher
    mod_scheduler.py      APScheduler wrapper — interval, cron, run-now
    mod_runner.py         Subprocess runner — captures stdout, token cost
    mod_containers.py     Monitor external Python processes
  templates/
    dashboard.html        Live hub — signals, luck, scheduler overview
    signals.html          Signal log with filter
    patterns.html         Demon catcher view — what was written and when
    scheduler.html        Job manager
    database.html         Table browser + SELECT query box
    numbers.html          Luck oracle — L IS FOR LUCK
parsers/
  parser_core.py          Parse any file by extension
  parser_rules.json       Rules per ext: .txt .md .py .gd .log .csv
numbers/
  luck_tables.json        Number → mode → meaning → color → vibe
```

## Install

```
pip install -r requirements.txt
```

## Luck modes

| Mode | Numbers | Meaning |
|------|---------|---------|
| FLOW | 1, 3, 9 | Go. Start. Push. |
| BALANCE | 2, 6 | Wait. Listen. Connect. |
| BUILD | 4, 8 | Work. Build. Endure. |
| CHAOS | 5, 7 | Alert. Shift. Adapt. |
| AMPLIFIED | 11, 22, 33 | Everything x10. |

## Branches

- `main` — stable base
- `feature/excel-database` — xlsx/xlsm file indexer and search
- `feature/launch-sequence` — 12-station animated boot sequence
- `feature/vector-studio` — Photoshop-like layer editor in HTML
