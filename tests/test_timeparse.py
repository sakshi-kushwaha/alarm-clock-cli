import unittest
from datetime import time

from alarm_clock.timeparse import TimeParseError, parse_duration, parse_time_of_day


class ParseTimeOfDay(unittest.TestCase):
    def test_24h(self):
        self.assertEqual(parse_time_of_day("07:30"), time(7, 30))
        self.assertEqual(parse_time_of_day("23:00"), time(23, 0))
        self.assertEqual(parse_time_of_day("9"), time(9, 0))

    def test_am_pm(self):
        self.assertEqual(parse_time_of_day("7:30am"), time(7, 30))
        self.assertEqual(parse_time_of_day("7:30 PM"), time(19, 30))
        self.assertEqual(parse_time_of_day("12am"), time(0, 0))
        self.assertEqual(parse_time_of_day("12pm"), time(12, 0))

    def test_words(self):
        self.assertEqual(parse_time_of_day("noon"), time(12, 0))
        self.assertEqual(parse_time_of_day("midnight"), time(0, 0))

    def test_invalid(self):
        for bad in ["25:00", "07:60", "13pm", "abc", "", "7:5"]:
            with self.assertRaises(TimeParseError):
                parse_time_of_day(bad)


class ParseDuration(unittest.TestCase):
    def test_units(self):
        self.assertEqual(parse_duration("90s"), 90)
        self.assertEqual(parse_duration("10m"), 600)
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_bare_number_is_minutes(self):
        self.assertEqual(parse_duration("45"), 45 * 60)

    def test_invalid(self):
        for bad in ["0m", "0", "10x", "1h foo", "", "abc"]:
            with self.assertRaises(TimeParseError):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
