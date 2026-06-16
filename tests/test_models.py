import unittest
from datetime import datetime

from alarm_clock.models import Alarm


class NextOccurrence(unittest.TestCase):
    def test_clock_later_today(self):
        a = Alarm(id=1, hour=9, minute=0)
        now = datetime(2026, 1, 1, 8, 0)  # Thursday
        self.assertEqual(a.next_occurrence(now), datetime(2026, 1, 1, 9, 0))

    def test_clock_wraps_to_tomorrow(self):
        a = Alarm(id=1, hour=7, minute=0)
        now = datetime(2026, 1, 1, 8, 0)
        self.assertEqual(a.next_occurrence(now), datetime(2026, 1, 2, 7, 0))

    def test_weekdays_skips_weekend(self):
        a = Alarm(id=1, hour=7, minute=0, repeat="weekdays")
        # 2026-01-03 is a Saturday at 08:00 -> next weekday occurrence is Monday 5th.
        now = datetime(2026, 1, 3, 8, 0)
        self.assertEqual(a.next_occurrence(now), datetime(2026, 1, 5, 7, 0))

    def test_oneshot_future(self):
        a = Alarm(id=1, fire_at="2026-01-01T09:00:00")
        self.assertEqual(a.next_occurrence(datetime(2026, 1, 1, 8, 0)),
                         datetime(2026, 1, 1, 9, 0))

    def test_oneshot_past_still_returns_time_and_is_overdue(self):
        a = Alarm(id=1, fire_at="2026-01-01T07:00:00")
        now = datetime(2026, 1, 1, 8, 0)
        self.assertEqual(a.next_occurrence(now), datetime(2026, 1, 1, 7, 0))
        self.assertTrue(a.is_overdue(now))

    def test_future_oneshot_not_overdue(self):
        a = Alarm(id=1, fire_at="2026-01-01T09:00:00")
        self.assertFalse(a.is_overdue(datetime(2026, 1, 1, 8, 0)))


class Validation(unittest.TestCase):
    def test_needs_exactly_one_kind(self):
        with self.assertRaises(ValueError):
            Alarm(id=1)  # neither clock nor fire_at
        with self.assertRaises(ValueError):
            Alarm(id=1, hour=7, minute=0, fire_at="2026-01-01T07:00:00")  # both

    def test_bad_repeat(self):
        with self.assertRaises(ValueError):
            Alarm(id=1, hour=7, minute=0, repeat="hourly")


class RoundTrip(unittest.TestCase):
    def test_to_from_dict(self):
        a = Alarm(id=2, label="wake", hour=6, minute=30, repeat="daily")
        self.assertEqual(Alarm.from_dict(a.to_dict()), a)


if __name__ == "__main__":
    unittest.main()
