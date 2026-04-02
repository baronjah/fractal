# fractal — therapy notes

## what it was supposed to be

A program that watches itself.
Every action leaves a mark. Every mark has a number. Every number has a mood.
You don't need to open logs to know what happened — the system tells you its feeling.

## what it actually is

Flask server with 10 modules and a numerology engine.
It logs everything. It catches patterns. It scores luck.
The demon catcher is real — it works.

The numbers page shows FLOW/BALANCE/BUILD/CHAOS/AMPLIFIED.
That part feels right.

## what's in reverse

It was supposed to grow FROM files — scan them, understand them, reshape itself.
Right now it only watches what you feed it through the web interface.
The parser exists but nothing drops files into it automatically.

The scheduler exists but has no default jobs.
An empty scheduler is a clock with no appointments.

## what to fix next

- drop folder watcher: when any .txt/.md/.py lands in `scripts/drop/`, auto-parse → demon catcher
- default scheduler job: scan `D:\Informational_space\` daily at 08:00, log what's new
- the containers page monitors processes but starts with nothing — add fractal itself as a container

## the real direction

This program should eventually know:
- what files exist and when they changed
- what scripts ran and what they touched
- what the luck of the day is before you ask

It's a personal OS layer, not a web app.
The web interface is just the window.

## branch plan

- `feature/excel-database` — make it understand .xlsx the way it understands .py
- `feature/launch-sequence` — 12 stations, manual + auto, dark, symbolic
- `feature/vector-studio` — HTML Photoshop with layers and states
