import unittest

from playing_god.core.social import SocialGraph


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


if __name__ == "__main__":
    unittest.main()