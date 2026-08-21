import unittest
from types import SimpleNamespace

from playing_god.core.exposure import detect_exposures

import random

from playing_god.core.exposure import (
    Exposure,
    detect_exposures,
    interaction_probability,
    resolve_interactions,
)
from playing_god.core.world import World

class ExposureTests(unittest.TestCase):

    def test_agents_at_same_location_are_exposed(self):
        agents = [
            SimpleNamespace(
                id="npc_001",
                current_location="market",
            ),
            SimpleNamespace(
                id="npc_002",
                current_location="market",
            ),
            SimpleNamespace(
                id="npc_003",
                current_location="home",
            ),
        ]

        exposures = detect_exposures(agents)

        self.assertEqual(len(exposures), 1)

        exposure = exposures[0]

        self.assertEqual(exposure.agent_a, "npc_001")
        self.assertEqual(exposure.agent_b, "npc_002")
        self.assertEqual(exposure.location, "market")

    def test_three_agents_create_three_possible_pairs(self):
        agents = [
            SimpleNamespace(id="npc_001", current_location="cafe"),
            SimpleNamespace(id="npc_002", current_location="cafe"),
            SimpleNamespace(id="npc_003", current_location="cafe"),
        ]

        exposures = detect_exposures(agents)

        self.assertEqual(len(exposures), 3)

    def test_different_locations_create_no_exposure(self):
        agents = [
            SimpleNamespace(id="npc_001", current_location="home"),
            SimpleNamespace(id="npc_002", current_location="factory"),
        ]

        exposures = detect_exposures(agents)

        self.assertEqual(exposures, [])

    def test_sociability_affects_interaction_probability(self):
        low_a = SimpleNamespace(traits={"sociability": 0.0})
        low_b = SimpleNamespace(traits={"sociability": 0.0})

        high_a = SimpleNamespace(traits={"sociability": 1.0})
        high_b = SimpleNamespace(traits={"sociability": 1.0})

        low = interaction_probability(low_a, low_b)
        high = interaction_probability(high_a, high_b)

        self.assertLess(low, high)

    def test_social_energy_affects_interaction_probability(self):
        rested = SimpleNamespace(
            traits={"sociability": 1.0},
            social_energy=1.0,
        )
        depleted = SimpleNamespace(
            traits={"sociability": 1.0},
            social_energy=0.0,
        )

        high = interaction_probability(rested, rested)
        low = interaction_probability(depleted, depleted)

        self.assertGreater(high, low)
        self.assertEqual(low, 0.0)

    def test_interaction_resolution_is_reproducible(self):
        agents = {
            "npc_001": SimpleNamespace(
                id="npc_001",
                sociability=0.8,
            ),
            "npc_002": SimpleNamespace(
                id="npc_002",
                sociability=0.8,
            ),
        }

        exposures = [
            Exposure(
                agent_a="npc_001",
                agent_b="npc_002",
                location="market",
            )
        ]

        first = resolve_interactions(
            exposures,
            agents,
            random.Random(42),
        )

        second = resolve_interactions(
            exposures,
            agents,
            random.Random(42),
        )

        self.assertEqual(first, second)

    def test_world_interaction_requires_exposure_and_adds_familiarity(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "market"
        second.current_location = "market"
        first.traits["sociability"] = 1.0
        second.traits["sociability"] = 1.0
        world.day = 1

        before = world.social.get_relationship(
            first.id,
            second.id,
        )["familiarity"]
        interactions = world.resolve_daily_interactions()
        after = world.social.get_relationship(
            first.id,
            second.id,
        )["familiarity"]

        self.assertEqual(len(world.last_exposures), 1)
        self.assertEqual(len(interactions), 1)
        self.assertGreater(after, before)
        self.assertEqual(
            after,
            world.social.get_relationship(
                second.id,
                first.id,
            )["familiarity"],
        )

        first_event = first.events[-1]
        second_event = second.events[-1]
        self.assertEqual(first_event.kind, "interaction")
        self.assertEqual(first_event.target_id, second.id)
        self.assertEqual(first_event.location, "market")
        self.assertEqual(second_event.target_id, first.id)
        self.assertEqual(second_event.location, "market")
        self.assertLess(first.social_energy, first.energy)
        self.assertLess(second.social_energy, second.energy)

    def test_separate_locations_cannot_create_interaction(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "home"
        second.current_location = "work"
        world.day = 1

        before = world.social.get_relationship(
            first.id,
            second.id,
        )["familiarity"]
        interactions = world.resolve_daily_interactions()

        self.assertEqual(world.last_exposures, [])
        self.assertEqual(interactions, [])
        self.assertEqual(
            world.social.get_relationship(
                first.id,
                second.id,
            )["familiarity"],
            before,
        )

if __name__ == "__main__":
    unittest.main()
