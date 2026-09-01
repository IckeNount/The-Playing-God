from __future__ import annotations

from dataclasses import asdict
import unittest
from unittest.mock import patch

from playing_god.core.adaptive import (
    capture_state,
    consequence_between,
    context_for,
    learn,
    learned_preferences,
)
from playing_god.core.decision import choose
from playing_god.core.world import World


class PeakChoiceRandom:
    def choices(
        self,
        population: list[str],
        *,
        weights: list[float],
        k: int,
    ) -> list[str]:
        winner = max(
            range(len(population)),
            key=weights.__getitem__,
        )
        return [population[winner]]


class ContextualAdaptationTests(unittest.TestCase):
    def prepare_improve_skill_agent(self, world: World):
        agent = world.agents[0]
        for trait in agent.traits:
            agent.traits[trait] = 0.0
        agent.traits["ambition"] = 0.20
        agent.traits["discipline"] = 0.20
        for sin in agent.sins:
            agent.sins[sin] = 0.0
        for other_id in agent.relationships:
            agent.relationships[other_id] = 0.0
        agent.employed = True
        agent.money = 200.0
        agent.skill = 0.40
        agent.energy = 0.65
        agent.social_energy = 0.65
        agent.stress = 0.10
        agent.reputation = 0.0
        agent.job_level = 1
        agent.goal = "improve_skill"
        return agent

    def record_training_experience(
        self,
        world: World,
        *,
        admitted: bool,
    ):
        agent = self.prepare_improve_skill_agent(world)
        agent.current_location = (
            world.school.location
            if admitted
            else "home"
        )
        context = context_for(agent)
        before = capture_state(agent)

        world.act(agent, "train")

        consequence = consequence_between(
            before,
            capture_state(agent),
        )
        learn(agent, context, "train", consequence)
        return agent

    def test_different_training_outcomes_change_future_preference(self):
        admitted = self.record_training_experience(
            World(seed=1947, population=1),
            admitted=True,
        )
        denied = self.record_training_experience(
            World(seed=1947, population=1),
            admitted=False,
        )

        self.prepare_improve_skill_agent_state(admitted)
        self.prepare_improve_skill_agent_state(denied)

        admitted_action = choose(
            admitted,
            PeakChoiceRandom(),
            learned_preferences=learned_preferences(
                admitted,
                "improve_skill",
            ),
        )
        denied_action = choose(
            denied,
            PeakChoiceRandom(),
            learned_preferences=learned_preferences(
                denied,
                "improve_skill",
            ),
        )

        self.assertEqual(admitted_action, "train")
        self.assertEqual(denied_action, "rest")
        self.assertGreater(
            learned_preferences(admitted, "improve_skill")["train"],
            learned_preferences(denied, "improve_skill")["train"],
        )

    def prepare_improve_skill_agent_state(self, agent) -> None:
        agent.employed = True
        agent.money = 200.0
        agent.skill = 0.40
        agent.energy = 0.65
        agent.social_energy = 0.65
        agent.stress = 0.10
        agent.reputation = 0.0
        agent.job_level = 1
        agent.goal = "improve_skill"

    def test_learning_record_preserves_multidimensional_consequence(self):
        agent = self.record_training_experience(
            World(seed=1947, population=1),
            admitted=True,
        )

        value = agent.adaptive_values["improve_skill"]["train"]

        self.assertEqual(value.observations, 1)
        self.assertGreater(value.mean_consequence.skill, 0.0)
        self.assertLess(value.mean_consequence.money, 0.0)
        self.assertGreater(value.mean_feedback, 0.0)

    def test_world_updates_online_only_when_adaptation_is_enabled(self):
        adaptive = World(
            seed=1947,
            population=1,
            adaptive_cognition=True,
        )
        legacy = World(seed=1947, population=1)

        with patch(
            "playing_god.core.world.choose",
            return_value="rest",
        ):
            adaptive.run(1)
            legacy.run(1)

        adaptive_values = adaptive.agents[0].adaptive_values
        learned_action = next(iter(adaptive_values.values()))["rest"]
        self.assertEqual(learned_action.observations, 1)
        self.assertEqual(legacy.agents[0].adaptive_values, {})

    def test_seeded_online_learning_is_reproducible(self):
        first = World(
            seed=1947,
            population=3,
            adaptive_cognition=True,
        )
        second = World(
            seed=1947,
            population=3,
            adaptive_cognition=True,
        )

        first.run(30)
        second.run(30)

        self.assertEqual(
            [asdict(agent) for agent in first.agents],
            [asdict(agent) for agent in second.agents],
        )
        self.assertEqual(first.rng.getstate(), second.rng.getstate())


if __name__ == "__main__":
    unittest.main()
