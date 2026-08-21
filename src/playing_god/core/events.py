from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    day: int
    kind: str
    description: str
    significance: float