from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Iterable

from playing_god.core.culture import CulturalState
from playing_god.core.civilization import AgentKnowledgeState
from playing_god.core.events import Event
from playing_god.core.faith import Attribution
from playing_god.core.intervention import (
    INTERVENTION_KINDS,
    Intervention,
    InterventionResponse,
)
from playing_god.core.lifecycle import LifecycleState
from playing_god.core.perception import Belief, Observation
from playing_god.core.prayer import Prayer
from playing_god.core.world import World


@dataclass(frozen=True)
class ScheduledIntervention:
    day: int
    kind: str
    target_id: str
    theme: str
    suggested_action: str
    strength: float = 0.70
    location: str | None = None
    duration: int = 7

    def __post_init__(self) -> None:
        if self.day < 0:
            raise ValueError(
                "Scheduled intervention day cannot be negative"
            )
        if self.kind not in INTERVENTION_KINDS:
            raise ValueError(
                f"Unknown intervention kind: {self.kind}"
            )
        if not self.theme.strip():
            raise ValueError(
                "Scheduled intervention theme cannot be empty"
            )
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                "Scheduled intervention strength must be within [0, 1]"
            )
        if self.duration < 1:
            raise ValueError(
                "Scheduled intervention duration must be at least one day"
            )


@dataclass(frozen=True)
class EventSnapshot:
    day: int
    kind: str
    description: str
    significance: float
    target_id: str | None
    location: str | None


@dataclass(frozen=True)
class AgentSnapshot:
    agent_id: str
    name: str
    age: int
    traits: tuple[tuple[str, float], ...]
    sins: tuple[tuple[str, float], ...]
    money: float
    employed: bool
    salary: float
    job_level: int
    skill: float
    energy: float
    social_energy: float
    stress: float
    reputation: float
    faith: float
    goal: str
    relationships: tuple[tuple[str, float], ...]
    actions: tuple[tuple[str, int], ...]
    observations: tuple[Observation, ...]
    beliefs: tuple[tuple[str, Belief], ...]
    prayers: tuple[Prayer, ...]
    attributions: tuple[Attribution, ...]
    events: tuple[EventSnapshot, ...]
    current_location: str
    destination: str | None
    lifecycle: LifecycleState
    culture: CulturalState
    knowledge: AgentKnowledgeState
    social_ties: tuple[
        tuple[str, tuple[tuple[str, float], ...]],
        ...,
    ]


@dataclass(frozen=True)
class EventDifference:
    event_index: int
    baseline: EventSnapshot | None
    intervention: EventSnapshot | None

    @property
    def day(self) -> int:
        days = [
            event.day
            for event in (self.baseline, self.intervention)
            if event is not None
        ]
        return min(days)


@dataclass(frozen=True)
class AgentDifference:
    agent_id: str
    changed_fields: tuple[str, ...]
    baseline: AgentSnapshot
    intervention: AgentSnapshot
    first_event_difference: EventDifference | None


@dataclass(frozen=True)
class CounterfactualComparison:
    seed: int
    days: int
    population: int
    schedule: tuple[ScheduledIntervention, ...]
    first_divergence_day: int | None
    agent_differences: tuple[AgentDifference, ...]
    created_interventions: tuple[Intervention, ...]
    intervention_responses: tuple[InterventionResponse, ...]
    baseline_world: World = field(compare=False, repr=False)
    intervention_world: World = field(compare=False, repr=False)

    @property
    def diverged(self) -> bool:
        return bool(self.agent_differences)

    @property
    def affected_agent_ids(self) -> tuple[str, ...]:
        return tuple(
            difference.agent_id
            for difference in self.agent_differences
        )


def _event_snapshot(event: Event) -> EventSnapshot:
    return EventSnapshot(
        day=event.day,
        kind=event.kind,
        description=event.description,
        significance=event.significance,
        target_id=event.target_id,
        location=event.location,
    )


def _social_ties(
    world: World,
    agent_id: str,
) -> tuple[
    tuple[str, tuple[tuple[str, float], ...]],
    ...,
]:
    return tuple(
        (
            target_id,
            tuple(
                sorted(
                    (key, float(value))
                    for key, value in data.items()
                )
            ),
        )
        for _, target_id, data in sorted(
            world.social.graph.out_edges(agent_id, data=True),
            key=lambda edge: edge[1],
        )
    )


def snapshot_agents(world: World) -> tuple[AgentSnapshot, ...]:
    """Capture immutable, comparable state without mutating a world."""
    snapshots = []

    for agent in world.agents:
        snapshots.append(
            AgentSnapshot(
                agent_id=agent.id,
                name=agent.name,
                age=agent.age,
                traits=tuple(sorted(agent.traits.items())),
                sins=tuple(sorted(agent.sins.items())),
                money=agent.money,
                employed=agent.employed,
                salary=agent.salary,
                job_level=agent.job_level,
                skill=agent.skill,
                energy=agent.energy,
                social_energy=agent.social_energy,
                stress=agent.stress,
                reputation=agent.reputation,
                faith=agent.faith,
                goal=agent.goal,
                relationships=tuple(
                    sorted(agent.relationships.items())
                ),
                actions=tuple(sorted(agent.actions.items())),
                observations=tuple(agent.observations),
                beliefs=tuple(sorted(agent.beliefs.items())),
                prayers=tuple(agent.prayers),
                attributions=tuple(agent.attributions),
                events=tuple(
                    _event_snapshot(event)
                    for event in agent.events
                ),
                current_location=agent.current_location,
                destination=agent.destination,
                lifecycle=agent.lifecycle,
                culture=agent.culture,
                knowledge=agent.knowledge,
                social_ties=_social_ties(world, agent.id),
            )
        )

    return tuple(snapshots)


def _today_events(agent, day: int) -> tuple[EventSnapshot, ...]:
    events = []
    for event in reversed(agent.events):
        if event.day < day:
            break
        if event.day == day:
            events.append(_event_snapshot(event))
    return tuple(reversed(events))


def _trajectory_signature(world: World) -> tuple:
    """Compare current causal state without rescanning full histories."""
    return tuple(
        (
            agent.id,
            agent.age,
            tuple(sorted(agent.sins.items())),
            agent.money,
            agent.employed,
            agent.salary,
            agent.job_level,
            agent.skill,
            agent.energy,
            agent.social_energy,
            agent.stress,
            agent.reputation,
            agent.faith,
            agent.goal,
            tuple(sorted(agent.relationships.items())),
            tuple(sorted(agent.actions.items())),
            tuple(sorted(agent.beliefs.items())),
            len(agent.observations),
            len(agent.prayers),
            len(agent.attributions),
            len(agent.events),
            _today_events(agent, world.day),
            agent.current_location,
            agent.destination,
            agent.lifecycle,
            agent.culture,
            _social_ties(world, agent.id),
        )
        for agent in world.agents
    )


def _first_event_difference(
    baseline: tuple[EventSnapshot, ...],
    intervention: tuple[EventSnapshot, ...],
) -> EventDifference | None:
    count = max(len(baseline), len(intervention))

    for index in range(count):
        baseline_event = (
            baseline[index]
            if index < len(baseline)
            else None
        )
        intervention_event = (
            intervention[index]
            if index < len(intervention)
            else None
        )
        if baseline_event != intervention_event:
            return EventDifference(
                event_index=index,
                baseline=baseline_event,
                intervention=intervention_event,
            )

    return None


def _compare_agents(
    baseline_world: World,
    intervention_world: World,
) -> tuple[AgentDifference, ...]:
    baseline = snapshot_agents(baseline_world)
    intervention = snapshot_agents(intervention_world)
    differences = []

    for before, after in zip(baseline, intervention, strict=True):
        changed_fields = tuple(
            item.name
            for item in fields(AgentSnapshot)
            if item.name != "agent_id"
            and getattr(before, item.name) != getattr(after, item.name)
        )
        if not changed_fields:
            continue

        differences.append(
            AgentDifference(
                agent_id=before.agent_id,
                changed_fields=changed_fields,
                baseline=before,
                intervention=after,
                first_event_difference=_first_event_difference(
                    before.events,
                    after.events,
                ),
            )
        )

    return tuple(differences)


def compare_counterfactual(
    *,
    seed: int,
    days: int,
    schedule: Iterable[ScheduledIntervention] = (),
    population: int = 10,
) -> CounterfactualComparison:
    """Run same-seed branches and compare inferred trajectory effects."""
    if days < 0:
        raise ValueError("Counterfactual days cannot be negative")
    if population < 1:
        raise ValueError(
            "Counterfactual population must be at least one"
        )

    normalized_schedule = tuple(
        sorted(tuple(schedule), key=lambda item: item.day)
    )
    for item in normalized_schedule:
        if item.day >= days:
            raise ValueError(
                "Scheduled intervention day must be before "
                f"the final day: {item.day} >= {days}"
            )

    baseline_world = World(seed=seed, population=population)
    intervention_world = World(seed=seed, population=population)
    by_day: dict[int, list[ScheduledIntervention]] = {}
    for item in normalized_schedule:
        by_day.setdefault(item.day, []).append(item)

    first_divergence_day = None

    for day in range(days):
        for item in by_day.get(day, ()):
            intervention_world.create_intervention(
                kind=item.kind,
                target_id=item.target_id,
                theme=item.theme,
                suggested_action=item.suggested_action,
                strength=item.strength,
                location=item.location,
                duration=item.duration,
            )

        baseline_world.run(1)
        intervention_world.run(1)

        if (
            first_divergence_day is None
            and _trajectory_signature(baseline_world)
            != _trajectory_signature(intervention_world)
        ):
            first_divergence_day = baseline_world.day

    return CounterfactualComparison(
        seed=seed,
        days=days,
        population=population,
        schedule=normalized_schedule,
        first_divergence_day=first_divergence_day,
        agent_differences=_compare_agents(
            baseline_world,
            intervention_world,
        ),
        created_interventions=tuple(
            intervention_world.interventions
        ),
        intervention_responses=tuple(
            intervention_world.intervention_responses
        ),
        baseline_world=baseline_world,
        intervention_world=intervention_world,
    )
