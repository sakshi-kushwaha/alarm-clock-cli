"""Command-line interface for the alarm clock.

Walking skeleton: ``set`` waits for a clock time or duration in the foreground and
rings; ``timer`` is a quick duration-only countdown. Persistence and the background
``run`` watcher arrive in later commits.
"""

from __future__ import annotations

import argparse
import sys
import time as _time
from datetime import datetime, timedelta

from . import __version__
from .models import REPEAT_CHOICES, Alarm
from .scheduler import Watcher
from .sound import ring
from .storage import Store
from .timeparse import TimeParseError, parse_duration, parse_time_of_day


def _seconds_until_time(target, now: datetime) -> float:
    """Seconds from ``now`` until the next occurrence of wall-clock ``target``."""
    when = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    if when <= now:
        when += timedelta(days=1)
    return (when - now).total_seconds()


def _resolve_wait(spec: str, now: datetime) -> tuple[float, datetime]:
    """Turn a time-or-duration spec into (seconds_to_wait, fire_at datetime).

    Tries clock-time first, then duration; raises TimeParseError if neither fits.
    """
    try:
        tod = parse_time_of_day(spec)
    except TimeParseError:
        seconds = parse_duration(spec)  # may raise TimeParseError
        return float(seconds), now + timedelta(seconds=seconds)
    seconds = _seconds_until_time(tod, now)
    return seconds, now + timedelta(seconds=seconds)


def _countdown(seconds: float, label: str, fire_at: datetime, no_sound: bool) -> int:
    """Sleep until fire_at, then ring. Returns a process exit code."""
    pretty = fire_at.strftime("%H:%M:%S")
    tag = f" ({label})" if label else ""
    print(f"Alarm set for {pretty}{tag} — {_humanize(seconds)} from now. Ctrl-C to cancel.")
    try:
        _time.sleep(seconds)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    print(f"\n⏰ ALARM{tag} — {fire_at.strftime('%H:%M:%S')}")
    ring(no_sound=no_sound)
    return 0


def _humanize(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if sec and not hours:
        parts.append(f"{sec}s")
    return "".join(parts) or "0s"


def _cmd_set(args: argparse.Namespace) -> int:
    try:
        seconds, fire_at = _resolve_wait(args.when, datetime.now())
    except TimeParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return _countdown(seconds, args.label or "", fire_at, args.no_sound)


def _cmd_timer(args: argparse.Namespace) -> int:
    try:
        seconds = parse_duration(args.duration)
    except TimeParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    fire_at = datetime.now() + timedelta(seconds=seconds)
    return _countdown(float(seconds), args.label or "", fire_at, args.no_sound)


def _build_alarm(spec: str, alarm_id: int, label: str, repeat: str, now: datetime) -> Alarm:
    """Construct an Alarm from a time-or-duration spec (raises TimeParseError).

    ``repeat`` (daily/weekdays) only applies to clock-time alarms; recurrence on a
    duration is meaningless, so it is rejected.
    """
    try:
        tod = parse_time_of_day(spec)
    except TimeParseError:
        seconds = parse_duration(spec)  # may raise TimeParseError
        if repeat != "none":
            raise TimeParseError("--repeat only works with a clock time, not a duration.")
        fire_at = (now + timedelta(seconds=seconds)).replace(microsecond=0)
        return Alarm(
            id=alarm_id,
            label=label,
            fire_at=fire_at.isoformat(),
            created_at=now.isoformat(timespec="seconds"),
        )
    return Alarm(
        id=alarm_id,
        label=label,
        hour=tod.hour,
        minute=tod.minute,
        repeat=repeat,
        created_at=now.isoformat(timespec="seconds"),
    )


def _cmd_add(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    now = datetime.now()
    try:
        alarm = _build_alarm(args.when, store.next_id(alarms), args.label or "", args.repeat, now)
    except TimeParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    alarms.append(alarm)
    store.save(alarms)
    when = alarm.next_occurrence(now).strftime("%Y-%m-%d %H:%M")
    tag = f" ({alarm.label})" if alarm.label else ""
    print(f"Added alarm #{alarm.id}{tag}: {alarm.describe_schedule()} — next at {when}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    if not alarms:
        print("No alarms set. Add one with: alarm add 07:30")
        return 0
    now = datetime.now()
    print(f"{'ID':>3}  {'NEXT':<16}  {'SCHEDULE':<18}  {'ON':<3}  LABEL")
    for a in sorted(alarms, key=lambda x: x.id):
        nxt = a.next_occurrence(now)
        when = nxt.strftime("%Y-%m-%d %H:%M")
        if a.is_overdue(now):
            when += " (passed)"
        on = "yes" if a.enabled else "no"
        print(f"{a.id:>3}  {when:<16}  {a.describe_schedule():<18}  {on:<3}  {a.label}")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    remaining = [a for a in alarms if a.id != args.id]
    if len(remaining) == len(alarms):
        print(f"error: no alarm with id {args.id}", file=sys.stderr)
        return 1
    store.save(remaining)
    print(f"Removed alarm #{args.id}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    store = Store()
    alarms = [a for a in store.load() if a.enabled]
    if not alarms and args.once:
        print("No enabled alarms to wait for.")
        return 0
    if not args.once:
        print("Watching for alarms… Ctrl-C to stop.")
    watcher = Watcher(store, no_sound=args.no_sound)
    try:
        return watcher.run(once=args.once)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A small, dependency-free alarm clock for the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Wait for a time or duration, then ring.")
    p_set.add_argument("when", help="Clock time (07:30, 7:30am, noon) or duration (10m, 1h30m).")
    p_set.add_argument("--label", "-l", help="Optional label for the alarm.")
    p_set.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_set.set_defaults(func=_cmd_set)

    p_timer = sub.add_parser("timer", help="Quick countdown for a duration, then ring.")
    p_timer.add_argument("duration", help="Duration like 10m, 1h30m, 90s, or a bare number of minutes.")
    p_timer.add_argument("--label", "-l", help="Optional label for the timer.")
    p_timer.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_timer.set_defaults(func=_cmd_timer)

    p_add = sub.add_parser("add", help="Save an alarm to fire at a clock time or after a duration.")
    p_add.add_argument("when", help="Clock time (07:30, 7:30am, noon) or duration (10m, 1h30m).")
    p_add.add_argument("--label", "-l", help="Optional label for the alarm.")
    p_add.add_argument(
        "--repeat", "-r", choices=REPEAT_CHOICES, default="none",
        help="Recurrence for a clock-time alarm (default: none).",
    )
    p_add.set_defaults(func=_cmd_add)

    p_list = sub.add_parser("list", help="List saved alarms.")
    p_list.set_defaults(func=_cmd_list)

    p_remove = sub.add_parser("remove", help="Remove a saved alarm by id.")
    p_remove.add_argument("id", type=int, help="The alarm id (see 'alarm list').")
    p_remove.set_defaults(func=_cmd_remove)

    p_run = sub.add_parser("run", help="Watch saved alarms in the foreground and ring when due.")
    p_run.add_argument("--once", action="store_true", help="Exit after the first alarm fires.")
    p_run.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_run.set_defaults(func=_cmd_run)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
