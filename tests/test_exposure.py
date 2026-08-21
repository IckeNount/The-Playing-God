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
        low_a = SimpleNamespace(sociability=0.0)
        low_b = SimpleNamespace(sociability=0.0)

        high_a = SimpleNamespace(sociability=1.0)
        high_b = SimpleNamespace(sociability=1.0)

        low = interaction_probability(low_a, low_b)
        high = interaction_probability(high_a, high_b)

        self.assertLess(low, high)

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

if __name__ == "__main__":
    unittest.main()