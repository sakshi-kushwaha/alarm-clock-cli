"""The watcher loop that actually fires alarms.

``next_due`` is a pure helper; ``Watcher`` wraps it in a loop. The clock, the sleep
function, and the ring function are all injected so the loop can be driven by a fake
clock in tests -- no real sleeping, no real sound.
"""

from __future__ import annotations

import time as _time
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from .models import Alarm
from .sound import ring as real_ring
from .storage import Store

__all__ = ["next_due", "Watcher"]

# How often the loop wakes up to re-read the store, so alarms added while it runs
# get picked up without restarting the watcher.
POLL_INTERVAL = 30.0


def next_due(alarms: List[Alarm], now: datetime) -> Optional[Tuple[Alarm, datetime]]:
    """The enabled alarm with the soonest upcoming occurrence, or ``None``."""
    best: Optional[Tuple[Alarm, datetime]] = None
    for alarm in alarms:
        if not alarm.enabled:
            continue
        when = alarm.next_occurrence(now)
        if when is None:
            continue
        if best is None or when < best[1]:
            best = (alarm, when)
    return best


class Watcher:
    def __init__(
        self,
        store: Store,
        now_fn: Callable[[], datetime] = datetime.now,
        sleep_fn: Callable[[float], None] = _time.sleep,
        ring_fn: Callable[..., None] = real_ring,
        poll_interval: float = POLL_INTERVAL,
        no_sound: bool = False,
    ):
        self.store = store
        self.now_fn = now_fn
        self.sleep_fn = sleep_fn
        self.ring_fn = ring_fn
        self.poll_interval = poll_interval
        self.no_sound = no_sound

    def run(self, once: bool = False) -> int:
        """Watch and fire alarms. With ``once=True``, return after the first ring
        (or immediately if there is nothing to wait for)."""
        last_fired = None  # (id, when) guard against re-firing the same occurrence
        while True:
            now = self.now_fn()
            due = next_due(self.store.load(), now)
            if due is None:
                if once:
                    return 0
                self.sleep_fn(self.poll_interval)
                continue

            alarm, when = due
            wait = (when - now).total_seconds()
            if wait > 0:
                self.sleep_fn(min(wait, self.poll_interval))
                continue

            if (alarm.id, when) == last_fired:
                # Already rang this exact moment; let the clock move past it.
                self.sleep_fn(min(self.poll_interval, 1.0))
                continue

            self._fire(alarm, when)
            last_fired = (alarm.id, when)
            if once:
                return 0

    def _fire(self, alarm: Alarm, when: datetime) -> None:
        tag = f" ({alarm.label})" if alarm.label else ""
        print(f"\n⏰ ALARM{tag} — {when.strftime('%Y-%m-%d %H:%M')}")
        self.ring_fn(no_sound=self.no_sound)
        self._retire(alarm)

    def _retire(self, alarm: Alarm) -> None:
        """After firing: recurring alarms re-arm automatically; one-shots are removed.

        Reloads the store first so concurrent edits (add/remove) are not clobbered.
        """
        if alarm.repeat in ("daily", "weekdays"):
            return
        alarms = self.store.load()
        remaining = [a for a in alarms if a.id != alarm.id]
        if len(remaining) != len(alarms):
            self.store.save(remaining)
