from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import TYPE_CHECKING

from playing_god.core.causal_history import (
    ExplicitCausalReference,
    HistoricalEventReference,
    explicit_causal_references,
)
from playing_god.core.events import Event

if TYPE_CHECKING:
    from playing_god.core.world import World


HISTORY_ANALYSIS_VERSION = "episode-v1"
DEFAULT_MAX_DAY_GAP = 3
DEFAULT_MAX_EPISODE_DURATION = 7
DEFAULT_MAX_EPISODE_EVENTS = 12
EPISODE_CAUSAL_RELATIONS = frozenset({
    "problem_evidence_to_recognition",
    "recognition_to_discovery_attempt",
    "discovery_attempt_to_resolution",
})


@dataclass(frozen=True)
class HistoricalEpisode:
    """Immutable, derived grouping of authoritative source events."""

    id: str
    start_day: int
    end_day: int
    participating_agent_ids: tuple[str, ...]
    source_event_references: tuple[HistoricalEventReference, ...]
    event_kinds: tuple[str, ...]
    magnitude: float
    explicit_causal_references: tuple[ExplicitCausalReference, ...]


@dataclass(frozen=True)
class _HistoricalEvent:
    reference: HistoricalEventReference
    event: Event
    participant_ids: frozenset[str]


@dataclass
class _EpisodeBuilder:
    events: list[_HistoricalEvent]
    participant_ids: set[str]
    start_day: int
    end_day: int


def resolve_source_event(
    world: World,
    reference: HistoricalEventReference,
) -> Event:
    """Resolve an episode reference without copying authoritative data."""
    agent = next(
        (
            item
            for item in world.agents
            if item.id == reference.agent_id
        ),
        None,
    )
    if agent is None or not 0 <= reference.event_index < len(agent.events):
        raise ValueError(f"Unknown historical event: {reference}")
    return agent.events[reference.event_index]


def _flatten_events(world: World) -> tuple[_HistoricalEvent, ...]:
    agent_ids = {agent.id for agent in world.agents}
    events = []
    for agent in world.agents:
        for event_index, event in enumerate(agent.events):
            participant_ids = {agent.id}
            if event.target_id in agent_ids:
                participant_ids.add(event.target_id)
            events.append(_HistoricalEvent(
                reference=HistoricalEventReference(
                    agent_id=agent.id,
                    event_index=event_index,
                ),
                event=event,
                participant_ids=frozenset(participant_ids),
            ))
    return tuple(sorted(
        events,
        key=lambda item: (
            item.event.day,
            item.reference.agent_id,
            item.reference.event_index,
        ),
    ))


def _episode_id(
    references: tuple[HistoricalEventReference, ...],
) -> str:
    canonical = "|".join(
        (
            HISTORY_ANALYSIS_VERSION,
            *(f"{item.agent_id}:{item.event_index}" for item in references),
        )
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"historical-episode:{HISTORY_ANALYSIS_VERSION}:{digest}"


def _validate_bounds(
    max_day_gap: int,
    max_duration: int,
    max_events: int,
) -> None:
    for name, value, minimum in (
        ("max_day_gap", max_day_gap, 0),
        ("max_duration", max_duration, 0),
        ("max_events", max_events, 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
        if value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")


def extract_historical_episodes(
    world: World,
    *,
    max_day_gap: int = DEFAULT_MAX_DAY_GAP,
    max_duration: int = DEFAULT_MAX_EPISODE_DURATION,
    max_events: int = DEFAULT_MAX_EPISODE_EVENTS,
) -> tuple[HistoricalEpisode, ...]:
    """Derive deterministic bounded episodes without mutating the world."""
    _validate_bounds(max_day_gap, max_duration, max_events)
    source_events = _flatten_events(world)
    causal_references = tuple(
        item
        for item in explicit_causal_references(world)
        if item.relation in EPISODE_CAUSAL_RELATIONS
    )
    causal_neighbors: dict[
        HistoricalEventReference,
        set[HistoricalEventReference],
    ] = {}
    for link in causal_references:
        causal_neighbors.setdefault(link.cause, set()).add(link.effect)
        causal_neighbors.setdefault(link.effect, set()).add(link.cause)

    builders: list[_EpisodeBuilder] = []
    for source_event in source_events:
        candidates = []
        for index, builder in enumerate(builders):
            if source_event.event.day - builder.end_day > max_day_gap:
                continue
            if source_event.event.day - builder.start_day > max_duration:
                continue
            if len(builder.events) >= max_events:
                continue

            explicit_link = any(
                item.reference
                in causal_neighbors.get(source_event.reference, set())
                for item in builder.events
            )
            shared_participants = len(
                source_event.participant_ids & builder.participant_ids
            )
            if not explicit_link and shared_participants == 0:
                continue
            candidates.append((
                explicit_link,
                shared_participants,
                builder.end_day,
                -index,
                index,
            ))

        if not candidates:
            builders.append(_EpisodeBuilder(
                events=[source_event],
                participant_ids=set(source_event.participant_ids),
                start_day=source_event.event.day,
                end_day=source_event.event.day,
            ))
            continue

        *_, selected_index = max(candidates)
        selected = builders[selected_index]
        selected.events.append(source_event)
        selected.participant_ids.update(source_event.participant_ids)
        selected.end_day = source_event.event.day

    episodes = []
    for builder in builders:
        references = tuple(
            item.reference
            for item in builder.events
        )
        reference_set = frozenset(references)
        episodes.append(HistoricalEpisode(
            id=_episode_id(references),
            start_day=builder.start_day,
            end_day=builder.end_day,
            participating_agent_ids=tuple(sorted(builder.participant_ids)),
            source_event_references=references,
            event_kinds=tuple(sorted({
                item.event.kind
                for item in builder.events
            })),
            magnitude=max(
                float(item.event.significance)
                for item in builder.events
            ),
            explicit_causal_references=tuple(
                link
                for link in causal_references
                if link.cause in reference_set
                and link.effect in reference_set
            ),
        ))

    return tuple(episodes)
