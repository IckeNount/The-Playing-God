from __future__ import annotations

import unittest

from playing_god.core.decision import choose
from playing_god.core.world import World


class PeakChoiceRandom:
    """Select the largest supplied weight while exposing the candidates."""

    def __init__(self) -> None:
        self.population: list[str] = []

    def choices(
        self,
        population: list[str],
        *,
        weights: list[float],
        k: int,
    ) -> list[str]:
        self.population = population
        winner = max(
            range(len(population)),
            key=weights.__getitem__,
        )
        return [population[winner]]


class AdaptiveDecisionBoundaryTests(unittest.TestCase):
    def test_learned_preference_can_change_choice_among_valid_actions(self):
        agent = World(seed=1947, population=1).agents[0]
        rng = PeakChoiceRandom()

        action = choose(
            agent,
            rng,
            learned_preferences={"train": 100.0},
        )

        self.assertEqual(action, "train")
        self.assertIn("train", rng.population)

    def test_preferences_cannot_make_an_ineligible_action_available(self):
        agent = World(seed=1947, population=1).agents[0]
        agent.employed = False
        rng = PeakChoiceRandom()

        choose(
            agent,
            rng,
            score_adjustments={"work": 100.0},
            learned_preferences={"work": 100.0},
        )

        self.assertNotIn("work", rng.population)


if __name__ == "__main__":
    unittest.main()
