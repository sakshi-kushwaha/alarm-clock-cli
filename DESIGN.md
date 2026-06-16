# Alarm Clock CLI — Design

A small, dependency-free alarm clock you drive entirely from the terminal.
Built with the Python standard library only. No web UI, no database.

This document is the thinking behind the build: the requirements we settled on,
the design, and the agile process we follow to get there.

## Goals & scope

"Solid core" alarm clock:

- Add alarms by **clock time** (`07:30`, `7:30am`) or **duration** (`10m`, `1h30m`, `90s`).
- Optional `--label` and recurrence (`--repeat daily` / `--repeat weekdays`).
- `list`, `remove`, `enable`/`disable` alarms by id.
- `run` — a foreground watcher that sleeps until the next alarm is due, rings it,
  then advances recurring alarms or disables one-shots. Snooze supported.
- `timer <duration>` — a quick blocking countdown that rings when it elapses.

Non-goals: web/GUI, a real database, background daemon/service management,
calendar-grade scheduling.

## Constraints & principles

- **Standard library only**, Python 3.9+ — zero install, runs anywhere Python does.
- **Pure core, impure edges.** Time math, parsing, and persistence are pure and
  unit-tested. Sleeping and sound are isolated and injected so tests stay fast and
  deterministic.
- **Best-effort sound.** Ringing must never crash the app; it degrades to the
  terminal bell (`\a`) if no audio backend is available.
- **Human-friendly errors** for bad input instead of stack traces.

## Architecture

Single package `alarm_clock/`:

| Module | Responsibility |
|---|---|
| `timeparse.py` | Parse clock times and durations. Pure, heavily tested. |
| `models.py` | `Alarm` dataclass + `next_occurrence(now)`, JSON (de)serialization. |
| `storage.py` | Atomic JSON load/save; tolerant of missing/corrupt files. |
| `sound.py` | Cross-platform ring (`afplay` / `winsound` / `paplay`/`aplay` / bell). |
| `scheduler.py` | Pure `next_due(alarms, now)` + a `Watcher` loop (clock/sleep injected). |
| `cli.py` | `argparse` subcommands; `main(argv)` returns an exit code. |
| `__main__.py` | Enables `python -m alarm_clock`. |

**Persistence:** a JSON file at `alarms.json` in the project root, overridable via
the `ALARM_CLOCK_HOME` env var (handy for tests and throwaway runs).

**Sound backends**, chosen by platform, all wrapped so failure is non-fatal:
macOS → `afplay`; Windows → `winsound`; Linux → `paplay`/`aplay`; fallback → bell.

## Usage (target)

```
alarm add 07:30 --label "wake up" --repeat weekdays
alarm add 10m --label tea
alarm list
alarm remove 3
alarm disable 2
alarm run            # foreground watcher; rings due alarms
alarm timer 5m       # quick one-off countdown
```

Also runnable as `python -m alarm_clock ...` without installing.

## Testing strategy

Stdlib `unittest` (also runnable under `pytest`):

- **timeparse** — valid/invalid times and durations, edge cases (`12am`, `noon`, `0m`).
- **models** — `next_occurrence` for one-shot vs daily vs weekdays (day wrap, weekend
  skip); `to_dict`/`from_dict` round-trip.
- **scheduler** — `next_due` picks the soonest enabled alarm; `Watcher` rings then
  advances/disables using a fake clock + sleep and a recording sound stub.
- **storage** — round-trip + corrupt-file tolerance against a temp `ALARM_CLOCK_HOME`.
- **cli** — `add` → `list` → `remove`; `timer 1s --once --no-sound` exits 0 quickly.

## Process — agile, one feature per commit

We ship a minimal working alarm first, then grow it one feature at a time. Every
commit keeps the suite green.

1. **Design doc** (this file) + `.gitignore`.
2. **Basic alarm** — set by time/duration, wait in the foreground, ring. The first
   working app.
3. **Persistence + `add`/`list`/`remove`** — JSON storage and the `Alarm` model.
4. **`run` watcher** — fire the soonest due alarm; `--once` for scripting/tests.
5. **Recurrence** — `--repeat daily|weekdays` with occurrence rollover.
6. **Snooze + enable/disable + polish** — snooze on ring, toggles, README, flags,
   friendlier errors.

Each step: implement → run tests → smoke-test → commit with a focused message.
Later steps may refactor earlier code (e.g. extracting `models.py`); that's expected.
