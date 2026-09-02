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
