from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from playing_god.core.events import Event
from playing_god.core.intervention import InterventionResponse
from playing_god.core.prayer import Prayer

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


ATTRIBUTION_CAUSES = {
    "miracle",
    "coincidence",
    "personal_effort",
    "social_help",
    "institutional",
    "manipulation",
    "unknown",
}


@dataclass(frozen=True)
class Outcome:
    valence: str
    desire_type: str
    action: str | None
    explicit_cause: str | None = None


@dataclass(frozen=True)
class Attribution:
    agent_id: str
    day: int
    outcome_event_index: int
    outcome_kind: str
    outcome_valence: str
    cause: str
    confidence: float
    faith_before: float
    faith_after: float
    prayer_timestamp: int | None = None
    intervention_id: str | None = None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def classify_outcome(event: Event) -> Outcome | None:
    description = event.description

    if event.kind == "career":
        if description.startswith("Found a job"):
            return Outcome("positive", "employment", "job_hunt")
        if description.startswith("Promoted"):
            return Outcome("positive", "advancement", "work")
        if description == "Lost job in workplace downsizing":
            return Outcome(
                "negative",
                "advancement",
                None,
                "institutional",
            )
        if description.startswith("Lost their job"):
            return Outcome("negative", "employment", "work")

    if event.kind == "growth":
        return Outcome("positive", "growth", "train")

    if event.kind == "fortune":
        return Outcome("positive", "security", "risky_move")

    if event.kind == "misfortune":
        return Outcome("negative", "security", "risky_move")

    if event.kind == "crisis":
        return Outcome("negative", "security", None)

    if event.kind == "relationship":
        if description.startswith(("Became close", "Helping")):
            action = (
                "help"
                if description.startswith("Helping")
                else "socialize"
            )
            return Outcome("positive", "belonging", action)
        if description.endswith("turned hostile"):
            return Outcome("negative", "belonging", "socialize")

    if event.kind == "status":
        if description.startswith("Outperformed"):
            return Outcome("positive", "advancement", "compete")
        if description.startswith("Lost badly"):
            return Outcome("negative", "advancement", "compete")

    if event.kind == "support":
        return Outcome(
            "positive",
            "security",
            None,
            "social_help",
        )

    return None


def recent_matching_prayer(
    agent: Agent,
    desire_type: str,
    day: int,
    *,
    window: int = 30,
) -> Prayer | None:
    matches = [
        prayer
        for prayer in agent.prayers
        if prayer.desire_type == desire_type
        and 0 < day - prayer.timestamp <= window
    ]
    return max(matches, key=lambda prayer: prayer.timestamp, default=None)


def select_cause(
    agent: Agent,
    event: Event,
    outcome: Outcome,
    *,
    prayer: Prayer | None,
    response: InterventionResponse | None,
) -> tuple[str, float]:
    if outcome.explicit_cause is not None:
        return outcome.explicit_cause, _clamp(event.significance)

    skepticism = 1 - agent.faith
    scores = {
        "unknown": 0.30 + (0.15 if prayer is None and response is None else 0),
        "coincidence": (
            0.25
            + 0.35 * skepticism
            + (0.15 if outcome.action == "risky_move" else 0)
        ),
    }

    if outcome.valence == "positive" and outcome.action is not None:
        scores["personal_effort"] = (
            0.25
            + 0.30 * agent.traits["discipline"]
            + 0.25 * agent.traits["ambition"]
        )

    if outcome.valence == "positive" and prayer is not None:
        scores["miracle"] = (
            0.25
            + 0.25 * agent.faith
            + 0.20 * prayer.intensity
            + (
                0.20 * response.confidence
                if response is not None
                else 0.0
            )
        )

    if outcome.valence == "negative" and response is not None:
        scores["manipulation"] = (
            0.25
            + 0.30 * skepticism
            + 0.30 * response.confidence
        )

    cause, score = max(
        scores.items(),
        key=lambda item: (item[1], item[0]),
    )
    return cause, _clamp(score * event.significance)


def update_faith(
    faith: float,
    cause: str,
    confidence: float,
) -> float:
    if cause == "miracle":
        faith += 0.12 * confidence * (1 - faith)
    elif cause == "manipulation":
        faith -= 0.12 * confidence * faith
    elif cause == "coincidence":
        faith -= 0.06 * confidence * faith
    elif cause == "personal_effort":
        faith -= 0.04 * confidence * faith
    elif cause == "institutional":
        faith -= 0.03 * confidence * faith

    return _clamp(faith)


def create_attribution(
    agent: Agent,
    event: Event,
    event_index: int,
    outcome: Outcome,
    *,
    prayer: Prayer | None,
    response: InterventionResponse | None,
) -> Attribution:
    cause, confidence = select_cause(
        agent,
        event,
        outcome,
        prayer=prayer,
        response=response,
    )
    faith_before = agent.faith
    faith_after = update_faith(
        faith_before,
        cause,
        confidence,
    )
    return Attribution(
        agent_id=agent.id,
        day=event.day,
        outcome_event_index=event_index,
        outcome_kind=event.kind,
        outcome_valence=outcome.valence,
        cause=cause,
        confidence=confidence,
        faith_before=faith_before,
        faith_after=faith_after,
        prayer_timestamp=(
            prayer.timestamp
            if prayer is not None
            else None
        ),
        intervention_id=(
            response.intervention_id
            if response is not None
            else None
        ),
    )
