from __future__ import annotations

from dataclasses import dataclass
import math
from random import Random


FOUNDER_EVENT_KINDS = (
    "capability_exposure",
    "livelihood_entry",
    "recent_conditions",
)

FOUNDER_STATE_FIELDS = (
    "skill",
    "employed",
    "salary",
    "job_level",
    "money",
    "energy",
    "social_energy",
    "stress",
    "reputation",
)

_EVENT_YEARS = {
    "capability_exposure": 6,
    "livelihood_entry": 2,
    "recent_conditions": 0,
}

_EVENT_EFFECT_FIELDS = {
    "capability_exposure": {"skill"},
    "livelihood_entry": {
        "employed",
        "salary",
        "job_level",
    },
    "recent_conditions": {
        "money",
        "energy",
        "social_energy",
        "stress",
        "reputation",
    },
}


@dataclass(frozen=True)
class FounderEvent:
    kind: str
    years_before_start: int
    effects: dict[str, float | int | bool]


def generate_founder_prehistory(
    rng: Random,
) -> tuple[int, list[FounderEvent]]:
    """Generate three compact prior-life records for one G0 adult."""
    employed = rng.random() < 0.70
    skill = rng.uniform(0.20, 0.60)
    job_level = (
        rng.choice([1, 1, 1, 2])
        if employed
        else 0
    )
    salary = (
        22 + 7 * job_level + 8 * skill
        if employed
        else 0
    )
    age = rng.randint(20, 38)
    money = rng.uniform(120, 520)
    energy = rng.uniform(0.55, 0.95)
    stress = rng.uniform(0.10, 0.45)
    reputation = rng.uniform(-0.10, 0.20)

    return age, [
        FounderEvent(
            kind="capability_exposure",
            years_before_start=6,
            effects={"skill": skill},
        ),
        FounderEvent(
            kind="livelihood_entry",
            years_before_start=2,
            effects={
                "employed": employed,
                "salary": salary,
                "job_level": job_level,
            },
        ),
        FounderEvent(
            kind="recent_conditions",
            years_before_start=0,
            effects={
                "money": money,
                "energy": energy,
                "social_energy": energy,
                "stress": stress,
                "reputation": reputation,
            },
        ),
    ]


def founder_starting_state(
    prehistory: list[FounderEvent],
) -> dict[str, float | int | bool]:
    """Reduce structured founder history into authoritative G0 state."""
    if tuple(event.kind for event in prehistory) != FOUNDER_EVENT_KINDS:
        raise ValueError(
            "Founder prehistory must contain the three canonical events."
        )

    state: dict[str, float | int | bool] = {}

    for event in prehistory:
        if (
            event.years_before_start != _EVENT_YEARS[event.kind]
            or set(event.effects) != _EVENT_EFFECT_FIELDS[event.kind]
        ):
            raise ValueError(
                f"Invalid founder event structure: {event.kind}"
            )

        for field, value in event.effects.items():
            if field in state:
                raise ValueError(
                    f"Founder state field appears more than once: {field}"
                )
            state[field] = value

    missing = set(FOUNDER_STATE_FIELDS) - set(state)
    extra = set(state) - set(FOUNDER_STATE_FIELDS)
    if missing or extra:
        raise ValueError(
            "Founder prehistory does not define exact starting state."
        )

    numeric_fields = set(FOUNDER_STATE_FIELDS) - {
        "employed",
        "job_level",
    }
    if (
        not isinstance(state["employed"], bool)
        or isinstance(state["job_level"], bool)
        or not isinstance(state["job_level"], int)
        or state["job_level"] < 0
        or any(
            isinstance(state[field], bool)
            or not isinstance(state[field], (int, float))
            or not math.isfinite(state[field])
            for field in numeric_fields
        )
    ):
        raise ValueError("Founder prehistory contains invalid effect values.")

    if (
        not 0.0 <= state["skill"] <= 1.0
        or state["money"] < 0.0
        or state["salary"] < 0.0
        or not 0.0 <= state["energy"] <= 1.0
        or not 0.0 <= state["social_energy"] <= 1.0
        or not 0.0 <= state["stress"] <= 1.0
        or not -1.0 <= state["reputation"] <= 1.0
        or (
            not state["employed"]
            and (
                state["job_level"] != 0
                or state["salary"] != 0.0
            )
        )
        or (
            state["employed"]
            and (
                state["job_level"] < 1
                or state["salary"] <= 0.0
            )
        )
    ):
        raise ValueError("Founder prehistory effects are inconsistent.")

    return state


def founder_prehistory_from_data(
    data: object,
) -> list[FounderEvent]:
    """Parse persisted structured history using the model's strict shape."""
    if not isinstance(data, list):
        raise ValueError("Founder prehistory must be a list.")
    if not data:
        return []

    events = []
    for item in data:
        if (
            not isinstance(item, dict)
            or set(item) != {
                "kind",
                "years_before_start",
                "effects",
            }
            or not isinstance(item["kind"], str)
            or isinstance(item["years_before_start"], bool)
            or not isinstance(item["years_before_start"], int)
            or not isinstance(item["effects"], dict)
            or any(
                not isinstance(field, str)
                for field in item["effects"]
            )
        ):
            raise ValueError("Invalid founder prehistory record.")

        events.append(
            FounderEvent(
                kind=item["kind"],
                years_before_start=item["years_before_start"],
                effects=dict(item["effects"]),
            )
        )

    founder_starting_state(events)
    return events
