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
