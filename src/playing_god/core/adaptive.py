from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


LEARNING_CONTEXTS = (
    "find_job",
    "build_savings",
    "improve_skill",
    "build_relationships",
    "advance_career",
)
MAX_PREFERENCE_ADJUSTMENT = 0.75


def bounded(value: float) -> float:
    return max(-1.0, min(1.0, value))


@dataclass(frozen=True)
class AgentState:
    money: float
    skill: float
    energy: float
    social_energy: float
    stress: float
    reputation: float
    relationship_affinity: float
    employed: bool
    job_level: int


@dataclass(frozen=True)
class Consequence:
    money: float = 0.0
    skill: float = 0.0
    energy: float = 0.0
    social_energy: float = 0.0
    stress_reduction: float = 0.0
    reputation: float = 0.0
    relationship_affinity: float = 0.0
    employment: float = 0.0
    job_level: float = 0.0


@dataclass
class ActionValue:
    observations: int = 0
    mean_feedback: float = 0.0
    mean_consequence: Consequence = field(
        default_factory=Consequence,
    )


def context_for(agent: Agent) -> str:
    """Use the existing goal as the compact learning context."""
    if agent.goal not in LEARNING_CONTEXTS:
        raise ValueError(
            f"Agent has no valid learning context: {agent.goal!r}"
        )
    return agent.goal


def capture_state(agent: Agent) -> AgentState:
    return AgentState(
        money=agent.money,
        skill=agent.skill,
        energy=agent.energy,
        social_energy=agent.social_energy,
        stress=agent.stress,
        reputation=agent.reputation,
        relationship_affinity=sum(agent.relationships.values()),
        employed=agent.employed,
        job_level=agent.job_level,
    )


def consequence_between(
    before: AgentState,
    after: AgentState,
) -> Consequence:
    """Keep observed action consequences separate instead of one score."""
    return Consequence(
        money=after.money - before.money,
        skill=after.skill - before.skill,
        energy=after.energy - before.energy,
        social_energy=(
            after.social_energy - before.social_energy
        ),
        stress_reduction=before.stress - after.stress,
        reputation=after.reputation - before.reputation,
        relationship_affinity=(
            after.relationship_affinity
            - before.relationship_affinity
        ),
        employment=(
            float(after.employed)
            - float(before.employed)
        ),
        job_level=float(after.job_level - before.job_level),
    )


def feedback_for(
    context: str,
    consequence: Consequence,
) -> float:
    """Project consequences onto the NPC's current goal, not happiness."""
    if context == "find_job":
        feedback = consequence.employment
    elif context == "build_savings":
        feedback = consequence.money / 50.0
    elif context == "improve_skill":
        feedback = consequence.skill / 0.02
    elif context == "build_relationships":
        feedback = consequence.relationship_affinity / 0.10
    elif context == "advance_career":
        feedback = (
            consequence.job_level
            + 0.25 * consequence.reputation / 0.10
            + 0.25 * consequence.skill / 0.02
        )
    else:
        raise ValueError(f"Unknown learning context: {context}")

    return bounded(feedback)


def _updated_mean(
    current: float,
    observed: float,
    observations: int,
) -> float:
    return current + (observed - current) / observations


def _updated_consequence(
    current: Consequence,
    observed: Consequence,
    observations: int,
) -> Consequence:
    return Consequence(**{
        item.name: _updated_mean(
            getattr(current, item.name),
            getattr(observed, item.name),
            observations,
        )
        for item in fields(Consequence)
    })


def learn(
    agent: Agent,
    context: str,
    action: str,
    consequence: Consequence,
) -> ActionValue:
    feedback = feedback_for(context, consequence)
    values = agent.adaptive_values.setdefault(context, {})
    value = values.setdefault(action, ActionValue())
    value.observations += 1
    value.mean_feedback = _updated_mean(
        value.mean_feedback,
        feedback,
        value.observations,
    )
    value.mean_consequence = _updated_consequence(
        value.mean_consequence,
        consequence,
        value.observations,
    )
    return value


def learned_preferences(
    agent: Agent,
    context: str,
) -> dict[str, float]:
    return {
        action: (
            MAX_PREFERENCE_ADJUSTMENT
            * bounded(value.mean_feedback)
        )
        for action, value in agent.adaptive_values.get(
            context,
            {},
        ).items()
    }
