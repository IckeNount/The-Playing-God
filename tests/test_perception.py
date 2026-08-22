import unittest

from playing_god.core.perception import (
    Observation,
    belief_key,
    perceive,
    update_belief,
)
from playing_god.core.world import World


class PerceptionTests(unittest.TestCase):

    def test_interaction_creates_reciprocal_location_beliefs(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "market"
        second.current_location = "market"
        first.traits["sociability"] = 1.0
        second.traits["sociability"] = 1.0
        world.day = 1

        interactions = world.resolve_daily_interactions()

        self.assertEqual(len(interactions), 1)
        self.assertEqual(len(first.observations), 1)
        self.assertEqual(len(second.observations), 1)

        observation = first.observations[0]
        self.assertEqual(observation.kind, "agent_location")
        self.assertEqual(observation.subject_id, second.id)
        self.assertEqual(observation.value, "market")
        self.assertEqual(observation.source_id, second.id)

        belief = first.beliefs[
            belief_key("agent_location", second.id)
        ]
        self.assertEqual(belief.value, "market")
        self.assertEqual(belief.confidence, 1.0)
        self.assertEqual(belief.evidence_count, 1)

    def test_world_truth_does_not_silently_refresh_belief(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "market"
        second.current_location = "market"
        first.traits["sociability"] = 1.0
        second.traits["sociability"] = 1.0
        world.day = 1
        world.resolve_daily_interactions()

        second.current_location = "work"

        belief = first.beliefs[
            belief_key("agent_location", second.id)
        ]
        self.assertEqual(second.current_location, "work")
        self.assertEqual(belief.value, "market")

    def test_perception_confidence_is_separate_from_observation(self):
        observation = Observation(
            day=3,
            kind="agent_location",
            subject_id="npc_002",
            value="cafe",
            source_id="npc_002",
            reliability=0.8,
            location="cafe",
        )

        perception = perceive(observation, attention=0.5)

        self.assertEqual(observation.reliability, 0.8)
        self.assertEqual(perception.confidence, 0.4)

    def test_new_evidence_updates_belief_without_mutating_history(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        first = Observation(
            day=1,
            kind="agent_location",
            subject_id="npc_002",
            value="market",
            source_id="npc_002",
            reliability=1.0,
            location="market",
        )
        second = Observation(
            day=2,
            kind="agent_location",
            subject_id="npc_002",
            value="work",
            source_id="npc_002",
            reliability=0.7,
            location="work",
        )

        update_belief(agent, perceive(first))
        update_belief(agent, perceive(second))

        belief = agent.beliefs[
            belief_key("agent_location", "npc_002")
        ]
        self.assertEqual(first.value, "market")
        self.assertEqual(belief.value, "work")
        self.assertEqual(belief.confidence, 0.7)
        self.assertEqual(belief.updated_day, 2)
        self.assertEqual(belief.evidence_count, 2)


if __name__ == "__main__":
    unittest.main()
