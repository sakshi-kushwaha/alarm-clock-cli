"""Manage saved alarms: ``add``, ``list``, ``remove``, ``enable``, ``disable``.

These commands read and write the persisted alarm store; none of them block or
ring (that is the watcher's job, see :mod:`.watch`).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from ..models import REPEAT_CHOICES, Alarm
from ..storage import Store
from ..timeparse import TimeParseError, parse_duration, parse_time_of_day
from . import fail


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


def cmd_add(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    now = datetime.now()
    try:
        alarm = _build_alarm(args.when, store.next_id(alarms), args.label or "", args.repeat, now)
    except TimeParseError as exc:
        return fail(exc)
    alarms.append(alarm)
    store.save(alarms)
    when = alarm.next_occurrence(now).strftime("%Y-%m-%d %H:%M")
    tag = f" ({alarm.label})" if alarm.label else ""
    print(f"Added alarm #{alarm.id}{tag}: {alarm.describe_schedule()} — next at {when}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    if not alarms:
        print("No alarms set. Add one with: alarm add 07:30")
        return 0
    now = datetime.now()
    print(f"{'ID':>3}  {'NEXT':<16}  {'SCHEDULE':<18}  {'ON':<3}  LABEL")
    for a in sorted(alarms, key=lambda x: x.id):
        when = a.next_occurrence(now).strftime("%Y-%m-%d %H:%M")
        if a.is_overdue(now):
            when += " (passed)"
        on = "yes" if a.enabled else "no"
        print(f"{a.id:>3}  {when:<16}  {a.describe_schedule():<18}  {on:<3}  {a.label}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    store = Store()
    alarms = store.load()
    remaining = [a for a in alarms if a.id != args.id]
    if len(remaining) == len(alarms):
        return fail(f"no alarm with id {args.id}", code=1)
    store.save(remaining)
    print(f"Removed alarm #{args.id}")
    return 0


def _set_enabled(alarm_id: int, enabled: bool) -> int:
    store = Store()
    alarms = store.load()
    for a in alarms:
        if a.id == alarm_id:
            a.enabled = enabled
            store.save(alarms)
            print(f"{'Enabled' if enabled else 'Disabled'} alarm #{alarm_id}")
            return 0
    return fail(f"no alarm with id {alarm_id}", code=1)


def cmd_enable(args: argparse.Namespace) -> int:
    return _set_enabled(args.id, True)


def cmd_disable(args: argparse.Namespace) -> int:
    return _set_enabled(args.id, False)


def register(sub) -> None:
    p_add = sub.add_parser("add", help="Save an alarm to fire at a clock time or after a duration.")
    p_add.add_argument("when", help="Clock time (07:30, 7:30am, noon) or duration (10m, 1h30m).")
    p_add.add_argument("--label", "-l", help="Optional label for the alarm.")
    p_add.add_argument(
        "--repeat", "-r", choices=REPEAT_CHOICES, default="none",
        help="Recurrence for a clock-time alarm (default: none).",
    )
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List saved alarms.")
    p_list.set_defaults(func=cmd_list)

    p_remove = sub.add_parser("remove", help="Remove a saved alarm by id.")
    p_remove.add_argument("id", type=int, help="The alarm id (see 'alarm list').")
    p_remove.set_defaults(func=cmd_remove)

    p_enable = sub.add_parser("enable", help="Enable a saved alarm by id.")
    p_enable.add_argument("id", type=int, help="The alarm id (see 'alarm list').")
    p_enable.set_defaults(func=cmd_enable)

    p_disable = sub.add_parser("disable", help="Disable a saved alarm by id.")
    p_disable.add_argument("id", type=int, help="The alarm id (see 'alarm list').")
    p_disable.set_defaults(func=cmd_disable)
