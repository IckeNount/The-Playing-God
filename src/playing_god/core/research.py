from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, TYPE_CHECKING

from playing_god.core.causal_history import (
    CAUSAL_TRACE_ANALYSIS_VERSION,
    DEFAULT_MAX_TRACE_DEPTH,
    DEFAULT_MAX_TRACE_NODES,
    CausalTrace,
    HistoricalEventReference,
    trace_causal_ancestors,
    trace_causal_descendants,
)
from playing_god.core.civilization_metrics import Phase8MetricComparison
from playing_god.core.counterfactual import snapshot_agents, snapshot_phase8
from playing_god.core.counterfactual_history import (
    COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION,
    BranchCausalEvidence,
    FirstObservedDivergence,
    compare_counterfactual_histories,
)
from playing_god.core.history import (
    HISTORY_ANALYSIS_VERSION,
    HistoricalEpisode,
    extract_historical_episodes,
)
from playing_god.core.trajectory import (
    TRAJECTORY_ANALYSIS_VERSION,
    ComparisonWindow,
    HistoricalTrajectoryComparison,
    TrajectoryComponentComparison,
    compare_trajectories,
)
from playing_god.persistence.sqlite_store import SCHEMA_VERSION

if TYPE_CHECKING:
    from playing_god.core.world import World


RESEARCH_QUERY_ANALYSIS_VERSION = "research-query-v1"
RESEARCH_PACKET_ANALYSIS_VERSION = "research-packet-v1"
DEFAULT_MAX_EPISODES = 12
MAX_EPISODES = 64
MAX_TRAJECTORY_SUBJECTS = 8
DEFAULT_PACKET_EPISODES = 6
DEFAULT_PACKET_COMPONENTS = 12
DEFAULT_PACKET_CAUSAL_TRACES = 8
MAX_PACKET_COMPONENTS = 64
MAX_PACKET_CAUSAL_TRACES = 32


@dataclass(frozen=True)
class ResearchProvenance:
    analysis_version: str
    seed: int
    observed_day: int
    schema_version: int
    agent_ids: tuple[str, ...]
    source_fingerprint: str


@dataclass(frozen=True)
class EpisodeQueryResult:
    provenance: ResearchProvenance
    window: ComparisonWindow
    subject_agent_id: str | None
    episodes: tuple[HistoricalEpisode, ...]
    total_matching_episodes: int
    configured_max_episodes: int

    @property
    def truncated(self) -> bool:
        return len(self.episodes) < self.total_matching_episodes


@dataclass(frozen=True)
class CausalQueryResult:
    provenance: ResearchProvenance
    trace: CausalTrace


@dataclass(frozen=True)
class TrajectoryQueryResult:
    baseline_provenance: ResearchProvenance
    comparison_provenance: ResearchProvenance
    comparison: HistoricalTrajectoryComparison


@dataclass(frozen=True)
class ResearchPacketSelection:
    configured_max_episodes_per_branch: int
    configured_max_components: int
    configured_max_causal_traces: int
    baseline_episode_count: int
    counterfactual_episode_count: int
    trajectory_component_count: int
    causal_trace_count: int
    baseline_episodes_truncated: bool
    counterfactual_episodes_truncated: bool
    trajectory_components_truncated: bool
    causal_traces_truncated: bool


@dataclass(frozen=True)
class CounterfactualResearchPacket:
    packet_id: str
    analysis_version: str
    question: str
    source_analysis_versions: tuple[str, ...]
    fork_day: int
    final_day: int
    baseline_pre_fork_provenance: ResearchProvenance
    counterfactual_pre_fork_provenance: ResearchProvenance
    baseline_provenance: ResearchProvenance
    counterfactual_provenance: ResearchProvenance
    valid_controlled_pair: bool
    first_observed_divergence: FirstObservedDivergence | None
    explanation: str
    phase8_metrics: Phase8MetricComparison
    trajectory_aggregate_distance: float | None
    trajectory_components: tuple[TrajectoryComponentComparison, ...]
    baseline_episodes: tuple[HistoricalEpisode, ...]
    counterfactual_episodes: tuple[HistoricalEpisode, ...]
    causal_evidence: tuple[BranchCausalEvidence, ...]
    source_event_references: tuple[HistoricalEventReference, ...]
    qualification_warnings: tuple[str, ...]
    selection: ResearchPacketSelection


def _validate_limit(
    name: str,
    value: int,
    maximum: int,
    *,
    minimum: int = 1,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be within [{minimum}, {maximum}]"
        )


def _world_fingerprint(world: World) -> str:
    payload = (
        RESEARCH_QUERY_ANALYSIS_VERSION,
        world.seed,
        world.day,
        world.adaptive_cognition,
        world.reproduction_enabled,
        world.lifecycle_enabled,
        world.economy.job_capacity,
        snapshot_agents(world),
        snapshot_phase8(world),
        world.economic_snapshot(),
        world.school_snapshot(),
        tuple(world.interventions),
        tuple(world.intervention_responses),
        tuple(world.information_items),
        world.rng.getstate(),
    )
    digest = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    return f"world:{RESEARCH_QUERY_ANALYSIS_VERSION}:{digest}"


def research_provenance(world: World) -> ResearchProvenance:
    """Identify one observed world without creating authoritative state."""
    return ResearchProvenance(
        analysis_version=RESEARCH_QUERY_ANALYSIS_VERSION,
        seed=world.seed,
        observed_day=world.day,
        schema_version=SCHEMA_VERSION,
        agent_ids=tuple(sorted(agent.id for agent in world.agents)),
        source_fingerprint=_world_fingerprint(world),
    )


def query_historical_episodes(
    world: World,
    *,
    subject_agent_id: str | None = None,
    start_day: int = 0,
    end_day: int | None = None,
    max_episodes: int = DEFAULT_MAX_EPISODES,
) -> EpisodeQueryResult:
    """Return bounded episodes overlapping an inclusive research window."""
    _validate_limit("max_episodes", max_episodes, MAX_EPISODES)
    window = ComparisonWindow(
        start_day=start_day,
        end_day=world.day if end_day is None else end_day,
    )
    if window.end_day > world.day:
        raise ValueError("Episode query cannot extend beyond the observed day.")
    agent_ids = {agent.id for agent in world.agents}
    if subject_agent_id is not None and subject_agent_id not in agent_ids:
        raise ValueError(f"Unknown research subject: {subject_agent_id}")

    matches = tuple(
        episode
        for episode in extract_historical_episodes(world)
        if episode.end_day >= window.start_day
        and episode.start_day <= window.end_day
        and (
            subject_agent_id is None
            or subject_agent_id in episode.participating_agent_ids
        )
    )
    return EpisodeQueryResult(
        provenance=research_provenance(world),
        window=window,
        subject_agent_id=subject_agent_id,
        episodes=matches[:max_episodes],
        total_matching_episodes=len(matches),
        configured_max_episodes=max_episodes,
    )


def query_causal_history(
    world: World,
    root: HistoricalEventReference,
    *,
    direction: str,
    max_depth: int = 8,
    max_nodes: int = 64,
) -> CausalQueryResult:
    """Return one bounded explicit-causality trace with world provenance."""
    _validate_limit(
        "max_depth",
        max_depth,
        DEFAULT_MAX_TRACE_DEPTH,
        minimum=0,
    )
    _validate_limit("max_nodes", max_nodes, DEFAULT_MAX_TRACE_NODES)
    if direction == "ancestors":
        trace = trace_causal_ancestors(
            world,
            root,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
    elif direction == "descendants":
        trace = trace_causal_descendants(
            world,
            root,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
    else:
        raise ValueError(f"Unknown causal trace direction: {direction}")
    return CausalQueryResult(
        provenance=research_provenance(world),
        trace=trace,
    )


def _query_subject_ids(
    world: World,
    agent_ids: Iterable[str] | None,
) -> tuple[str, ...]:
    selected = (
        tuple(sorted(agent.id for agent in world.agents))
        if agent_ids is None
        else tuple(agent_ids)
    )
    if len(selected) > MAX_TRAJECTORY_SUBJECTS:
        raise ValueError(
            "Research trajectory queries support at most "
            f"{MAX_TRAJECTORY_SUBJECTS} subjects; select a subset."
        )
    return selected


def query_trajectory_comparison(
    baseline_world: World,
    comparison_world: World,
    *,
    baseline_start_day: int = 0,
    comparison_start_day: int = 0,
    baseline_agent_ids: Iterable[str] | None = None,
    comparison_agent_ids: Iterable[str] | None = None,
) -> TrajectoryQueryResult:
    """Compare bounded subject sets through the existing Phase 9C analysis."""
    baseline_ids = _query_subject_ids(baseline_world, baseline_agent_ids)
    comparison_ids = _query_subject_ids(
        comparison_world,
        comparison_agent_ids,
    )
    comparison = compare_trajectories(
        baseline_world,
        comparison_world,
        baseline_start_day=baseline_start_day,
        comparison_start_day=comparison_start_day,
        baseline_agent_ids=baseline_ids,
        comparison_agent_ids=comparison_ids,
    )
    return TrajectoryQueryResult(
        baseline_provenance=research_provenance(baseline_world),
        comparison_provenance=research_provenance(comparison_world),
        comparison=comparison,
    )


def _limit_divergence(
    divergence: FirstObservedDivergence | None,
    *,
    max_components: int,
    max_causal_traces: int,
) -> FirstObservedDivergence | None:
    if divergence is None:
        return None
    return FirstObservedDivergence(
        day=divergence.day,
        basis=divergence.basis,
        event_differences=(
            divergence.event_differences[:max_causal_traces]
        ),
        trajectory_component_paths=(
            divergence.trajectory_component_paths[:max_components]
        ),
    )


def _packet_references(
    divergence: FirstObservedDivergence | None,
    baseline_episodes: tuple[HistoricalEpisode, ...],
    counterfactual_episodes: tuple[HistoricalEpisode, ...],
    causal_evidence: tuple[BranchCausalEvidence, ...],
) -> tuple[HistoricalEventReference, ...]:
    references = {
        reference
        for episode in baseline_episodes + counterfactual_episodes
        for reference in episode.source_event_references
    }
    if divergence is not None:
        references.update(
            item.reference
            for item in divergence.event_differences
        )
    references.update(
        node.reference
        for item in causal_evidence
        for node in item.trace.nodes
    )
    return tuple(sorted(references))


def _packet_id(parts: tuple) -> str:
    digest = hashlib.sha256(repr(parts).encode("utf-8")).hexdigest()
    return f"research-packet:{RESEARCH_PACKET_ANALYSIS_VERSION}:{digest}"


def build_counterfactual_research_packet(
    baseline_pre_fork: World,
    counterfactual_pre_fork: World,
    baseline_world: World,
    counterfactual_world: World,
    *,
    fork_day: int,
    max_episodes_per_branch: int = DEFAULT_PACKET_EPISODES,
    max_components: int = DEFAULT_PACKET_COMPONENTS,
    max_causal_traces: int = DEFAULT_PACKET_CAUSAL_TRACES,
) -> CounterfactualResearchPacket:
    """Compose one compact packet from the existing Phase 9 analyses."""
    _validate_limit(
        "max_episodes_per_branch",
        max_episodes_per_branch,
        MAX_EPISODES,
    )
    _validate_limit(
        "max_components",
        max_components,
        MAX_PACKET_COMPONENTS,
    )
    _validate_limit(
        "max_causal_traces",
        max_causal_traces,
        MAX_PACKET_CAUSAL_TRACES,
    )
    comparison = compare_counterfactual_histories(
        baseline_pre_fork,
        counterfactual_pre_fork,
        baseline_world,
        counterfactual_world,
        fork_day=fork_day,
    )
    trajectory_differences = (
        ()
        if comparison.post_fork_trajectory is None
        else comparison.post_fork_trajectory.component_differences
    )
    baseline_episodes = comparison.baseline_episodes[
        :max_episodes_per_branch
    ]
    counterfactual_episodes = comparison.counterfactual_episodes[
        :max_episodes_per_branch
    ]
    trajectory_components = trajectory_differences[:max_components]
    causal_evidence = comparison.causal_evidence[:max_causal_traces]
    divergence = _limit_divergence(
        comparison.first_observed_divergence,
        max_components=max_components,
        max_causal_traces=max_causal_traces,
    )
    selection = ResearchPacketSelection(
        configured_max_episodes_per_branch=max_episodes_per_branch,
        configured_max_components=max_components,
        configured_max_causal_traces=max_causal_traces,
        baseline_episode_count=len(comparison.baseline_episodes),
        counterfactual_episode_count=len(comparison.counterfactual_episodes),
        trajectory_component_count=len(trajectory_differences),
        causal_trace_count=len(comparison.causal_evidence),
        baseline_episodes_truncated=(
            len(baseline_episodes) < len(comparison.baseline_episodes)
        ),
        counterfactual_episodes_truncated=(
            len(counterfactual_episodes)
            < len(comparison.counterfactual_episodes)
        ),
        trajectory_components_truncated=(
            len(trajectory_components) < len(trajectory_differences)
        ),
        causal_traces_truncated=(
            len(causal_evidence) < len(comparison.causal_evidence)
        ),
    )
    warnings = list(comparison.qualification_warnings)
    for truncated, label in (
        (selection.baseline_episodes_truncated, "baseline episodes"),
        (
            selection.counterfactual_episodes_truncated,
            "counterfactual episodes",
        ),
        (selection.trajectory_components_truncated, "trajectory components"),
        (selection.causal_traces_truncated, "causal traces"),
    ):
        if truncated:
            warnings.append(f"research packet truncated {label}")

    provenances = tuple(
        research_provenance(world)
        for world in (
            baseline_pre_fork,
            counterfactual_pre_fork,
            baseline_world,
            counterfactual_world,
        )
    )
    references = _packet_references(
        divergence,
        baseline_episodes,
        counterfactual_episodes,
        causal_evidence,
    )
    explanation = (
        f"No post-fork divergence was observed through day {comparison.final_day}."
        if divergence is None
        else (
            f"First observed divergence appears on day {divergence.day} "
            f"in {divergence.basis.replace('_', ' ')} evidence."
        )
    )
    packet_id = _packet_id((
        fork_day,
        tuple(item.source_fingerprint for item in provenances),
        references,
        selection,
    ))

    return CounterfactualResearchPacket(
        packet_id=packet_id,
        analysis_version=RESEARCH_PACKET_ANALYSIS_VERSION,
        question="counterfactual_historical_divergence",
        source_analysis_versions=(
            HISTORY_ANALYSIS_VERSION,
            CAUSAL_TRACE_ANALYSIS_VERSION,
            TRAJECTORY_ANALYSIS_VERSION,
            COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION,
        ),
        fork_day=fork_day,
        final_day=comparison.final_day,
        baseline_pre_fork_provenance=provenances[0],
        counterfactual_pre_fork_provenance=provenances[1],
        baseline_provenance=provenances[2],
        counterfactual_provenance=provenances[3],
        valid_controlled_pair=comparison.valid_controlled_pair,
        first_observed_divergence=divergence,
        explanation=explanation,
        phase8_metrics=comparison.phase8_metrics,
        trajectory_aggregate_distance=(
            None
            if comparison.post_fork_trajectory is None
            else comparison.post_fork_trajectory.aggregate_distance
        ),
        trajectory_components=trajectory_components,
        baseline_episodes=baseline_episodes,
        counterfactual_episodes=counterfactual_episodes,
        causal_evidence=causal_evidence,
        source_event_references=references,
        qualification_warnings=tuple(warnings),
        selection=selection,
    )
