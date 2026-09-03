from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.world import World


CAUSAL_TRACE_ANALYSIS_VERSION = "causal-trace-v1"
DEFAULT_MAX_TRACE_DEPTH = 32
DEFAULT_MAX_TRACE_NODES = 256
TRACE_DIRECTIONS = frozenset({"ancestors", "descendants"})


@dataclass(frozen=True, order=True)
class HistoricalEventReference:
    """Stable reference to one authoritative per-agent event."""

    agent_id: str
    event_index: int


@dataclass(frozen=True, order=True)
class ExplicitCausalReference:
    """One existing structured causal relation between source events."""

    cause: HistoricalEventReference
    effect: HistoricalEventReference
    relation: str


@dataclass(frozen=True)
class UnresolvedCausalReference:
    """An explicit relation whose source history is missing or ambiguous."""

    cause: HistoricalEventReference | None
    effect: HistoricalEventReference | None
    relation: str
    reason: str


@dataclass(frozen=True, order=True)
class CausalTraceNode:
    depth: int
    reference: HistoricalEventReference


@dataclass(frozen=True, order=True)
class CausalTraceBoundary:
    reference: HistoricalEventReference
    reason: str


@dataclass(frozen=True)
class CausalTraceProvenance:
    analysis_version: str = CAUSAL_TRACE_ANALYSIS_VERSION
    event_identity: str = "agent_id,event_index"
    source: str = "authoritative structured simulation history"


@dataclass(frozen=True)
class CausalTrace:
    root: HistoricalEventReference
    direction: str
    nodes: tuple[CausalTraceNode, ...]
    edges: tuple[ExplicitCausalReference, ...]
    unresolved_references: tuple[UnresolvedCausalReference, ...]
    cycle_edges: tuple[ExplicitCausalReference, ...]
    boundaries: tuple[CausalTraceBoundary, ...]
    configured_max_depth: int
    configured_max_nodes: int
    provenance: CausalTraceProvenance

    @property
    def causal_depth(self) -> int:
        return max((item.depth for item in self.nodes), default=0)

    @property
    def reachable_count(self) -> int:
        return max(0, len(self.nodes) - 1)

    @property
    def explicit_chain_length(self) -> int:
        return len(self.edges)

    @property
    def branch_count(self) -> int:
        effects_by_cause = Counter(edge.cause for edge in self.edges)
        return sum(count > 1 for count in effects_by_cause.values())

    @property
    def corrupt(self) -> bool:
        return bool(self.cycle_edges)

    @property
    def truncated(self) -> bool:
        return bool(self.boundaries)


@dataclass(frozen=True)
class _CausalEvidence:
    event_references: frozenset[HistoricalEventReference]
    edges: tuple[ExplicitCausalReference, ...]
    unresolved: tuple[UnresolvedCausalReference, ...]


def _unresolved_key(item: UnresolvedCausalReference) -> tuple:
    return (
        item.cause is None,
        item.cause or HistoricalEventReference("", -1),
        item.effect is None,
        item.effect or HistoricalEventReference("", -1),
        item.relation,
        item.reason,
    )


def _event_references(world: World) -> frozenset[HistoricalEventReference]:
    return frozenset(
        HistoricalEventReference(agent.id, event_index)
        for agent in world.agents
        for event_index, _ in enumerate(agent.events)
    )


def _knowledge_parent_from_description(
    description: str,
) -> HistoricalEventReference | None:
    marker = "adoption parent: "
    if marker not in description:
        return None
    value = description.split(marker, 1)[1].split(";", 1)[0]
    try:
        agent_id, event_index = value.rsplit(":", 1)
        return HistoricalEventReference(agent_id, int(event_index))
    except (ValueError, TypeError):
        return None


def _collect_causal_evidence(world: World) -> _CausalEvidence:
    valid_references = _event_references(world)
    edges: set[ExplicitCausalReference] = set()
    unresolved: set[UnresolvedCausalReference] = set()

    def add(
        cause: HistoricalEventReference | None,
        effect: HistoricalEventReference | None,
        relation: str,
        *,
        unavailable_reason: str = "referenced_event_unavailable",
    ) -> None:
        if cause in valid_references and effect in valid_references:
            edges.add(ExplicitCausalReference(cause, effect, relation))
            return
        unresolved.add(UnresolvedCausalReference(
            cause=cause,
            effect=effect,
            relation=relation,
            reason=unavailable_reason,
        ))

    accepted_knowledge_parents: dict[
        tuple[str, str],
        list[tuple[int, HistoricalEventReference]],
    ] = {}
    interaction_references: dict[
        tuple[str, int, str | None],
        list[HistoricalEventReference],
    ] = {}
    for agent in world.agents:
        for record in agent.knowledge.records:
            if record.response in {"accept", "modify"}:
                accepted_knowledge_parents.setdefault(
                    (agent.id, record.knowledge_id),
                    [],
                ).append((
                    record.day,
                    HistoricalEventReference(
                        record.causal_parent_agent_id,
                        record.causal_parent_event_index,
                    ),
                ))
        for event_index, event in enumerate(agent.events):
            if event.kind == "interaction":
                interaction_references.setdefault(
                    (agent.id, event.day, event.target_id),
                    [],
                ).append(HistoricalEventReference(
                    agent.id,
                    event_index,
                ))

    for agent in world.agents:
        for pressure in agent.discovery.pressures:
            recognition_index = pressure.recognition_event_index
            if recognition_index is None:
                continue
            recognition = HistoricalEventReference(
                agent.id,
                recognition_index,
            )
            for evidence in pressure.evidence:
                add(
                    HistoricalEventReference(
                        evidence.agent_id,
                        evidence.event_index,
                    ),
                    recognition,
                    "problem_evidence_to_recognition",
                )

        for attempt in agent.discovery.attempts:
            recognition = HistoricalEventReference(
                agent.id,
                attempt.pressure_recognition_event_index,
            )
            attempted = HistoricalEventReference(
                agent.id,
                attempt.attempt_event_index,
            )
            resolution = HistoricalEventReference(
                agent.id,
                attempt.resolution_event_index,
            )
            add(
                recognition,
                attempted,
                "recognition_to_discovery_attempt",
            )
            add(
                attempted,
                resolution,
                "discovery_attempt_to_resolution",
            )

        for record in agent.knowledge.records:
            if record.route == "discovery":
                continue
            effect = HistoricalEventReference(
                record.causal_parent_agent_id,
                record.causal_parent_event_index,
            )
            if record.route == "school":
                adoption = world.school.knowledge_adoption
                cause = (
                    HistoricalEventReference(
                        adoption.adoption_agent_id,
                        adoption.adoption_event_index,
                    )
                    if adoption is not None
                    and adoption.knowledge_id == record.knowledge_id
                    else None
                )
                add(
                    cause,
                    effect,
                    "institution_adoption_to_knowledge_exposure",
                    unavailable_reason="institution_adoption_event_unavailable",
                )
                continue

            possible_causes = {
                reference
                for day, reference in accepted_knowledge_parents.get(
                    (record.source_id, record.knowledge_id),
                    (),
                )
                if day < record.day
            }
            if len(possible_causes) == 1:
                cause = next(iter(possible_causes))
                reason = "referenced_event_unavailable"
            elif possible_causes:
                cause = None
                reason = "source_knowledge_event_ambiguous"
            else:
                cause = None
                reason = "source_knowledge_event_unavailable"
            add(
                cause,
                effect,
                "knowledge_source_to_exposure",
                unavailable_reason=reason,
            )

            if record.route == "social":
                interactions = tuple(
                    interaction_references.get(
                        (agent.id, record.day, record.source_id),
                        (),
                    )
                )
                add(
                    interactions[0] if len(interactions) == 1 else None,
                    effect,
                    "social_interaction_to_knowledge_exposure",
                    unavailable_reason=(
                        "social_interaction_event_ambiguous"
                        if interactions
                        else "social_interaction_event_unavailable"
                    ),
                )

        for event_index, event in enumerate(agent.events):
            if event.kind != "peer_training":
                continue
            effect = HistoricalEventReference(agent.id, event_index)
            cause = _knowledge_parent_from_description(event.description)
            add(
                cause,
                effect,
                "knowledge_adoption_to_peer_training",
                unavailable_reason="knowledge_parent_event_unavailable",
            )

    adoption = world.school.knowledge_adoption
    if adoption is not None:
        effect = HistoricalEventReference(
            adoption.adoption_agent_id,
            adoption.adoption_event_index,
        )
        add(
            HistoricalEventReference(
                adoption.origin_agent_id,
                adoption.origin_event_index,
            ),
            effect,
            "knowledge_origin_to_institution_adoption",
        )
        for evidence in world.school.knowledge_evidence:
            add(
                HistoricalEventReference(
                    evidence.teacher_id,
                    evidence.teacher_event_index,
                ),
                effect,
                "peer_training_evidence_to_institution_adoption",
            )

    return _CausalEvidence(
        event_references=valid_references,
        edges=tuple(sorted(edges)),
        unresolved=tuple(sorted(unresolved, key=_unresolved_key)),
    )


def explicit_causal_references(
    world: World,
) -> tuple[ExplicitCausalReference, ...]:
    """Return only event-to-event relations supported by source history."""
    return _collect_causal_evidence(world).edges


def _validate_trace_bounds(max_depth: int, max_nodes: int) -> None:
    for name, value, minimum in (
        ("max_depth", max_depth, 0),
        ("max_nodes", max_nodes, 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
        if value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")


def _find_cycle_edges(
    edges: set[ExplicitCausalReference],
    direction: str,
) -> tuple[ExplicitCausalReference, ...]:
    adjacency: dict[
        HistoricalEventReference,
        list[tuple[HistoricalEventReference, ExplicitCausalReference]],
    ] = {}
    nodes = set()
    for edge in edges:
        current, neighbor = (
            (edge.effect, edge.cause)
            if direction == "ancestors"
            else (edge.cause, edge.effect)
        )
        nodes.update((current, neighbor))
        adjacency.setdefault(current, []).append((neighbor, edge))
    for values in adjacency.values():
        values.sort(key=lambda item: (item[0], item[1]))

    state: dict[HistoricalEventReference, str] = {}
    cycle_edges = set()

    for reference in sorted(nodes):
        if reference in state:
            continue
        state[reference] = "active"
        stack = [(reference, 0)]
        while stack:
            current, index = stack[-1]
            neighbors = adjacency.get(current, ())
            if index >= len(neighbors):
                state[current] = "complete"
                stack.pop()
                continue
            neighbor, edge = neighbors[index]
            stack[-1] = (current, index + 1)
            if state.get(neighbor) == "active":
                cycle_edges.add(edge)
            elif neighbor not in state:
                state[neighbor] = "active"
                stack.append((neighbor, 0))
    return tuple(sorted(cycle_edges))


def _trace_causal_history(
    world: World,
    root: HistoricalEventReference,
    *,
    direction: str,
    max_depth: int,
    max_nodes: int,
) -> CausalTrace:
    if direction not in TRACE_DIRECTIONS:
        raise ValueError(f"Unknown causal trace direction: {direction}")
    _validate_trace_bounds(max_depth, max_nodes)
    evidence = _collect_causal_evidence(world)
    if root not in evidence.event_references:
        raise ValueError(f"Unknown historical event: {root}")

    adjacency: dict[
        HistoricalEventReference,
        list[tuple[HistoricalEventReference, ExplicitCausalReference]],
    ] = {}
    for edge in evidence.edges:
        current, neighbor = (
            (edge.effect, edge.cause)
            if direction == "ancestors"
            else (edge.cause, edge.effect)
        )
        adjacency.setdefault(current, []).append((neighbor, edge))
    for values in adjacency.values():
        values.sort(key=lambda item: (item[0], item[1]))

    unresolved_by_known: dict[
        HistoricalEventReference,
        list[UnresolvedCausalReference],
    ] = {}
    for item in evidence.unresolved:
        known = item.effect if direction == "ancestors" else item.cause
        missing = item.cause if direction == "ancestors" else item.effect
        if (
            known in evidence.event_references
            and missing not in evidence.event_references
        ):
            unresolved_by_known.setdefault(known, []).append(item)

    queue = deque([(root, 0, (root,))])
    depths = {root: 0}
    traced_edges: set[ExplicitCausalReference] = set()
    traced_unresolved: set[UnresolvedCausalReference] = set()
    boundaries: set[CausalTraceBoundary] = set()

    while queue:
        current, depth, path = queue.popleft()
        traced_unresolved.update(unresolved_by_known.get(current, ()))
        neighbors = adjacency.get(current, ())
        if depth >= max_depth:
            if neighbors:
                boundaries.add(CausalTraceBoundary(current, "max_depth"))
            continue

        for neighbor, edge in neighbors:
            if neighbor in path:
                traced_edges.add(edge)
                continue
            if neighbor in depths:
                traced_edges.add(edge)
                continue
            if len(depths) >= max_nodes:
                boundaries.add(CausalTraceBoundary(current, "max_nodes"))
                continue
            traced_edges.add(edge)
            depths[neighbor] = depth + 1
            queue.append((neighbor, depth + 1, path + (neighbor,)))

    return CausalTrace(
        root=root,
        direction=direction,
        nodes=tuple(
            CausalTraceNode(depth, reference)
            for reference, depth in sorted(
                depths.items(),
                key=lambda item: (item[1], item[0]),
            )
        ),
        edges=tuple(sorted(traced_edges)),
        unresolved_references=tuple(sorted(
            traced_unresolved,
            key=_unresolved_key,
        )),
        cycle_edges=_find_cycle_edges(traced_edges, direction),
        boundaries=tuple(sorted(boundaries)),
        configured_max_depth=max_depth,
        configured_max_nodes=max_nodes,
        provenance=CausalTraceProvenance(),
    )


def trace_causal_ancestors(
    world: World,
    root: HistoricalEventReference,
    *,
    max_depth: int = DEFAULT_MAX_TRACE_DEPTH,
    max_nodes: int = DEFAULT_MAX_TRACE_NODES,
) -> CausalTrace:
    """Trace bounded explicitly recorded causes of one event."""
    return _trace_causal_history(
        world,
        root,
        direction="ancestors",
        max_depth=max_depth,
        max_nodes=max_nodes,
    )


def trace_causal_descendants(
    world: World,
    root: HistoricalEventReference,
    *,
    max_depth: int = DEFAULT_MAX_TRACE_DEPTH,
    max_nodes: int = DEFAULT_MAX_TRACE_NODES,
) -> CausalTrace:
    """Trace bounded events that explicitly depend on one event."""
    return _trace_causal_history(
        world,
        root,
        direction="descendants",
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
