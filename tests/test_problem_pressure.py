from __future__ import annotations

import sqlite3
import tempfile
import unittest

from contextlib import closing
from dataclasses import replace
from pathlib import Path

from playing_god.core.civilization import (
    AgentDiscoveryState,
    CivilizationState,
    PROBLEM_RECOGNITION_THRESHOLD,
    REQUIRED_DISCOVERY_PRIMITIVES,
    TRAINING_ACCESS_PROBLEM_ID,
    discovery_eligibility,
    validate_discovery_links,
)
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    PersistenceError,
    WorldLoadError,
    load_world,
    save_world,
)


class ProblemPressureTests(unittest.TestCase):
    def prepared_world(self, *, population: int = 1) -> World:
        world = World(seed=1947, population=population)
        agent = world.agents[0]
        agent.age = 30
        agent.family = replace(agent.family, dependent=False)
        agent.skill = 0.50
        agent.money = 100.0
        agent.energy = 0.80

        world.day = 1
        agent.current_location = world.school.location
        world.act(agent, "train")
        return world

    def deny_training(self, world: World, day: int) -> None:
        agent = world.agents[0]
        world.day = day
        agent.current_location = "home"
        world.act(agent, "train")

    def test_repeated_denials_cross_threshold_on_third_day(self):
        world = self.prepared_world()
        agent = world.agents[0]

        for day in range(2, 2 + PROBLEM_RECOGNITION_THRESHOLD - 1):
            self.deny_training(world, day)
            pressure = agent.discovery.pressures[0]
            self.assertIsNone(pressure.recognized_day)

        recognition_day = 1 + PROBLEM_RECOGNITION_THRESHOLD
        self.deny_training(world, recognition_day)
        pressure = agent.discovery.pressures[0]

        self.assertEqual(pressure.id, TRAINING_ACCESS_PROBLEM_ID)
        self.assertEqual(
            pressure.occurrence_count,
            PROBLEM_RECOGNITION_THRESHOLD,
        )
        self.assertEqual(pressure.recognized_day, recognition_day)
        self.assertIsNotNone(pressure.recognition_event_index)
        self.assertFalse(pressure.resolved)
        self.assertEqual(
            [event.kind for event in agent.events].count(
                "problem_pressure_recognized"
            ),
            1,
        )
        self.assertEqual(world.civilization, CivilizationState())
        self.assertEqual(agent.knowledge.records, ())

    def test_bystander_without_exposure_gets_no_pressure(self):
        world = self.prepared_world(population=2)
        bystander = world.agents[1]

        for day in range(2, 2 + PROBLEM_RECOGNITION_THRESHOLD):
            self.deny_training(world, day)

        self.assertEqual(bystander.discovery, AgentDiscoveryState())

    def test_pressure_is_bounded_and_recognition_is_not_duplicated(self):
        world = self.prepared_world()
        agent = world.agents[0]

        for day in range(2, 22):
            self.deny_training(world, day)

        pressure = agent.discovery.pressures[0]
        self.assertEqual(pressure.occurrence_count, 8)
        self.assertEqual(len(pressure.evidence), 8)
        self.assertEqual(pressure.severity, 1.0)
        self.assertEqual(
            [event.kind for event in agent.events].count(
                "problem_pressure_recognized"
            ),
            1,
        )

    def test_recognition_without_primitive_exposure_is_ineligible(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        agent.age = 30
        agent.skill = 0.50
        agent.money = 100.0
        agent.energy = 0.80
        for day in range(1, 1 + PROBLEM_RECOGNITION_THRESHOLD):
            self.deny_training(world, day)

        result = discovery_eligibility(
            agent,
            current_day=world.day + 1,
        )

        self.assertFalse(result.eligible)
        self.assertEqual(result.primitive_ids, ())
        self.assertIn("primitives", result.blockers)

    def test_pressure_evidence_links_to_firsthand_denials(self):
        world = self.prepared_world()
        agent = world.agents[0]
        for day in range(2, 2 + PROBLEM_RECOGNITION_THRESHOLD):
            self.deny_training(world, day)

        validate_discovery_links([agent], current_day=world.day)
        pressure = agent.discovery.pressures[0]
        self.assertTrue(all(
            evidence.agent_id == agent.id
            and agent.events[evidence.event_index].kind == "institution"
            and "School denied training" in agent.events[
                evidence.event_index
            ].description
            for evidence in pressure.evidence
        ))

    def test_capacity_denial_uses_the_same_pressure_path(self):
        world = self.prepared_world(population=2)
        affected, admitted = world.agents
        world.day = 2
        admitted.current_location = world.school.location
        affected.current_location = world.school.location

        world.act(admitted, "train")
        world.act(affected, "train")

        evidence = affected.discovery.pressures[0].evidence[0]
        self.assertEqual(evidence.reason, "capacity_exhausted")
        self.assertIn(
            "daily capacity",
            affected.events[evidence.event_index].description,
        )

    def test_eligibility_is_deterministic_and_not_immediate(self):
        worlds = [self.prepared_world() for _ in range(2)]
        for world in worlds:
            for day in range(2, 2 + PROBLEM_RECOGNITION_THRESHOLD):
                self.deny_training(world, day)

        recognized_day = worlds[0].day
        immediate = discovery_eligibility(
            worlds[0].agents[0],
            current_day=recognized_day,
        )
        results = [
            discovery_eligibility(
                world.agents[0],
                current_day=recognized_day + 1,
            )
            for world in worlds
        ]

        self.assertFalse(immediate.eligible)
        self.assertIn("time", immediate.blockers)
        self.assertEqual(results[0], results[1])
        self.assertTrue(results[0].eligible)
        self.assertEqual(
            results[0].primitive_ids,
            REQUIRED_DISCOVERY_PRIMITIVES,
        )


class ProblemPressurePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "world.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def recognized_world(self) -> World:
        tests = ProblemPressureTests()
        world = tests.prepared_world()
        for day in range(2, 2 + PROBLEM_RECOGNITION_THRESHOLD):
            tests.deny_training(world, day)
        return world

    def test_recognized_pressure_survives_restart_without_duplicate(self):
        world = self.recognized_world()
        expected = world.agents[0].discovery

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(loaded.agents[0].discovery, expected)
        self.assertEqual(len(loaded.agents[0].discovery.pressures), 1)
        save_world(loaded, self.db_path)
        self.assertEqual(load_world(self.db_path).agents[0].discovery, expected)

    def test_save_rejects_pressure_with_missing_causal_parent(self):
        world = self.recognized_world()
        world.agents[0].events.clear()

        with self.assertRaisesRegex(
            PersistenceError,
            "Invalid discovery links",
        ):
            save_world(world, self.db_path)

    def test_corrupt_discovery_state_fails_clearly(self):
        world = World(seed=37, population=1)
        save_world(world, self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "UPDATE agents SET discovery_json = '[]' WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid discovery state",
        ):
            load_world(self.db_path)

    def test_schema18_loads_empty_discovery_and_migrates_to_current(self):
        world = World(seed=31, population=2)
        expected_rng_state = world.rng.getstate()
        save_world(world, self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "ALTER TABLE agents DROP COLUMN discovery_json"
            )
            conn.execute(
                "UPDATE world_state SET schema_version = 18 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertTrue(all(
            agent.discovery == AgentDiscoveryState()
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        with closing(sqlite3.connect(self.db_path)) as conn:
            schema_version = conn.execute(
                "SELECT schema_version FROM world_state WHERE id = 1"
            ).fetchone()[0]
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(agents)")
            }

        self.assertEqual(schema_version, 21)
        self.assertIn("discovery_json", columns)


if __name__ == "__main__":
    unittest.main()
