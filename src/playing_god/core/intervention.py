from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


INTERVENTION_KINDS = {
    "dream",
    "sign",
    "opportunity",
}

INTERPRETATIONS = {
    "missed",
    "ignored",
    "aligned",
    "misinterpreted",
}


@dataclass(frozen=True)
class Intervention:
    id: str
    kind: str
    target_id: str
    theme: str
    suggested_action: str
    strength: float
    created_day: int
    expires_day: int
    location: str | None = None


@dataclass(frozen=True)
class InterventionResponse:
    intervention_id: str
    agent_id: str
    day: int
    noticed: bool
    interpretation: str
    interpreted_action: str | None
    confidence: float


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def intervention_attention(agent: Agent) -> float:
    """Derive attention from existing measurable state."""
    return _clamp(
        0.45 * agent.traits["discipline"]
        + 0.30 * agent.traits["risk_tolerance"]
        + 0.25 * (1 - agent.stress)
    )


def intervention_confidence(
    agent: Agent,
    intervention: Intervention,
) -> float:
    return _clamp(
        intervention.strength
        * intervention_attention(agent)
    )


def classify_interpretation(confidence: float) -> str:
    """Map confidence to a deterministic, non-guaranteed response."""
    if confidence < 0.25:
        return "missed"

    if confidence < 0.35:
        return "ignored"

    if confidence < 0.55:
        return "misinterpreted"

    return "aligned"
