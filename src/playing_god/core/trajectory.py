from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
from typing import Iterable

from playing_god.core.adaptive import ActionValue
from playing_god.core.agent import Agent
from playing_god.core.counterfactual import trajectory_signature
from playing_god.core.world import World


TRAJECTORY_ANALYSIS_VERSION = "trajectory-comparison-v1"

EXACT = "exact"
BOUNDED_01 = "bounded_0_1"
BOUNDED_SIGNED = "bounded_minus1_1"
RELATIVE = "symmetric_relative"
FREQUENCY = "frequency_distribution"


@dataclass(frozen=True)
class ComparisonWindow:
    """Inclusive simulated-day window ending at the observed world state."""

    start_day: int
    end_day: int

    def __post_init__(self) -> None:
        if self.start_day < 0:
            raise ValueError("Trajectory window cannot start before day zero.")
        if self.end_day < self.start_day:
            raise ValueError("Trajectory window end cannot precede its start.")

    @property
    def day_count(self) -> int:
        return self.end_day - self.start_day + 1

    def contains(self, day: int) -> bool:
        return self.start_day <= day <= self.end_day


@dataclass(frozen=True)
class TrajectoryObservation:
    """One observed value, or an explicit statement that it is unavailable."""

    available: bool
    value: object = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.available and self.reason is not None:
            raise ValueError(
                "Observed trajectory values cannot have a missing reason."
            )
        if not self.available and not self.reason:
            raise ValueError("Missing trajectory values require a reason.")

    @classmethod
    def observed(cls, value: object) -> TrajectoryObservation:
        return cls(available=True, value=value)

    @classmethod
    def missing(cls, reason: str) -> TrajectoryObservation:
        return cls(available=False, reason=reason)


@dataclass(frozen=True)
class TrajectoryComponent:
    path: str
    category: str
    normalization: str
    observation: TrajectoryObservation


@dataclass(frozen=True)
class HistoricalTrajectorySignature:
    """A named, window-qualified projection of the Phase 8G signature."""

    analysis_version: str
    window: ComparisonWindow
    source_day: int
    source_agent_ids: tuple[str, ...]
    components: tuple[TrajectoryComponent, ...]
    phase8_signature: tuple = field(repr=False)


@dataclass(frozen=True)
class TrajectoryComponentComparison:
    path: str
    category: str
    normalization: str
    baseline: TrajectoryObservation
    comparison: TrajectoryObservation
    normalized_distance: float | None

    @property
    def differs(self) -> bool:
        if self.baseline.available != self.comparison.available:
            return True
        if not self.baseline.available:
            return self.baseline.reason != self.comparison.reason
        return self.baseline.value != self.comparison.value


@dataclass(frozen=True)
class HistoricalTrajectoryComparison:
    analysis_version: str
    baseline_window: ComparisonWindow
    comparison_window: ComparisonWindow
    baseline_agent_ids: tuple[str, ...]
    comparison_agent_ids: tuple[str, ...]
    component_results: tuple[TrajectoryComponentComparison, ...]
    aggregate_distance: float | None
    source_signatures_equal: bool
    qualification_warnings: tuple[str, ...]

    @property
    def component_differences(
        self,
    ) -> tuple[TrajectoryComponentComparison, ...]:
        return tuple(item for item in self.component_results if item.differs)

    @property
    def equivalent(self) -> bool:
        return not self.component_differences


def _component(
    path: str,
    category: str,
    normalization: str,
    value: object,
) -> TrajectoryComponent:
    return TrajectoryComponent(
        path=path,
        category=category,
        normalization=normalization,
        observation=TrajectoryObservation.observed(value),
    )


def _missing_component(
    path: str,
    category: str,
    normalization: str,
    reason: str,
) -> TrajectoryComponent:
    return TrajectoryComponent(
        path=path,
        category=category,
        normalization=normalization,
        observation=TrajectoryObservation.missing(reason),
    )


def _in_window(
    items: Iterable[object],
    window: ComparisonWindow,
    *,
    day_field: str = "day",
) -> tuple:
    return tuple(
        item
        for item in items
        if window.contains(getattr(item, day_field))
    )


def _adaptive_train_value(agent: Agent) -> ActionValue | None:
    return agent.adaptive_values.get("improve_skill", {}).get("train")


def _agent_components(
    agent: Agent,
    *,
    subject_index: int,
    window: ComparisonWindow,
) -> list[TrajectoryComponent]:
    prefix = f"subjects.{subject_index}"
    events = _in_window(agent.events, window)
    observations = _in_window(agent.observations, window)
    prayers = _in_window(agent.prayers, window, day_field="timestamp")
    attributions = _in_window(agent.attributions, window)
    development = _in_window(agent.development.records, window)
    knowledge = _in_window(agent.knowledge.records, window)
    attempts = _in_window(agent.discovery.attempts, window)
    event_kinds = tuple(sorted(Counter(item.kind for item in events).items()))
    components = [
        _component(f"{prefix}.age", "life_context", RELATIVE, agent.age),
        _component(
            f"{prefix}.generation",
            "life_context",
            RELATIVE,
            agent.family.generation,
        ),
        _component(
            f"{prefix}.traits",
            "life_context",
            EXACT,
            tuple(sorted(agent.traits.items())),
        ),
        _component(
            f"{prefix}.sins",
            "life_context",
            EXACT,
            tuple(sorted(agent.sins.items())),
        ),
        _component(
            f"{prefix}.skill",
            "capability",
            BOUNDED_01,
            agent.skill,
        ),
        _component(f"{prefix}.money", "resources", RELATIVE, agent.money),
        _component(
            f"{prefix}.employed",
            "opportunity",
            EXACT,
            agent.employed,
        ),
        _component(f"{prefix}.salary", "resources", RELATIVE, agent.salary),
        _component(
            f"{prefix}.job_level",
            "opportunity",
            RELATIVE,
            agent.job_level,
        ),
        _component(f"{prefix}.energy", "wellbeing", BOUNDED_01, agent.energy),
        _component(
            f"{prefix}.social_energy",
            "wellbeing",
            BOUNDED_01,
            agent.social_energy,
        ),
        _component(
            f"{prefix}.stress",
            "wellbeing",
            BOUNDED_01,
            agent.stress,
        ),
        _component(
            f"{prefix}.reputation",
            "social",
            BOUNDED_SIGNED,
            agent.reputation,
        ),
        _component(
            f"{prefix}.faith",
            "belief_culture",
            BOUNDED_01,
            agent.faith,
        ),
        _component(f"{prefix}.goal", "belief_culture", EXACT, agent.goal),
        _component(
            f"{prefix}.relationships",
            "social",
            EXACT,
            tuple(sorted(agent.relationships.items())),
        ),
        _component(
            f"{prefix}.beliefs",
            "belief_culture",
            EXACT,
            tuple(sorted(agent.beliefs.items())),
        ),
        _component(
            f"{prefix}.observations.count",
            "history",
            RELATIVE,
            len(observations),
        ),
        _component(
            f"{prefix}.prayers.count",
            "history",
            RELATIVE,
            len(prayers),
        ),
        _component(
            f"{prefix}.attributions.count",
            "history",
            RELATIVE,
            len(attributions),
        ),
        _component(
            f"{prefix}.events.count",
            "history",
            RELATIVE,
            len(events),
        ),
        _component(
            f"{prefix}.events.kind_frequencies",
            "history",
            FREQUENCY,
            event_kinds,
        ),
        _component(
            f"{prefix}.current_location",
            "opportunity",
            EXACT,
            agent.current_location,
        ),
        _component(
            f"{prefix}.destination",
            "opportunity",
            EXACT,
            agent.destination,
        ),
        _component(
            f"{prefix}.lifecycle",
            "life_context",
            EXACT,
            agent.lifecycle,
        ),
        _component(f"{prefix}.culture", "belief_culture", EXACT, agent.culture),
        _component(
            f"{prefix}.knowledge",
            "civilization",
            EXACT,
            agent.knowledge,
        ),
        _component(
            f"{prefix}.discovery",
            "civilization",
            EXACT,
            agent.discovery,
        ),
        _component(
            f"{prefix}.knowledge_exposures.count",
            "civilization",
            RELATIVE,
            len(knowledge),
        ),
        _component(
            f"{prefix}.discovery_attempts.count",
            "civilization",
            RELATIVE,
            len(attempts),
        ),
        _component(
            f"{prefix}.validated_discoveries.count",
            "civilization",
            RELATIVE,
            sum(item.outcome == "validated" for item in attempts),
        ),
    ]

    if window.start_day == 0:
        components.append(
            _component(
                f"{prefix}.actions",
                "activity",
                EXACT,
                tuple(sorted(agent.actions.items())),
            )
        )
    else:
        components.append(
            _missing_component(
                f"{prefix}.actions",
                "activity",
                EXACT,
                "action counters are not timestamped",
            )
        )

    if development:
        components.extend((
            _component(
                f"{prefix}.development.checkpoints",
                "institution_access",
                RELATIVE,
                len(development),
            ),
            _component(
                f"{prefix}.development.school_access_rate",
                "institution_access",
                BOUNDED_01,
                sum(item.school_access for item in development)
                / len(development),
            ),
            _component(
                f"{prefix}.development.mean_school_opportunity",
                "institution_access",
                BOUNDED_01,
                sum(item.school_opportunity for item in development)
                / len(development),
            ),
            _component(
                f"{prefix}.development.skill_gain",
                "capability",
                BOUNDED_01,
                sum(item.skill_gain for item in development),
            ),
        ))
    else:
        reason = "no developmental checkpoint observed in this window"
        components.extend(
            _missing_component(path, category, normalization, reason)
            for path, category, normalization in (
                (
                    f"{prefix}.development.checkpoints",
                    "institution_access",
                    RELATIVE,
                ),
                (
                    f"{prefix}.development.school_access_rate",
                    "institution_access",
                    BOUNDED_01,
                ),
                (
                    f"{prefix}.development.mean_school_opportunity",
                    "institution_access",
                    BOUNDED_01,
                ),
                (f"{prefix}.development.skill_gain", "capability", BOUNDED_01),
            )
        )

    adaptive = _adaptive_train_value(agent)
    if adaptive is None:
        components.extend((
            _missing_component(
                f"{prefix}.adaptive.train_observations",
                "learning",
                RELATIVE,
                "no learned training value was observed",
            ),
            _missing_component(
                f"{prefix}.adaptive.train_mean_feedback",
                "learning",
                BOUNDED_SIGNED,
                "no learned training value was observed",
            ),
        ))
    else:
        components.extend((
            _component(
                f"{prefix}.adaptive.train_observations",
                "learning",
                RELATIVE,
                adaptive.observations,
            ),
            _component(
                f"{prefix}.adaptive.train_mean_feedback",
                "learning",
                BOUNDED_SIGNED,
                adaptive.mean_feedback,
            ),
        ))

    return components


def build_trajectory_signature(
    world: World,
    *,
    start_day: int = 0,
    end_day: int | None = None,
    agent_ids: Iterable[str] | None = None,
) -> HistoricalTrajectorySignature:
    """Canonize a Phase 8G signature into named historical components."""
    window = ComparisonWindow(
        start_day=start_day,
        end_day=world.day if end_day is None else end_day,
    )
    if window.end_day != world.day:
        raise ValueError(
            "Trajectory endpoint must equal the observed world day; "
            "past state is not reconstructed from later state."
        )

    agents_by_id = {agent.id: agent for agent in world.agents}
    selected_ids = (
        tuple(sorted(agents_by_id))
        if agent_ids is None
        else tuple(agent_ids)
    )
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Trajectory agent IDs must be unique.")
    unknown = tuple(
        agent_id
        for agent_id in selected_ids
        if agent_id not in agents_by_id
    )
    if unknown:
        raise ValueError(f"Unknown trajectory agent IDs: {', '.join(unknown)}")

    school_evidence = _in_window(world.school.knowledge_evidence, window)
    components = [
        _component(
            "world.civilization",
            "civilization",
            EXACT,
            world.civilization,
        ),
        _component(
            "world.school.knowledge_evidence",
            "institution_access",
            EXACT,
            school_evidence,
        ),
        _component(
            "world.school.knowledge_adoption",
            "institution_access",
            EXACT,
            world.school.knowledge_adoption,
        ),
    ]
    for index, agent_id in enumerate(selected_ids):
        components.extend(_agent_components(
            agents_by_id[agent_id],
            subject_index=index,
            window=window,
        ))

    return HistoricalTrajectorySignature(
        analysis_version=TRAJECTORY_ANALYSIS_VERSION,
        window=window,
        source_day=world.day,
        source_agent_ids=selected_ids,
        components=tuple(components),
        phase8_signature=trajectory_signature(world, agent_ids=selected_ids),
    )


def _normalized_distance(
    baseline: object,
    comparison: object,
    normalization: str,
) -> float:
    if baseline == comparison:
        return 0.0
    if normalization == EXACT:
        return 1.0
    if normalization == FREQUENCY:
        first = dict(baseline)
        second = dict(comparison)
        keys = set(first) | set(second)
        difference = sum(
            abs(first.get(key, 0) - second.get(key, 0))
            for key in keys
        )
        total = sum(first.values()) + sum(second.values())
        return difference / max(total, 1)
    if isinstance(baseline, bool) or isinstance(comparison, bool):
        raise ValueError(
            "Boolean trajectory values require exact normalization."
        )
    if (
        not isinstance(baseline, (int, float))
        or not isinstance(comparison, (int, float))
    ):
        raise ValueError(
            "Numeric normalization requires numeric trajectory values."
        )
    first = float(baseline)
    second = float(comparison)
    if not math.isfinite(first) or not math.isfinite(second):
        raise ValueError("Trajectory values must be finite.")
    if normalization == BOUNDED_01:
        return min(1.0, abs(first - second))
    if normalization == BOUNDED_SIGNED:
        return min(1.0, abs(first - second) / 2.0)
    if normalization == RELATIVE:
        return min(
            1.0,
            abs(first - second) / max(abs(first), abs(second), 1.0),
        )
    raise ValueError(f"Unknown trajectory normalization: {normalization}")


def compare_trajectory_signatures(
    baseline: HistoricalTrajectorySignature,
    comparison: HistoricalTrajectorySignature,
) -> HistoricalTrajectoryComparison:
    """Compare two signatures without consulting or changing either world."""
    if baseline.analysis_version != comparison.analysis_version:
        raise ValueError("Trajectory analysis versions must match.")
    if baseline.window.day_count != comparison.window.day_count:
        raise ValueError("Trajectory comparison windows must have equal day counts.")
    if len(baseline.source_agent_ids) != len(comparison.source_agent_ids):
        raise ValueError("Trajectory comparisons require equal subject counts.")
    baseline_keys = tuple(
        (item.path, item.category, item.normalization)
        for item in baseline.components
    )
    comparison_keys = tuple(
        (item.path, item.category, item.normalization)
        for item in comparison.components
    )
    if baseline_keys != comparison_keys:
        raise ValueError("Trajectory signatures do not expose matching components.")

    results = []
    warnings = []
    distances = []
    for first, second in zip(
        baseline.components,
        comparison.components,
        strict=True,
    ):
        if first.observation.available and second.observation.available:
            distance = _normalized_distance(
                first.observation.value,
                second.observation.value,
                first.normalization,
            )
            distances.append(distance)
        else:
            distance = None
            if first.observation != second.observation:
                warnings.append(
                    f"{first.path}: source completeness differs"
                )
        results.append(
            TrajectoryComponentComparison(
                path=first.path,
                category=first.category,
                normalization=first.normalization,
                baseline=first.observation,
                comparison=second.observation,
                normalized_distance=distance,
            )
        )

    return HistoricalTrajectoryComparison(
        analysis_version=baseline.analysis_version,
        baseline_window=baseline.window,
        comparison_window=comparison.window,
        baseline_agent_ids=baseline.source_agent_ids,
        comparison_agent_ids=comparison.source_agent_ids,
        component_results=tuple(results),
        aggregate_distance=(
            sum(distances) / len(distances)
            if distances
            else None
        ),
        source_signatures_equal=(
            baseline.phase8_signature == comparison.phase8_signature
        ),
        qualification_warnings=tuple(warnings),
    )


def compare_trajectories(
    baseline_world: World,
    comparison_world: World,
    *,
    baseline_start_day: int = 0,
    comparison_start_day: int = 0,
    baseline_agent_ids: Iterable[str] | None = None,
    comparison_agent_ids: Iterable[str] | None = None,
) -> HistoricalTrajectoryComparison:
    """Build and compare equal-duration endpoint trajectory signatures."""
    baseline = build_trajectory_signature(
        baseline_world,
        start_day=baseline_start_day,
        agent_ids=baseline_agent_ids,
    )
    comparison = build_trajectory_signature(
        comparison_world,
        start_day=comparison_start_day,
        agent_ids=comparison_agent_ids,
    )
    return compare_trajectory_signatures(baseline, comparison)
