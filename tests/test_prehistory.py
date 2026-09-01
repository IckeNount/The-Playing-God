from __future__ import annotations

import unittest

from dataclasses import asdict

from playing_god.core.prehistory import (
    FOUNDER_EVENT_KINDS,
    FOUNDER_STATE_FIELDS,
    founder_starting_state,
)
from playing_god.core.world import World


class FounderPrehistoryTests(unittest.TestCase):

    def test_compact_history_causes_important_starting_state(self):
        world = World(seed=1947, population=3)

        for agent in world.agents:
            self.assertEqual(
                tuple(
                    event.kind
                    for event in agent.founder_prehistory
                ),
                FOUNDER_EVENT_KINDS,
            )
            starting_state = founder_starting_state(
                agent.founder_prehistory
            )

            for field in FOUNDER_STATE_FIELDS:
                self.assertEqual(
                    getattr(agent, field),
                    starting_state[field],
                )

            self.assertEqual(agent.adaptive_values, {})

    def test_same_seed_repeats_exact_founder_history(self):
        first = World(seed=71, population=4)
        second = World(seed=71, population=4)

        self.assertEqual(
            [
                [asdict(event) for event in agent.founder_prehistory]
                for agent in first.agents
            ],
            [
                [asdict(event) for event in agent.founder_prehistory]
                for agent in second.agents
            ],
        )
        self.assertEqual(first.rng.getstate(), second.rng.getstate())

    def test_priors_remain_separate_from_lived_history(self):
        agent = World(seed=1947, population=1).agents[0]
        effect_fields = {
            field
            for event in agent.founder_prehistory
            for field in event.effects
        }

        self.assertTrue(effect_fields.isdisjoint(agent.traits))
        self.assertTrue(effect_fields.isdisjoint(agent.sins))


if __name__ == "__main__":
    unittest.main()
