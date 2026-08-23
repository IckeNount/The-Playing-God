from __future__ import annotations

import unittest

from playing_god.core.decision import scores
from playing_god.core.world import World


class PrayerTests(unittest.TestCase):
    def test_stress_increases_prayer_utility(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        agent.goal = "advance_career"
        agent.energy = 0.80
        agent.stress = 0.10
        low_stress_score = scores(agent)["pray"]

        agent.stress = 0.90
        high_stress_score = scores(agent)["pray"]

        self.assertGreater(
            high_stress_score,
            low_stress_score,
        )

    def test_prayer_at_shrine_creates_structured_record_and_event(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        world.day = 12
        agent.goal = "find_job"
        agent.employed = False
        agent.stress = 0.80
        agent.current_location = "shrine"

        world.act(agent, "pray")

        self.assertEqual(len(agent.prayers), 1)
        prayer = agent.prayers[0]
        self.assertEqual(prayer.agent_id, agent.id)
        self.assertEqual(prayer.desire_type, "employment")
        self.assertEqual(prayer.related_goal, "find_job")
        self.assertEqual(prayer.timestamp, 12)
        self.assertGreater(prayer.intensity, 0.0)
        self.assertLessEqual(prayer.intensity, 1.0)

        event = agent.events[-1]
        self.assertEqual(event.kind, "prayer")
        self.assertEqual(event.location, "shrine")
        self.assertEqual(event.significance, prayer.intensity)

    def test_prayer_is_not_recorded_away_from_shrine(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        agent.current_location = "home"

        world.act(agent, "pray")

        self.assertEqual(agent.prayers, [])
        self.assertFalse(
            any(event.kind == "prayer" for event in agent.events)
        )

    def test_seeded_run_produces_only_shrine_prayers(self):
        world = World(seed=1947)

        world.run(120)

        prayers = [
            prayer
            for agent in world.agents
            for prayer in agent.prayers
        ]
        prayer_events = [
            event
            for agent in world.agents
            for event in agent.events
            if event.kind == "prayer"
        ]

        self.assertGreater(len(prayers), 0)
        self.assertEqual(len(prayers), len(prayer_events))
        self.assertTrue(
            all(event.location == "shrine" for event in prayer_events)
        )


if __name__ == "__main__":
    unittest.main()
