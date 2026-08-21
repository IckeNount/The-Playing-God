from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    day: int
    kind: str
    description: str
    significance: float
    target_id: str | None = None
    location: str | None = None
