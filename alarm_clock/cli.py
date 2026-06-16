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
from .sound import ring
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

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
