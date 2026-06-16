"""The ``run`` command: a foreground watcher over saved alarms.

Loads the persisted alarms and hands them to a :class:`~alarm_clock.scheduler.Watcher`
that sleeps until each is due and rings it.
"""

from __future__ import annotations

import argparse

from ..scheduler import Watcher
from ..storage import Store


def cmd_run(args: argparse.Namespace) -> int:
    store = Store()
    enabled = [a for a in store.load() if a.enabled]
    if not enabled and args.once:
        print("No enabled alarms to wait for.")
        return 0
    if not args.once:
        print("Watching for alarms… Ctrl-C to stop.")
    watcher = Watcher(store, no_sound=args.no_sound, snooze_minutes=args.snooze)
    try:
        return watcher.run(once=args.once)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


def register(sub) -> None:
    p_run = sub.add_parser("run", help="Watch saved alarms in the foreground and ring when due.")
    p_run.add_argument("--once", action="store_true", help="Exit after the first alarm fires.")
    p_run.add_argument("--no-sound", action="store_true", help="Do not play a sound when ringing.")
    p_run.add_argument(
        "--snooze", type=int, default=0, metavar="MIN",
        help="On ring, offer to snooze this many minutes (interactive; default: off).",
    )
    p_run.set_defaults(func=cmd_run)
