from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent
    from playing_god.core.social import SocialGraph


SCHOOL_START_AGE = 6
ADULT_AGE = 18
SCHOOL_OPPORTUNITY_THRESHOLD = 0.45
ANNUAL_SKILL_RATE = 0.075


@dataclass(frozen=True)
class DevelopmentRecord:
    day: int
    age: int
    stage: str
    guardian_ids: tuple[str, ...]
    household_money: float
    employed_guardians: int
    guardian_stress: float
    relationship_support: float
    learning_potential: float
    school_opportunity: float
    school_available: bool
    school_access: bool
    practice: float
    feedback: float
    skill_before: float
    skill_gain: float
    skill_after: float


@dataclass(frozen=True)
class DevelopmentState:
    records: tuple[DevelopmentRecord, ...] = ()


@dataclass(frozen=True)
class DevelopmentOutcome:
    state: DevelopmentState
    skill: float
    became_adult: bool


def developmental_stage(age: int) -> str:
    if age < SCHOOL_START_AGE:
        return "early_childhood"
    if age < 13:
        return "school_age"
    if age < ADULT_AGE:
        return "adolescence"
    return "adult"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _relationship_support(
    child: Agent,
    guardians: list[Agent],
    social: SocialGraph,
) -> float:
    values = []
    for guardian in guardians:
        relationship = social.get_relationship(
            guardian.id,
            child.id,
        )
        if relationship is None:
            values.append(0.0)
            continue
        values.append(
            (
                relationship["trust"]
                + relationship["familiarity"]
            )
            / 2
        )
    return sum(values) / len(values)


def advance_development(
    child: Agent,
    guardians: list[Agent],
    social: SocialGraph,
    *,
    day: int,
    age: int,
    school_available: bool,
) -> DevelopmentOutcome:
    """Resolve one annual, age-appropriate developmental checkpoint."""
    if not guardians:
        raise ValueError("Development requires at least one guardian.")
    if age < 1 or age > ADULT_AGE:
        raise ValueError("Development age must be within [1, 18].")

    household_money = sum(guardian.money for guardian in guardians)
    employed_guardians = sum(guardian.employed for guardian in guardians)
    guardian_stress = sum(
        guardian.stress
        for guardian in guardians
    ) / len(guardians)
    relationship_support = _relationship_support(
        child,
        guardians,
        social,
    )
    resource_security = _clamp(household_money / 600.0)
    employment_stability = employed_guardians / len(guardians)
    family_support = _clamp(
        0.45 * relationship_support
        + 0.30 * (1 - guardian_stress)
        + 0.25 * resource_security
    )
    learning_potential = _clamp(
        (
            child.traits["discipline"]
            + child.traits["ambition"]
        )
        / 2
    )
    school_opportunity = _clamp(
        0.45 * resource_security
        + 0.30 * employment_stability
        + 0.25 * family_support
    )
    school_age = SCHOOL_START_AGE <= age < ADULT_AGE
    school_access = (
        school_available
        and school_age
        and school_opportunity >= SCHOOL_OPPORTUNITY_THRESHOLD
    )
    practice = 1.0 if school_access else 0.0
    feedback = (
        0.5 + 0.5 * family_support
        if school_access
        else 0.0
    )
    skill_before = child.skill
    potential_skill_gain = (
        ANNUAL_SKILL_RATE
        * learning_potential
        * practice
        * school_opportunity
        * feedback
    )
    skill_after = _clamp(skill_before + potential_skill_gain)
    skill_gain = skill_after - skill_before
    record = DevelopmentRecord(
        day=day,
        age=age,
        stage=developmental_stage(age),
        guardian_ids=tuple(guardian.id for guardian in guardians),
        household_money=household_money,
        employed_guardians=employed_guardians,
        guardian_stress=guardian_stress,
        relationship_support=relationship_support,
        learning_potential=learning_potential,
        school_opportunity=school_opportunity,
        school_available=school_available,
        school_access=school_access,
        practice=practice,
        feedback=feedback,
        skill_before=skill_before,
        skill_gain=skill_gain,
        skill_after=skill_after,
    )
    state = DevelopmentState(
        records=child.development.records + (record,),
    )
    return DevelopmentOutcome(
        state=state,
        skill=skill_after,
        became_adult=age == ADULT_AGE,
    )


def development_state_from_data(data: object) -> DevelopmentState:
    """Parse persisted development without inventing missing history."""
    if not isinstance(data, dict) or set(data) != {"records"}:
        raise ValueError("Invalid development state structure.")
    records_data = data["records"]
    if not isinstance(records_data, list):
        raise ValueError("Development records must be stored as a list.")

    expected_fields = set(DevelopmentRecord.__dataclass_fields__)
    records = []
    for item in records_data:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ValueError("Invalid development record structure.")
        guardian_ids = item["guardian_ids"]
        if not isinstance(guardian_ids, list):
            raise ValueError("Development guardian IDs must be a list.")
        records.append(DevelopmentRecord(
            **{
                **item,
                "guardian_ids": tuple(guardian_ids),
            }
        ))

    state = DevelopmentState(records=tuple(records))
    validate_development_state(state)
    return state


def validate_development_state(state: DevelopmentState) -> None:
    if not isinstance(state.records, tuple):
        raise ValueError("Invalid development state values.")

    previous = None
    for record in state.records:
        if not isinstance(record, DevelopmentRecord):
            raise ValueError("Invalid development record values.")
        numeric = (
            record.household_money,
            record.guardian_stress,
            record.relationship_support,
            record.learning_potential,
            record.school_opportunity,
            record.practice,
            record.feedback,
            record.skill_before,
            record.skill_gain,
            record.skill_after,
        )
        if (
            isinstance(record.day, bool)
            or not isinstance(record.day, int)
            or record.day < 0
            or isinstance(record.age, bool)
            or not isinstance(record.age, int)
            or not 1 <= record.age <= ADULT_AGE
            or record.stage != developmental_stage(record.age)
            or not isinstance(record.guardian_ids, tuple)
            or not record.guardian_ids
            or len(record.guardian_ids) != len(set(record.guardian_ids))
            or any(
                not isinstance(agent_id, str) or not agent_id
                for agent_id in record.guardian_ids
            )
            or isinstance(record.employed_guardians, bool)
            or not isinstance(record.employed_guardians, int)
            or not 0 <= record.employed_guardians <= len(record.guardian_ids)
            or not isinstance(record.school_access, bool)
            or not isinstance(record.school_available, bool)
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in numeric
            )
            or not 0.0 <= record.guardian_stress <= 1.0
            or not 0.0 <= record.relationship_support <= 1.0
            or not 0.0 <= record.learning_potential <= 1.0
            or not 0.0 <= record.school_opportunity <= 1.0
            or record.practice not in (0.0, 1.0)
            or not 0.0 <= record.feedback <= 1.0
            or not 0.0 <= record.skill_before <= 1.0
            or not 0.0 <= record.skill_gain <= 1.0
            or not 0.0 <= record.skill_after <= 1.0
            or record.school_access != (record.practice == 1.0)
            or record.school_access != (
                record.school_available
                and SCHOOL_START_AGE <= record.age < ADULT_AGE
                and record.school_opportunity
                >= SCHOOL_OPPORTUNITY_THRESHOLD
            )
            or (
                record.school_access
                and not SCHOOL_START_AGE <= record.age < ADULT_AGE
            )
            or not math.isclose(
                record.skill_after,
                record.skill_before + record.skill_gain,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("Invalid development record values.")

        if previous is not None and (
            record.day <= previous.day
            or record.age <= previous.age
            or record.skill_before != previous.skill_after
        ):
            raise ValueError("Development history is inconsistent.")
        previous = record


def validate_development_links(
    agents: list[Agent],
    *,
    current_day: int | None = None,
) -> None:
    agents_by_id = {agent.id: agent for agent in agents}
    for agent in agents:
        validate_development_state(agent.development)
        if not agent.family.parent_ids:
            if agent.development.records:
                raise ValueError("Founders cannot have child development.")
            continue

        for record in agent.development.records:
            if any(
                guardian_id not in agents_by_id
                for guardian_id in record.guardian_ids
            ):
                raise ValueError("Development references missing guardian.")
            expected_day = agent.family.birth_day + record.age * 365
            if record.day != expected_day:
                raise ValueError("Development record is not an anniversary.")
            if current_day is not None and record.day > current_day:
                raise ValueError("Development record is in the future.")
            expected_potential = _clamp(
                (
                    agent.traits["discipline"]
                    + agent.traits["ambition"]
                )
                / 2
            )
            if not math.isclose(
                record.learning_potential,
                expected_potential,
                abs_tol=1e-12,
            ):
                raise ValueError("Development aptitude is inconsistent.")

        if (
            agent.development.records
            and agent.development.records[-1].age == ADULT_AGE
            and agent.family.dependent
        ):
            raise ValueError("Adult development retained dependency.")
