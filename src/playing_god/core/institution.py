from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class SchoolSnapshot:
    location: str
    day: int
    daily_training_capacity: int
    admissions_used: int
    remaining_capacity: int


@dataclass
class SchoolState:
    """One concrete institution with a daily training limit."""

    location: ClassVar[str] = "school"
    daily_training_capacity: ClassVar[int] = 1
    current_day: int | None = field(default=None, init=False)
    admissions_used: int = field(default=0, init=False)

    def start_day(self, day: int) -> None:
        if day != self.current_day:
            self.current_day = day
            self.admissions_used = 0

    def admit_training(self, day: int) -> int | None:
        """Return the admitted slot number, or None when full."""
        self.start_day(day)
        if self.admissions_used >= self.daily_training_capacity:
            return None

        self.admissions_used += 1
        return self.admissions_used

    def snapshot(self, day: int) -> SchoolSnapshot:
        admissions_used = (
            self.admissions_used
            if self.current_day == day
            else 0
        )
        return SchoolSnapshot(
            location=self.location,
            day=day,
            daily_training_capacity=self.daily_training_capacity,
            admissions_used=admissions_used,
            remaining_capacity=(
                self.daily_training_capacity - admissions_used
            ),
        )
