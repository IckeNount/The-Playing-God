from __future__ import annotations

import sqlite3
import tempfile
import unittest

from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path

from playing_god.core.civilization import (
    AgentDiscoveryState,
    BoundedEffect,
    PEER_TRAIN_AFFORDANCE,
    PEER_TRAIN_KNOWLEDGE_ID,
    compose_peer_training_candidate,
)
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world


def eligible_world(seed: int) -> World:
    world = World(seed=seed, population=1)
    agent = world.agents[0]
    agent.age = 30
    agent.family = replace(agent.family, dependent=False)
    agent.skill = 0.60
    agent.traits["discipline"] = 0.50
    agent.traits["risk_tolerance"] = 0.50
    agent.money = 100.0
    agent.energy = 0.80
    agent.stress = 0.10

    world.day = 1
    agent.current_location = world.school.location
    world.act(agent, "train")
    for day in (2, 3, 4):
        world.day = day
        agent.current_location = "home"
        world.act(agent, "train")
    world.day = 5
    return world


class DiscoveryAttemptTests(unittest.TestCase):
    def test_seeded_success_and_failure_pay_costs_with_causal_events(self):
        success_worlds = [eligible_world(1), eligible_world(1)]
        failure_world = eligible_world(5)

        success_before = (
            success_worlds[0].agents[0].money,
            success_worlds[0].agents[0].energy,
            success_worlds[0].agents[0].stress,
        )
        successes = [
            world.attempt_discovery(world.agents[0].id)
            for world in success_worlds
        ]
        failure_before = (
            failure_world.agents[0].money,
            failure_world.agents[0].energy,
            failure_world.agents[0].stress,
        )
        failure = failure_world.attempt_discovery(
            failure_world.agents[0].id
        )

        self.assertEqual(successes[0], successes[1])
        self.assertEqual(successes[0].outcome, "validated")
        self.assertEqual(failure.outcome, "failed")
        self.assertEqual(
            (
                success_worlds[0].agents[0].money,
                success_worlds[0].agents[0].energy,
                success_worlds[0].agents[0].stress,
            ),
            (
                success_before[0] - 7.0,
                success_before[1] - 0.12,
                success_before[2] + 0.04,
            ),
        )
        self.assertEqual(
            (
                failure_world.agents[0].money,
                failure_world.agents[0].energy,
                failure_world.agents[0].stress,
            ),
            (
                failure_before[0] - 7.0,
                failure_before[1] - 0.12,
                failure_before[2] + 0.04,
            ),
        )
        attempt = successes[0]
        agent = success_worlds[0].agents[0]
        self.assertEqual(
            agent.events[attempt.attempt_event_index].kind,
            "discovery_attempted",
        )
        self.assertEqual(
            agent.events[attempt.resolution_event_index].kind,
            "discovery_validated",
        )
        self.assertEqual(
            success_worlds[0].civilization.knowledge[0].id,
            PEER_TRAIN_KNOWLEDGE_ID,
        )
        self.assertEqual(
            success_worlds[0].civilization.affordances,
            (PEER_TRAIN_AFFORDANCE,),
        )
        self.assertEqual(
            agent.knowledge.records[0].causal_parent_event_index,
            attempt.resolution_event_index,
        )
        self.assertEqual(failure_world.civilization.knowledge, ())
        self.assertEqual(failure_world.agents[0].knowledge.records, ())
        self.assertEqual(
            failure_world.agents[0].events[
                failure.resolution_event_index
            ].kind,
            "discovery_rejected",
        )

    def test_ineligible_is_free_and_invalid_candidate_rejects_without_rng(self):
        blocked = World(seed=11, population=1)
        blocked_agent = blocked.agents[0]
        blocked_resources = (
            blocked_agent.money,
            blocked_agent.energy,
            blocked_agent.stress,
        )
        blocked_event_count = len(blocked_agent.events)
        blocked_rng = blocked.rng.getstate()

        self.assertIsNone(blocked.attempt_discovery(blocked_agent.id))
        self.assertEqual(
            (
                blocked_agent.money,
                blocked_agent.energy,
                blocked_agent.stress,
            ),
            blocked_resources,
        )
        self.assertEqual(blocked.rng.getstate(), blocked_rng)
        self.assertEqual(len(blocked_agent.events), blocked_event_count)

        world = eligible_world(1)
        agent = world.agents[0]
        candidate = compose_peer_training_candidate(agent)
        invalid = replace(
            candidate,
            effects=(BoundedEffect("run_python", "learner", 0.1),),
        )
        resources_before = (agent.money, agent.energy, agent.stress)
        rng_before = world.rng.getstate()

        attempt = world.attempt_discovery(agent.id, candidate=invalid)

        self.assertEqual(attempt.outcome, "structural_rejection")
        self.assertEqual(attempt.validation_errors, ("effects",))
        self.assertNotEqual(
            (agent.money, agent.energy, agent.stress),
            resources_before,
        )
        self.assertEqual(world.rng.getstate(), rng_before)
        self.assertEqual(world.civilization.knowledge, ())


class DiscoveryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "world.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resolved_attempt_round_trips_and_cannot_reresolve(self):
        world = eligible_world(5)
        agent = world.agents[0]
        expected_attempt = world.attempt_discovery(agent.id)
        expected_state = asdict(agent)
        expected_civilization = world.civilization
        expected_rng = world.rng.getstate()

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)
        loaded_attempt = loaded.attempt_discovery(agent.id)

        self.assertEqual(loaded_attempt, expected_attempt)
        self.assertEqual(asdict(loaded.agents[0]), expected_state)
        self.assertEqual(loaded.civilization, expected_civilization)
        self.assertEqual(loaded.rng.getstate(), expected_rng)
        self.assertEqual(len(loaded.agents[0].discovery.attempts), 1)
        self.assertEqual(loaded.civilization.knowledge, ())

    def test_schema19_loads_empty_attempts_and_migrates_to_current(self):
        world = World(seed=31, population=1)
        save_world(world, self.db_path)
        expected_rng = world.rng.getstate()

        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "UPDATE agents SET discovery_json = ?",
                ('{"pressures": [], "primitive_exposures": []}',),
            )
            conn.execute(
                "UPDATE world_state SET schema_version = 19 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertEqual(loaded.agents[0].discovery, AgentDiscoveryState())
        self.assertEqual(loaded.rng.getstate(), expected_rng)
        save_world(loaded, self.db_path)
        with closing(sqlite3.connect(self.db_path)) as conn:
            version = conn.execute(
                "SELECT schema_version FROM world_state WHERE id = 1"
            ).fetchone()[0]
        self.assertEqual(version, 21)


if __name__ == "__main__":
    unittest.main()
