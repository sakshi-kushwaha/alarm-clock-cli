# Demo — every command

A complete tour of the alarm clock CLI with real output. Every command works as
`alarm <args>` (after `pip install -e .`) **or** `python -m alarm_clock <args>`.

Examples below use `alarm`.

---

## Help & version

```text
$ alarm --help
usage: alarm [-h] [--version]
             {set,timer,add,list,remove,enable,disable,run} ...

A small, dependency-free alarm clock for the terminal.

positional arguments:
  {set,timer,add,list,remove,enable,disable,run}
    set                 Wait for a time or duration, then ring.
    timer               Quick countdown for a duration, then ring.
    add                 Save an alarm to fire at a clock time or after a duration.
    list                List saved alarms.
    remove              Remove a saved alarm by id.
    enable              Enable a saved alarm by id.
    disable             Disable a saved alarm by id.
    run                 Watch saved alarms in the foreground and ring when due.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

$ alarm --version
alarm 0.1.0
```

---

## Foreground alarms (block, then ring)

These wait in the terminal and ring — nothing is persisted.

```text
# Duration-only countdown
$ alarm timer 2s
Alarm set for 00:35:33 — 2s from now. Ctrl-C to cancel.

⏰ ALARM — 00:35:33

# Same, but silent (handy for scripts/tests)
$ alarm timer 90s --no-sound

# 'set' accepts a clock time or a duration, plus a label
$ alarm set 10m --label tea
Alarm set for 00:45:33 (tea) — 10m from now. Ctrl-C to cancel.

⏰ ALARM (tea) — 00:45:33

$ alarm set 7:30am --label "wake up"
$ alarm set noon
```

---

## Saved alarms

Persisted to `alarms.json` in the project root (override the directory with the
`ALARM_CLOCK_HOME` environment variable).

### add

```text
# Clock time, recurring on weekdays
$ alarm add 07:30 --label gym --repeat weekdays
Added alarm #1 (gym): 07:30 on weekdays — next at 2026-06-17 07:30

# Clock time, recurring daily
$ alarm add 22:00 --label meds --repeat daily
Added alarm #2 (meds): 22:00 daily — next at 2026-06-17 22:00

# 12-hour clock time
$ alarm add 7:30am --label "wake up"
Added alarm #3 (wake up): 07:30 — next at 2026-06-17 07:30

# Duration -> one-shot, fires once
$ alarm add 25m --label laundry
Added alarm #4 (laundry): 2026-06-17 01:00 — next at 2026-06-17 01:00

# Word times work too (noon / midnight / midday)
$ alarm add noon --label lunch
Added alarm #5 (lunch): 12:00 — next at 2026-06-17 12:00
```

### list

```text
$ alarm list
 ID  NEXT              SCHEDULE            ON   LABEL
  1  2026-06-17 07:30  07:30 on weekdays   yes  gym
  2  2026-06-17 22:00  22:00 daily         yes  meds
  3  2026-06-17 07:30  07:30               yes  wake up
  4  2026-06-17 01:00  2026-06-17 01:00    yes  laundry
  5  2026-06-17 12:00  12:00               yes  lunch
```

(A one-shot whose time has already passed is flagged `(passed)` in the NEXT column.)

### disable / enable

```text
$ alarm disable 2
Disabled alarm #2
$ alarm enable 2
Enabled alarm #2
```

### remove

```text
$ alarm remove 5
Removed alarm #5
```

---

## Watch and ring (the `run` watcher)

Loads saved alarms, sleeps until the soonest is due, rings it, then re-arms
recurring alarms and retires one-shots.

```text
# Run until stopped
$ alarm run
Watching for alarms… Ctrl-C to stop.

⏰ ALARM (gym) — 2026-06-17 07:30

# Exit after the first alarm fires (great for scripting/tests)
$ alarm run --once

# Offer an interactive snooze on each ring
$ alarm run --snooze 9
Watching for alarms… Ctrl-C to stop.

⏰ ALARM (gym) — 2026-06-17 07:30
Snooze 9m? [y/N] y
Snoozed until 07:39.

# Silent watcher
$ alarm run --no-sound
```

---

## Error handling

Bad input fails cleanly with a message and a non-zero exit code — no stack traces.

```text
# Unknown id -> exit code 1
$ alarm remove 99
error: no alarm with id 99

# Recurrence on a duration is meaningless -> exit code 2
$ alarm add 10m --repeat daily
error: --repeat only works with a clock time, not a duration.

# Unparseable time/duration -> exit code 2
$ alarm timer nonsense
error: Could not understand duration 'nonsense'. Try formats like 10m, 1h30m, or 90s.
```

---

## Input formats

- **Clock time:** `07:30`, `7:30am`, `7:30 PM`, `23:00`, `9`, `noon`, `midnight`.
- **Duration:** `90s`, `10m`, `1h30m`, `2h`, `1d`, or a bare number (minutes).
- **Recurrence (`--repeat`):** `none` (default), `daily`, `weekdays` — clock-time alarms only.
- **Common flags:** `--label/-l`, `--no-sound`; `run` also has `--once` and `--snooze MIN`.
