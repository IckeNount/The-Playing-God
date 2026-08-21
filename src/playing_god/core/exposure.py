from dataclasses import dataclass
from itertools import combinations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class Exposure:
    agent_a: str
    agent_b: str
    location: str

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Interaction:
    agent_a: str
    agent_b: str
    location: str


def interaction_probability(agent_a, agent_b) -> float:
    sociability_a = getattr(agent_a, "sociability", 0.5)
    sociability_b = getattr(agent_b, "sociability", 0.5)

    probability = 0.2 + 0.6 * (
        (sociability_a + sociability_b) / 2
    )

    return max(0.0, min(1.0, probability))


def resolve_interactions(
    exposures: list[Exposure],
    agents_by_id: dict,
    rng: random.Random,
) -> list[Interaction]:

    interactions: list[Interaction] = []

    for exposure in exposures:
        agent_a = agents_by_id[exposure.agent_a]
        agent_b = agents_by_id[exposure.agent_b]

        probability = interaction_probability(
            agent_a,
            agent_b,
        )

        if rng.random() < probability:
            interactions.append(
                Interaction(
                    agent_a=exposure.agent_a,
                    agent_b=exposure.agent_b,
                    location=exposure.location,
                )
            )

    return interactions

def detect_exposures(agents) -> list[Exposure]:
    by_location: dict[str, list] = {}

    for agent in agents:
        location = agent.current_location

        if location is None:
            continue

        by_location.setdefault(location, []).append(agent)

    exposures: list[Exposure] = []

    for location, occupants in by_location.items():
        for agent_a, agent_b in combinations(occupants, 2):
            exposures.append(
                Exposure(
                    agent_a=agent_a.id,
                    agent_b=agent_b.id,
                    location=location,
                )
            )

    return exposures