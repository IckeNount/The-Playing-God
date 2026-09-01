from __future__ import annotations

from dataclasses import dataclass
import math
from random import Random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent
    from playing_god.core.social import SocialGraph


MIN_PARENT_AGE = 20
MAX_PARENT_AGE = 45
MIN_HOUSEHOLD_MONEY = 300.0
MAX_PARENT_STRESS = 0.75
MIN_MUTUAL_AFFINITY = 0.30
MIN_MUTUAL_TRUST = 0.55
MIN_MUTUAL_FAMILIARITY = 0.55
REPRODUCTION_DAILY_CHANCE = 0.01
REPRODUCTION_COOLDOWN_DAYS = 365
REPRODUCTION_COST = 120.0
INHERITANCE_VARIATION = 0.08
MAX_POPULATION = 100


@dataclass(frozen=True)
class BirthContext:
    day: int
    parent_ids: tuple[str, str]
    guardian_ids: tuple[str, ...]
    location: str
    household_money: float
    employed_guardians: int
    guardian_stress: float
    mutual_affinity: float
    mutual_trust: float
    mutual_familiarity: float
    reproduction_roll: float


@dataclass(frozen=True)
class FamilyState:
    generation: int = 0
    birth_day: int | None = None
    dependent: bool = False
    parent_ids: tuple[str, ...] = ()
    guardian_ids: tuple[str, ...] = ()
    child_ids: tuple[str, ...] = ()
    birth_context: BirthContext | None = None


@dataclass(frozen=True)
class ReproductionEligibility:
    eligible: bool
    reasons: tuple[str, ...]
    mutual_affinity: float
    mutual_trust: float
    mutual_familiarity: float


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _relationship_minimum(
    social: SocialGraph,
    first_id: str,
    second_id: str,
    field: str,
) -> float:
    first = social.get_relationship(first_id, second_id) or {}
    second = social.get_relationship(second_id, first_id) or {}
    return min(first.get(field, 0.0), second.get(field, 0.0))


def _are_close_family(first: Agent, second: Agent) -> bool:
    if (
        first.id in second.family.parent_ids
        or second.id in first.family.parent_ids
    ):
        return True
    return bool(
        set(first.family.parent_ids)
        & set(second.family.parent_ids)
    )


def _has_recent_child(
    parent: Agent,
    agents_by_id: dict[str, Agent],
    day: int,
) -> bool:
    return any(
        child is not None
        and child.family.birth_day is not None
        and day - child.family.birth_day < REPRODUCTION_COOLDOWN_DAYS
        for child_id in parent.family.child_ids
        for child in [agents_by_id.get(child_id)]
    )


def reproduction_eligibility(
    first: Agent,
    second: Agent,
    social: SocialGraph,
    agents_by_id: dict[str, Agent],
    day: int,
) -> ReproductionEligibility:
    """Explain whether current world state permits one birth attempt."""
    affinity = min(
        first.relationships.get(second.id, 0.0),
        second.relationships.get(first.id, 0.0),
    )
    trust = _relationship_minimum(
        social,
        first.id,
        second.id,
        "trust",
    )
    familiarity = _relationship_minimum(
        social,
        first.id,
        second.id,
        "familiarity",
    )
    reasons = []

    if first.id == second.id:
        reasons.append("same_agent")
    if first.family.dependent or second.family.dependent:
        reasons.append("dependent")
    if not (
        MIN_PARENT_AGE <= first.age <= MAX_PARENT_AGE
        and MIN_PARENT_AGE <= second.age <= MAX_PARENT_AGE
    ):
        reasons.append("age")
    if first.current_location != second.current_location:
        reasons.append("not_colocated")
    if affinity < MIN_MUTUAL_AFFINITY:
        reasons.append("affinity")
    if trust < MIN_MUTUAL_TRUST:
        reasons.append("trust")
    if familiarity < MIN_MUTUAL_FAMILIARITY:
        reasons.append("familiarity")
    if first.money + second.money < MIN_HOUSEHOLD_MONEY:
        reasons.append("resources")
    if not (first.employed or second.employed):
        reasons.append("employment")
    if max(first.stress, second.stress) > MAX_PARENT_STRESS:
        reasons.append("stress")
    if _are_close_family(first, second):
        reasons.append("close_family")
    if (
        _has_recent_child(first, agents_by_id, day)
        or _has_recent_child(second, agents_by_id, day)
    ):
        reasons.append("cooldown")

    return ReproductionEligibility(
        eligible=not reasons,
        reasons=tuple(reasons),
        mutual_affinity=affinity,
        mutual_trust=trust,
        mutual_familiarity=familiarity,
    )


def inherited_priors(
    first: Agent,
    second: Agent,
    rng: Random,
) -> tuple[dict[str, float], dict[str, float]]:
    """Blend parent priors with small independent bounded variation."""
    traits = {
        key: _clamp(
            (first.traits[key] + second.traits[key]) / 2
            + rng.uniform(-INHERITANCE_VARIATION, INHERITANCE_VARIATION)
        )
        for key in first.traits
    }
    sins = {
        key: _clamp(
            (first.sins[key] + second.sins[key]) / 2
            + rng.uniform(-INHERITANCE_VARIATION, INHERITANCE_VARIATION)
        )
        for key in first.sins
    }
    return traits, sins


def family_state_from_data(data: object) -> FamilyState:
    """Parse one persisted family record without reconstructing history."""
    if not isinstance(data, dict) or set(data) != {
        "generation",
        "birth_day",
        "dependent",
        "parent_ids",
        "guardian_ids",
        "child_ids",
        "birth_context",
    }:
        raise ValueError("Invalid family state structure.")

    def id_tuple(value: object) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise ValueError("Family IDs must be stored as a list.")
        return tuple(value)

    parent_ids = id_tuple(data["parent_ids"])
    guardian_ids = id_tuple(data["guardian_ids"])
    child_ids = id_tuple(data["child_ids"])
    birth_data = data["birth_context"]
    birth_context = None
    if birth_data is not None:
        if not isinstance(birth_data, dict) or set(birth_data) != {
            "day",
            "parent_ids",
            "guardian_ids",
            "location",
            "household_money",
            "employed_guardians",
            "guardian_stress",
            "mutual_affinity",
            "mutual_trust",
            "mutual_familiarity",
            "reproduction_roll",
        }:
            raise ValueError("Invalid birth context structure.")
        birth_context = BirthContext(
            day=birth_data["day"],
            parent_ids=id_tuple(birth_data["parent_ids"]),
            guardian_ids=id_tuple(birth_data["guardian_ids"]),
            location=birth_data["location"],
            household_money=birth_data["household_money"],
            employed_guardians=birth_data["employed_guardians"],
            guardian_stress=birth_data["guardian_stress"],
            mutual_affinity=birth_data["mutual_affinity"],
            mutual_trust=birth_data["mutual_trust"],
            mutual_familiarity=birth_data["mutual_familiarity"],
            reproduction_roll=birth_data["reproduction_roll"],
        )

    state = FamilyState(
        generation=data["generation"],
        birth_day=data["birth_day"],
        dependent=data["dependent"],
        parent_ids=parent_ids,
        guardian_ids=guardian_ids,
        child_ids=child_ids,
        birth_context=birth_context,
    )
    validate_family_state(state)
    return state


def validate_family_state(state: FamilyState) -> None:
    id_groups = (
        state.parent_ids,
        state.guardian_ids,
        state.child_ids,
    )
    if (
        isinstance(state.generation, bool)
        or not isinstance(state.generation, int)
        or state.generation < 0
        or not isinstance(state.dependent, bool)
        or (
            state.birth_day is not None
            and (
                isinstance(state.birth_day, bool)
                or not isinstance(state.birth_day, int)
                or state.birth_day < 0
            )
        )
        or any(
            not isinstance(ids, tuple)
            or any(
                not isinstance(agent_id, str) or not agent_id
                for agent_id in ids
            )
            or len(ids) != len(set(ids))
            for ids in id_groups
        )
    ):
        raise ValueError("Invalid family state values.")

    context = state.birth_context
    if not state.parent_ids:
        if (
            state.generation != 0
            or state.birth_day is not None
            or state.dependent
            or state.guardian_ids
            or context is not None
        ):
            raise ValueError("Founder family state is inconsistent.")
        return

    if (
        len(state.parent_ids) != 2
        or not state.guardian_ids
        or state.birth_day is None
        or context is None
        or context.day != state.birth_day
        or context.parent_ids != state.parent_ids
        or context.guardian_ids != state.guardian_ids
    ):
        raise ValueError("Child family state is inconsistent.")

    numeric = (
        context.household_money,
        context.guardian_stress,
        context.mutual_affinity,
        context.mutual_trust,
        context.mutual_familiarity,
        context.reproduction_roll,
    )
    if (
        isinstance(context.day, bool)
        or not isinstance(context.day, int)
        or context.day < 0
        or not isinstance(context.location, str)
        or not context.location
        or isinstance(context.employed_guardians, bool)
        or not isinstance(context.employed_guardians, int)
        or not 0 <= context.employed_guardians <= len(context.guardian_ids)
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in numeric
        )
        or context.household_money < 0.0
        or not 0.0 <= context.guardian_stress <= 1.0
        or not 0.0 <= context.mutual_trust <= 1.0
        or not 0.0 <= context.mutual_familiarity <= 1.0
        or not 0.0 <= context.reproduction_roll <= 1.0
        or not -1.0 <= context.mutual_affinity <= 1.0
    ):
        raise ValueError("Invalid birth context values.")


def validate_family_links(
    agents: list[Agent],
    *,
    current_day: int | None = None,
    valid_locations: set[str] | None = None,
) -> None:
    agents_by_id = {agent.id: agent for agent in agents}

    for agent in agents:
        validate_family_state(agent.family)
        referenced_ids = (
            agent.family.parent_ids
            + agent.family.guardian_ids
            + agent.family.child_ids
        )
        if (
            agent.id in referenced_ids
            or any(agent_id not in agents_by_id for agent_id in referenced_ids)
        ):
            raise ValueError(f"Invalid family reference for {agent.id}.")

        if agent.family.parent_ids:
            context = agent.family.birth_context
            if (
                current_day is not None
                and agent.family.birth_day > current_day
            ):
                raise ValueError(
                    f"Future birth day for {agent.id}."
                )
            if (
                valid_locations is not None
                and context.location not in valid_locations
            ):
                raise ValueError(
                    f"Invalid birth location for {agent.id}."
                )
            parents = [
                agents_by_id[parent_id]
                for parent_id in agent.family.parent_ids
            ]
            if agent.family.generation != max(
                parent.family.generation for parent in parents
            ) + 1:
                raise ValueError(
                    f"Invalid family generation for {agent.id}."
                )
            if any(
                agent.id not in parent.family.child_ids
                for parent in parents
            ):
                raise ValueError(
                    f"Missing reciprocal parent link for {agent.id}."
                )

        for child_id in agent.family.child_ids:
            if agent.id not in agents_by_id[child_id].family.parent_ids:
                raise ValueError(
                    f"Missing reciprocal child link for {agent.id}."
                )
