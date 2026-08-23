from __future__ import annotations

import unittest

from dataclasses import asdict
from unittest.mock import patch

from playing_god.core.perception import belief_key
from playing_god.core.world import World


class InterventionTests(unittest.TestCase):
    def make_high_attention(self, agent) -> None:
        agent.traits["discipline"] = 1.0
        agent.traits["risk_tolerance"] = 1.0
        agent.stress = 0.0

    def test_creation_changes_world_condition_not_agent_state(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        before = asdict(target)

        intervention = world.create_intervention(
            kind="opportunity",
            target_id=target.id,
            theme="a promising apprenticeship",
            suggested_action="train",
            strength=0.80,
            location="school",
            duration=5,
        )

        self.assertEqual(asdict(target), before)
        self.assertEqual(
            intervention.id,
            "intervention_000001",
        )
        self.assertEqual(intervention.created_day, 0)
        self.assertEqual(intervention.expires_day, 5)

    def test_location_stimulus_can_expire_unseen(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        target.current_location = "home"
        world.create_intervention(
            kind="sign",
            target_id=target.id,
            theme="an open school gate",
            suggested_action="train",
            strength=1.0,
            location="school",
            duration=2,
        )

        world.day = 1
        self.assertEqual(world.resolve_interventions(), [])
        world.day = 3
        target.current_location = "school"
        self.assertEqual(world.resolve_interventions(), [])
        self.assertEqual(world.intervention_responses, [])
        self.assertEqual(target.observations, [])

    def test_high_attention_dream_is_perceived_and_aligned(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        self.make_high_attention(target)
        intervention = world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="mastering a difficult craft",
            suggested_action="train",
            strength=1.0,
        )
        world.day = 1

        rng_state = world.rng.getstate()

        responses = world.resolve_interventions()

        self.assertEqual(len(responses), 1)
        response = responses[0]
        self.assertTrue(response.noticed)
        self.assertEqual(response.interpretation, "aligned")
        self.assertEqual(response.interpreted_action, "train")
        self.assertEqual(response.confidence, 1.0)
        self.assertEqual(len(target.observations), 1)
        self.assertEqual(
            target.beliefs[
                belief_key("dream", intervention.id)
            ].value,
            intervention.theme,
        )
        self.assertEqual(target.events[-1].kind, "dream")
        self.assertEqual(world.rng.getstate(), rng_state)

    def test_weak_dream_can_be_missed_without_forcing_belief(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        intervention = world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="a distant road",
            suggested_action="risky_move",
            strength=0.10,
        )
        world.day = 1

        response = world.resolve_interventions()[0]

        self.assertFalse(response.noticed)
        self.assertEqual(response.interpretation, "missed")
        self.assertIsNone(response.interpreted_action)
        self.assertNotIn(
            belief_key("dream", intervention.id),
            target.beliefs,
        )
        self.assertFalse(
            any(event.kind == "dream" for event in target.events)
        )

    def test_ambiguous_stimulus_uses_strongest_competing_motive(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        target.traits["discipline"] = 0.50
        target.traits["risk_tolerance"] = 0.50
        target.stress = 0.20
        world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="a crowded marketplace",
            suggested_action="train",
            strength=0.80,
        )
        world.day = 1

        response = world.resolve_interventions()[0]

        self.assertEqual(response.interpretation, "misinterpreted")
        self.assertIsNotNone(response.interpreted_action)
        self.assertNotEqual(response.interpreted_action, "train")

    def test_interpreted_stimulus_only_adjusts_normal_action_score(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        self.make_high_attention(target)
        world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="mastering a difficult craft",
            suggested_action="train",
            strength=1.0,
            duration=1,
        )

        with patch(
            "playing_god.core.world.choose",
            return_value="rest",
        ) as mocked_choose:
            world.run(1)

        target_call = next(
            call
            for call in mocked_choose.call_args_list
            if call.args[0].id == target.id
        )
        self.assertEqual(
            target_call.kwargs["score_adjustments"],
            {"train": 0.9},
        )
        self.assertEqual(target.actions["rest"], 1)
        self.assertEqual(target.actions["train"], 0)

    def test_invalid_intervention_is_rejected(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]

        with self.assertRaises(ValueError):
            world.create_intervention(
                kind="opportunity",
                target_id=target.id,
                theme="work",
                suggested_action="work",
                location=None,
            )

    def test_single_agent_world_accepts_an_intervention(self):
        world = World(seed=1947, population=1)

        intervention = world.create_intervention(
            kind="dream",
            target_id=world.agents[0].id,
            theme="a solitary path",
            suggested_action="rest",
        )

        self.assertEqual(intervention.target_id, "npc_001")


if __name__ == "__main__":
    unittest.main()
