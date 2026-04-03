# FRACTAL — WIRING MAP
> Auto-generated reference. What exists, what touches what, what's missing.

---

## ARCHITECTURE AT A GLANCE

```
BROWSER
  │
  ▼
core_server.py  (Flask, port 5331)
  │
  ├── mod_db       ← everyone calls this. THE CENTER.
  ├── mod_signal   ← the bus. everyone emits here.
  ├── mod_patterns ← demon catcher. swallows all text.
  ├── mod_numbers  ← luck engine. every string has a number.
  ├── mod_cache    ← key/value. fast + persistent.
  ├── mod_lock     ← file locks. acquire before write.
  ├── mod_file     ← file I/O. goes through lock + log.
  ├── mod_scheduler← APScheduler. runs scripts on interval/cron.
  ├── mod_runner   ← subprocess. runs any .py, captures output.
  └── mod_containers← process monitor. start/stop/restart scripts.
```

---

## SIGNAL CONSTANTS

| ID  | Constant        | Emitted by                         |
|-----|-----------------|------------------------------------|
| SYS | SIG_SYSTEM      | boot(), mod_lock, system_check.py  |
| DAT | SIG_DATA        | mod_file, daily_seed.py            |
| SCH | SIG_SCHEDULE    | mod_scheduler (start/end/reschedule)|
| UI  | SIG_UI          | /api/signal/emit (user triggers)   |
| PAT | SIG_PATTERN     | mod_patterns.catch()               |
| LCK | SIG_LUCK        | *(not yet emitted on mode change)* |
| EXT | SIG_EXTERNAL    | mod_containers                     |

**GAP:** `SIG_LUCK` is defined but never emitted. mod_numbers changes mode but doesn't signal it.

---

## API ENDPOINTS — FULL WIRING TABLE

### SIGNALS
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/signals | GET | mod_signal | — | signal_log |
| /api/signal/emit | POST | mod_signal, mod_patterns | any SIG_* | signal_log, patterns_log |
| /api/signals/routes | GET | mod_signal | — | signal_routes |
| /api/signals/routes/add | POST | mod_signal | — | signal_routes |
| /api/signals/routes/<id> | DELETE | mod_signal | — | signal_routes |
| /api/signals/routes/<id>/toggle | POST | mod_signal | — | signal_routes |

### PATTERNS (DEMON CATCHER)
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/patterns | GET | mod_patterns | — | patterns_log |
| /api/patterns/catch | POST | mod_patterns, mod_numbers | PAT | patterns_log, numbers_log |
| /api/patterns/hours | GET | mod_patterns | — | patterns_log |

### NUMBERS / LUCK
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/numbers/calculate | POST | mod_numbers | — | numbers_log |
| /api/numbers/current | GET | mod_numbers | — | numbers_log |
| /api/numbers/log | GET | mod_numbers | — | numbers_log |

### SCHEDULER
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/scheduler/jobs | GET | mod_scheduler | — | schedule_list |
| /api/scheduler/add | POST | mod_scheduler | SCH | schedule_list |
| /api/scheduler/run/<id> | POST | mod_scheduler, mod_runner | SCH | schedule_list, script_history |
| /api/scheduler/remove/<id> | DELETE | mod_scheduler | — | schedule_list |

### RUNNER
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/runner/run | POST | mod_runner | — | script_history |
| /api/runner/history | GET | mod_runner | — | script_history |

### DATABASE
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/db/stats | GET | mod_db | — | all 10 (COUNT) |
| /api/db/query | POST | mod_db | — | any (SELECT only) |

### FILES
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/files/parse | POST | parser_core, mod_patterns | PAT | patterns_log |
| /api/files/list | GET | os (direct) | — | — |
| /api/files/history | GET | mod_file | — | file_access_log |
| /api/files/locks | GET | mod_lock | — | lock_registry |

### SCRIPTS
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/scripts/list | GET | os.glob | — | — |
| /api/scripts/view | GET | os.open | — | — |
| /api/scripts/run | POST | mod_runner | — | script_history |

### MODULES
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/modules/inspect | GET | inspect module | — | module_calls |

### CACHE
| Endpoint | Method | Modules touched | Signal emitted | DB tables |
|----------|--------|-----------------|----------------|-----------|
| /api/cache | GET | mod_cache | — | cache_store |
| /api/cache/set | POST | mod_cache | — | cache_store |
| /api/cache/get/<key> | GET | mod_cache | — | cache_store |

---

## SCRIPTS — WHAT THEY TOUCH

| Script | Reads | Writes | Signals emitted | Scheduled? |
|--------|-------|--------|-----------------|------------|
| daily_seed.py | mod_db | numbers_log, (cache sweep) | DAT | YES (add manually) |
| drop_watcher.py | scripts/drop/ (files) | patterns_log, numbers_log | PAT | YES (60s interval) |
| system_check.py | all 10 modules | signal_log | SYS | manually |

---

## MODULE CALL GRAPH (who calls who)

```
mod_db          ← called by EVERYONE
mod_signal      ← called by: mod_file, mod_lock, mod_patterns, mod_runner,
                              mod_scheduler, mod_containers, core_server
mod_patterns    ← called by: core_server, mod_file
mod_numbers     ← called by: core_server, mod_patterns
mod_cache       ← called by: core_server, daily_seed.py
mod_lock        ← called by: core_server, mod_file
mod_file        ← called by: core_server
mod_scheduler   ← called by: core_server
mod_runner      ← called by: core_server, mod_scheduler
mod_containers  ← called by: core_server (inspect only, dynamic import)
```

---

## WHAT'S MISSING — GAP LIST

### 1. SIG_LUCK never fires
- `mod_numbers.calculate()` changes the luck mode but emits no signal
- Scripts cannot react to luck mode changes
- **Fix needed:** emit `SIG_LUCK` in `log_calculation()` when mode changes

### 2. Vector Studio has no server persistence
- Canvas state saves to `localStorage` only
- Wires defined in studio are not stored in fractal.db
- **Needed:** `/api/studio/canvas` (save/load JSON to DB or file)
- **Needed:** studio wires table in DB — link elemId → signal_id → event

### 3. No theme/element library storage
- UI element presets are hardcoded in vector_studio.html JS
- No way to save custom elements, share across sessions
- **Needed:** `/api/studio/library` — CRUD for named element packs
- **Needed:** `/api/studio/themes` — named color/style packs

### 4. No "what's watching this signal" query
- signal_routes table maps signal_id → script_path
- But there's no API to ask "what happens when PAT fires?"
- **Needed:** `/api/signals/watchers/<signal_id>` — list all routes for a signal

### 5. mod_containers not wired to nav
- Accessible via /api/modules/inspect?mod=mod_containers
- No dedicated /containers page
- **Needed:** `/containers` page (start/stop/restart processes from UI)

### 6. parser_core not exposed to UI directly
- Only accessible via /api/files/parse (POST with path)
- No drag-drop or paste-to-parse interface
- **Partially covered** by files.html

### 7. No live signal push
- Dashboard polls `/api/signals` every 2s
- Real architecture needs WebSocket or SSE for zero-latency signal feed
- **Needed:** `/api/signals/stream` (SSE endpoint)

### 8. No script editor
- Scripts can be viewed in /scripts but not edited in browser
- **Needed:** textarea edit + save in scripts page

### 9. Cache inspector incomplete
- mod_cache has list_all(), but no dedicated /cache page
- Only accessible via /api/cache
- **Needed:** `/cache` page (browse, set, delete entries by scope)

---

## VECTOR STUDIO ↔ FRACTAL WIRING STATUS

| Studio feature | Fractal endpoint needed | Status |
|----------------|------------------------|--------|
| Draw + stamp elements | — (client-only) | ✓ works |
| Wire signal to element | /api/signal/emit | ✓ export wires it |
| Wire script to element | /api/runner/run | ✓ export wires it |
| Save canvas to server | /api/studio/canvas | ✗ MISSING |
| Load canvas from server | /api/studio/canvas | ✗ MISSING |
| Theme packs | /api/studio/themes | ✗ MISSING |
| Element library | /api/studio/library | ✗ MISSING |
| Inspect live signals | /api/signals | ✗ not in studio |
| Current luck mode | /api/numbers/current | ✗ not in studio |
| Live signal feed in canvas | /api/signals/stream (SSE) | ✗ MISSING |

---

## PRIORITY BUILD ORDER

1. **emit SIG_LUCK** — 5 lines in mod_numbers.py, unblocks a whole class of reactive scripts
2. **script editor in /scripts** — textarea + save, no new endpoints needed
3. **/api/studio/canvas** — save/load studio state to server (JSON in cache or file)
4. **SSE stream** — `/api/signals/stream` for live push to dashboard + studio
5. **/containers page** — dedicated UI for mod_containers
6. **/cache page** — browse/edit cache scopes
7. **element library** — studio preset packs stored server-side
8. **theme packs** — CSS variable sets, one-click apply
