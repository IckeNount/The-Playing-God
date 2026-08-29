from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

from playing_god.core.agent import Agent, clamp
from playing_god.core.decision import money_pressure
from playing_god.core.information import EMPLOYMENT_STATUS
from playing_god.core.social import SocialGraph


PARTICIPATION_THRESHOLD = 0.75
PARTICIPATION_STATUS = "participation_status"
PARTICIPATED = "participated"
MAX_PARTICIPATION_AGE_DAYS = 7


@dataclass(frozen=True)
class ParticipationPressure:
    """Inspectably decomposed willingness to join a gathering."""

    personal_pressure: float
    social_confirmation: float
    trusted_information: float
    social_motivation: float
    perceived_cost: float
    risk_aversion: float
    score: float
    threshold: float = PARTICIPATION_THRESHOLD

    @property
    def eligible(self) -> bool:
        return self.score >= self.threshold


@dataclass(frozen=True)
class CollectiveSnapshot:
    participant_ids: tuple[str, ...]
    participants: int
    participation_rate: float
    first_participant_day: int | None
    peak_participants: int
    cascade_depth: int


@dataclass(frozen=True)
class ParticipationTrace:
    agent_id: str
    participation_day: int
    personal_pressure: float
    social_confirmation: float
    trusted_information: float
    social_motivation: float
    perceived_cost: float
    risk_aversion: float
    score: float
    threshold: float
    threshold_passed: bool
    decision: str
    movement_event_index: int | None
    movement: str
    participation_event_index: int
    participation_event: str
    influencer_ids: tuple[str, ...]
    social_evidence_ids: tuple[str, ...]
    trusted_information_evidence_ids: tuple[str, ...]


def _trusted_unemployment_information(
    agent: Agent,
    social: SocialGraph,
) -> float:
    signals = []

    for belief in agent.beliefs.values():
        if (
            belief.kind != EMPLOYMENT_STATUS
            or belief.value != "unemployed"
            or belief.subject_id == agent.id
        ):
            continue

        evidence = next(
            (
                observation
                for observation in reversed(agent.observations)
                if (
                    observation.kind == belief.kind
                    and observation.subject_id == belief.subject_id
                    and observation.value == belief.value
                    and observation.day == belief.updated_day
                )
            ),
            None,
        )
        if evidence is None or evidence.source_id is None:
            continue

        relationship = social.get_relationship(
            agent.id,
            evidence.source_id,
        )
        trust = (
            relationship["trust"]
            if relationship is not None
            else 0.0
        )
        signals.append(belief.confidence * trust)

    return clamp(max(signals, default=0.0))


def participation_information_id(
    participant_id: str,
    participation_day: int,
) -> str:
    return (
        f"{PARTICIPATION_STATUS}:"
        f"{participant_id}:"
        f"{participation_day}"
    )


def recent_participation_day(
    agent: Agent,
    day: int,
) -> int | None:
    earliest_day = day - MAX_PARTICIPATION_AGE_DAYS

    for event in reversed(agent.events):
        if event.day > day:
            continue
        if event.day < earliest_day:
            break
        if event.kind == "participation":
            return event.day

    return None


def _trusted_participation_confirmation(
    agent: Agent,
    social: SocialGraph,
    day: int | None,
) -> float:
    signals = []

    for belief in agent.beliefs.values():
        if (
            belief.kind != PARTICIPATION_STATUS
            or belief.value != PARTICIPATED
            or belief.subject_id == agent.id
        ):
            continue

        evidence = next(
            (
                observation
                for observation in reversed(agent.observations)
                if (
                    observation.kind == belief.kind
                    and observation.subject_id == belief.subject_id
                    and observation.value == belief.value
                    and observation.day == belief.updated_day
                )
            ),
            None,
        )
        if evidence is None or evidence.source_id is None:
            continue

        participation_day = (
            evidence.origin_day
            if evidence.origin_day is not None
            else evidence.day
        )
        if (
            day is not None
            and not (
                0
                <= day - participation_day
                <= MAX_PARTICIPATION_AGE_DAYS
            )
        ):
            continue

        relationship = social.get_relationship(
            agent.id,
            evidence.source_id,
        )
        trust = (
            relationship["trust"]
            if relationship is not None
            else 0.0
        )
        signals.append(belief.confidence * trust)

    return clamp(max(signals, default=0.0))


def _first_participation(agent: Agent):
    return next(
        (
            (index, event)
            for index, event in enumerate(agent.events)
            if event.kind == "participation"
        ),
        None,
    )


def _participation_components(description: str) -> dict[str, float]:
    components = {}

    for segment in description.split("; ")[1:]:
        if ": " not in segment:
            continue
        label, value = segment.rsplit(": ", 1)
        try:
            components[label] = float(value)
        except ValueError:
            continue

    required = {
        "score",
        "threshold",
        "personal",
        "confirmation",
        "trusted information",
        "social motivation",
        "cost",
        "risk aversion",
    }
    missing = required - components.keys()
    if missing:
        raise ValueError(
            "Participation event lacks causal components: "
            + ", ".join(sorted(missing))
        )

    return components


def _latest_observations_before(
    agent: Agent,
    day: int,
):
    latest = {}

    for observation in agent.observations:
        if observation.day >= day:
            continue
        latest[(observation.kind, observation.subject_id)] = observation

    return latest.values()


def _causal_social_evidence(
    agent: Agent,
    participation_day: int,
):
    return [
        observation
        for observation in _latest_observations_before(
            agent,
            participation_day,
        )
        if (
            observation.kind == PARTICIPATION_STATUS
            and observation.value == PARTICIPATED
            and observation.information_id is not None
            and observation.origin_day is not None
            and 0
            <= participation_day - observation.origin_day
            <= MAX_PARTICIPATION_AGE_DAYS
        )
    ]


def build_collective_snapshot(
    agents: Sequence[Agent],
    social: SocialGraph,
) -> CollectiveSnapshot:
    """Derive collective outcomes without mutating world state."""
    first_participations = {
        agent.id: first
        for agent in agents
        if (first := _first_participation(agent)) is not None
    }
    agents_by_id = {
        agent.id: agent
        for agent in agents
    }
    participant_ids = tuple(sorted(first_participations))
    participants_by_day = defaultdict(set)

    for agent in agents:
        for event in agent.events:
            if event.kind == "participation":
                participants_by_day[event.day].add(agent.id)

    depths = {}
    ordered_participants = sorted(
        participant_ids,
        key=lambda agent_id: (
            first_participations[agent_id][1].day,
            agent_id,
        ),
    )
    for agent_id in ordered_participants:
        _, event = first_participations[agent_id]
        try:
            components = _participation_components(event.description)
        except ValueError:
            components = {"confirmation": 0.0}

        parents = []
        if components["confirmation"] > 0.0:
            agent = agents_by_id[agent_id]
            for observation in _causal_social_evidence(
                agent,
                event.day,
            ):
                parent = first_participations.get(
                    observation.subject_id
                )
                relationship = social.get_relationship(
                    agent_id,
                    observation.source_id,
                ) if observation.source_id is not None else None
                if (
                    parent is not None
                    and parent[1].day < event.day
                    and relationship is not None
                    and relationship["trust"] > 0.0
                ):
                    parents.append(observation.subject_id)

        depths[agent_id] = max(
            (depths[parent] + 1 for parent in parents),
            default=0,
        )

    participant_count = len(participant_ids)
    first_day = (
        min(
            event.day
            for _, event in first_participations.values()
        )
        if first_participations
        else None
    )

    return CollectiveSnapshot(
        participant_ids=participant_ids,
        participants=participant_count,
        participation_rate=(
            round(participant_count / len(agents), 6)
            if agents
            else 0.0
        ),
        first_participant_day=first_day,
        peak_participants=max(
            (len(ids) for ids in participants_by_day.values()),
            default=0,
        ),
        cascade_depth=max(depths.values(), default=0),
    )


def build_participation_trace(
    agent: Agent,
    social: SocialGraph,
) -> ParticipationTrace:
    first = _first_participation(agent)
    if first is None:
        raise ValueError(f"Agent did not participate: {agent.id}")

    participation_index, participation_event = first
    components = _participation_components(
        participation_event.description
    )
    social_evidence = _causal_social_evidence(
        agent,
        participation_event.day,
    )
    social_evidence = [
        observation
        for observation in social_evidence
        if (
            observation.source_id is not None
            and (
                relationship := social.get_relationship(
                    agent.id,
                    observation.source_id,
                )
            ) is not None
            and relationship["trust"] > 0.0
        )
    ]
    employment_evidence = []

    for observation in _latest_observations_before(
        agent,
        participation_event.day,
    ):
        if (
            observation.kind != EMPLOYMENT_STATUS
            or observation.value != "unemployed"
            or observation.information_id is None
        ):
            continue
        relationship = social.get_relationship(
            agent.id,
            observation.source_id,
        ) if observation.source_id is not None else None
        if relationship is not None and relationship["trust"] > 0.0:
            employment_evidence.append(observation)

    movement_index = None
    movement = "Already at park; no travel required"
    for index in range(participation_index - 1, -1, -1):
        event = agent.events[index]
        if event.day < participation_event.day:
            break
        if (
            event.kind == "travel"
            and "for participate" in event.description
        ):
            movement_index = index
            movement = event.description
            break

    return ParticipationTrace(
        agent_id=agent.id,
        participation_day=participation_event.day,
        personal_pressure=components["personal"],
        social_confirmation=components["confirmation"],
        trusted_information=components["trusted information"],
        social_motivation=components["social motivation"],
        perceived_cost=components["cost"],
        risk_aversion=components["risk aversion"],
        score=components["score"],
        threshold=components["threshold"],
        threshold_passed=(
            components["score"] >= components["threshold"]
        ),
        decision="participate",
        movement_event_index=movement_index,
        movement=movement,
        participation_event_index=participation_index,
        participation_event=participation_event.description,
        influencer_ids=tuple(
            sorted(
                {
                    observation.subject_id
                    for observation in social_evidence
                }
            )
        ),
        social_evidence_ids=tuple(
            sorted(
                observation.information_id
                for observation in social_evidence
            )
        ),
        trusted_information_evidence_ids=tuple(
            sorted(
                observation.information_id
                for observation in employment_evidence
            )
        ),
    )


def participation_pressure(
    agent: Agent,
    social: SocialGraph,
    *,
    observed_participation: float = 0.0,
    day: int | None = None,
) -> ParticipationPressure:
    """Derive willingness from current state, without causal randomness."""
    positive_ties = [
        max(0.0, affinity)
        for affinity in agent.relationships.values()
    ]
    average_positive_tie = (
        sum(positive_ties) / len(positive_ties)
        if positive_ties
        else 0.0
    )

    personal = clamp(
        0.55 * money_pressure(agent)
        + 0.25 * float(not agent.employed)
        + 0.20 * agent.stress
    )
    confirmation = max(
        clamp(observed_participation),
        _trusted_participation_confirmation(
            agent,
            social,
            day,
        ),
    )
    trusted = _trusted_unemployment_information(agent, social)
    motivation = clamp(
        0.50 * average_positive_tie
        + 0.25 * agent.traits["sociability"]
        + 0.25 * agent.traits["empathy"]
    )
    cost = clamp(
        0.60 * (1.0 - agent.energy)
        + 0.40 * (1.0 - agent.social_energy)
    )
    risk_aversion = clamp(1.0 - agent.traits["risk_tolerance"])

    # These are model parameters, not empirical claims about people.
    score = (
        personal
        + 0.35 * confirmation
        + 0.35 * trusted
        + 0.15 * motivation
        - 0.25 * cost
        - 0.25 * risk_aversion
    )

    return ParticipationPressure(
        personal_pressure=personal,
        social_confirmation=confirmation,
        trusted_information=trusted,
        social_motivation=motivation,
        perceived_cost=cost,
        risk_aversion=risk_aversion,
        score=score,
    )
