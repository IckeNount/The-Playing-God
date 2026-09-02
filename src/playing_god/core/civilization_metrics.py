from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from playing_god.core.civilization import (
    PEER_TRAIN_KNOWLEDGE_ID,
    TRAINING_ACCESS_PROBLEM_ID,
)

if TYPE_CHECKING:
    from playing_god.core.world import World


@dataclass(frozen=True)
class Phase8Metrics:
    problem_recognition_day: int | None
    attempt_count: int
    successful_attempt_count: int
    rejected_attempt_count: int
    validation_day: int | None
    recognition_to_validation_days: int | None
    exposed_agent_ids: tuple[str, ...]
    exposed_agent_count: int
    adopting_agent_ids: tuple[str, ...]
    adopting_agent_count: int
    affordance_first_use_day: int | None
    peer_training_use_count: int
    institution_adoption_day: int | None
    current_opportunity_agent_ids: tuple[str, ...]
    current_opportunity_count: int


@dataclass(frozen=True)
class Phase8MetricComparison:
    discovery: Phase8Metrics
    counterfactual: Phase8Metrics
    skill_deltas: tuple[tuple[str, float], ...]
    total_skill_delta: float
    opportunity_count_delta: int


def build_phase8_metrics(world: World) -> Phase8Metrics:
    """Derive compact Phase 8 history without mutating the world."""
    recognition_days = [
        pressure.recognized_day
        for agent in world.agents
        for pressure in agent.discovery.pressures
        if pressure.id == TRAINING_ACCESS_PROBLEM_ID
        and pressure.recognized_day is not None
    ]
    attempts = tuple(
        attempt
        for agent in world.agents
        for attempt in agent.discovery.attempts
    )
    validation_days = [
        entry.creation_day
        for entry in world.civilization.knowledge
        if entry.id == PEER_TRAIN_KNOWLEDGE_ID
    ]
    recognition_day = min(recognition_days, default=None)
    validation_day = min(validation_days, default=None)
    exposed_agent_ids = tuple(sorted(
        agent.id
        for agent in world.agents
        if any(
            record.knowledge_id == PEER_TRAIN_KNOWLEDGE_ID
            and record.route != "discovery"
            for record in agent.knowledge.records
        )
    ))
    adopting_agent_ids = tuple(sorted(
        agent.id
        for agent in world.agents
        if any(
            record.knowledge_id == PEER_TRAIN_KNOWLEDGE_ID
            and record.response in {"accept", "modify"}
            for record in agent.knowledge.records
        )
    ))
    peer_training_days = [
        event.day
        for agent in world.agents
        for event in agent.events
        if event.kind == "peer_training"
        and event.description.startswith("Peer-trained ")
        and PEER_TRAIN_KNOWLEDGE_ID in event.description
    ]
    opportunity_agent_ids = tuple(
        agent.id
        for agent in sorted(world.living_agents(), key=lambda item: item.id)
        if world.peer_training_utility(agent) is not None
    )
    adoption = world.school.knowledge_adoption
    successful_attempt_count = sum(
        attempt.outcome == "validated"
        for attempt in attempts
    )
    return Phase8Metrics(
        problem_recognition_day=recognition_day,
        attempt_count=len(attempts),
        successful_attempt_count=successful_attempt_count,
        rejected_attempt_count=(
            len(attempts) - successful_attempt_count
        ),
        validation_day=validation_day,
        recognition_to_validation_days=(
            validation_day - recognition_day
            if recognition_day is not None and validation_day is not None
            else None
        ),
        exposed_agent_ids=exposed_agent_ids,
        exposed_agent_count=len(exposed_agent_ids),
        adopting_agent_ids=adopting_agent_ids,
        adopting_agent_count=len(adopting_agent_ids),
        affordance_first_use_day=min(peer_training_days, default=None),
        peer_training_use_count=len(peer_training_days),
        institution_adoption_day=(
            adoption.day if adoption is not None else None
        ),
        current_opportunity_agent_ids=opportunity_agent_ids,
        current_opportunity_count=len(opportunity_agent_ids),
    )


def compare_phase8_metrics(
    discovery: World,
    counterfactual: World,
) -> Phase8MetricComparison:
    """Compare shared agents after one controlled Phase 8 fork."""
    discovery_agents = {
        agent.id: agent
        for agent in discovery.agents
    }
    counterfactual_agents = {
        agent.id: agent
        for agent in counterfactual.agents
    }
    if set(discovery_agents) != set(counterfactual_agents):
        raise ValueError("Phase 8 comparison requires matching agents.")

    skill_deltas = tuple(
        (
            agent_id,
            round(
                discovery_agents[agent_id].skill
                - counterfactual_agents[agent_id].skill,
                6,
            ),
        )
        for agent_id in sorted(discovery_agents)
    )
    discovery_metrics = build_phase8_metrics(discovery)
    counterfactual_metrics = build_phase8_metrics(counterfactual)
    return Phase8MetricComparison(
        discovery=discovery_metrics,
        counterfactual=counterfactual_metrics,
        skill_deltas=skill_deltas,
        total_skill_delta=round(
            sum(agent.skill for agent in discovery_agents.values())
            - sum(
                agent.skill
                for agent in counterfactual_agents.values()
            ),
            6,
        ),
        opportunity_count_delta=(
            discovery_metrics.current_opportunity_count
            - counterfactual_metrics.current_opportunity_count
        ),
    )
