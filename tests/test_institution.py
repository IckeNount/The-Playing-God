from __future__ import annotations

import unittest
from copy import deepcopy
from unittest.mock import patch

from playing_god.core.institution import SchoolSnapshot, SchoolState
from playing_god.core.world import World


class InstitutionTests(unittest.TestCase):
    def make_world(self) -> World:
        world = World(seed=1947, population=2)
        world.school = SchoolState()
        world.day = 1
        for agent in world.agents:
            agent.current_location = "school"
        return world

    def test_training_succeeds_while_capacity_exists(self):
        world = self.make_world()
        agent = world.agents[0]
        skill_before = agent.skill
        money_before = agent.money

        world.act(agent, "train")

        self.assertGreater(agent.skill, skill_before)
        self.assertEqual(agent.money, money_before - 7)
        self.assertEqual(world.school.admissions_used, 1)
        self.assertTrue(
            any(
                event.kind == "institution"
                and "admitted" in event.description
                for event in agent.events
            )
        )

    def test_daily_training_capacity_cannot_be_exceeded(self):
        world = self.make_world()
        first, second = world.agents

        world.act(first, "train")
        world.act(second, "train")

        self.assertEqual(world.school.admissions_used, 1)
        admitted = [
            agent
            for agent in world.agents
            if any(
                event.kind == "institution"
                and "admitted" in event.description
                for event in agent.events
            )
        ]
        self.assertEqual(admitted, [first])

    def test_denied_training_has_no_skill_or_full_cost(self):
        world = self.make_world()
        first, denied = world.agents
        world.act(first, "train")
        skill_before = denied.skill
        money_before = denied.money
        energy_before = denied.energy

        world.act(denied, "train")

        self.assertEqual(denied.skill, skill_before)
        self.assertEqual(denied.money, money_before)
        self.assertEqual(denied.energy, energy_before)
        self.assertIn("capacity", denied.events[-1].description)

    def test_capacity_resets_on_the_next_day(self):
        world = self.make_world()
        first, second = world.agents
        world.act(first, "train")
        second_skill_before = second.skill

        world.day = 2
        world.act(second, "train")

        self.assertGreater(second.skill, second_skill_before)
        self.assertEqual(world.school.current_day, 2)
        self.assertEqual(world.school.admissions_used, 1)

    def test_seeded_daily_order_reproduces_admission(self):
        worlds = [World(seed=1947, population=2) for _ in range(2)]

        for world in worlds:
            world.school = SchoolState()
            with patch(
                "playing_god.core.world.choose",
                return_value="train",
            ):
                world.run(1)

        admitted_ids = [
            [
                agent.id
                for agent in world.agents
                if any(
                    event.kind == "institution"
                    and "admitted" in event.description
                    for event in agent.events
                )
            ]
            for world in worlds
        ]

        self.assertEqual(admitted_ids[0], admitted_ids[1])
        self.assertEqual(len(admitted_ids[0]), 1)

    def test_agent_away_from_school_does_not_consume_capacity(self):
        world = self.make_world()
        away, present = world.agents
        away.current_location = "home"
        away_skill_before = away.skill

        world.act(away, "train")
        world.act(present, "train")

        self.assertEqual(away.skill, away_skill_before)
        self.assertEqual(world.school.admissions_used, 1)
        self.assertIn("not at school", away.events[-1].description)

    def test_school_snapshot_is_read_only_and_exposes_rule(self):
        world = self.make_world()
        world.act(world.agents[0], "train")
        agents_before = deepcopy(world.agents)
        school_before = deepcopy(world.school)
        rng_before = world.rng.getstate()

        snapshot = world.school_snapshot()

        self.assertEqual(
            snapshot,
            SchoolSnapshot(
                location="school",
                day=1,
                daily_training_capacity=1,
                admissions_used=1,
                remaining_capacity=0,
            ),
        )
        self.assertEqual(world.agents, agents_before)
        self.assertEqual(world.school, school_before)
        self.assertEqual(world.rng.getstate(), rng_before)


if __name__ == "__main__":
    unittest.main()
