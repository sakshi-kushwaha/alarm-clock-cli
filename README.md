# alarm-clock-cli

A small, dependency-free alarm clock you drive entirely from the terminal.
Pure Python standard library — no install required, no web UI, no database.

See [DESIGN.md](DESIGN.md) for the requirements, design, and the agile process
behind the build.

## Requirements

- Python 3.9+

## Running the commands

Every command can be run as **`alarm <args>`** _or_ **`python -m alarm_clock <args>`** —
the two forms are identical:

- `alarm` is the console command, available after `pip install -e .`.
- `python -m alarm_clock` needs no install and runs straight from a checkout.

```bash
pip install -e .         # optional: enables the `alarm` command
alarm --help             # or: python -m alarm_clock --help
```

The examples below use `alarm` for brevity.

## Usage

```bash
# Quick one-off: wait in the foreground, then ring
alarm set 10m --label tea
alarm set 7:30am --label "wake up"
alarm timer 90s                 # duration-only countdown

# Saved alarms (persisted to ~/.config/alarm-clock/alarms.json)
alarm add 07:30 --label gym --repeat weekdays
alarm add 22:00 --label meds --repeat daily
alarm add 25m --label laundry   # one-shot, fires once
alarm list
alarm disable 2
alarm enable 2
alarm remove 3

# Watch saved alarms and ring when due (foreground; Ctrl-C to stop)
alarm run
alarm run --once                # exit after the first alarm fires
alarm run --snooze 9            # offer a 9-minute snooze on each ring
```

### Example output

Adding alarms confirms the schedule and the next time each will fire:

```text
$ alarm add 07:30 --label gym --repeat weekdays
Added alarm #1 (gym): 07:30 on weekdays — next at 2026-06-17 07:30
$ alarm add 22:00 --label meds --repeat daily
Added alarm #2 (meds): 22:00 daily — next at 2026-06-17 22:00
$ alarm add 25m --label laundry
Added alarm #3 (laundry): 2026-06-17 00:38 — next at 2026-06-17 00:38
```

`list` prints a table; one-shots whose time has passed are flagged `(passed)`:

```text
$ alarm list
 ID  NEXT              SCHEDULE            ON   LABEL
  1  2026-06-17 07:30  07:30 on weekdays   yes  gym
  2  2026-06-17 22:00  22:00 daily         yes  meds
  3  2026-06-17 00:38  2026-06-17 00:38    yes  laundry
```

`set` and `timer` count down in the foreground, then ring:

```text
$ alarm timer 10m --label tea
Alarm set for 00:23:30 (tea) — 10m from now. Ctrl-C to cancel.

⏰ ALARM (tea) — 00:23:30
```

The watcher prints the same banner when a saved alarm fires:

```text
$ alarm run --snooze 9
Watching for alarms… Ctrl-C to stop.

⏰ ALARM (gym) — 2026-06-17 07:30
Snooze 9m? [y/N] y
Snoozed until 07:39.
```

Managing alarms gives a short confirmation (or an error and non-zero exit if the
id is unknown):

```text
$ alarm disable 2
Disabled alarm #2
$ alarm remove 3
Removed alarm #3
$ alarm remove 99
error: no alarm with id 99
```

### Time and duration formats

- **Clock time:** `07:30`, `7:30am`, `23:00`, `9`, `noon`, `midnight`.
- **Duration:** `90s`, `10m`, `1h30m`, `2h`, `1d`, or a bare number (minutes).

### Recurrence

- `--repeat daily` — every day at the given time.
- `--repeat weekdays` — Monday–Friday only.
- Recurrence applies to clock-time alarms; it is not valid with a duration.

### Sound

Best-effort and non-fatal. macOS uses `afplay`, Windows `winsound`, Linux
`paplay`/`aplay`; if none is available it falls back to the terminal bell. Pass
`--no-sound` to stay silent (handy for scripting or testing).

### Storage location

Alarms live in `~/.config/alarm-clock/alarms.json`. Override the directory with
the `ALARM_CLOCK_HOME` environment variable.

## Development

Run the test suite (standard-library `unittest`, no extra deps):

```bash
python -m unittest discover -s tests
```

## Built with

Requirements refinement, design, and implementation were done with the help of
**Claude** (Anthropic), following the agile, one-feature-per-commit process
described in [DESIGN.md](DESIGN.md).
