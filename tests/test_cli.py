import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from alarm_clock import cli


class ResolveWait(unittest.TestCase):
    def test_duration_spec(self):
        now = datetime(2026, 1, 1, 8, 0, 0)
        seconds, fire_at = cli._resolve_wait("10m", now)
        self.assertEqual(seconds, 600)
        self.assertEqual(fire_at, datetime(2026, 1, 1, 8, 10, 0))

    def test_clock_time_later_today(self):
        now = datetime(2026, 1, 1, 8, 0, 0)
        seconds, fire_at = cli._resolve_wait("09:00", now)
        self.assertEqual(seconds, 3600)
        self.assertEqual(fire_at.hour, 9)

    def test_clock_time_wraps_to_tomorrow(self):
        now = datetime(2026, 1, 1, 8, 0, 0)
        _, fire_at = cli._resolve_wait("07:00", now)
        self.assertEqual(fire_at.day, 2)


class TimerCommand(unittest.TestCase):
    def test_timer_rings_without_real_sleep(self):
        with mock.patch.object(cli._time, "sleep") as sleep, \
             mock.patch.object(cli, "ring") as ring:
            rc = cli.main(["timer", "5m", "--no-sound", "--label", "tea"])
        self.assertEqual(rc, 0)
        sleep.assert_called_once_with(300.0)
        ring.assert_called_once()

    def test_bad_duration_exits_2(self):
        rc = cli.main(["timer", "nonsense"])
        self.assertEqual(rc, 2)


class AddListRemove(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._prev = os.environ.get("ALARM_CLOCK_HOME")
        os.environ["ALARM_CLOCK_HOME"] = self._dir.name

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("ALARM_CLOCK_HOME", None)
        else:
            os.environ["ALARM_CLOCK_HOME"] = self._prev
        self._dir.cleanup()

    def test_add_then_list_then_remove(self):
        self.assertEqual(cli.main(["add", "07:30", "--label", "wake"]), 0)
        self.assertEqual(cli.main(["add", "10m"]), 0)
        self.assertEqual(cli.main(["list"]), 0)
        # Removing a real id succeeds; an unknown id is an error.
        self.assertEqual(cli.main(["remove", "1"]), 0)
        self.assertEqual(cli.main(["remove", "99"]), 1)

    def test_add_bad_spec_exits_2(self):
        self.assertEqual(cli.main(["add", "nonsense"]), 2)


if __name__ == "__main__":
    unittest.main()
