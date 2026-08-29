from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, median
from typing import TYPE_CHECKING, Iterable

from playing_god.core.perception import belief_key

if TYPE_CHECKING:
    from playing_god.core.agent import Agent
    from playing_god.core.perception import Observation


EMPLOYMENT_STATUS = "employment_status"
MAX_TESTIMONY_AGE_DAYS = 30
TESTIMONY_DECAY = 0.85


@dataclass(frozen=True)
class InformationItem:
    """One structured claim transmitted through social contact."""

    id: str
    kind: str
    subject_id: str
    value: str
    origin_agent_id: str
    origin_day: int
    reliability: float
    hop_count: int


@dataclass(frozen=True)
class DiffusionSnapshot:
    """Read-only reach and current-belief metrics for one item."""

    information_id: str
    kind: str
    subject_id: str
    value: str
    origin_agent_id: str
    origin_day: int
    reached_agent_ids: tuple[str, ...]
    reached_agent_count: int
    informed_agent_ids: tuple[str, ...]
    informed_agent_count: int
    max_hops_from_origin: int
    average_belief_confidence: float
    median_belief_confidence: float


def employment_status(employed: bool) -> str:
    return "employed" if employed else "unemployed"


def employment_information_id(
    origin_agent_id: str,
    origin_day: int,
    value: str,
) -> str:
    return (
        f"{EMPLOYMENT_STATUS}:"
        f"{origin_agent_id}:"
        f"{origin_day}:"
        f"{value}"
    )


def observation_information_id(
    observation: Observation,
) -> str | None:
    if observation.information_id is not None:
        return observation.information_id

    if (
        observation.kind == EMPLOYMENT_STATUS
        and observation.source_id == observation.subject_id
    ):
        return employment_information_id(
            observation.subject_id,
            observation.day,
            observation.value,
        )

    return None


def _observation_origin(
    observation: Observation,
) -> tuple[str, int, int] | None:
    if (
        observation.origin_agent_id is not None
        and observation.origin_day is not None
        and observation.hop_count is not None
    ):
        return (
            observation.origin_agent_id,
            observation.origin_day,
            observation.hop_count,
        )

    if (
        observation.kind == EMPLOYMENT_STATUS
        and observation.source_id == observation.subject_id
    ):
        return (
            observation.subject_id,
            observation.day,
            0,
        )

    return None


def diffusion_snapshot(
    agents: Iterable[Agent],
    information_id: str,
) -> DiffusionSnapshot:
    """Derive diffusion metrics without mutating agents or RNG state."""
    reached = []

    for agent in agents:
        matches = [
            observation
            for observation in agent.observations
            if observation_information_id(observation) == information_id
        ]
        if not matches:
            continue

        observation = min(
            matches,
            key=lambda item: (
                (_observation_origin(item) or ("", 0, 0))[2],
                item.day,
            ),
        )
        origin = _observation_origin(observation)
        if origin is None:
            continue
        reached.append((agent, observation, origin))

    if not reached:
        raise ValueError(
            f"Unknown information item: {information_id}"
        )

    _, canonical_observation, canonical_origin = min(
        reached,
        key=lambda item: (
            item[2][2],
            item[1].day,
            item[0].id,
        ),
    )
    origin_agent_id, origin_day, _ = canonical_origin

    informed = []
    for agent, observation, origin in reached:
        if (
            observation.kind != canonical_observation.kind
            or observation.subject_id
            != canonical_observation.subject_id
            or observation.value != canonical_observation.value
            or origin[:2] != canonical_origin[:2]
        ):
            raise ValueError(
                "Information identity has inconsistent observations: "
                f"{information_id}"
            )

        belief = agent.beliefs.get(
            belief_key(observation.kind, observation.subject_id)
        )
        if belief is not None and belief.value == observation.value:
            informed.append((agent.id, belief.confidence))

    reached_agent_ids = tuple(
        sorted(agent.id for agent, _, _ in reached)
    )
    informed.sort()
    confidences = [confidence for _, confidence in informed]

    return DiffusionSnapshot(
        information_id=information_id,
        kind=canonical_observation.kind,
        subject_id=canonical_observation.subject_id,
        value=canonical_observation.value,
        origin_agent_id=origin_agent_id,
        origin_day=origin_day,
        reached_agent_ids=reached_agent_ids,
        reached_agent_count=len(reached_agent_ids),
        informed_agent_ids=tuple(
            agent_id
            for agent_id, _ in informed
        ),
        informed_agent_count=len(informed),
        max_hops_from_origin=max(
            origin[2]
            for _, _, origin in reached
        ),
        average_belief_confidence=(
            round(fmean(confidences), 6)
            if confidences
            else 0.0
        ),
        median_belief_confidence=(
            round(median(confidences), 6)
            if confidences
            else 0.0
        ),
    )


def _testimony_reliability(
    source_confidence: float,
    evidence_reliability: float,
    relationship: dict[str, float] | None,
) -> float:
    relationship = relationship or {}
    trust = relationship.get("trust", 0.25)
    familiarity = relationship.get("familiarity", 0.10)
    social_limit = 0.50 + 0.30 * trust + 0.20 * familiarity
    return round(
        min(
            source_confidence * TESTIMONY_DECAY,
            evidence_reliability * TESTIMONY_DECAY,
            social_limit,
        ),
        6,
    )


def select_testimony(
    source: Agent,
    recipient: Agent,
    *,
    day: int,
    relationship: dict[str, float] | None,
    recipient_evidence: set[str] | None = None,
    source_information: Iterable[Observation] | None = None,
) -> InformationItem | None:
    """Select one unseen employment claim without consuming RNG."""
    latest_by_subject = {}
    if recipient_evidence is None:
        recipient_evidence = {
            evidence_id
            for observation in recipient.observations
            if (
                evidence_id := observation_information_id(observation)
            ) is not None
        }

    if source_information is None:
        for observation in reversed(source.observations):
            if observation.day < day - MAX_TESTIMONY_AGE_DAYS:
                break
            if observation.kind != EMPLOYMENT_STATUS:
                continue
            latest_by_subject.setdefault(
                observation.subject_id,
                observation,
            )
    else:
        latest_by_subject = {
            observation.subject_id: observation
            for observation in source_information
        }

    candidates = []

    for observation in latest_by_subject.values():
        if observation.subject_id in {source.id, recipient.id}:
            continue
        evidence_id = observation_information_id(observation)
        if evidence_id is None or evidence_id in recipient_evidence:
            continue

        age = day - observation.day
        if age < 0 or age > MAX_TESTIMONY_AGE_DAYS:
            continue

        belief = source.beliefs.get(
            belief_key(EMPLOYMENT_STATUS, observation.subject_id)
        )
        if (
            belief is None
            or belief.value != observation.value
            or belief.updated_day != observation.day
        ):
            continue

        reliability = _testimony_reliability(
            belief.confidence,
            observation.reliability,
            relationship,
        )
        if reliability <= 0.0:
            continue

        origin = _observation_origin(observation)
        if origin is None:
            continue
        origin_agent_id, origin_day, source_hop_count = origin

        recipient_belief = recipient.beliefs.get(
            belief_key(EMPLOYMENT_STATUS, observation.subject_id)
        )
        if (
            recipient_belief is not None
            and recipient_belief.value == observation.value
            and recipient_belief.confidence >= reliability
        ):
            continue

        candidates.append(
            (
                -observation.day,
                observation.subject_id,
                -belief.confidence,
                InformationItem(
                    id=evidence_id,
                    kind=EMPLOYMENT_STATUS,
                    subject_id=observation.subject_id,
                    value=observation.value,
                    origin_agent_id=origin_agent_id,
                    origin_day=origin_day,
                    reliability=reliability,
                    hop_count=source_hop_count + 1,
                ),
            )
        )

    if not candidates:
        return None

    return min(candidates)[-1]
