from __future__ import annotations

import unittest
from copy import deepcopy
from unittest.mock import patch

from playing_god.core.economy import EconomySnapshot, EconomyState
from playing_god.core.world import World


class EconomyTests(unittest.TestCase):
    def test_snapshot_reports_manually_prepared_economic_state(self):
        world = World(seed=1947, population=3)
        balances = (-10.0, 20.0, 50.0)
        employment = (True, True, False)
        for agent, money, employed in zip(
            world.agents,
            balances,
            employment,
        ):
            agent.money = money
            agent.employed = employed
        world.economy = EconomyState(job_capacity=3)

        snapshot = world.economic_snapshot()

        self.assertEqual(
            snapshot,
            EconomySnapshot(
                population=3,
                employed_count=2,
                unemployed_count=1,
                employment_rate=2 / 3,
                job_capacity=3,
                vacancies=1,
                total_agent_money=60.0,
                median_agent_money=20.0,
                negative_balance_count=1,
            ),
        )

    def test_snapshot_is_deterministic_and_read_only(self):
        world = World(seed=1947)
        agents_before = deepcopy(world.agents)
        economy_before = world.economy
        rng_before = world.rng.getstate()

        first = world.economic_snapshot()
        second = world.economic_snapshot()

        self.assertEqual(first, second)
        self.assertEqual(world.agents, agents_before)
        self.assertEqual(world.economy, economy_before)
        self.assertEqual(world.rng.getstate(), rng_before)

    def test_initial_capacity_covers_existing_workers(self):
        world = World(seed=2, population=10)

        self.assertGreaterEqual(
            world.economy.job_capacity,
            world.economy.occupied_jobs(world.agents),
        )

    def test_initial_capacity_uses_deterministic_half_up_rounding(self):
        world = World(seed=1947, population=5)
        for agent in world.agents:
            agent.employed = False

        economy = EconomyState.from_agents(world.agents)

        self.assertEqual(economy.job_capacity, 4)

    def test_two_seekers_cannot_consume_one_vacancy(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        for agent in world.agents:
            agent.employed = False
            agent.salary = 0
            agent.job_level = 0
        world.economy = EconomyState(job_capacity=1)

        with patch.object(
            world.rng,
            "random",
            side_effect=[0.0, 0.0],
        ) as random_draw:
            world.act(first, "job_hunt")
            world.act(second, "job_hunt")

        self.assertTrue(first.employed)
        self.assertFalse(second.employed)
        self.assertEqual(
            world.economy.occupied_jobs(world.agents),
            1,
        )
        self.assertEqual(world.economy.vacancies(world.agents), 0)
        self.assertEqual(random_draw.call_count, 2)
        for detail in ("vacancies before", "chance", "roll"):
            self.assertIn(detail, first.events[-1].description)
            self.assertIn(detail, second.events[-1].description)
        self.assertIn("no vacancy", second.events[-1].description)

    def test_released_job_can_be_filled(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.employed = True
        first.job_level = 1
        first.salary = 30
        second.employed = False
        second.job_level = 0
        second.salary = 0
        world.economy = EconomyState(job_capacity=1)

        first.employed = False
        first.job_level = 0
        first.salary = 0

        with patch.object(world.rng, "random", return_value=0.0):
            world.act(second, "job_hunt")

        self.assertTrue(second.employed)
        self.assertEqual(world.economy.vacancies(world.agents), 0)

    def test_same_seed_and_setup_produce_same_economic_result(self):
        worlds = [World(seed=1947, population=3) for _ in range(2)]

        for world in worlds:
            for agent in world.agents:
                agent.employed = False
                agent.salary = 0
                agent.job_level = 0
            world.economy = EconomyState(job_capacity=1)
            for agent in world.agents:
                world.act(agent, "job_hunt")

        outcomes = [
            (
                [agent.employed for agent in world.agents],
                [agent.money for agent in world.agents],
                [
                    event.description
                    for agent in world.agents
                    for event in agent.events
                ],
                world.rng.getstate(),
            )
            for world in worlds
        ]

        self.assertEqual(outcomes[0], outcomes[1])


if __name__ == "__main__":
    unittest.main()
