from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from playing_god.core.adaptive import ActionValue
from playing_god.core.development import DevelopmentState
from playing_god.core.events import Event
from playing_god.core.family import FamilyState
from playing_god.core.faith import Attribution
from playing_god.core.perception import Belief, Observation
from playing_god.core.prehistory import FounderEvent
from playing_god.core.prayer import Prayer


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

    social_energy: float | None = field(
        default=None,
        kw_only=True,
    )
    faith: float = field(
        default=0.5,
        kw_only=True,
    )

    goal: str = ""

    relationships: dict[str, float] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    actions: Counter = field(default_factory=Counter)

    observations: list[Observation] = field(default_factory=list)
    beliefs: dict[str, Belief] = field(default_factory=dict)
    prayers: list[Prayer] = field(default_factory=list)
    attributions: list[Attribution] = field(default_factory=list)
    adaptive_values: dict[
        str,
        dict[str, ActionValue],
    ] = field(default_factory=dict)
    founder_prehistory: list[FounderEvent] = field(
        default_factory=list,
    )
    family: FamilyState = field(default_factory=FamilyState)
    development: DevelopmentState = field(
        default_factory=DevelopmentState,
    )

    current_location: str = "home"
    destination: str | None = None

    def __post_init__(self) -> None:
        if self.social_energy is None:
            self.social_energy = self.energy

    def normalize(self) -> None:
        self.skill = clamp(self.skill)
        self.energy = clamp(self.energy)
        self.social_energy = clamp(self.social_energy)
        self.faith = clamp(self.faith)
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

    @property
    def physical_energy(self) -> float:
        """Explicit Phase 4 name for the legacy energy state."""
        return self.energy

    @physical_energy.setter
    def physical_energy(self, value: float) -> None:
        self.energy = value

    @property
    def skepticism(self) -> float:
        return 1 - self.faith
