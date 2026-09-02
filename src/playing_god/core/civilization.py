from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.:-]*$")

KNOWLEDGE_STATUS = "validated"
KNOWLEDGE_RESPONSES = frozenset({"accept", "modify", "reject"})
KNOWLEDGE_ROUTES = frozenset({"discovery"})

AFFORDANCE_AVAILABILITY = "knowledge_required"
AFFORDANCE_USERS = "adopters"
AFFORDANCE_PRECONDITIONS = frozenset(
    {
        "adult",
        "co_located",
        "knowledge_adopted",
        "learner_energy",
        "relationship",
        "teacher_energy",
        "teacher_skill",
    }
)

COST_OPERATIONS = frozenset(
    {"consume_energy", "increase_stress", "spend_money"}
)
RESULT_OPERATIONS = frozenset({"increase_skill"})
EFFECT_LIMITS = {
    "consume_energy": 1.0,
    "increase_skill": 1.0,
    "increase_stress": 1.0,
    "spend_money": 100.0,
}
EFFECT_TARGETS = frozenset({"learner", "teacher"})

TRAINING_ACCESS_PROBLEM_ID = "problem:training_access"
TRAINING_DENIAL_REASONS = frozenset(
    {"capacity_exhausted", "not_at_school"}
)
PROBLEM_RECOGNITION_THRESHOLD = 3
MAX_PROBLEM_EVIDENCE = 8
DISCOVERY_SKILL_THRESHOLD = 0.35
DISCOVERY_ENERGY_THRESHOLD = 0.35
DISCOVERY_MONEY_THRESHOLD = 7.0
REQUIRED_DISCOVERY_PRIMITIVES = (
    "demonstration",
    "feedback",
    "shared_practice",
)


@dataclass(frozen=True)
class BasePrimitive:
    id: str
    category: str
    tags: tuple[str, ...]
    capabilities: tuple[str, ...]
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class BoundedEffect:
    operation: str
    target: str
    amount: float


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    signature: str
    origin_agent_id: str
    origin_event_index: int
    discoverer_ids: tuple[str, ...]
    primitive_ids: tuple[str, ...]
    action_id: str
    creation_day: int
    status: str = KNOWLEDGE_STATUS


@dataclass(frozen=True)
class AgentKnowledgeRecord:
    day: int
    knowledge_id: str
    source_id: str
    route: str
    response: str
    variant_id: str | None
    causal_parent_agent_id: str
    causal_parent_event_index: int


@dataclass(frozen=True)
class AgentKnowledgeState:
    records: tuple[AgentKnowledgeRecord, ...] = ()


@dataclass(frozen=True)
class PrimitiveExposure:
    primitive_id: str
    day: int
    agent_id: str
    event_index: int
    route: str = "institutional_training"


@dataclass(frozen=True)
class ProblemEvidence:
    day: int
    agent_id: str
    event_index: int
    reason: str


@dataclass(frozen=True)
class ProblemPressure:
    id: str
    occurrence_count: int
    severity: float
    first_evidence_day: int
    latest_evidence_day: int
    evidence: tuple[ProblemEvidence, ...]
    recognized_day: int | None = None
    recognition_event_index: int | None = None
    resolved: bool = False


@dataclass(frozen=True)
class AgentDiscoveryState:
    primitive_exposures: tuple[PrimitiveExposure, ...] = ()
    pressures: tuple[ProblemPressure, ...] = ()


@dataclass(frozen=True)
class DiscoveryEligibility:
    agent_id: str
    problem_id: str
    eligible: bool
    blockers: tuple[str, ...]
    primitive_ids: tuple[str, ...]


@dataclass(frozen=True)
class AffordanceDefinition:
    id: str
    source_knowledge_id: str
    preconditions: tuple[str, ...]
    costs: tuple[BoundedEffect, ...]
    effects: tuple[BoundedEffect, ...]
    available_to: str = AFFORDANCE_USERS
    availability: str = AFFORDANCE_AVAILABILITY


@dataclass(frozen=True)
class CivilizationState:
    knowledge: tuple[KnowledgeEntry, ...] = ()
    affordances: tuple[AffordanceDefinition, ...] = ()


BASE_PRIMITIVES = (
    BasePrimitive(
        id="demonstration",
        category="learning_process",
        tags=("instruction", "social"),
        capabilities=("demonstrate_skill",),
        requirements=("relevant_skill",),
    ),
    BasePrimitive(
        id="feedback",
        category="learning_process",
        tags=("evaluation", "learning"),
        capabilities=("correct_error",),
        requirements=("relevant_skill",),
    ),
    BasePrimitive(
        id="shared_practice",
        category="learning_process",
        tags=("cooperative", "learning"),
        capabilities=("practice_together",),
        requirements=("co_location",),
    ),
)


def knowledge_signature(
    primitive_ids: tuple[str, ...],
    action_id: str,
) -> str:
    """Return an ordering-independent discovery identity."""
    normalized = tuple(sorted(set(primitive_ids)))
    payload = json.dumps(
        {
            "action_id": action_id,
            "primitive_ids": normalized,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"discovery:{digest}"


def base_primitive(
    primitive_id: str,
) -> BasePrimitive | None:
    return next(
        (
            primitive
            for primitive in BASE_PRIMITIVES
            if primitive.id == primitive_id
        ),
        None,
    )


def knowledge_entry(
    state: CivilizationState,
    knowledge_id: str,
) -> KnowledgeEntry | None:
    return next(
        (
            entry
            for entry in state.knowledge
            if entry.id == knowledge_id
        ),
        None,
    )


def affordance_definition(
    state: CivilizationState,
    action_id: str,
) -> AffordanceDefinition | None:
    return next(
        (
            affordance
            for affordance in state.affordances
            if affordance.id == action_id
        ),
        None,
    )


def adopted_knowledge_ids(
    state: AgentKnowledgeState,
) -> tuple[str, ...]:
    return tuple(sorted({
        record.knowledge_id
        for record in state.records
        if record.response in {"accept", "modify"}
    }))


def record_primitive_exposure(
    state: AgentDiscoveryState,
    *,
    agent_id: str,
    day: int,
    event_index: int,
) -> AgentDiscoveryState:
    """Record first direct exposure to each required primitive."""
    existing = {
        exposure.primitive_id
        for exposure in state.primitive_exposures
    }
    additions = tuple(
        PrimitiveExposure(
            primitive_id=primitive_id,
            day=day,
            agent_id=agent_id,
            event_index=event_index,
        )
        for primitive_id in REQUIRED_DISCOVERY_PRIMITIVES
        if primitive_id not in existing
    )
    updated = AgentDiscoveryState(
        primitive_exposures=tuple(sorted(
            state.primitive_exposures + additions,
            key=lambda exposure: exposure.primitive_id,
        )),
        pressures=state.pressures,
    )
    validate_agent_discovery_state(updated)
    return updated


def record_training_access_denial(
    state: AgentDiscoveryState,
    *,
    agent_id: str,
    day: int,
    event_index: int,
    reason: str,
    recognition_event_index: int,
) -> tuple[AgentDiscoveryState, bool]:
    """Accumulate one first-hand denial without retaining unbounded history."""
    if reason not in TRAINING_DENIAL_REASONS:
        raise ValueError("Unknown training denial reason.")
    existing = next(
        (
            pressure
            for pressure in state.pressures
            if pressure.id == TRAINING_ACCESS_PROBLEM_ID
        ),
        None,
    )
    evidence = ProblemEvidence(
        day=day,
        agent_id=agent_id,
        event_index=event_index,
        reason=reason,
    )
    previous_evidence = existing.evidence if existing else ()
    retained = (previous_evidence + (evidence,))[-MAX_PROBLEM_EVIDENCE:]
    count = min(
        MAX_PROBLEM_EVIDENCE,
        (existing.occurrence_count if existing else 0) + 1,
    )
    newly_recognized = (
        existing is None or existing.recognized_day is None
    ) and count >= PROBLEM_RECOGNITION_THRESHOLD
    pressure = ProblemPressure(
        id=TRAINING_ACCESS_PROBLEM_ID,
        occurrence_count=count,
        severity=count / MAX_PROBLEM_EVIDENCE,
        first_evidence_day=(
            existing.first_evidence_day if existing else day
        ),
        latest_evidence_day=day,
        evidence=retained,
        recognized_day=(
            day
            if newly_recognized
            else existing.recognized_day if existing else None
        ),
        recognition_event_index=(
            recognition_event_index
            if newly_recognized
            else existing.recognition_event_index if existing else None
        ),
        resolved=existing.resolved if existing else False,
    )
    pressures = tuple(
        item
        for item in state.pressures
        if item.id != TRAINING_ACCESS_PROBLEM_ID
    ) + (pressure,)
    updated = AgentDiscoveryState(
        primitive_exposures=state.primitive_exposures,
        pressures=tuple(sorted(pressures, key=lambda item: item.id)),
    )
    validate_agent_discovery_state(updated)
    return updated, newly_recognized


def discovery_eligibility(
    agent: Agent,
    *,
    current_day: int,
) -> DiscoveryEligibility:
    """Return a deterministic, read-only discovery eligibility result."""
    pressure = next(
        (
            item
            for item in agent.discovery.pressures
            if item.id == TRAINING_ACCESS_PROBLEM_ID
        ),
        None,
    )
    possessed = tuple(
        primitive_id
        for primitive_id in REQUIRED_DISCOVERY_PRIMITIVES
        if any(
            exposure.primitive_id == primitive_id
            for exposure in agent.discovery.primitive_exposures
        )
    )
    blockers = []
    if (
        pressure is None
        or pressure.recognized_day is None
        or pressure.resolved
    ):
        blockers.append("pressure")
    if not agent.lifecycle.alive:
        blockers.append("alive")
    if agent.age < 18 or agent.family.dependent:
        blockers.append("adult")
    if agent.skill < DISCOVERY_SKILL_THRESHOLD:
        blockers.append("skill")
    if possessed != REQUIRED_DISCOVERY_PRIMITIVES:
        blockers.append("primitives")
    if agent.energy < DISCOVERY_ENERGY_THRESHOLD:
        blockers.append("energy")
    if agent.money < DISCOVERY_MONEY_THRESHOLD:
        blockers.append("money")
    if (
        pressure is not None
        and pressure.recognized_day is not None
        and current_day <= pressure.recognized_day
    ):
        blockers.append("time")
    return DiscoveryEligibility(
        agent_id=agent.id,
        problem_id=TRAINING_ACCESS_PROBLEM_ID,
        eligible=not blockers,
        blockers=tuple(blockers),
        primitive_ids=possessed,
    )


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))


def _is_canonical_identifiers(values: object) -> bool:
    return (
        isinstance(values, tuple)
        and bool(values)
        and all(_is_identifier(value) for value in values)
        and values == tuple(sorted(set(values)))
    )


def _effect_key(effect: BoundedEffect) -> tuple[str, str, float]:
    return effect.operation, effect.target, effect.amount


def _knowledge_record_key(
    record: AgentKnowledgeRecord,
) -> tuple[int, str, str, str]:
    return record.day, record.knowledge_id, record.source_id, record.route


def validate_base_primitives(
    primitives: tuple[BasePrimitive, ...] = BASE_PRIMITIVES,
) -> None:
    if (
        not isinstance(primitives, tuple)
        or not all(
            isinstance(item, BasePrimitive) for item in primitives
        )
        or tuple(item.id for item in primitives)
        != tuple(sorted(item.id for item in primitives))
        or len({item.id for item in primitives}) != len(primitives)
    ):
        raise ValueError("Invalid base primitive registry.")

    for primitive in primitives:
        if (
            not _is_identifier(primitive.id)
            or not _is_identifier(primitive.category)
            or not _is_canonical_identifiers(primitive.tags)
            or not _is_canonical_identifiers(primitive.capabilities)
            or not _is_canonical_identifiers(primitive.requirements)
        ):
            raise ValueError("Invalid base primitive definition.")


def _validate_effect(
    effect: BoundedEffect,
    *,
    allowed_operations: frozenset[str],
) -> None:
    if (
        not isinstance(effect, BoundedEffect)
        or effect.operation not in allowed_operations
        or effect.target not in EFFECT_TARGETS
        or isinstance(effect.amount, bool)
        or not isinstance(effect.amount, (int, float))
        or not math.isfinite(effect.amount)
        or not 0.0 < effect.amount <= EFFECT_LIMITS[effect.operation]
    ):
        raise ValueError("Invalid bounded civilization effect.")


def validate_civilization_state(
    state: CivilizationState,
) -> None:
    validate_base_primitives()
    if (
        not isinstance(state, CivilizationState)
        or not isinstance(state.knowledge, tuple)
        or not isinstance(state.affordances, tuple)
        or not all(
            isinstance(entry, KnowledgeEntry)
            and isinstance(entry.id, str)
            and isinstance(entry.signature, str)
            for entry in state.knowledge
        )
        or not all(
            isinstance(item, AffordanceDefinition)
            for item in state.affordances
        )
    ):
        raise ValueError("Invalid civilization state.")

    knowledge_ids = tuple(entry.id for entry in state.knowledge)
    signatures = tuple(entry.signature for entry in state.knowledge)
    if (
        knowledge_ids != tuple(sorted(knowledge_ids))
        or len(set(knowledge_ids)) != len(knowledge_ids)
        or len(set(signatures)) != len(signatures)
    ):
        raise ValueError("Duplicate or unordered knowledge registry.")

    primitive_ids = {primitive.id for primitive in BASE_PRIMITIVES}
    knowledge_by_id: dict[str, KnowledgeEntry] = {}
    for entry in state.knowledge:
        if (
            not _is_identifier(entry.id)
            or not _is_identifier(entry.origin_agent_id)
            or isinstance(entry.origin_event_index, bool)
            or not isinstance(entry.origin_event_index, int)
            or entry.origin_event_index < 0
            or not _is_canonical_identifiers(entry.discoverer_ids)
            or not _is_canonical_identifiers(entry.primitive_ids)
            or not set(entry.primitive_ids).issubset(primitive_ids)
            or not _is_identifier(entry.action_id)
            or isinstance(entry.creation_day, bool)
            or not isinstance(entry.creation_day, int)
            or entry.creation_day < 0
            or entry.status != KNOWLEDGE_STATUS
            or entry.signature
            != knowledge_signature(entry.primitive_ids, entry.action_id)
        ):
            raise ValueError("Invalid validated knowledge entry.")
        knowledge_by_id[entry.id] = entry

    affordance_ids = tuple(item.id for item in state.affordances)
    source_ids = tuple(
        item.source_knowledge_id for item in state.affordances
    )
    if (
        affordance_ids != tuple(sorted(affordance_ids))
        or len(set(affordance_ids)) != len(affordance_ids)
        or len(set(source_ids)) != len(source_ids)
        or set(source_ids) != set(knowledge_ids)
    ):
        raise ValueError("Invalid knowledge-affordance registry.")

    for affordance in state.affordances:
        if (
            not _is_identifier(affordance.id)
            or affordance.source_knowledge_id not in knowledge_by_id
            or knowledge_by_id[
                affordance.source_knowledge_id
            ].action_id
            != affordance.id
            or not _is_canonical_identifiers(affordance.preconditions)
            or not set(affordance.preconditions).issubset(
                AFFORDANCE_PRECONDITIONS
            )
            or "knowledge_adopted" not in affordance.preconditions
            or not isinstance(affordance.costs, tuple)
            or not affordance.costs
            or not all(
                isinstance(effect, BoundedEffect)
                for effect in affordance.costs
            )
            or affordance.costs
            != tuple(sorted(affordance.costs, key=_effect_key))
            or not isinstance(affordance.effects, tuple)
            or not affordance.effects
            or not all(
                isinstance(effect, BoundedEffect)
                for effect in affordance.effects
            )
            or affordance.effects
            != tuple(sorted(affordance.effects, key=_effect_key))
            or affordance.available_to != AFFORDANCE_USERS
            or affordance.availability != AFFORDANCE_AVAILABILITY
        ):
            raise ValueError("Invalid civilization affordance.")
        for effect in affordance.costs:
            _validate_effect(
                effect,
                allowed_operations=COST_OPERATIONS,
            )
        for effect in affordance.effects:
            _validate_effect(
                effect,
                allowed_operations=RESULT_OPERATIONS,
            )


def validate_agent_knowledge_state(
    state: AgentKnowledgeState,
) -> None:
    if (
        not isinstance(state, AgentKnowledgeState)
        or not isinstance(state.records, tuple)
        or not all(
            isinstance(record, AgentKnowledgeRecord)
            for record in state.records
        )
    ):
        raise ValueError("Invalid agent knowledge state.")

    if state.records != tuple(
        sorted(state.records, key=_knowledge_record_key)
    ):
        raise ValueError("Agent knowledge records are unordered.")
    identities = tuple(
        _knowledge_record_key(item) for item in state.records
    )
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate agent knowledge record.")

    for record in state.records:
        if (
            isinstance(record.day, bool)
            or not isinstance(record.day, int)
            or record.day < 0
            or not _is_identifier(record.knowledge_id)
            or not _is_identifier(record.source_id)
            or record.route not in KNOWLEDGE_ROUTES
            or record.response not in KNOWLEDGE_RESPONSES
            or (
                record.variant_id is not None
                and not _is_identifier(record.variant_id)
            )
            or (
                record.response == "modify"
                and record.variant_id is None
            )
            or (
                record.response != "modify"
                and record.variant_id is not None
            )
            or not _is_identifier(record.causal_parent_agent_id)
            or isinstance(record.causal_parent_event_index, bool)
            or not isinstance(record.causal_parent_event_index, int)
            or record.causal_parent_event_index < 0
        ):
            raise ValueError("Invalid agent knowledge record.")


def validate_agent_discovery_state(
    state: AgentDiscoveryState,
) -> None:
    if (
        not isinstance(state, AgentDiscoveryState)
        or not isinstance(state.primitive_exposures, tuple)
        or not isinstance(state.pressures, tuple)
        or not all(
            isinstance(item, PrimitiveExposure)
            for item in state.primitive_exposures
        )
        or not all(
            isinstance(item, ProblemPressure)
            for item in state.pressures
        )
    ):
        raise ValueError("Invalid agent discovery state.")

    exposure_ids = tuple(
        item.primitive_id for item in state.primitive_exposures
    )
    if (
        exposure_ids != tuple(sorted(exposure_ids))
        or len(set(exposure_ids)) != len(exposure_ids)
        or not set(exposure_ids).issubset(
            REQUIRED_DISCOVERY_PRIMITIVES
        )
    ):
        raise ValueError("Invalid primitive exposure registry.")
    for exposure in state.primitive_exposures:
        if (
            not _is_identifier(exposure.agent_id)
            or isinstance(exposure.day, bool)
            or not isinstance(exposure.day, int)
            or exposure.day < 0
            or isinstance(exposure.event_index, bool)
            or not isinstance(exposure.event_index, int)
            or exposure.event_index < 0
            or exposure.route != "institutional_training"
        ):
            raise ValueError("Invalid primitive exposure.")

    pressure_ids = tuple(item.id for item in state.pressures)
    if (
        pressure_ids != tuple(sorted(pressure_ids))
        or len(set(pressure_ids)) != len(pressure_ids)
        or not set(pressure_ids).issubset(
            {TRAINING_ACCESS_PROBLEM_ID}
        )
    ):
        raise ValueError("Invalid problem pressure registry.")
    for pressure in state.pressures:
        evidence_keys = tuple(
            (item.day, item.event_index)
            for item in pressure.evidence
        )
        recognized = pressure.recognized_day is not None
        if (
            isinstance(pressure.occurrence_count, bool)
            or not isinstance(pressure.occurrence_count, int)
            or not 1 <= pressure.occurrence_count <= MAX_PROBLEM_EVIDENCE
            or isinstance(pressure.severity, bool)
            or not isinstance(pressure.severity, (int, float))
            or not math.isfinite(pressure.severity)
            or pressure.severity
            != pressure.occurrence_count / MAX_PROBLEM_EVIDENCE
            or isinstance(pressure.first_evidence_day, bool)
            or not isinstance(pressure.first_evidence_day, int)
            or pressure.first_evidence_day < 0
            or isinstance(pressure.latest_evidence_day, bool)
            or not isinstance(pressure.latest_evidence_day, int)
            or pressure.latest_evidence_day < pressure.first_evidence_day
            or not isinstance(pressure.evidence, tuple)
            or len(pressure.evidence) != pressure.occurrence_count
            or evidence_keys != tuple(sorted(evidence_keys))
            or len(set(evidence_keys)) != len(evidence_keys)
            or pressure.evidence[-1].day
            != pressure.latest_evidence_day
            or not isinstance(pressure.resolved, bool)
            or recognized
            != (pressure.recognition_event_index is not None)
            or (
                recognized
                and (
                    isinstance(pressure.recognized_day, bool)
                    or not isinstance(pressure.recognized_day, int)
                    or pressure.recognized_day
                    < pressure.first_evidence_day
                    or pressure.recognized_day
                    > pressure.latest_evidence_day
                    or isinstance(
                        pressure.recognition_event_index,
                        bool,
                    )
                    or not isinstance(
                        pressure.recognition_event_index,
                        int,
                    )
                    or pressure.recognition_event_index < 0
                )
            )
            or (
                not recognized
                and pressure.occurrence_count
                >= PROBLEM_RECOGNITION_THRESHOLD
            )
            or (pressure.resolved and not recognized)
        ):
            raise ValueError("Invalid problem pressure.")
        for evidence in pressure.evidence:
            if (
                not isinstance(evidence, ProblemEvidence)
                or not _is_identifier(evidence.agent_id)
                or isinstance(evidence.day, bool)
                or not isinstance(evidence.day, int)
                or evidence.day < pressure.first_evidence_day
                or evidence.day > pressure.latest_evidence_day
                or isinstance(evidence.event_index, bool)
                or not isinstance(evidence.event_index, int)
                or evidence.event_index < 0
                or evidence.reason not in TRAINING_DENIAL_REASONS
            ):
                raise ValueError("Invalid problem evidence.")


def validate_discovery_links(
    agents: list[Agent],
    *,
    current_day: int,
) -> None:
    denial_prefixes = {
        "capacity_exhausted": (
            "School denied training: daily capacity "
        ),
        "not_at_school": (
            "School denied training: agent is not at school"
        ),
    }
    for agent in agents:
        validate_agent_discovery_state(agent.discovery)

        def linked_event(event_index: int):
            if event_index >= len(agent.events):
                raise ValueError("Discovery link has unknown event.")
            return agent.events[event_index]

        for exposure in agent.discovery.primitive_exposures:
            event = linked_event(exposure.event_index)
            if (
                exposure.agent_id != agent.id
                or exposure.day > current_day
                or event.day != exposure.day
                or event.kind != "institution"
                or not event.description.startswith(
                    "School admitted training slot "
                )
            ):
                raise ValueError("Invalid primitive exposure link.")
        for pressure in agent.discovery.pressures:
            for evidence in pressure.evidence:
                event = linked_event(evidence.event_index)
                if (
                    evidence.agent_id != agent.id
                    or evidence.day > current_day
                    or event.day != evidence.day
                    or event.kind != "institution"
                    or not event.description.startswith(
                        denial_prefixes[evidence.reason]
                    )
                ):
                    raise ValueError("Invalid problem evidence link.")
            if pressure.recognition_event_index is not None:
                event = linked_event(pressure.recognition_event_index)
                if (
                    event.day != pressure.recognized_day
                    or event.day > current_day
                    or event.kind != "problem_pressure_recognized"
                ):
                    raise ValueError("Invalid problem recognition link.")


def validate_civilization_links(
    state: CivilizationState,
    agents: list[Agent],
    *,
    current_day: int,
) -> None:
    validate_civilization_state(state)
    agents_by_id = {agent.id: agent for agent in agents}
    knowledge_by_id = {entry.id: entry for entry in state.knowledge}

    def linked_event(agent_id: str, event_index: int):
        if agent_id not in agents_by_id:
            raise ValueError("Civilization link has unknown agent.")
        events = agents_by_id[agent_id].events
        if event_index >= len(events):
            raise ValueError("Civilization link has unknown event.")
        return events[event_index]

    for entry in state.knowledge:
        if (
            entry.creation_day > current_day
            or entry.origin_agent_id not in entry.discoverer_ids
            or any(
                agent_id not in agents_by_id
                for agent_id in entry.discoverer_ids
            )
        ):
            raise ValueError("Invalid knowledge timeline or discoverer.")
        origin = linked_event(
            entry.origin_agent_id,
            entry.origin_event_index,
        )
        if (
            origin.kind != "discovery_attempted"
            or origin.day > entry.creation_day
        ):
            raise ValueError("Knowledge lacks a valid origin attempt.")

    for agent in agents:
        validate_agent_knowledge_state(agent.knowledge)
        for record in agent.knowledge.records:
            entry = knowledge_by_id.get(record.knowledge_id)
            if (
                entry is None
                or record.day < entry.creation_day
                or record.day > current_day
            ):
                raise ValueError("Invalid agent knowledge timeline.")
            parent = linked_event(
                record.causal_parent_agent_id,
                record.causal_parent_event_index,
            )
            if (
                parent.kind != "discovery_validated"
                or parent.day != record.day
            ):
                raise ValueError("Invalid agent knowledge causal parent.")
            if (
                record.source_id != agent.id
                or agent.id not in entry.discoverer_ids
                or record.response != "accept"
                or record.day != entry.creation_day
            ):
                raise ValueError("Invalid discoverer knowledge record.")


def civilization_state_from_data(data: object) -> CivilizationState:
    if not isinstance(data, dict) or set(data) != {
        "affordances",
        "knowledge",
    }:
        raise ValueError("Invalid civilization state structure.")
    if not isinstance(data["knowledge"], list) or not isinstance(
        data["affordances"], list
    ):
        raise ValueError("Invalid civilization registry structure.")

    knowledge_fields = set(KnowledgeEntry.__dataclass_fields__)
    knowledge = []
    for item in data["knowledge"]:
        if not isinstance(item, dict) or set(item) != knowledge_fields:
            raise ValueError("Invalid knowledge entry structure.")
        values = dict(item)
        for name in ("discoverer_ids", "primitive_ids"):
            if not isinstance(values[name], list):
                raise ValueError("Invalid knowledge collection.")
            values[name] = tuple(values[name])
        knowledge.append(KnowledgeEntry(**values))

    affordance_fields = set(AffordanceDefinition.__dataclass_fields__)
    effect_fields = set(BoundedEffect.__dataclass_fields__)
    affordances = []
    for item in data["affordances"]:
        if not isinstance(item, dict) or set(item) != affordance_fields:
            raise ValueError("Invalid affordance structure.")
        values = dict(item)
        if not isinstance(values["preconditions"], list):
            raise ValueError("Invalid affordance preconditions.")
        values["preconditions"] = tuple(values["preconditions"])
        for name in ("costs", "effects"):
            if not isinstance(values[name], list):
                raise ValueError("Invalid affordance effects.")
            parsed = []
            for effect in values[name]:
                if (
                    not isinstance(effect, dict)
                    or set(effect) != effect_fields
                ):
                    raise ValueError("Invalid bounded effect structure.")
                parsed.append(BoundedEffect(**effect))
            values[name] = tuple(parsed)
        affordances.append(AffordanceDefinition(**values))

    state = CivilizationState(
        knowledge=tuple(knowledge),
        affordances=tuple(affordances),
    )
    validate_civilization_state(state)
    return state


def agent_knowledge_state_from_data(
    data: object,
) -> AgentKnowledgeState:
    if not isinstance(data, dict) or set(data) != {"records"}:
        raise ValueError("Invalid agent knowledge state structure.")
    if not isinstance(data["records"], list):
        raise ValueError("Invalid agent knowledge records.")
    expected_fields = set(AgentKnowledgeRecord.__dataclass_fields__)
    records = []
    for item in data["records"]:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ValueError("Invalid agent knowledge record structure.")
        records.append(AgentKnowledgeRecord(**item))
    state = AgentKnowledgeState(records=tuple(records))
    validate_agent_knowledge_state(state)
    return state


def agent_discovery_state_from_data(
    data: object,
) -> AgentDiscoveryState:
    if not isinstance(data, dict) or set(data) != {
        "pressures",
        "primitive_exposures",
    }:
        raise ValueError("Invalid agent discovery state structure.")
    if not isinstance(data["primitive_exposures"], list) or not isinstance(
        data["pressures"], list
    ):
        raise ValueError("Invalid agent discovery collections.")

    exposure_fields = set(PrimitiveExposure.__dataclass_fields__)
    exposures = []
    for item in data["primitive_exposures"]:
        if not isinstance(item, dict) or set(item) != exposure_fields:
            raise ValueError("Invalid primitive exposure structure.")
        exposures.append(PrimitiveExposure(**item))

    evidence_fields = set(ProblemEvidence.__dataclass_fields__)
    pressure_fields = set(ProblemPressure.__dataclass_fields__)
    pressures = []
    for item in data["pressures"]:
        if not isinstance(item, dict) or set(item) != pressure_fields:
            raise ValueError("Invalid problem pressure structure.")
        values = dict(item)
        if not isinstance(values["evidence"], list):
            raise ValueError("Invalid problem evidence collection.")
        evidence = []
        for record in values["evidence"]:
            if (
                not isinstance(record, dict)
                or set(record) != evidence_fields
            ):
                raise ValueError("Invalid problem evidence structure.")
            evidence.append(ProblemEvidence(**record))
        values["evidence"] = tuple(evidence)
        pressures.append(ProblemPressure(**values))

    state = AgentDiscoveryState(
        primitive_exposures=tuple(exposures),
        pressures=tuple(pressures),
    )
    validate_agent_discovery_state(state)
    return state
