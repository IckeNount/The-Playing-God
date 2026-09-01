from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


RETIREMENT_AGE = 65
MIN_MORTALITY_AGE = 70
MAX_MORTALITY_AGE = 90
ANNUAL_DEPENDENT_SUPPORT = 48.0


@dataclass(frozen=True)
class SupportContribution:
    guardian_id: str
    amount: float


@dataclass(frozen=True)
class HouseholdSupportRecord:
    day: int
    age: int
    dependent_id: str
    guardian_ids: tuple[str, ...]
    contributions: tuple[SupportContribution, ...]
    total_support: float
    stress_before: float
    stress_after: float


@dataclass(frozen=True)
class InheritanceTransfer:
    day: int
    deceased_id: str
    heir_id: str
    amount: float


@dataclass(frozen=True)
class MortalityCheck:
    day: int
    age: int
    probability: float
    roll: float
    died: bool


@dataclass(frozen=True)
class DeathRecord:
    day: int
    age: int
    estate: float
    transfers: tuple[InheritanceTransfer, ...]
    unallocated: float


@dataclass(frozen=True)
class LifecycleState:
    alive: bool = True
    retired: bool = False
    retirement_day: int | None = None
    last_age_day: int | None = None
    support_received: tuple[HouseholdSupportRecord, ...] = ()
    inheritance_received: tuple[InheritanceTransfer, ...] = ()
    mortality_checks: tuple[MortalityCheck, ...] = ()
    death: DeathRecord | None = None


@dataclass(frozen=True)
class HouseholdSnapshot:
    dependent_id: str
    guardian_ids: tuple[str, ...]
    living_guardian_ids: tuple[str, ...]
    available_money: float
    employed_guardians: int
    average_guardian_stress: float
    annual_support_target: float


def mortality_probability(age: int, stress: float) -> float:
    if age < MIN_MORTALITY_AGE:
        return 0.0
    if age >= MAX_MORTALITY_AGE:
        return 1.0
    return min(
        1.0,
        0.03
        + 0.04 * (age - MIN_MORTALITY_AGE)
        + 0.12 * max(0.0, min(1.0, stress)),
    )


def household_snapshot(
    dependent: Agent,
    agents_by_id: dict[str, Agent],
) -> HouseholdSnapshot:
    if not dependent.family.parent_ids:
        raise ValueError("Household snapshots require a later-generation agent.")
    guardians = [
        agents_by_id[guardian_id]
        for guardian_id in dependent.family.guardian_ids
    ]
    living = [guardian for guardian in guardians if guardian.lifecycle.alive]
    return HouseholdSnapshot(
        dependent_id=dependent.id,
        guardian_ids=dependent.family.guardian_ids,
        living_guardian_ids=tuple(guardian.id for guardian in living),
        available_money=(
            max(0.0, dependent.money)
            + sum(
                max(0.0, guardian.money)
                for guardian in living
            )
        ),
        employed_guardians=sum(guardian.employed for guardian in living),
        average_guardian_stress=(
            sum(guardian.stress for guardian in living) / len(living)
            if living
            else 1.0
        ),
        annual_support_target=ANNUAL_DEPENDENT_SUPPORT,
    )


def lifecycle_state_from_data(data: object) -> LifecycleState:
    """Parse persisted lifecycle state without reconstructing history."""
    if not isinstance(data, dict) or set(data) != {
        "alive",
        "retired",
        "retirement_day",
        "last_age_day",
        "support_received",
        "inheritance_received",
        "mortality_checks",
        "death",
    }:
        raise ValueError("Invalid lifecycle state structure.")

    def records(value: object, cls, nested=()):
        if not isinstance(value, list):
            raise ValueError("Lifecycle histories must be stored as lists.")
        expected = set(cls.__dataclass_fields__)
        parsed = []
        for item in value:
            if not isinstance(item, dict) or set(item) != expected:
                raise ValueError("Invalid lifecycle record structure.")
            values = dict(item)
            for field_name, nested_cls in nested:
                nested_value = values[field_name]
                if not isinstance(nested_value, list):
                    raise ValueError("Nested lifecycle history must be a list.")
                nested_expected = set(nested_cls.__dataclass_fields__)
                nested_records = []
                for nested_item in nested_value:
                    if (
                        not isinstance(nested_item, dict)
                        or set(nested_item) != nested_expected
                    ):
                        raise ValueError("Invalid nested lifecycle record.")
                    nested_records.append(nested_cls(**nested_item))
                values[field_name] = tuple(nested_records)
            if "guardian_ids" in values:
                if not isinstance(values["guardian_ids"], list):
                    raise ValueError("Lifecycle IDs must be stored as a list.")
                values["guardian_ids"] = tuple(values["guardian_ids"])
            parsed.append(cls(**values))
        return tuple(parsed)

    support_received = records(
        data["support_received"],
        HouseholdSupportRecord,
        (("contributions", SupportContribution),),
    )
    inheritance_received = records(
        data["inheritance_received"],
        InheritanceTransfer,
    )
    mortality_checks = records(
        data["mortality_checks"],
        MortalityCheck,
    )
    death_data = data["death"]
    death = None
    if death_data is not None:
        parsed_death = records(
            [death_data],
            DeathRecord,
            (("transfers", InheritanceTransfer),),
        )
        death = parsed_death[0]

    state = LifecycleState(
        alive=data["alive"],
        retired=data["retired"],
        retirement_day=data["retirement_day"],
        last_age_day=data["last_age_day"],
        support_received=support_received,
        inheritance_received=inheritance_received,
        mortality_checks=mortality_checks,
        death=death,
    )
    validate_lifecycle_state(state)
    return state


def _valid_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _valid_day(value: object) -> bool:
    return (
        value is None
        or (
            not isinstance(value, bool)
            and isinstance(value, int)
            and value >= 0
        )
    )


def _valid_required_day(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and value >= 0
    )


def validate_lifecycle_state(state: LifecycleState) -> None:
    if (
        not isinstance(state.alive, bool)
        or not isinstance(state.retired, bool)
        or not _valid_day(state.retirement_day)
        or not _valid_day(state.last_age_day)
        or state.retired != (state.retirement_day is not None)
        or state.alive != (state.death is None)
        or not all(
            isinstance(history, tuple)
            for history in (
                state.support_received,
                state.inheritance_received,
                state.mortality_checks,
            )
        )
    ):
        raise ValueError("Invalid lifecycle state values.")

    previous_day = -1
    for record in state.support_received:
        if (
            not isinstance(record, HouseholdSupportRecord)
            or not _valid_required_day(record.day)
            or record.day <= previous_day
            or isinstance(record.age, bool)
            or not isinstance(record.age, int)
            or not 1 <= record.age < 18
            or not isinstance(record.dependent_id, str)
            or not record.dependent_id
            or not isinstance(record.guardian_ids, tuple)
            or not record.guardian_ids
            or len(record.guardian_ids) != len(set(record.guardian_ids))
            or not isinstance(record.contributions, tuple)
            or tuple(
                contribution.guardian_id
                for contribution in record.contributions
            ) != record.guardian_ids
            or any(
                not isinstance(contribution, SupportContribution)
                or not _valid_number(contribution.amount)
                or contribution.amount < 0.0
                for contribution in record.contributions
            )
            or not all(_valid_number(value) for value in (
                record.total_support,
                record.stress_before,
                record.stress_after,
            ))
            or record.total_support < 0.0
            or not 0.0 <= record.stress_before <= 1.0
            or not 0.0 <= record.stress_after <= 1.0
            or not math.isclose(
                record.total_support,
                sum(
                    contribution.amount
                    for contribution in record.contributions
                ),
                abs_tol=1e-12,
            )
        ):
            raise ValueError("Invalid household support history.")
        previous_day = record.day

    for transfer in state.inheritance_received:
        if not _valid_transfer(transfer):
            raise ValueError("Invalid inheritance history.")

    previous_age = MIN_MORTALITY_AGE - 1
    for check in state.mortality_checks:
        if (
            not isinstance(check, MortalityCheck)
            or not _valid_required_day(check.day)
            or isinstance(check.age, bool)
            or not isinstance(check.age, int)
            or check.age <= previous_age
            or check.age < MIN_MORTALITY_AGE
            or not _valid_number(check.probability)
            or not 0.0 <= check.probability <= 1.0
            or not _valid_number(check.roll)
            or not 0.0 <= check.roll <= 1.0
            or not isinstance(check.died, bool)
            or check.died != (check.roll < check.probability)
        ):
            raise ValueError("Invalid mortality history.")
        previous_age = check.age

    if state.death is not None:
        death = state.death
        if (
            not isinstance(death, DeathRecord)
            or not _valid_required_day(death.day)
            or isinstance(death.age, bool)
            or not isinstance(death.age, int)
            or death.age < MIN_MORTALITY_AGE
            or not _valid_number(death.estate)
            or death.estate < 0.0
            or not isinstance(death.transfers, tuple)
            or any(not _valid_transfer(item) for item in death.transfers)
            or not _valid_number(death.unallocated)
            or death.unallocated < 0.0
            or not state.mortality_checks
            or not state.mortality_checks[-1].died
            or state.mortality_checks[-1].day != death.day
            or state.mortality_checks[-1].age != death.age
            or not math.isclose(
                death.estate,
                sum(item.amount for item in death.transfers)
                + death.unallocated,
                abs_tol=1e-9,
            )
        ):
            raise ValueError("Invalid death history.")


def _valid_transfer(transfer: object) -> bool:
    return (
        isinstance(transfer, InheritanceTransfer)
        and _valid_required_day(transfer.day)
        and isinstance(transfer.deceased_id, str)
        and bool(transfer.deceased_id)
        and isinstance(transfer.heir_id, str)
        and bool(transfer.heir_id)
        and transfer.deceased_id != transfer.heir_id
        and _valid_number(transfer.amount)
        and transfer.amount >= 0.0
    )


def validate_lifecycle_links(
    agents: list[Agent],
    *,
    current_day: int | None = None,
) -> None:
    agents_by_id = {agent.id: agent for agent in agents}
    receipts = {
        (
            transfer.deceased_id,
            transfer.heir_id,
            transfer.day,
            transfer.amount,
        )
        for agent in agents
        for transfer in agent.lifecycle.inheritance_received
    }

    for agent in agents:
        validate_lifecycle_state(agent.lifecycle)
        if not agent.lifecycle.alive and agent.employed:
            raise ValueError("A deceased agent cannot remain employed.")
        if agent.lifecycle.retired and agent.employed:
            raise ValueError("A retired agent cannot remain employed.")
        if not agent.lifecycle.alive and agent.money != 0.0:
            raise ValueError("A deceased estate was not closed.")
        if current_day is not None:
            days = [
                record.day
                for record in agent.lifecycle.support_received
            ] + [
                record.day
                for record in agent.lifecycle.inheritance_received
            ] + [
                record.day
                for record in agent.lifecycle.mortality_checks
            ]
            if any(day > current_day for day in days):
                raise ValueError("Lifecycle history is in the future.")
            if (
                agent.lifecycle.retirement_day is not None
                and agent.lifecycle.retirement_day > current_day
            ):
                raise ValueError("Retirement history is in the future.")
            if (
                agent.lifecycle.last_age_day is not None
                and agent.lifecycle.last_age_day > current_day
            ):
                raise ValueError("Lifecycle age history is in the future.")
        if agent.lifecycle.retired and agent.age < RETIREMENT_AGE:
            raise ValueError("Retirement age is inconsistent.")

        for record in agent.lifecycle.support_received:
            if (
                not agent.family.parent_ids
                or agent.family.birth_day is None
            ):
                raise ValueError("Founder cannot receive dependent support.")
            if record.dependent_id != agent.id:
                raise ValueError("Household support owner is inconsistent.")
            if any(
                guardian_id not in agents_by_id
                for guardian_id in record.guardian_ids
            ):
                raise ValueError("Household support guardian is missing.")
            if agent.family.birth_day + record.age * 365 != record.day:
                raise ValueError("Household support is not an anniversary.")

        for transfer in agent.lifecycle.inheritance_received:
            if (
                transfer.heir_id != agent.id
                or transfer.deceased_id not in agents_by_id
            ):
                raise ValueError("Inheritance receipt is inconsistent.")
            deceased = agents_by_id[transfer.deceased_id]
            if (
                deceased.lifecycle.death is None
                or transfer not in deceased.lifecycle.death.transfers
                or agent.id not in deceased.family.child_ids
            ):
                raise ValueError("Inheritance source is inconsistent.")

        death = agent.lifecycle.death
        if death is None:
            continue
        if (
            death.age != agent.age
            or not agent.lifecycle.retired
            or agent.lifecycle.last_age_day != death.day
        ):
            raise ValueError("Death age is inconsistent.")
        if current_day is not None and death.day > current_day:
            raise ValueError("Death history is in the future.")
        for transfer in death.transfers:
            if transfer.deceased_id != agent.id:
                raise ValueError("Estate owner is inconsistent.")
            key = (
                transfer.deceased_id,
                transfer.heir_id,
                transfer.day,
                transfer.amount,
            )
            if key not in receipts:
                raise ValueError("Inheritance receipt is missing.")
