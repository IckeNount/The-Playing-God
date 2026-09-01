from __future__ import annotations

import unittest

from unittest.mock import patch

from playing_god.core.decision import scores
from playing_god.core.lifecycle import (
    ANNUAL_DEPENDENT_SUPPORT,
    RETIREMENT_AGE,
)
from playing_god.core.world import World


def prepare_eligible_pair(world: World):
    first, second = world.agents[:2]
    for parent in (first, second):
        parent.age = 30
        parent.money = 400.0
        parent.stress = 0.20
        parent.current_location = "home"
    first.employed = True
    second.employed = False
    first.relationships[second.id] = 0.50
    second.relationships[first.id] = 0.50
    world.social.add_relationship(
        first.id,
        second.id,
        affinity=0.50,
        trust=0.70,
        familiarity=0.80,
    )
    world.social.add_relationship(
        second.id,
        first.id,
        affinity=0.50,
        trust=0.70,
        familiarity=0.80,
    )
    return first, second


def create_child(world: World):
    first, second = prepare_eligible_pair(world)
    with patch(
        "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
        1.0,
    ):
        child = world.resolve_reproduction()[0]
    return first, second, child


class LifecycleTests(unittest.TestCase):

    def test_lifecycle_defaults_follow_reproduction_without_forcing_legacy(self):
        self.assertFalse(World(seed=1, population=1).lifecycle_enabled)
        self.assertTrue(World(
            seed=1,
            population=1,
            reproduction_enabled=True,
        ).lifecycle_enabled)
        self.assertFalse(World(
            seed=1,
            population=1,
            reproduction_enabled=True,
            lifecycle_enabled=False,
        ).lifecycle_enabled)

    def test_household_support_is_material_and_inspectable(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        first, second, child = create_child(world)
        before = world.household_snapshot(child.id)
        parent_money = (first.money, second.money)
        stress_before = child.stress

        world.day = child.family.birth_day + 365
        world.resolve_development()

        record = child.lifecycle.support_received[-1]
        self.assertEqual(before.living_guardian_ids, (first.id, second.id))
        self.assertEqual(record.total_support, ANNUAL_DEPENDENT_SUPPORT)
        self.assertEqual(
            tuple(item.amount for item in record.contributions),
            (24.0, 24.0),
        )
        self.assertEqual(first.money, parent_money[0] - 24.0)
        self.assertEqual(second.money, parent_money[1] - 24.0)
        self.assertLess(child.stress, stress_before)

    def test_retirement_ends_employment_and_job_hunting(self):
        world = World(
            seed=1947,
            population=1,
            lifecycle_enabled=True,
        )
        agent = world.agents[0]
        agent.age = RETIREMENT_AGE - 1
        agent.employed = True
        agent.salary = 30.0
        world.day = 365

        world.resolve_lifecycle()
        actions_before = dict(agent.actions)
        money_before = agent.money
        world.act(agent, "job_hunt")

        self.assertTrue(agent.lifecycle.retired)
        self.assertFalse(agent.employed)
        self.assertEqual(agent.salary, 0.0)
        self.assertEqual(scores(agent)["job_hunt"], -99)
        self.assertEqual(dict(agent.actions), actions_before)
        self.assertEqual(agent.money, money_before)
        self.assertTrue(any(
            event.description == f"Retired at age {RETIREMENT_AGE}"
            for event in agent.events
        ))

    def test_death_preserves_history_and_transfers_estate_to_child(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        parent, _, child = create_child(world)
        parent.age = 89
        parent.money = 101.0
        parent.employed = True
        world.day = 365

        with patch.object(world.rng, "random", return_value=0.50):
            transitioned = world.resolve_lifecycle()

        self.assertIn(parent, transitioned)
        self.assertFalse(parent.lifecycle.alive)
        self.assertEqual(parent.money, 0.0)
        self.assertFalse(parent.employed)
        self.assertEqual(parent.lifecycle.death.estate, 101.0)
        self.assertEqual(parent.lifecycle.death.unallocated, 0.0)
        self.assertEqual(child.money, 101.0)
        transfer = child.lifecycle.inheritance_received[-1]
        self.assertEqual(transfer.deceased_id, parent.id)
        self.assertEqual(transfer.heir_id, child.id)
        self.assertEqual(transfer.amount, 101.0)
        self.assertIn(child.id, parent.family.child_ids)
        self.assertIn(parent.id, child.family.parent_ids)

        actions_before = dict(parent.actions)
        world.act(parent, "rest")
        world.resolve_daily_interactions()
        self.assertEqual(dict(parent.actions), actions_before)
        self.assertTrue(all(
            parent.id not in {exposure.agent_a, exposure.agent_b}
            for exposure in world.last_exposures
        ))
        self.assertEqual(world.economic_snapshot().population, 2)
        self.assertIn(
            "deceased",
            world.reproduction_eligibility(parent.id, world.agents[1].id).reasons,
        )
        with self.assertRaisesRegex(ValueError, "living target"):
            world.create_intervention(
                kind="dream",
                target_id=parent.id,
                theme="return",
                suggested_action="rest",
            )

    def test_death_reopens_population_guardrail_for_birth(self):
        world = World(
            seed=83,
            population=3,
            reproduction_enabled=True,
        )
        first, second = prepare_eligible_pair(world)
        deceased = world.agents[2]
        deceased.age = 89
        deceased.money = 0.0
        world.day = 365
        with patch.object(world.rng, "random", return_value=0.50):
            world.resolve_lifecycle()
        self.assertFalse(deceased.lifecycle.alive)

        with (
            patch("playing_god.core.world.MAX_POPULATION", 3),
            patch(
                "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
                1.0,
            ),
        ):
            child = world.attempt_reproduction(first.id, second.id)

        self.assertIsNotNone(child)
        self.assertEqual(len(world.living_agents()), 3)
        self.assertEqual(len(world.agents), 4)

    def test_same_seed_mortality_is_exact(self):
        worlds = [
            World(
                seed=91,
                population=1,
                lifecycle_enabled=True,
            )
            for _ in range(2)
        ]
        for world in worlds:
            world.agents[0].age = 69
            world.agents[0].stress = 0.40
            world.day = 365
            world.resolve_lifecycle()

        self.assertEqual(
            worlds[0].agents[0].lifecycle,
            worlds[1].agents[0].lifecycle,
        )
        self.assertEqual(
            worlds[0].rng.getstate(),
            worlds[1].rng.getstate(),
        )


if __name__ == "__main__":
    unittest.main()
