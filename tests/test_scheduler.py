import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from alarm_clock.models import Alarm
from alarm_clock.scheduler import Watcher, next_due
from alarm_clock.storage import Store


class FakeClock:
    """A clock the test controls; sleeping advances it."""

    def __init__(self, start: datetime):
        self.now = start
        self.slept = []

    def now_fn(self) -> datetime:
        return self.now

    def sleep_fn(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += timedelta(seconds=seconds)


class NextDue(unittest.TestCase):
    def test_picks_soonest_enabled(self):
        now = datetime(2026, 1, 1, 8, 0)
        a = Alarm(id=1, hour=9, minute=0)
        b = Alarm(id=2, hour=8, minute=30)
        disabled = Alarm(id=3, hour=8, minute=10, enabled=False)
        alarm, when = next_due([a, b, disabled], now)
        self.assertEqual(alarm.id, 2)
        self.assertEqual(when, datetime(2026, 1, 1, 8, 30))

    def test_none_when_empty(self):
        self.assertIsNone(next_due([], datetime(2026, 1, 1, 8, 0)))


class WatcherFiring(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self._dir.name))

    def tearDown(self):
        self._dir.cleanup()

    def _watcher(self, clock, rings):
        return Watcher(
            self.store,
            now_fn=clock.now_fn,
            sleep_fn=clock.sleep_fn,
            ring_fn=lambda **_: rings.append(True),
            poll_interval=30.0,
        )

    def test_oneshot_fires_and_is_removed(self):
        fire_at = datetime(2026, 1, 1, 8, 1, 0)
        self.store.save([Alarm(id=1, fire_at=fire_at.isoformat(), label="x")])
        clock = FakeClock(datetime(2026, 1, 1, 8, 0, 0))
        rings = []
        rc = self._watcher(clock, rings).run(once=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(rings), 1)
        self.assertEqual(self.store.load(), [])  # one-shot retired

    def test_recurring_fires_and_remains(self):
        self.store.save([Alarm(id=1, hour=8, minute=1, repeat="daily")])
        clock = FakeClock(datetime(2026, 1, 1, 8, 0, 0))
        rings = []
        rc = self._watcher(clock, rings).run(once=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(rings), 1)
        self.assertEqual(len(self.store.load()), 1)  # daily alarm kept

    def test_snooze_reschedules_oneshot(self):
        fire_at = datetime(2026, 1, 1, 8, 1, 0)
        self.store.save([Alarm(id=1, fire_at=fire_at.isoformat(), label="x")])
        clock = FakeClock(datetime(2026, 1, 1, 8, 0, 0))
        rings = []
        watcher = Watcher(
            self.store,
            now_fn=clock.now_fn,
            sleep_fn=clock.sleep_fn,
            ring_fn=lambda **_: rings.append(True),
            poll_interval=30.0,
            snooze_minutes=9,
            prompt_fn=lambda _msg: True,  # always snooze
        )
        watcher.run(once=True)
        alarms = self.store.load()
        # Original retired, a single snooze one-shot 9 minutes after firing remains.
        self.assertEqual(len(alarms), 1)
        self.assertIn("snoozed", alarms[0].label)
        self.assertEqual(
            datetime.fromisoformat(alarms[0].fire_at), datetime(2026, 1, 1, 8, 10, 0)
        )

    def test_once_with_no_alarms_returns_immediately(self):
        clock = FakeClock(datetime(2026, 1, 1, 8, 0, 0))
        rings = []
        rc = self._watcher(clock, rings).run(once=True)
        self.assertEqual(rc, 0)
        self.assertEqual(rings, [])


if __name__ == "__main__":
    unittest.main()
