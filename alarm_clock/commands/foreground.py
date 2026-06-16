"""``set`` and ``timer``: foreground alarms that block, then ring.

Neither command touches persistence -- they wait in the terminal until the moment
arrives, ring, and exit. ``set`` accepts a clock time or a duration; ``timer`` is
duration-only.
"""

from __future__ import annotations

import argparse
import time as _time
from datetime import datetime, timedelta

from ..sound import ring
from ..timeparse import TimeParseError, parse_duration, parse_time_of_day
from . import fail


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


def _humanize(seconds: float) -> str:
    """Render a number of seconds as a compact "1h30m" / "45s" string."""
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


def cmd_set(args: argparse.Namespace) -> int:
    try:
        seconds, fire_at = _resolve_wait(args.when, datetime.now())
    except TimeParseError as exc:
        return fail(exc)
    return _countdown(seconds, args.label or "", fire_at, args.no_sound)


def cmd_timer(args: argparse.Namespace) -> int:
    try:
        seconds = parse_duration(args.duration)
    except TimeParseError as exc:
        return fail(exc)
    fire_at = datetime.now() + timedelta(seconds=seconds)
    return _countdown(float(seconds), args.label or "", fire_at, args.no_sound)


def register(sub) -> None:
    p_set = sub.add_parser("set", help="Wait for a time or duration, then ring.")
    p_set.add_argument("when", help="Clock time (07:30, 7:30am, noon) or duration (10m, 1h30m).")
    p_set.add_argument("--label", "-l", help="Optional label for the alarm.")
    p_set.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_set.set_defaults(func=cmd_set)

    p_timer = sub.add_parser("timer", help="Quick countdown for a duration, then ring.")
    p_timer.add_argument("duration", help="Duration like 10m, 1h30m, 90s, or a bare number of minutes.")
    p_timer.add_argument("--label", "-l", help="Optional label for the timer.")
    p_timer.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_timer.set_defaults(func=cmd_timer)
