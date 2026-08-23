from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


DESIRE_TYPES = {
    "find_job": "employment",
    "build_savings": "security",
    "improve_skill": "growth",
    "build_relationships": "belonging",
    "advance_career": "advancement",
}


@dataclass(frozen=True)
class Prayer:
    agent_id: str
    desire_type: str
    intensity: float
    related_goal: str
    timestamp: int


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def goal_blockage(agent: Agent) -> float:
    """Measure how far the agent is from its current goal."""
    if agent.goal == "find_job":
        return 0.0 if agent.employed else 1.0

    if agent.goal == "build_savings":
        return _clamp((260 - agent.money) / 260)

    if agent.goal == "improve_skill":
        return _clamp((0.75 - agent.skill) / 0.75)

    if agent.goal == "build_relationships":
        positive_ties = [
            max(0.0, value)
            for value in agent.relationships.values()
        ]
        average = (
            sum(positive_ties) / len(positive_ties)
            if positive_ties
            else 0.0
        )
        return _clamp((0.55 - average) / 0.55)

    if agent.goal == "advance_career":
        return _clamp((5 - agent.job_level) / 5)

    return 0.0


def prayer_habit(agent: Agent) -> float:
    return _clamp(agent.actions["pray"] / 20)


def prayer_need(agent: Agent) -> float:
    """Deterministic utility input derived from existing state."""
    tired = 1 - agent.energy
    return (
        0.95 * agent.stress
        + 0.65 * goal_blockage(agent)
        + 0.25 * prayer_habit(agent)
        + 0.30 * (agent.faith - 0.5)
        - 0.30 * tired
    )


def create_prayer(agent: Agent, day: int) -> Prayer:
    intensity = _clamp(
        0.50 * agent.stress
        + 0.35 * goal_blockage(agent)
        + 0.15 * prayer_habit(agent)
    )
    return Prayer(
        agent_id=agent.id,
        desire_type=DESIRE_TYPES.get(
            agent.goal,
            "relief",
        ),
        intensity=intensity,
        related_goal=agent.goal,
        timestamp=day,
    )
