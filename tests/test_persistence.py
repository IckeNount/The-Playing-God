from __future__ import annotations

import sqlite3
import tempfile
import unittest

from dataclasses import asdict
from pathlib import Path

from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    WorldLoadError,
    load_world,
    save_world,
)


def agent_snapshot(agent) -> dict:
    """
    Convert one Agent into plain comparable data.
    """
    data = asdict(agent)
    data["actions"] = dict(agent.actions)
    return data


def world_snapshot(world: World) -> dict:
    """
    Capture all state that should survive persistence.
    """
    return {
        "seed": world.seed,
        "day": world.day,
        "agents": {
            agent.id: agent_snapshot(agent)
            for agent in world.agents
        },
        "social": {
            f"{source_id}->{target_id}": dict(data)
            for source_id, target_id, data
            in world.social.graph.edges(data=True)
        },
    }


class PersistenceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = (
            Path(self.temp_dir.name)
            / "universe.db"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # ---------------------------------------------------------
    # TEST 2
    # Saved agent values equal loaded values.
    # ---------------------------------------------------------

    def test_saved_agent_values_equal_loaded_values(self):
        world = World(seed=1947)
        world.run(120)

        before = world_snapshot(world)

        save_world(
            world,
            self.db_path,
        )

        loaded = load_world(
            self.db_path
        )

        after = world_snapshot(loaded)

        self.assertEqual(
            before,
            after,
        )

        self.assertEqual(
            world.rng.getstate(),
            loaded.rng.getstate(),
        )

    def test_agent_spatial_state_survives_restart(self):
        world = World(seed=1947)
        world.agents[0].current_location = "market"
        world.agents[0].destination = "work"

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(
            loaded.agents[0].current_location,
            "market",
        )
        self.assertEqual(
            loaded.agents[0].destination,
            "work",
        )

        with sqlite3.connect(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(schema_version, 6)

    def test_schema4_defaults_social_energy_to_physical_energy(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE agents "
                "DROP COLUMN social_energy"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 4 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            self.assertEqual(agent.social_energy, agent.energy)

        loaded.agents[0].social_energy = 0.31
        save_world(loaded, self.db_path)
        reloaded = load_world(self.db_path)

        self.assertEqual(reloaded.agents[0].social_energy, 0.31)

    def test_observations_and_beliefs_survive_restart(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "market"
        second.current_location = "market"
        first.traits["sociability"] = 1.0
        second.traits["sociability"] = 1.0
        world.day = 1
        world.resolve_daily_interactions()

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(
            world_snapshot(world),
            world_snapshot(loaded),
        )

        with sqlite3.connect(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(schema_version, 6)

    def test_schema5_defaults_to_empty_perception_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DROP TABLE observations")
            conn.execute("DROP TABLE beliefs")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 5 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            self.assertEqual(agent.observations, [])
            self.assertEqual(agent.beliefs, {})

        save_world(loaded, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table'"
                )
            }

        self.assertIn("observations", tables)
        self.assertIn("beliefs", tables)

    def test_phase2_database_defaults_missing_spatial_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE agents "
                "DROP COLUMN current_location"
            )
            conn.execute(
                "ALTER TABLE agents "
                "DROP COLUMN destination"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 2 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            self.assertEqual(agent.current_location, "home")
            self.assertIsNone(agent.destination)

    # ---------------------------------------------------------
    # TEST 3
    # Events survive restart and remain chronological.
    # ---------------------------------------------------------

    def test_events_survive_restart_and_are_chronological(self):
        world = World(seed=1947)
        world.run(365)

        before_events = {
            agent.id: [
                (
                    event.day,
                    event.kind,
                    event.description,
                    event.significance,
                    event.target_id,
                    event.location,
                )
                for event in agent.events
            ]
            for agent in world.agents
        }

        save_world(
            world,
            self.db_path,
        )

        loaded = load_world(
            self.db_path
        )

        after_events = {
            agent.id: [
                (
                    event.day,
                    event.kind,
                    event.description,
                    event.significance,
                    event.target_id,
                    event.location,
                )
                for event in agent.events
            ]
            for agent in loaded.agents
        }

        self.assertEqual(
            before_events,
            after_events,
        )

        for agent in loaded.agents:
            days = [
                event.day
                for event in agent.events
            ]

            self.assertEqual(
                days,
                sorted(days),
                msg=(
                    f"Events are not chronological "
                    f"for {agent.id}"
                ),
            )

    def test_schema3_events_load_without_encounter_context(self):
        world = World(seed=1947, population=2)
        world.run(1)
        save_world(world, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE events DROP COLUMN target_id"
            )
            conn.execute(
                "ALTER TABLE events DROP COLUMN location"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 3 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            for event in agent.events:
                self.assertIsNone(event.target_id)
                self.assertIsNone(event.location)

        save_world(loaded, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(events)"
                )
            }

        self.assertIn("target_id", columns)
        self.assertIn("location", columns)

    # ---------------------------------------------------------
    # TEST 4
    # Relationships persist exactly.
    # ---------------------------------------------------------

    def test_relationships_persist(self):
        world = World(seed=1947)
        world.run(120)

        before = {
            agent.id: dict(
                agent.relationships
            )
            for agent in world.agents
        }

        save_world(
            world,
            self.db_path,
        )

        loaded = load_world(
            self.db_path
        )

        after = {
            agent.id: dict(
                agent.relationships
            )
            for agent in loaded.agents
        }

        self.assertEqual(
            before,
            after,
        )

        # 10 agents × 9 directed relationships.
        relationship_count = sum(
            len(agent.relationships)
            for agent in loaded.agents
        )

        self.assertEqual(
            relationship_count,
            90,
        )

    # ---------------------------------------------------------
    # TEST 5
    #
    # Day 120 save
    # -> process death
    # -> restart
    # -> Day 365
    #
    # must equal uninterrupted Day 1 -> 365.
    # ---------------------------------------------------------

    def test_restart_continuation_matches_uninterrupted_run(self):
        # Universe A
        uninterrupted = World(
            seed=1947
        )

        uninterrupted.run(365)

        uninterrupted_snapshot = (
            world_snapshot(
                uninterrupted
            )
        )

        # Universe B
        interrupted = World(
            seed=1947
        )

        interrupted.run(120)

        self.assertEqual(
            interrupted.day,
            120,
        )

        save_world(
            interrupted,
            self.db_path,
        )

        # Simulate process death.
        del interrupted

        resumed = load_world(
            self.db_path
        )

        self.assertEqual(
            resumed.day,
            120,
        )

        resumed.run(245)

        self.assertEqual(
            resumed.day,
            365,
        )

        resumed_snapshot = (
            world_snapshot(
                resumed
            )
        )

        self.assertEqual(
            uninterrupted_snapshot,
            resumed_snapshot,
        )

        self.assertEqual(
            uninterrupted.rng.getstate(),
            resumed.rng.getstate(),
        )

    # ---------------------------------------------------------
    # TEST 7
    # Repeated saves must not duplicate agents or events.
    # ---------------------------------------------------------

    def test_repeated_save_does_not_duplicate_data(self):
        world = World(seed=1947)
        world.run(120)

        expected_agent_count = len(
            world.agents
        )

        expected_event_count = sum(
            len(agent.events)
            for agent in world.agents
        )
        expected_observation_count = sum(
            len(agent.observations)
            for agent in world.agents
        )

        save_world(
            world,
            self.db_path,
        )

        # Save identical universe again.
        save_world(
            world,
            self.db_path,
        )

        loaded = load_world(
            self.db_path
        )

        self.assertEqual(
            len(loaded.agents),
            expected_agent_count,
        )

        loaded_event_count = sum(
            len(agent.events)
            for agent in loaded.agents
        )

        self.assertEqual(
            loaded_event_count,
            expected_event_count,
        )

        with sqlite3.connect(
            self.db_path
        ) as conn:
            agent_rows = conn.execute(
                """
                SELECT COUNT(*)
                FROM agents
                """
            ).fetchone()[0]

            event_rows = conn.execute(
                """
                SELECT COUNT(*)
                FROM events
                """
            ).fetchone()[0]

            observation_rows = conn.execute(
                """
                SELECT COUNT(*)
                FROM observations
                """
            ).fetchone()[0]

        self.assertEqual(
            agent_rows,
            expected_agent_count,
        )

        self.assertEqual(
            event_rows,
            expected_event_count,
        )

        self.assertEqual(
            observation_rows,
            expected_observation_count,
        )

    # ---------------------------------------------------------
    # Extra protection for append-only events.
    #
    # Saving Day 120, continuing to Day 200,
    # then saving again should add only new events.
    # ---------------------------------------------------------

    def test_later_save_appends_new_events_without_duplication(self):
        world = World(seed=1947)

        world.run(120)

        save_world(
            world,
            self.db_path,
        )

        events_at_120 = sum(
            len(agent.events)
            for agent in world.agents
        )

        world.run(80)

        self.assertEqual(
            world.day,
            200,
        )

        save_world(
            world,
            self.db_path,
        )

        expected_events = sum(
            len(agent.events)
            for agent in world.agents
        )

        self.assertGreaterEqual(
            expected_events,
            events_at_120,
        )

        loaded = load_world(
            self.db_path
        )

        loaded_events = sum(
            len(agent.events)
            for agent in loaded.agents
        )

        self.assertEqual(
            loaded_events,
            expected_events,
        )

    # ---------------------------------------------------------
    # TEST 8A
    # Missing DB must fail clearly.
    # ---------------------------------------------------------

    def test_missing_database_fails_clearly(self):
        missing_path = (
            Path(self.temp_dir.name)
            / "missing.db"
        )

        self.assertFalse(
            missing_path.exists()
        )

        with self.assertRaises(
            WorldLoadError
        ) as context:
            load_world(
                missing_path
            )

        self.assertIn(
            "does not exist",
            str(context.exception),
        )

        # Loading must not create an empty DB.
        self.assertFalse(
            missing_path.exists()
        )

    # ---------------------------------------------------------
    # TEST 8B
    # Garbage/corrupted SQLite file must fail clearly.
    # ---------------------------------------------------------

    def test_corrupted_database_fails_clearly(self):
        self.db_path.write_text(
            "this is not sqlite",
            encoding="utf-8",
        )

        with self.assertRaises(
            WorldLoadError
        ) as context:
            load_world(
                self.db_path
            )

        self.assertIn(
            "corrupted",
            str(context.exception).lower(),
        )

    # ---------------------------------------------------------
    # Extra corruption test:
    # valid SQLite but not a Playing God universe.
    # ---------------------------------------------------------

    def test_unrelated_sqlite_database_fails_clearly(self):
        with sqlite3.connect(
            self.db_path
        ) as conn:
            conn.execute(
                """
                CREATE TABLE random_table (
                    value TEXT
                )
                """
            )

        with self.assertRaises(
            WorldLoadError
        ) as context:
            load_world(
                self.db_path
            )

        self.assertIn(
            "missing tables",
            str(context.exception).lower(),
        )


if __name__ == "__main__":
    unittest.main()
