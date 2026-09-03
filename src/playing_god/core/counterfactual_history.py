from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from playing_god.core.causal_history import (
    CausalTrace,
    HistoricalEventReference,
    explicit_causal_references,
    trace_causal_descendants,
)
from playing_god.core.civilization_metrics import (
    Phase8MetricComparison,
    compare_phase8_metrics,
)
from playing_god.core.counterfactual import (
    AgentSnapshot,
    EventDifference,
    EventSnapshot,
    Phase8StateSnapshot,
    snapshot_agents,
    snapshot_phase8,
)
from playing_god.core.history import (
    HistoricalEpisode,
    extract_historical_episodes,
    resolve_source_event,
)
from playing_god.core.trajectory import (
    HistoricalTrajectoryComparison,
    compare_trajectories,
)

if TYPE_CHECKING:
    from playing_god.core.world import World


COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION = "counterfactual-history-v1"


@dataclass(frozen=True)
class PreForkEquivalence:
    fork_day: int
    baseline_agent_snapshot: tuple[AgentSnapshot, ...]
    counterfactual_agent_snapshot: tuple[AgentSnapshot, ...]
    baseline_phase8_snapshot: Phase8StateSnapshot
    counterfactual_phase8_snapshot: Phase8StateSnapshot
    trajectory: HistoricalTrajectoryComparison | None
    episodes_equal: bool
    causal_references_equal: bool
    rng_state_equal: bool
    world_context_equal: bool
    qualification_reasons: tuple[str, ...]

    @property
    def equivalent(self) -> bool:
        return not self.qualification_reasons


@dataclass(frozen=True)
class ReferencedEventDifference:
    reference: HistoricalEventReference
    difference: EventDifference


@dataclass(frozen=True)
class FirstObservedDivergence:
    day: int
    basis: str
    event_differences: tuple[ReferencedEventDifference, ...]
    trajectory_component_paths: tuple[str, ...]


@dataclass(frozen=True)
class BranchCausalEvidence:
    branch: str
    trace: CausalTrace

    @property
    def explicit_path_available(self) -> bool:
        return bool(self.trace.edges)


@dataclass(frozen=True)
class CounterfactualHistoricalComparison:
    analysis_version: str
    fork_day: int
    final_day: int
    pre_fork: PreForkEquivalence
    post_fork_trajectory: HistoricalTrajectoryComparison | None
    phase8_metrics: Phase8MetricComparison
    baseline_episodes: tuple[HistoricalEpisode, ...]
    counterfactual_episodes: tuple[HistoricalEpisode, ...]
    first_observed_divergence: FirstObservedDivergence | None
    causal_evidence: tuple[BranchCausalEvidence, ...]
    causal_path_notes: tuple[str, ...]
    baseline_continuity_valid: bool
    counterfactual_continuity_valid: bool
    qualification_warnings: tuple[str, ...]

    @property
    def valid_controlled_pair(self) -> bool:
        return (
            self.pre_fork.equivalent
            and self.baseline_continuity_valid
            and self.counterfactual_continuity_valid
        )

    @property
    def diverged(self) -> bool:
        return self.first_observed_divergence is not None


def _agent_ids(world: World) -> tuple[str, ...]:
    return tuple(sorted(agent.id for agent in world.agents))


def _configuration(world: World) -> tuple:
    return (
        world.seed,
        world.adaptive_cognition,
        world.reproduction_enabled,
        world.lifecycle_enabled,
        world.economy.job_capacity,
    )


def _world_context(world: World) -> tuple:
    return (
        world.economic_snapshot(),
        world.school_snapshot(),
        tuple(world.interventions),
        tuple(world.intervention_responses),
        tuple(world.information_items),
    )


def _pre_fork_equivalence(
    baseline: World,
    counterfactual: World,
    *,
    fork_day: int,
) -> PreForkEquivalence:
    baseline_agents = snapshot_agents(baseline)
    counterfactual_agents = snapshot_agents(counterfactual)
    baseline_phase8 = snapshot_phase8(baseline)
    counterfactual_phase8 = snapshot_phase8(counterfactual)
    reasons = []

    if baseline.day != fork_day or counterfactual.day != fork_day:
        reasons.append("pre_fork_world_day_mismatch")
    if _configuration(baseline) != _configuration(counterfactual):
        reasons.append("pre_fork_configuration_mismatch")
    if baseline_agents != counterfactual_agents:
        reasons.append("pre_fork_agent_snapshot_mismatch")
    if baseline_phase8 != counterfactual_phase8:
        reasons.append("pre_fork_phase8_snapshot_mismatch")
    if baseline.day == counterfactual.day:
        trajectory = compare_trajectories(baseline, counterfactual)
        if (
            not trajectory.equivalent
            or not trajectory.source_signatures_equal
        ):
            reasons.append("pre_fork_trajectory_mismatch")
    else:
        trajectory = None
        reasons.append("pre_fork_trajectory_window_mismatch")

    baseline_episodes = extract_historical_episodes(baseline)
    counterfactual_episodes = extract_historical_episodes(counterfactual)
    episodes_equal = baseline_episodes == counterfactual_episodes
    if not episodes_equal:
        reasons.append("pre_fork_episode_mismatch")
    causal_references_equal = (
        explicit_causal_references(baseline)
        == explicit_causal_references(counterfactual)
    )
    if not causal_references_equal:
        reasons.append("pre_fork_causal_reference_mismatch")
    rng_state_equal = baseline.rng.getstate() == counterfactual.rng.getstate()
    if not rng_state_equal:
        reasons.append("pre_fork_rng_state_mismatch")
    world_context_equal = _world_context(baseline) == _world_context(
        counterfactual
    )
    if not world_context_equal:
        reasons.append("pre_fork_world_context_mismatch")

    return PreForkEquivalence(
        fork_day=fork_day,
        baseline_agent_snapshot=baseline_agents,
        counterfactual_agent_snapshot=counterfactual_agents,
        baseline_phase8_snapshot=baseline_phase8,
        counterfactual_phase8_snapshot=counterfactual_phase8,
        trajectory=trajectory,
        episodes_equal=episodes_equal,
        causal_references_equal=causal_references_equal,
        rng_state_equal=rng_state_equal,
        world_context_equal=world_context_equal,
        qualification_reasons=tuple(reasons),
    )


def _event_snapshots(
    world: World,
    *,
    after_day: int,
) -> dict[HistoricalEventReference, EventSnapshot]:
    snapshots = snapshot_agents(world)
    return {
        HistoricalEventReference(agent.agent_id, index): event
        for agent in snapshots
        for index, event in enumerate(agent.events)
        if event.day > after_day
    }


def _event_differences(
    baseline: World,
    counterfactual: World,
    *,
    fork_day: int,
) -> tuple[ReferencedEventDifference, ...]:
    baseline_events = _event_snapshots(baseline, after_day=fork_day)
    counterfactual_events = _event_snapshots(
        counterfactual,
        after_day=fork_day,
    )
    differences = []
    for reference in sorted(set(baseline_events) | set(counterfactual_events)):
        first = baseline_events.get(reference)
        second = counterfactual_events.get(reference)
        if first == second:
            continue
        differences.append(ReferencedEventDifference(
            reference=reference,
            difference=EventDifference(
                event_index=reference.event_index,
                baseline=first,
                intervention=second,
            ),
        ))
    return tuple(sorted(
        differences,
        key=lambda item: (item.difference.day, item.reference),
    ))


def _post_fork_episodes(
    world: World,
    *,
    fork_day: int,
) -> tuple[HistoricalEpisode, ...]:
    return tuple(
        episode
        for episode in extract_historical_episodes(world)
        if any(
            resolve_source_event(world, reference).day > fork_day
            for reference in episode.source_event_references
        )
    )


def _history_continues_from(
    prefix: PreForkEquivalence,
    final_world: World,
    *,
    baseline: bool,
) -> bool:
    snapshots = (
        prefix.baseline_agent_snapshot
        if baseline
        else prefix.counterfactual_agent_snapshot
    )
    final_by_id = {
        item.agent_id: item
        for item in snapshot_agents(final_world)
    }
    return all(
        snapshot.agent_id in final_by_id
        and final_by_id[snapshot.agent_id].events[:len(snapshot.events)]
        == snapshot.events
        for snapshot in snapshots
    )


def _first_observed_divergence(
    event_differences: tuple[ReferencedEventDifference, ...],
    trajectory: HistoricalTrajectoryComparison | None,
    *,
    final_day: int,
) -> FirstObservedDivergence | None:
    component_paths = (
        ()
        if trajectory is None
        else tuple(
            item.path
            for item in trajectory.component_differences
        )
    )
    if event_differences:
        first_day = event_differences[0].difference.day
        return FirstObservedDivergence(
            day=first_day,
            basis="authoritative_event",
            event_differences=tuple(
                item
                for item in event_differences
                if item.difference.day == first_day
            ),
            trajectory_component_paths=component_paths,
        )
    if trajectory is not None and not trajectory.equivalent:
        return FirstObservedDivergence(
            day=final_day,
            basis="trajectory_endpoint",
            event_differences=(),
            trajectory_component_paths=component_paths,
        )
    return None


def _causal_evidence(
    baseline: World,
    counterfactual: World,
    divergence: FirstObservedDivergence | None,
) -> tuple[
    tuple[BranchCausalEvidence, ...],
    tuple[str, ...],
]:
    if divergence is None:
        return (), ()
    if not divergence.event_differences:
        return (), (
            "observed divergence, causal path unavailable: "
            "no differing source event",
        )

    evidence = []
    notes = []
    for item in divergence.event_differences:
        for branch, world, event in (
            ("baseline", baseline, item.difference.baseline),
            ("counterfactual", counterfactual, item.difference.intervention),
        ):
            if event is None:
                continue
            trace = trace_causal_descendants(world, item.reference)
            branch_evidence = BranchCausalEvidence(
                branch=branch,
                trace=trace,
            )
            evidence.append(branch_evidence)
            if not branch_evidence.explicit_path_available:
                notes.append(
                    "observed divergence, causal path unavailable: "
                    f"{branch}:{item.reference.agent_id}:"
                    f"{item.reference.event_index}"
                )
    return tuple(evidence), tuple(notes)


def compare_counterfactual_histories(
    baseline_pre_fork: World,
    counterfactual_pre_fork: World,
    baseline_world: World,
    counterfactual_world: World,
    *,
    fork_day: int,
) -> CounterfactualHistoricalComparison:
    """Compare a frozen shared prefix and two completed historical branches."""
    if isinstance(fork_day, bool) or not isinstance(fork_day, int):
        raise ValueError("Fork day must be an integer.")
    if fork_day < 0:
        raise ValueError("Fork day cannot be negative.")
    agent_ids = _agent_ids(baseline_pre_fork)
    if any(
        _agent_ids(world) != agent_ids
        for world in (
            counterfactual_pre_fork,
            baseline_world,
            counterfactual_world,
        )
    ):
        raise ValueError(
            "Counterfactual history requires matching agent identities."
        )
    if baseline_world.day != counterfactual_world.day:
        raise ValueError(
            "Counterfactual branches require the same analysis end day."
        )
    if baseline_world.day < fork_day:
        raise ValueError("Counterfactual history cannot end before the fork.")

    pre_fork = _pre_fork_equivalence(
        baseline_pre_fork,
        counterfactual_pre_fork,
        fork_day=fork_day,
    )
    warnings = list(pre_fork.qualification_reasons)
    continuity = {}
    for label, prefix, final, baseline in (
        ("baseline", baseline_pre_fork, baseline_world, True),
        (
            "counterfactual",
            counterfactual_pre_fork,
            counterfactual_world,
            False,
        ),
    ):
        configuration_valid = _configuration(prefix) == _configuration(final)
        history_valid = _history_continues_from(
            pre_fork,
            final,
            baseline=baseline,
        )
        continuity[label] = configuration_valid and history_valid
        if not configuration_valid:
            warnings.append(f"{label}_configuration_changed_after_prefix")
        if not history_valid:
            warnings.append(f"{label}_history_does_not_continue_prefix")

    post_fork_trajectory = (
        None
        if baseline_world.day == fork_day
        else compare_trajectories(
            baseline_world,
            counterfactual_world,
            baseline_start_day=fork_day + 1,
            comparison_start_day=fork_day + 1,
        )
    )
    if post_fork_trajectory is not None:
        warnings.extend(post_fork_trajectory.qualification_warnings)
    metrics = compare_phase8_metrics(baseline_world, counterfactual_world)
    baseline_episodes = _post_fork_episodes(
        baseline_world,
        fork_day=fork_day,
    )
    counterfactual_episodes = _post_fork_episodes(
        counterfactual_world,
        fork_day=fork_day,
    )
    event_differences = _event_differences(
        baseline_world,
        counterfactual_world,
        fork_day=fork_day,
    )
    divergence = _first_observed_divergence(
        event_differences,
        post_fork_trajectory,
        final_day=baseline_world.day,
    )
    causal_evidence, causal_notes = _causal_evidence(
        baseline_world,
        counterfactual_world,
        divergence,
    )

    return CounterfactualHistoricalComparison(
        analysis_version=COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION,
        fork_day=fork_day,
        final_day=baseline_world.day,
        pre_fork=pre_fork,
        post_fork_trajectory=post_fork_trajectory,
        phase8_metrics=metrics,
        baseline_episodes=baseline_episodes,
        counterfactual_episodes=counterfactual_episodes,
        first_observed_divergence=divergence,
        causal_evidence=causal_evidence,
        causal_path_notes=causal_notes,
        baseline_continuity_valid=continuity["baseline"],
        counterfactual_continuity_valid=continuity["counterfactual"],
        qualification_warnings=tuple(warnings),
    )
