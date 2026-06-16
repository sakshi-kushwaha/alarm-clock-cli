import tempfile
import unittest
from pathlib import Path

from alarm_clock.models import Alarm
from alarm_clock.storage import Store


class StorageRoundTrip(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.home = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_empty_when_missing(self):
        self.assertEqual(Store(self.home).load(), [])

    def test_save_and_load(self):
        store = Store(self.home)
        alarms = [Alarm(id=1, hour=7, minute=0), Alarm(id=2, fire_at="2026-01-01T09:00:00")]
        store.save(alarms)
        loaded = Store(self.home).load()
        self.assertEqual(loaded, alarms)

    def test_corrupt_file_tolerated(self):
        store = Store(self.home)
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text("{ not json", encoding="utf-8")
        self.assertEqual(store.load(), [])

    def test_skips_malformed_entry(self):
        store = Store(self.home)
        store.home.mkdir(parents=True, exist_ok=True)
        store.path.write_text(
            '{"alarms": [{"id": 1, "hour": 7, "minute": 0}, {"id": 2}]}',
            encoding="utf-8",
        )
        loaded = store.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, 1)

    def test_next_id(self):
        store = Store(self.home)
        self.assertEqual(store.next_id([]), 1)
        self.assertEqual(store.next_id([Alarm(id=4, hour=7, minute=0)]), 5)


if __name__ == "__main__":
    unittest.main()
