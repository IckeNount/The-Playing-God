from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from playing_god.core.events import Event


NAMES = [
    "Mira",
    "Noah",
    "Lina",
    "Ren",
    "Sora",
    "Kai",
    "Ari",
    "Niko",
    "Iris",
    "Theo",
]

TRAITS = (
    "discipline",
    "sociability",
    "ambition",
    "risk_tolerance",
    "empathy",
)

SINS = (
    "pride",
    "greed",
    "lust",
    "envy",
    "gluttony",
    "wrath",
    "sloth",
)


def clamp(
    x: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:
    return max(low, min(high, x))


@dataclass
class Agent:
    id: str
    name: str
    age: int

    traits: dict[str, float]
    sins: dict[str, float]

    money: float
    employed: bool
    salary: float
    job_level: int

    skill: float
    energy: float
    stress: float
    reputation: float

    goal: str = ""

    relationships: dict[str, float] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    actions: Counter = field(default_factory=Counter)

    current_location: str = "home"
    destination: str | None = None

    def normalize(self) -> None:
        self.skill = clamp(self.skill)
        self.energy = clamp(self.energy)
        self.stress = clamp(self.stress)
        self.reputation = clamp(
            self.reputation,
            -1.0,
            1.0,
        )

        for other in self.relationships:
            self.relationships[other] = clamp(
                self.relationships[other],
                -1.0,
                1.0,
            )