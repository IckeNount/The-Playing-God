from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


@dataclass(frozen=True)
class Observation:
    """Information that physically reached one agent."""

    day: int
    kind: str
    subject_id: str
    value: str
    source_id: str | None
    reliability: float
    location: str | None = None


@dataclass(frozen=True)
class Perception:
    """One agent's interpretation of received information."""

    day: int
    kind: str
    subject_id: str
    value: str
    confidence: float


@dataclass(frozen=True)
class Belief:
    """An agent's current, revisable claim about the world."""

    kind: str
    subject_id: str
    value: str
    confidence: float
    updated_day: int
    evidence_count: int


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def belief_key(kind: str, subject_id: str) -> str:
    return f"{kind}:{subject_id}"


def perceive(
    observation: Observation,
    *,
    attention: float = 1.0,
) -> Perception:
    """Interpret evidence without consuming causal randomness."""
    return Perception(
        day=observation.day,
        kind=observation.kind,
        subject_id=observation.subject_id,
        value=observation.value,
        confidence=_clamp(
            observation.reliability * _clamp(attention)
        ),
    )


def update_belief(
    agent: Agent,
    perception: Perception,
) -> Belief:
    key = belief_key(
        perception.kind,
        perception.subject_id,
    )
    prior = agent.beliefs.get(key)
    belief = Belief(
        kind=perception.kind,
        subject_id=perception.subject_id,
        value=perception.value,
        confidence=perception.confidence,
        updated_day=perception.day,
        evidence_count=(
            prior.evidence_count + 1
            if prior is not None
            else 1
        ),
    )
    agent.beliefs[key] = belief
    return belief


def receive_observation(
    agent: Agent,
    observation: Observation,
    *,
    attention: float = 1.0,
) -> Belief:
    """Append received evidence, then revise current belief state."""
    agent.observations.append(observation)
    return update_belief(
        agent,
        perceive(
            observation,
            attention=attention,
        ),
    )
