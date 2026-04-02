# FRACTAL CORE — Build Plan
**Project root:** `D:\fractal\`
**Deadline:** Tuesday 2026-04-07 (play with it by then)
**Seed:** ExcelMorphicEngine (`app.py` ~4500 lines, Flask/Python)
**Architecture doc:** `D:\fab\Evolve_Us\claude_excel_database_browser\one.txt` (sections A–P, MOD-I through MOD-P)

---

## WHAT THIS IS

A self-managing, self-aware program that grows from EME.
**Core law:** Every action passes through a module. Every module logs. Every log feeds the visualizer.

Two layers:
- `BACKEND` — Python/Flask + scheduler + signal bus + database + pattern catcher
- `FRONTEND` — Godot 4 (visualizer, UI builder, script IDE) + HTML (inherited from EME)

---

## FOLDER STRUCTURE

```
D:\fractal\
├── server\
│   ├── core_server.py          ← Flask hub: all routes, imports modules
│   ├── modules\
│   │   ├── mod_signal.py       ← MOD-N: signal bus (in-memory + SQLite log)
│   │   ├── mod_scheduler.py    ← MOD-C: APScheduler wrapper
│   │   ├── mod_runner.py       ← MOD-F: subprocess runner + log catcher
│   │   ├── mod_db.py           ← MOD-D + MOD-P: SQLite database core
│   │   ├── mod_cache.py        ← MOD-B: scoped key-value cache with expiry
│   │   ├── mod_lock.py         ← MOD-H: zone lock manager
│   │   ├── mod_file.py         ← MOD-G2..G5: file access with lock + log
│   │   ├── mod_patterns.py     ← DEMON CATCHER: logs what/when/who writes
│   │   ├── mod_numbers.py      ← L=LUCK: numerology engine, hell↔luck mode
│   │   └── mod_containers.py   ← MOD-M: monitor external Python processes
│   ├── databases\
│   │   └── fractal.db          ← SQLite: all internal DBs as tables
│   ├── scripts\                ← user-created schedulable scripts
│   ├── bundles\                ← script combos
│   └── templates\
│       ├── dashboard.html      ← main hub
│       ├── signals.html        ← live signal board
│       ├── scheduler.html      ← scheduler board
│       ├── patterns.html       ← what was written + when (demon catcher view)
│       ├── database.html       ← database browser
│       └── numbers.html        ← luck/numerology view
├── parsers\
│   ├── parser_rules.json       ← rules per file extension
│   ├── parse_txt.py
│   ├── parse_md.py
│   ├── parse_py.py
│   ├── parse_gdscript.py
│   └── parser_core.py         ← fire any parser at any file
├── numbers\
│   └── luck_tables.json        ← the number→meaning mapping
├── godot\                      ← Godot frontend (evolve from D:\fab)
└── docs\
    └── ARCHITECTURE.md         ← living architecture doc (copy of sections A-P)
```

---

## PHASE α — FOUNDATION (Days 1–2, now → Thursday)

### α1. core_server.py
- Flask app on port 5331 (5330 = EME, runs in parallel)
- Imports all modules
- Routes: `/`, `/signals`, `/scheduler`, `/patterns`, `/db`, `/numbers`
- EME's app.py routes PRESERVED — copy them over as Phase 0/1/2 bundle

### α2. mod_db.py — SQLite Core
Tables:
- `signal_log` (id, timestamp, signal_id, source, target, status, payload)
- `script_history` (id, script_id, run_time, duration_ms, tokens_used, result, log)
- `file_access_log` (id, file_path, script_id, action, lock_state, timestamp)
- `schedule_list` (id, script_id, type, interval_sec, last_run, next_run, token_cost, enabled)
- `module_calls` (id, module_id, caller, call_count, timestamp)
- `cache_store` (id, key, value, scope, expires_at)
- `patterns_log` (id, timestamp, source, content, content_type, char_count, word_count, numbers_found, luck_score)
- `lock_registry` (id, file_path, lock_type, locked_by, locked_at, expires_at)
- `numbers_log` (id, timestamp, input, calculated_value, luck_mode, notes)

### α3. mod_signal.py — Signal Bus
- `emit(signal_id, source, target, payload)` — logs + dispatches
- `register_handler(signal_id, fn)` — attach callable
- `get_log(limit, filter_source)` — query signal_log table
- Signal groups: SIG_SYSTEM, SIG_DATA, SIG_SCHEDULE, SIG_UI, SIG_PATTERN, SIG_LUCK

### α4. mod_patterns.py — DEMON CATCHER
- Watches: file writes, server input, text submissions
- `catch(content, source, content_type)` — logs to patterns_log
- `find_numbers(text)` — extract all numbers
- `get_patterns(since, source)` — query patterns
- Hooks into every POST endpoint in core_server

### α5. dashboard.html
- Single page hub: 5 panels
  - Live signal feed (poll /api/signals every 2s)
  - Scheduler status (running/idle scripts)
  - Pattern log (last 20 caught patterns)
  - Database tables (row counts, last touched)
  - Numbers/luck score (current "mode")

---

## PHASE β — SCHEDULER + RUNNER (Days 2–3, Thursday–Friday)

### β1. mod_scheduler.py
- APScheduler (BackgroundScheduler)
- `add_job(script_path, trigger, interval_sec, label)`
- `list_jobs()` — returns all with next_run, last_run, status
- `run_now(job_id)` — manual trigger
- Logs start/end to script_history

### β2. mod_runner.py
- `run_script(path, args, sandbox)` — subprocess.Popen
- Captures stdout/stderr line by line
- `token_cost` = line_count × module_call_count (simple measure)
- Logs to script_history

### β3. Text Parsers
- `parser_core.py` — detect extension → dispatch to right parser
- Each parser: reads file, applies rules from `parser_rules.json`, returns cleaned text
- Rules: strip comments, normalize whitespace, extract numbers, extract structure
- Store parse result in patterns_log

---

## PHASE γ — NUMBERS + LUCK (Day 3, Friday)

### mod_numbers.py — L IS FOR LUCK
The system:
- Every number has a base value 1–9 (digit sum reduction, classic numerology)
- Special numbers: 11, 22, 33 (master numbers — stay as-is)
- Input: any string, date, event name, timestamp
- `calculate(input)` → base_value, master_number, luck_mode
- `luck_mode`: based on the number:
  - 1,3,9 → FLOW (peaceful easy mode)
  - 2,6 → BALANCE
  - 4,8 → BUILD (work mode)
  - 5,7 → CHAOS (hell mode — stay alert)
  - 11,22,33 → AMPLIFIED (everything × 10)
- Database gets populated: every pattern caught → auto-calculate luck score
- Timestamp of each event gets its own luck number → you can see what time of day is lucky

### luck_tables.json
- Number → meaning, color, element, mode
- Editable by user for custom mappings

---

## PHASE δ — GODOT FRONTEND (Days 3–5, Fri–Tue)

Move/copy `D:\fab\` → `D:\fractal\godot\`

New Godot scenes (connect to core_server via HTTP):
- `Dashboard.tscn` — polls /api/* endpoints, renders live
- `PatternViewer.tscn` — the demon catcher view, 3D scatter of caught patterns
- `NumbersOrb.tscn` — visual luck mode display (pulsing sphere, color = mode)

The octree: `OctreeGrid.gd`
- 3D grid of chunks, each chunk = a time window of patterns
- Chunks split when they fill up (fractal subdivision)
- Items (patterns, signals, numbers) placed by their timestamp + luck value

---

## DEMON CATCHER — what it catches specifically

1. **Text submissions** — anything POSTed to the server
2. **File touches** — any file read/written through mod_file
3. **Script runs** — what ran, how long, result
4. **Your typing patterns** — if you submit text, it timestamps + analyzes
5. **Number occurrences** — extracts all numbers from all caught content
6. **Time patterns** — what hour/day you're most active, lucky hour detection
7. **Automation targets** — notepad files, text files → parsers clean them on schedule

---

## SIGNAL TYPES (for mod_signal.py enum)

```python
SIG_SYSTEM   = "SYS"    # health, locks, restarts
SIG_DATA     = "DAT"    # file read/write/delete
SIG_SCHEDULE = "SCH"    # script start/end/reschedule
SIG_UI       = "UI"     # button clicks, form submits
SIG_PATTERN  = "PAT"    # demon catcher caught something
SIG_LUCK     = "LCK"    # luck mode changed
SIG_EXTERNAL = "EXT"    # container process events
```

---

## BY TUESDAY — WHAT YOU CAN PLAY WITH

1. Open browser → `localhost:5331` → Dashboard
2. See: live signal feed, recent patterns, scheduler status, luck mode
3. Type anything into the pattern catcher → it logs, calculates your luck number, stores it
4. View your typing history → demon catcher shows when you wrote what
5. Run a script from the scheduler board → see live output
6. Browse database tables → inspect what's stored
7. See your current "luck mode" and the 3D number orb (Godot if opened)
8. File parsers: drop a .txt file → it gets parsed, cleaned, numbers extracted

---

## WHAT TO PULL FROM ANTIGRAVITY SERVER

From `D:\AI_COORDINATION\`:
- `dna_server.py` → DNA tagging system → becomes a pattern rule in mod_patterns
- `prompt_parser.py` → text parsing logic → feeds parser_core.py
- `prompts_database.csv` → seed data for patterns_log
- `scan_projects.py` → project scanner → becomes a scheduled script in scripts/

---

## OPEN QUESTIONS (decide next session)
- Port for core_server: 5331? (5330 = EME)
- SQLite file: `D:\fractal\server\databases\fractal.db`
- Keep EME routes inside core_server or keep EME separate on 5330?
- Godot: HTTP polling or WebSocket for live updates?
- Luck number input: manual submit only, or also auto-catch timestamps?

---

*Version 1 — Session 2026-04-02*
