"""Parsing of clock times and durations from user input.

Pure functions only -- no clock reads, no IO -- so they are trivial to test.
"""

from __future__ import annotations

import re
from datetime import time

__all__ = ["parse_time_of_day", "parse_duration", "TimeParseError"]


class TimeParseError(ValueError):
    """Raised when a time or duration string cannot be understood."""


_CLOCK_RE = re.compile(
    r"""^\s*
    (?P<hour>\d{1,2})
    (?: : (?P<minute>\d{2}) )?
    \s*
    (?P<ampm>am|pm)?
    \s*$""",
    re.IGNORECASE | re.VERBOSE,
)

_DURATION_TOKEN_RE = re.compile(r"(\d+)\s*([smhd])", re.IGNORECASE)

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_time_of_day(text: str) -> time:
    """Parse a wall-clock time like ``07:30``, ``7:30am``, ``noon`` or ``midnight``.

    Returns a :class:`datetime.time`. Raises :class:`TimeParseError` on bad input.
    """
    raw = text.strip().lower()
    if raw in ("noon", "midday"):
        return time(12, 0)
    if raw == "midnight":
        return time(0, 0)

    match = _CLOCK_RE.match(raw)
    if not match:
        raise TimeParseError(
            f"Could not understand time {text!r}. Try formats like 07:30, 7:30am, or noon."
        )

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    ampm = match.group("ampm")

    if ampm:
        if not 1 <= hour <= 12:
            raise TimeParseError(f"Hour must be 1-12 with am/pm, got {hour}.")
        if ampm == "am":
            hour = 0 if hour == 12 else hour
        else:  # pm
            hour = 12 if hour == 12 else hour + 12
    else:
        if not 0 <= hour <= 23:
            raise TimeParseError(f"Hour must be 0-23, got {hour}.")

    if not 0 <= minute <= 59:
        raise TimeParseError(f"Minute must be 0-59, got {minute}.")

    return time(hour, minute)


def parse_duration(text: str) -> int:
    """Parse a duration like ``10m``, ``1h30m``, ``90s`` or ``45`` into seconds.

    A bare number is interpreted as minutes. Raises :class:`TimeParseError`.
    """
    raw = text.strip().lower()
    if not raw:
        raise TimeParseError("Empty duration.")

    if raw.isdigit():
        seconds = int(raw) * 60
    else:
        tokens = _DURATION_TOKEN_RE.findall(raw)
        # Reject leftover junk like "10x" or "1h foo".
        if not tokens or _DURATION_TOKEN_RE.sub("", raw).strip():
            raise TimeParseError(
                f"Could not understand duration {text!r}. Try formats like 10m, 1h30m, or 90s."
            )
        seconds = sum(int(value) * _UNIT_SECONDS[unit.lower()] for value, unit in tokens)

    if seconds <= 0:
        raise TimeParseError("Duration must be greater than zero.")
    return seconds
