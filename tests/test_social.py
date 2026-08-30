import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.show_social_graph import main as show_social_graph_main
from playing_god.core.social import SocialGraph
from playing_god.core.world import World


class TestSocialGraph(unittest.TestCase):

    def setUp(self):
        self.social = SocialGraph()

        self.social.add_agent("npc_001")
        self.social.add_agent("npc_002")

        self.social.add_relationship(
            "npc_001",
            "npc_002",
        )

        self.social.add_relationship(
            "npc_002",
            "npc_001",
        )

    def test_agents_are_added(self):
        self.assertEqual(
            self.social.node_count(),
            2,
        )

    def test_social_graph_command_loads_supplied_database(self):
        world = SimpleNamespace(social=object())

        with (
            patch(
                "scripts.show_social_graph.load_world",
                return_value=world,
            ) as load,
            patch(
                "scripts.show_social_graph.show_social_graph",
            ) as show,
        ):
            show_social_graph_main("example.db")

        load.assert_called_once_with("example.db")
        show.assert_called_once_with(world.social)

    def test_directed_relationships_exist(self):
        self.assertEqual(
            self.social.relationship_count(),
            2,
        )

    def test_help_increases_target_trust(self):
        before = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.social.apply_social_event(
            "npc_001",
            "npc_002",
            "help",
        )

        after = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.assertGreater(
            after["trust"],
            before["trust"],
        )

    def test_betrayal_reduces_trust(self):
        before = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.social.apply_social_event(
            "npc_001",
            "npc_002",
            "betray",
        )

        after = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.assertLess(
            after["trust"],
            before["trust"],
        )

    def test_betrayal_increases_hostility(self):
        before = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.social.apply_social_event(
            "npc_001",
            "npc_002",
            "betray",
        )

        after = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.assertGreater(
            after["hostility"],
            before["hostility"],
        )

    def test_relationship_values_are_clamped(self):
        for _ in range(20):
            self.social.apply_social_event(
                "npc_001",
                "npc_002",
                "help",
            )

        relationship = self.social.get_relationship(
            "npc_002",
            "npc_001",
        )

        self.assertLessEqual(
            relationship["trust"],
            1.0,
        )

    def test_unknown_social_event_fails(self):
        with self.assertRaises(ValueError):
            self.social.apply_social_event(
                "npc_001",
                "npc_002",
                "dance_on_table",
            )

    def test_socialize_without_exposure_cannot_change_affinity(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "cafe"
        target.current_location = "work"
        before = actor.relationships[target.id]

        world.act(actor, "socialize")

        self.assertEqual(
            actor.relationships[target.id],
            before,
        )

    def test_repeated_interaction_unlocks_relationship_change(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "cafe"
        target.current_location = "cafe"
        actor.traits["sociability"] = 1.0
        target.traits["sociability"] = 1.0

        for day in range(1, 11):
            world.day = day
            world.resolve_daily_interactions()
            familiarity = world.social.get_relationship(
                actor.id,
                target.id,
            )["familiarity"]
            if familiarity >= 0.22:
                break

        self.assertGreaterEqual(familiarity, 0.22)
        before = actor.relationships[target.id]

        world.act(actor, "socialize")

        self.assertNotEqual(
            actor.relationships[target.id],
            before,
        )

    def test_help_requires_familiar_exposure_before_trust_change(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "cafe"
        target.current_location = "cafe"
        target_money = target.money

        world.act(actor, "help")

        self.assertEqual(target.money, target_money)

        actor.traits["sociability"] = 1.0
        target.traits["sociability"] = 1.0
        for day in range(1, 11):
            world.day = day
            world.resolve_daily_interactions()
            familiarity = world.social.get_relationship(
                actor.id,
                target.id,
            )["familiarity"]
            if familiarity >= 0.22:
                break

        before_trust = world.social.get_relationship(
            target.id,
            actor.id,
        )["trust"]
        world.act(actor, "help")
        after_trust = world.social.get_relationship(
            target.id,
            actor.id,
        )["trust"]

        self.assertGreater(target.money, target_money)
        self.assertGreater(after_trust, before_trust)


if __name__ == "__main__":
    unittest.main()
