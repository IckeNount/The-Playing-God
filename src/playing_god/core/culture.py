from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

from playing_god.core.information import InformationItem
from playing_god.core.perception import belief_key

if TYPE_CHECKING:
    from playing_god.core.agent import Agent
    from playing_god.core.perception import Belief, Observation


CULTURAL_NORM = "cultural_norm"
CULTURAL_VALUES = frozenset({"support", "oppose", "uncertain"})
CULTURAL_ROUTES = frozenset({"guardian", "social", "school"})
CULTURAL_RESPONSES = frozenset({"accept", "modify", "reject"})
SCHOOL_SOURCE_ID = "institution:school"
SCHOOL_NORM_SUBJECT = "learning"
SCHOOL_NORM_VALUE = "support"
CULTURAL_DECAY = 0.90


@dataclass(frozen=True)
class CulturalTransmission:
    """One explicit exposure and the recipient's bounded response."""

    day: int
    subject_id: str
    source_id: str
    route: str
    source_value: str
    source_confidence: float
    trust: float
    familiarity: float
    influence: float
    response: str
    resulting_value: str | None
    resulting_confidence: float
    information_id: str | None
    origin_agent_id: str | None
    origin_day: int | None
    hop_count: int | None


@dataclass(frozen=True)
class CulturalState:
    records: tuple[CulturalTransmission, ...] = ()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def cultural_information_id(
    subject_id: str,
    origin_agent_id: str,
    origin_day: int,
    value: str,
) -> str:
    return (
        f"{CULTURAL_NORM}:{subject_id}:"
        f"{origin_agent_id}:{origin_day}:{value}"
    )


def _latest_supporting_observation(
    source: Agent,
    belief: Belief,
) -> Observation | None:
    return next(
        (
            observation
            for observation in reversed(source.observations)
            if observation.kind == CULTURAL_NORM
            and observation.subject_id == belief.subject_id
            and observation.value == belief.value
            and observation.day <= belief.updated_day
        ),
        None,
    )


def select_cultural_claim(
    source: Agent,
    *,
    seen: set[tuple[str, str]],
    allow_repeat: bool,
) -> InformationItem | None:
    """Select one held norm for an actual exposure channel."""
    candidates = []
    for belief in source.beliefs.values():
        if belief.kind != CULTURAL_NORM:
            continue
        if belief.value not in CULTURAL_VALUES:
            continue

        observation = _latest_supporting_observation(source, belief)
        has_identity = observation is not None and all(
            value is not None
            for value in (
                observation.information_id,
                observation.origin_agent_id,
                observation.origin_day,
                observation.hop_count,
            )
        )
        if has_identity:
            information_id = observation.information_id
            origin_agent_id = observation.origin_agent_id
            origin_day = observation.origin_day
            hop_count = observation.hop_count + 1
            evidence_reliability = observation.reliability
        else:
            information_id = cultural_information_id(
                belief.subject_id,
                source.id,
                belief.updated_day,
                belief.value,
            )
            origin_agent_id = source.id
            origin_day = belief.updated_day
            hop_count = 1
            evidence_reliability = belief.confidence

        if (
            not allow_repeat
            and (source.id, information_id) in seen
        ):
            continue

        reliability = round(
            min(
                belief.confidence * CULTURAL_DECAY,
                evidence_reliability * CULTURAL_DECAY,
            ),
            6,
        )
        if reliability <= 0.0:
            continue

        candidates.append((
            belief.subject_id,
            -belief.confidence,
            InformationItem(
                id=information_id,
                kind=CULTURAL_NORM,
                subject_id=belief.subject_id,
                value=belief.value,
                origin_agent_id=origin_agent_id,
                origin_day=origin_day,
                reliability=reliability,
                hop_count=hop_count,
            ),
        ))

    if not candidates:
        return None
    return min(candidates)[-1]


def cultural_response(
    recipient: Agent,
    *,
    subject_id: str,
    source_value: str,
    source_confidence: float,
    trust: float,
    familiarity: float,
    route: str,
) -> tuple[float, str, str | None, float]:
    """Interpret an exposure without consuming simulation randomness."""
    if source_value not in CULTURAL_VALUES:
        raise ValueError(f"Unknown cultural value: {source_value}")
    if route not in CULTURAL_ROUTES:
        raise ValueError(f"Unknown cultural route: {route}")

    prior = recipient.beliefs.get(
        belief_key(CULTURAL_NORM, subject_id)
    )
    influence = (
        0.45 * _clamp(source_confidence)
        + 0.25 * _clamp(trust)
        + 0.15 * _clamp(familiarity)
        + 0.15 * recipient.traits["empathy"]
    )
    if route in {"guardian", "school"}:
        influence += 0.05
    if prior is not None:
        if prior.value == source_value:
            influence += 0.10 * prior.confidence
        elif (
            prior.value != "uncertain"
            and source_value != "uncertain"
        ):
            influence -= 0.20 * prior.confidence
    influence = round(_clamp(influence), 6)

    if influence >= 0.70:
        return influence, "accept", source_value, influence
    if influence >= 0.50 and source_value != "uncertain":
        return influence, "modify", "uncertain", influence
    return influence, "reject", None, 0.0


def make_transmission(
    recipient: Agent,
    *,
    day: int,
    subject_id: str,
    source_id: str,
    route: str,
    source_value: str,
    source_confidence: float,
    trust: float,
    familiarity: float,
    information_id: str | None,
    origin_agent_id: str | None,
    origin_day: int | None,
    hop_count: int | None,
) -> CulturalTransmission:
    influence, response, value, confidence = cultural_response(
        recipient,
        subject_id=subject_id,
        source_value=source_value,
        source_confidence=source_confidence,
        trust=trust,
        familiarity=familiarity,
        route=route,
    )
    return CulturalTransmission(
        day=day,
        subject_id=subject_id,
        source_id=source_id,
        route=route,
        source_value=source_value,
        source_confidence=source_confidence,
        trust=trust,
        familiarity=familiarity,
        influence=influence,
        response=response,
        resulting_value=value,
        resulting_confidence=confidence,
        information_id=information_id,
        origin_agent_id=origin_agent_id,
        origin_day=origin_day,
        hop_count=hop_count,
    )


def cultural_state_from_data(data: object) -> CulturalState:
    if not isinstance(data, dict) or set(data) != {"records"}:
        raise ValueError("Invalid cultural state structure.")
    records_data = data["records"]
    if not isinstance(records_data, list):
        raise ValueError("Cultural records must be stored as a list.")
    expected_fields = set(CulturalTransmission.__dataclass_fields__)
    records = []
    for item in records_data:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ValueError("Invalid cultural record structure.")
        records.append(CulturalTransmission(**item))
    state = CulturalState(records=tuple(records))
    validate_cultural_state(state)
    return state


def validate_cultural_state(state: CulturalState) -> None:
    if not isinstance(state.records, tuple):
        raise ValueError("Invalid cultural state values.")

    previous_day = -1
    for record in state.records:
        if not isinstance(record, CulturalTransmission):
            raise ValueError("Invalid cultural record values.")
        identity = (
            record.information_id,
            record.origin_agent_id,
            record.origin_day,
            record.hop_count,
        )
        numeric = (
            record.source_confidence,
            record.trust,
            record.familiarity,
            record.influence,
            record.resulting_confidence,
        )
        if (
            isinstance(record.day, bool)
            or not isinstance(record.day, int)
            or record.day < previous_day
            or not isinstance(record.subject_id, str)
            or not record.subject_id
            or not isinstance(record.source_id, str)
            or not record.source_id
            or record.route not in CULTURAL_ROUTES
            or record.source_value not in CULTURAL_VALUES
            or record.response not in CULTURAL_RESPONSES
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
                for value in numeric
            )
            or any(value is None for value in identity)
            != all(value is None for value in identity)
            or (
                record.information_id is not None
                and (
                    not isinstance(record.information_id, str)
                    or not record.information_id
                    or not isinstance(record.origin_agent_id, str)
                    or not record.origin_agent_id
                    or isinstance(record.origin_day, bool)
                    or not isinstance(record.origin_day, int)
                    or record.origin_day > record.day
                    or isinstance(record.hop_count, bool)
                    or not isinstance(record.hop_count, int)
                    or record.hop_count < 1
                )
            )
            or (
                record.response == "accept"
                and (
                    record.influence < 0.70
                    or record.resulting_value != record.source_value
                    or record.resulting_confidence != record.influence
                )
            )
            or (
                record.response == "modify"
                and (
                    not 0.50 <= record.influence < 0.70
                    or record.source_value == "uncertain"
                    or record.resulting_value != "uncertain"
                    or record.resulting_confidence != record.influence
                )
            )
            or (
                record.response == "reject"
                and (
                    record.influence >= 0.70
                    or (
                        record.influence >= 0.50
                        and record.source_value != "uncertain"
                    )
                    or record.resulting_value is not None
                    or record.resulting_confidence != 0.0
                )
            )
        ):
            raise ValueError("Invalid cultural record values.")
        previous_day = record.day


def validate_cultural_links(
    agents: list[Agent],
    *,
    current_day: int,
) -> None:
    agents_by_id = {agent.id: agent for agent in agents}
    for recipient in agents:
        validate_cultural_state(recipient.culture)
        school_days = {
            record.day
            for record in recipient.development.records
            if record.school_access
        }
        for record in recipient.culture.records:
            if record.day > current_day:
                raise ValueError("Cultural record occurs in the future.")
            if record.route == "school":
                if (
                    record.source_id != SCHOOL_SOURCE_ID
                    or record.day not in school_days
                    or record.information_id is not None
                ):
                    raise ValueError("Invalid school cultural link.")
            elif (
                record.source_id not in agents_by_id
                or record.source_id == recipient.id
                or record.information_id is None
            ):
                raise ValueError("Invalid cultural source link.")
            if (
                record.route == "guardian"
                and (
                    record.source_id not in recipient.family.guardian_ids
                    or not any(
                        development.day == record.day
                        and record.source_id
                        in development.guardian_ids
                        for development in recipient.development.records
                    )
                )
            ):
                raise ValueError("Invalid guardian cultural link.")
            if (
                record.route == "social"
                and not any(
                    event.day == record.day
                    and event.kind == "interaction"
                    and event.target_id == record.source_id
                    for event in recipient.events
                )
            ):
                raise ValueError("Invalid social cultural link.")
            if (
                record.origin_agent_id is not None
                and record.origin_agent_id not in agents_by_id
            ):
                raise ValueError("Invalid cultural origin link.")
            if not any(
                observation.day == record.day
                and observation.kind == CULTURAL_NORM
                and observation.subject_id == record.subject_id
                and observation.value == record.source_value
                and observation.source_id == record.source_id
                and observation.information_id == record.information_id
                for observation in recipient.observations
            ):
                raise ValueError("Cultural exposure lacks observation.")
