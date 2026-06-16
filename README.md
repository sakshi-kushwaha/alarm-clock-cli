# alarm-clock-cli

A small, dependency-free alarm clock you drive entirely from the terminal.
Pure Python standard library — no install required, no web UI, no database.

See [DESIGN.md](DESIGN.md) for the requirements, design, and the agile process
behind the build.

## Requirements

- Python 3.9+

## Install (optional)

It runs straight from a checkout:

```bash
python -m alarm_clock --help
```

Or install the `alarm` console command:

```bash
pip install -e .
alarm --help
```

## Usage

> **Note:** `alarm` is the console command available after `pip install -e .`.
> Without installing, replace `alarm` with `python -m alarm_clock` in any command
> below — both forms are shown.

```bash
# Quick one-off: wait in the foreground, then ring
alarm set 10m --label tea
python -m alarm_clock set 10m --label tea

alarm set 7:30am --label "wake up"
python -m alarm_clock set 7:30am --label "wake up"

alarm timer 90s                 # duration-only countdown
python -m alarm_clock timer 90s

# Saved alarms (persisted to ~/.config/alarm-clock/alarms.json)
alarm add 07:30 --label gym --repeat weekdays
python -m alarm_clock add 07:30 --label gym --repeat weekdays

alarm add 22:00 --label meds --repeat daily
python -m alarm_clock add 22:00 --label meds --repeat daily

alarm add 25m --label laundry   # one-shot, fires once
python -m alarm_clock add 25m --label laundry

alarm list
python -m alarm_clock list

alarm disable 2
python -m alarm_clock disable 2

alarm enable 2
python -m alarm_clock enable 2

alarm remove 3
python -m alarm_clock remove 3

# Watch saved alarms and ring when due (foreground; Ctrl-C to stop)
alarm run
python -m alarm_clock run

alarm run --once                # exit after the first alarm fires
python -m alarm_clock run --once

alarm run --snooze 9            # offer a 9-minute snooze on each ring
python -m alarm_clock run --snooze 9
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
