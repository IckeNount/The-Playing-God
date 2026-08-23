from __future__ import annotations

import math
import random

from playing_god.core.agent import Agent, clamp
from playing_god.core.prayer import prayer_need


def money_pressure(a: Agent) -> float:
    return clamp((260 - a.money) / 260)


def belonging_need(a: Agent) -> float:
    positive_ties = [max(0, x) for x in a.relationships.values()]
    average = (
        sum(positive_ties) / len(positive_ties)
        if positive_ties
        else 0.0
    )
    return clamp(0.55 - average)


def status_need(a: Agent) -> float:
    current_status = (
        0.18 * a.job_level
        + 0.25 * max(0, a.reputation)
    )
    return clamp(0.65 - current_status)


def scores(a: Agent) -> dict[str, float]:
    t = a.traits
    s = a.sins

    money = money_pressure(a)
    belonging = belonging_need(a)
    status = status_need(a)
    tired = 1 - a.energy
    socially_tired = 1 - a.social_energy

    return {
        "work": (
            1.2 * t["discipline"]
            + 0.7 * t["ambition"]
            + 0.5 * s["greed"]
            + money
            - s["sloth"]
            - 0.7 * tired
        ) if a.employed else -99,

        "job_hunt": (
            1.3 * t["ambition"]
            + 0.8 * t["discipline"]
            + 1.2 * money
            + 0.4 * s["greed"]
            - 0.8 * s["sloth"]
        ) if not a.employed else -99,

        "train": (
            1.0 * t["ambition"]
            + 0.9 * t["discipline"]
            + 0.7 * status
            - 0.8 * s["sloth"]
            - 0.5 * tired
        ),

        "socialize": (
            1.3 * t["sociability"]
            + belonging
            + 0.35 * s["lust"]
            - 0.5 * socially_tired
            - 0.3 * a.stress
        ),

        "help": (
            1.4 * t["empathy"]
            + 0.5 * belonging
            + 0.2 * s["pride"]
            - 0.8 * money
            - 0.4 * socially_tired
        ),

        "compete": (
            0.9 * t["ambition"]
            + 0.75 * s["envy"]
            + 0.6 * s["pride"]
            + 0.4 * status
            - 0.7 * t["empathy"]
            + 0.2 * s["wrath"]
            - 0.35 * socially_tired
        ),

        "risky_move": (
            1.1 * t["risk_tolerance"]
            + 0.9 * s["greed"]
            + 0.6 * money
            + 0.4 * t["ambition"]
            - 0.5 * t["discipline"]
        ),

        "pray": prayer_need(a),

        "rest": (
            1.5 * tired
            + 1.1 * a.stress
            + 0.45 * s["sloth"]
            + 0.25 * s["gluttony"]
        ),
    }


def choose(
    a: Agent,
    rng: random.Random,
    *,
    score_adjustments: dict[str, float] | None = None,
) -> str:
    action_scores = scores(a)

    if score_adjustments:
        for action, adjustment in score_adjustments.items():
            if action in action_scores:
                action_scores[action] += adjustment

    available = [
        (name, score)
        for name, score in action_scores.items()
        if score > -50
    ]

    peak = max(score for _, score in available)

    temperature = 0.75

    weights = [
        math.exp((score - peak) / temperature)
        for _, score in available
    ]

    return rng.choices(
        [name for name, _ in available],
        weights=weights,
        k=1,
    )[0]
