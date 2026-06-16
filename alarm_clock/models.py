"""The :class:`Alarm` data model and its next-occurrence logic.

Two flavours of alarm:

* **clock-time** -- has ``hour``/``minute`` and recurs according to ``repeat``.
* **one-shot** -- has an absolute ``fire_at`` timestamp (e.g. from a duration) and
  fires exactly once.

All methods here are pure: they take ``now`` rather than reading the clock, so the
behaviour is deterministic and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

REPEAT_CHOICES = ("none", "daily", "weekdays")


@dataclass
class Alarm:
    id: int
    label: str = ""
    hour: Optional[int] = None
    minute: Optional[int] = None
    fire_at: Optional[str] = None  # ISO timestamp for one-shot alarms
    repeat: str = "none"
    enabled: bool = True
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.repeat not in REPEAT_CHOICES:
            raise ValueError(f"Unknown repeat {self.repeat!r}; choose from {REPEAT_CHOICES}.")
        is_clock = self.hour is not None and self.minute is not None
        if is_clock == bool(self.fire_at):
            raise ValueError("Alarm needs exactly one of clock time (hour/minute) or fire_at.")

    @property
    def is_clock(self) -> bool:
        return self.hour is not None and self.minute is not None

    def next_occurrence(self, now: datetime) -> Optional[datetime]:
        """Next time this alarm should fire at or after ``now``.

        Returns ``None`` for a one-shot whose moment has already passed.
        """
        if not self.is_clock:
            fire = datetime.fromisoformat(self.fire_at)  # type: ignore[arg-type]
            return fire if fire >= now else None

        candidate = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if candidate < now:
            candidate += timedelta(days=1)

        if self.repeat == "weekdays":
            while candidate.weekday() >= 5:  # 5=Sat, 6=Sun
                candidate += timedelta(days=1)
        # "none" and "daily" both use the simple today/tomorrow candidate; the
        # difference between them is whether the watcher re-arms after firing.
        return candidate

    def describe_schedule(self) -> str:
        """Human-readable summary of when/how this alarm fires."""
        if self.is_clock:
            base = f"{self.hour:02d}:{self.minute:02d}"
            if self.repeat == "daily":
                return f"{base} daily"
            if self.repeat == "weekdays":
                return f"{base} on weekdays"
            return base
        fire = datetime.fromisoformat(self.fire_at)  # type: ignore[arg-type]
        return fire.strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "hour": self.hour,
            "minute": self.minute,
            "fire_at": self.fire_at,
            "repeat": self.repeat,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        return cls(
            id=data["id"],
            label=data.get("label", ""),
            hour=data.get("hour"),
            minute=data.get("minute"),
            fire_at=data.get("fire_at"),
            repeat=data.get("repeat", "none"),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", ""),
        )
