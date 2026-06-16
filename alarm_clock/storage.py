"""JSON persistence for alarms.

A single file holds the list of alarms. Writes are atomic (temp file + ``os.replace``)
so an interrupted save never corrupts the store, and a missing or unreadable file is
treated as "no alarms yet" rather than an error.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import List

from .models import Alarm

__all__ = ["Store", "default_home"]


def default_home() -> Path:
    """Directory where alarms are stored. Override with ``ALARM_CLOCK_HOME``."""
    override = os.environ.get("ALARM_CLOCK_HOME")
    if override:
        return Path(override)
    return Path.home() / ".config" / "alarm-clock"


class Store:
    """Load/save a list of :class:`Alarm` to ``<home>/alarms.json``."""

    def __init__(self, home: Path = None):
        self.home = Path(home) if home is not None else default_home()
        self.path = self.home / "alarms.json"

    def load(self) -> List[Alarm]:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (FileNotFoundError, ValueError):
            return []
        alarms = []
        for item in data.get("alarms", []):
            try:
                alarms.append(Alarm.from_dict(item))
            except (KeyError, ValueError):
                continue  # skip malformed entries rather than failing the whole load
        return alarms

    def save(self, alarms: List[Alarm]) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "alarms": [a.to_dict() for a in alarms]}
        fd, tmp = tempfile.mkstemp(dir=self.home, prefix=".alarms-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def next_id(self, alarms: List[Alarm]) -> int:
        return max((a.id for a in alarms), default=0) + 1
