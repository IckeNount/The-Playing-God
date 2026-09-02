from __future__ import annotations

import gc
import sqlite3
import tempfile
import unittest
import warnings

from contextlib import closing, contextmanager
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from playing_god.core.economy import EconomyState
from playing_god.core.events import Event
from playing_god.core.world import World
from playing_god.core.prayer import Prayer
from playing_god.persistence.sqlite_store import (
    PersistenceError,
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
        "adaptive_cognition": world.adaptive_cognition,
        "reproduction_enabled": world.reproduction_enabled,
        "lifecycle_enabled": world.lifecycle_enabled,
        "economy": asdict(world.economy),
        "civilization": asdict(world.civilization),
        "agents": {
            agent.id: agent_snapshot(agent)
            for agent in world.agents
        },
        "social": {
            f"{source_id}->{target_id}": dict(data)
            for source_id, target_id, data
            in world.social.graph.edges(data=True)
        },
        "interventions": [
            asdict(intervention)
            for intervention in world.interventions
        ],
        "intervention_responses": [
            asdict(response)
            for response in world.intervention_responses
        ],
    }


@contextmanager
def sqlite_connection(path):
    with closing(sqlite3.connect(path)) as conn, conn:
        yield conn


def prepare_family_pair(world: World):
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


def create_developing_child(world: World):
    prepare_family_pair(world)
    with patch(
        "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
        1.0,
    ):
        return world.resolve_reproduction()[0]


def progress_child(world: World, child, target_age: int) -> None:
    birth_day = child.family.birth_day
    for age in range(child.age + 1, target_age + 1):
        world.day = birth_day + age * 365
        world.resolve_development()


class PersistenceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = (
            Path(self.temp_dir.name)
            / "universe.db"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_and_load_close_sqlite_connections(self):
        world = World(seed=1947, population=2)
        gc.collect()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            for _ in range(3):
                save_world(world, self.db_path)
                loaded = load_world(self.db_path)
            del loaded
            gc.collect()

        sqlite_warnings = [
            warning
            for warning in caught
            if (
                issubclass(warning.category, ResourceWarning)
                and "sqlite3.Connection" in str(warning.message)
            )
        ]
        self.assertEqual(sqlite_warnings, [])

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

        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(schema_version, 20)

    def test_adaptive_state_survives_restart(self):
        world = World(
            seed=1947,
            population=2,
            adaptive_cognition=True,
        )
        world.run(15)
        before = world_snapshot(world)

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertTrue(loaded.adaptive_cognition)
        self.assertTrue(loaded.agents[0].adaptive_values)
        self.assertEqual(world_snapshot(loaded), before)

    def test_adaptive_continuation_matches_uninterrupted_run(self):
        uninterrupted = World(
            seed=1947,
            population=2,
            adaptive_cognition=True,
        )
        uninterrupted.run(40)

        interrupted = World(
            seed=1947,
            population=2,
            adaptive_cognition=True,
        )
        interrupted.run(17)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed.run(23)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_schema11_defaults_to_empty_disabled_adaptation(self):
        world = World(
            seed=1947,
            population=2,
            adaptive_cognition=True,
        )
        world.run(3)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE agents "
                "DROP COLUMN adaptive_values_json"
            )
            conn.execute(
                "ALTER TABLE world_state "
                "DROP COLUMN adaptive_cognition"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 11 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertFalse(loaded.adaptive_cognition)
        self.assertTrue(all(
            not agent.adaptive_values
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            world_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(world_state)"
                )
            }
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("adaptive_cognition", world_columns)
        self.assertIn("adaptive_values_json", agent_columns)

    def test_schema12_defaults_to_empty_founder_prehistory(self):
        world = World(seed=1947, population=2)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE agents "
                "DROP COLUMN founder_prehistory_json"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 12 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertTrue(all(
            not agent.founder_prehistory
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        migrated = load_world(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("founder_prehistory_json", agent_columns)
        self.assertTrue(all(
            not agent.founder_prehistory
            for agent in migrated.agents
        ))

    def test_corrupted_founder_prehistory_fails_clearly(self):
        world = World(seed=1947, population=1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents "
                "SET founder_prehistory_json = '{}' "
                "WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid founder prehistory",
        ):
            load_world(self.db_path)

    def test_invalid_founder_prehistory_cannot_be_saved(self):
        world = World(seed=1947, population=1)
        world.agents[0].founder_prehistory.pop()

        with self.assertRaisesRegex(
            PersistenceError,
            "Invalid founder prehistory",
        ):
            save_world(world, self.db_path)

    def test_family_state_survives_restart(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        prepare_family_pair(world)
        world.day = 12
        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            world.resolve_reproduction()
        before = world_snapshot(world)

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertTrue(loaded.reproduction_enabled)
        self.assertEqual(world_snapshot(loaded), before)
        self.assertEqual(loaded.rng.getstate(), world.rng.getstate())

    def test_family_continuation_matches_uninterrupted_run(self):
        def make_world():
            world = World(
                seed=71,
                population=2,
                reproduction_enabled=True,
            )
            prepare_family_pair(world)
            with patch(
                "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
                1.0,
            ):
                world.resolve_reproduction()
            return world

        uninterrupted = make_world()
        uninterrupted.run(10)

        interrupted = make_world()
        interrupted.run(4)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed.run(6)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_development_state_survives_restart(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
            adaptive_cognition=True,
        )
        child = create_developing_child(world)
        progress_child(world, child, 8)
        before = world_snapshot(world)

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(world_snapshot(loaded), before)
        self.assertEqual(loaded.rng.getstate(), world.rng.getstate())

    def test_development_continuation_matches_restart(self):
        def make_world():
            world = World(
                seed=71,
                population=2,
                reproduction_enabled=True,
                adaptive_cognition=True,
            )
            child = create_developing_child(world)
            return world, child

        uninterrupted, uninterrupted_child = make_world()
        progress_child(uninterrupted, uninterrupted_child, 12)

        interrupted, interrupted_child = make_world()
        progress_child(interrupted, interrupted_child, 8)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed_child = resumed.agents[-1]
        progress_child(resumed, resumed_child, 12)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_lifecycle_death_and_inheritance_survive_restart(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        child = create_developing_child(world)
        parent = world.agents[0]
        parent.age = 89
        parent.money = 101.0
        world.day = 365
        with patch.object(world.rng, "random", return_value=0.50):
            world.resolve_lifecycle()
        before = world_snapshot(world)

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(world_snapshot(loaded), before)
        self.assertFalse(loaded.agents[0].lifecycle.alive)
        self.assertEqual(
            loaded.agents[-1].lifecycle.inheritance_received[-1].amount,
            101.0,
        )
        self.assertEqual(child.money, 101.0)

    def test_lifecycle_continuation_matches_restart(self):
        uninterrupted = World(
            seed=91,
            population=1,
            lifecycle_enabled=True,
        )
        uninterrupted.agents[0].age = 68
        uninterrupted.run(730)

        interrupted = World(
            seed=91,
            population=1,
            lifecycle_enabled=True,
        )
        interrupted.agents[0].age = 68
        interrupted.run(365)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed.run(365)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_schema13_defaults_to_disabled_empty_family_state(self):
        world = World(
            seed=1947,
            population=2,
            reproduction_enabled=True,
        )
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute("ALTER TABLE agents DROP COLUMN family_json")
            conn.execute(
                "ALTER TABLE world_state "
                "DROP COLUMN reproduction_enabled"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 13 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertFalse(loaded.reproduction_enabled)
        self.assertTrue(all(
            agent.family.generation == 0
            and not agent.family.parent_ids
            and not agent.family.child_ids
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        migrated = load_world(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            world_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(world_state)"
                )
            }
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("reproduction_enabled", world_columns)
        self.assertIn("family_json", agent_columns)
        self.assertFalse(migrated.reproduction_enabled)

    def test_schema14_defaults_to_empty_development_state(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
            adaptive_cognition=True,
        )
        child = create_developing_child(world)
        progress_child(world, child, 8)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "ALTER TABLE agents DROP COLUMN development_json"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 14 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertTrue(all(
            not agent.development.records
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        migrated = load_world(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("development_json", agent_columns)
        self.assertTrue(all(
            not agent.development.records
            for agent in migrated.agents
        ))

    def test_corrupted_development_state_fails_clearly(self):
        world = World(seed=1947, population=1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents SET development_json = '[]' WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid development state",
        ):
            load_world(self.db_path)

    def test_schema15_defaults_to_disabled_empty_lifecycle_state(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        child = create_developing_child(world)
        progress_child(world, child, 2)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute("ALTER TABLE agents DROP COLUMN lifecycle_json")
            conn.execute(
                "ALTER TABLE world_state DROP COLUMN lifecycle_enabled"
            )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 15 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertFalse(loaded.lifecycle_enabled)
        self.assertTrue(all(
            agent.lifecycle.alive
            and not agent.lifecycle.support_received
            and not agent.lifecycle.inheritance_received
            and not agent.lifecycle.mortality_checks
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        migrated = load_world(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            world_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(world_state)"
                )
            }
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("lifecycle_enabled", world_columns)
        self.assertIn("lifecycle_json", agent_columns)
        self.assertFalse(migrated.lifecycle_enabled)

    def test_corrupted_lifecycle_state_fails_clearly(self):
        world = World(seed=1947, population=1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents SET lifecycle_json = '[]' WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid lifecycle state",
        ):
            load_world(self.db_path)

    def test_schema16_defaults_to_empty_cultural_state(self):
        world = World(seed=71, population=2)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with sqlite_connection(self.db_path) as conn:
            conn.execute("ALTER TABLE agents DROP COLUMN culture_json")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 16 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertTrue(all(
            not agent.culture.records
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        migrated = load_world(self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            agent_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("culture_json", agent_columns)
        self.assertTrue(all(
            not agent.culture.records
            for agent in migrated.agents
        ))

    def test_corrupted_cultural_state_fails_clearly(self):
        world = World(seed=1947, population=1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents SET culture_json = '[]' WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid cultural state",
        ):
            load_world(self.db_path)

    def test_corrupted_family_state_fails_clearly(self):
        world = World(seed=1947, population=1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents SET family_json = '[]' WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid family state",
        ):
            load_world(self.db_path)

    def test_broken_family_links_cannot_be_saved(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        first, _ = prepare_family_pair(world)
        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            world.resolve_reproduction()
        first.family = replace(first.family, child_ids=())

        with self.assertRaisesRegex(
            PersistenceError,
            "Invalid family state",
        ):
            save_world(world, self.db_path)

    def test_corrupted_adaptive_state_fails_clearly(self):
        world = World(
            seed=1947,
            population=1,
            adaptive_cognition=True,
        )
        world.run(1)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE agents "
                "SET adaptive_values_json = '[]' "
                "WHERE id = ?",
                (world.agents[0].id,),
            )

        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid adaptive state",
        ):
            load_world(self.db_path)

    def test_economy_capacity_survives_restart(self):
        world = World(seed=1947)
        world.economy = EconomyState(job_capacity=9)

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(loaded.economy.job_capacity, 9)
        self.assertEqual(
            loaded.economy.occupied_jobs(loaded.agents),
            world.economy.occupied_jobs(world.agents),
        )

    def test_schema9_derives_valid_economy_without_rng_draws(self):
        world = World(seed=2)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute("DROP TABLE economy_state")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 9 WHERE id = 1"
            )

        expected_rng_state = world.rng.getstate()
        loaded = load_world(self.db_path)

        self.assertGreaterEqual(
            loaded.economy.job_capacity,
            loaded.economy.occupied_jobs(loaded.agents),
        )
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            capacity = conn.execute(
                "SELECT job_capacity "
                "FROM economy_state WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(schema_version, 20)
        self.assertEqual(capacity, loaded.economy.job_capacity)

    def test_schema10_defaults_missing_information_identity(self):
        world = World(seed=1947, population=2)
        first, second = world.agents
        first.current_location = "market"
        second.current_location = "market"
        first.traits["sociability"] = 1.0
        second.traits["sociability"] = 1.0
        world.day = 1
        world.resolve_daily_interactions()
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            for column in (
                "information_id",
                "origin_agent_id",
                "origin_day",
                "hop_count",
            ):
                conn.execute(
                    f"ALTER TABLE observations DROP COLUMN {column}"
                )
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 10 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            for observation in agent.observations:
                self.assertIsNone(observation.information_id)
                self.assertIsNone(observation.origin_agent_id)
                self.assertIsNone(observation.origin_day)
                self.assertIsNone(observation.hop_count)

        save_world(loaded, self.db_path)
        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            observation_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(observations)"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertTrue(
            {
                "information_id",
                "origin_agent_id",
                "origin_day",
                "hop_count",
            }.issubset(observation_columns)
        )

    def test_economy_capacity_cannot_be_less_than_occupancy(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE economy_state SET job_capacity = 0 "
                "WHERE id = 1"
            )

        with self.assertRaises(WorldLoadError) as context:
            load_world(self.db_path)

        self.assertIn("occupied jobs", str(context.exception))

    def test_custom_capacity_continuation_matches_restart(self):
        def make_world():
            world = World(seed=1947, population=2)
            for agent in world.agents:
                agent.employed = False
                agent.job_level = 0
                agent.salary = 0
                agent.skill = 1.0
                agent.reputation = 20.0
                agent.traits["sociability"] = 1.0
            world.economy = EconomyState(job_capacity=2)
            return world

        uninterrupted = make_world()
        uninterrupted.act(uninterrupted.agents[0], "job_hunt")
        uninterrupted.act(uninterrupted.agents[1], "job_hunt")

        interrupted = make_world()
        interrupted.act(interrupted.agents[0], "job_hunt")
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed.act(resumed.agents[1], "job_hunt")

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_school_constraint_continuation_matches_restart(self):
        uninterrupted = World(seed=1947, population=2)
        with patch(
            "playing_god.core.world.choose",
            return_value="train",
        ):
            uninterrupted.run(4)

        interrupted = World(seed=1947, population=2)
        with patch(
            "playing_god.core.world.choose",
            return_value="train",
        ):
            interrupted.run(1)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        with patch(
            "playing_god.core.world.choose",
            return_value="train",
        ):
            resumed.run(3)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.school_snapshot(),
            uninterrupted.school_snapshot(),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_schema4_defaults_social_energy_to_physical_energy(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
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

        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(schema_version, 20)

    def test_prayers_survive_restart(self):
        world = World(seed=1947)
        agent = world.agents[0]
        agent.prayers.append(
            Prayer(
                agent_id=agent.id,
                desire_type="security",
                intensity=0.72,
                related_goal="build_savings",
                timestamp=4,
            )
        )

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(
            loaded.agents[0].prayers,
            agent.prayers,
        )

    def test_prayer_cannot_be_saved_under_wrong_agent(self):
        world = World(seed=1947)
        agent = world.agents[0]
        agent.prayers.append(
            Prayer(
                agent_id=world.agents[1].id,
                desire_type="security",
                intensity=0.72,
                related_goal="build_savings",
                timestamp=4,
            )
        )

        with self.assertRaises(PersistenceError):
            save_world(world, self.db_path)

    def test_schema6_defaults_to_empty_prayer_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute("DROP TABLE prayers")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 6 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            self.assertEqual(agent.prayers, [])

        save_world(loaded, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            prayer_table = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'prayers'"
            ).fetchone()

        self.assertEqual(schema_version, 20)
        self.assertIsNotNone(prayer_table)

    def test_schema7_defaults_to_empty_intervention_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute("DROP TABLE intervention_responses")
            conn.execute("DROP TABLE interventions")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 7 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertEqual(loaded.interventions, [])
        self.assertEqual(loaded.intervention_responses, [])

        save_world(loaded, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table'"
                )
            }

        self.assertEqual(schema_version, 20)
        self.assertIn("interventions", tables)
        self.assertIn("intervention_responses", tables)

    def test_schema8_defaults_to_neutral_empty_faith_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            conn.execute("DROP TABLE attributions")
            conn.execute("ALTER TABLE agents DROP COLUMN faith")
            conn.execute(
                "UPDATE world_state "
                "SET schema_version = 8 WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        for agent in loaded.agents:
            self.assertEqual(agent.faith, 0.5)
            self.assertEqual(agent.attributions, [])

        save_world(loaded, self.db_path)

        with sqlite_connection(self.db_path) as conn:
            schema_version = conn.execute(
                "SELECT schema_version "
                "FROM world_state WHERE id = 1"
            ).fetchone()[0]
            agent_columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(agents)")
            }
            attribution_table = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'attributions'"
            ).fetchone()

        self.assertEqual(schema_version, 20)
        self.assertIn("faith", agent_columns)
        self.assertIsNotNone(attribution_table)

    def test_interventions_and_responses_survive_restart(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        target.traits["discipline"] = 1.0
        target.traits["risk_tolerance"] = 1.0
        target.stress = 0.0
        world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="mastering a difficult craft",
            suggested_action="train",
            strength=1.0,
        )
        world.day = 1
        world.resolve_interventions()

        save_world(world, self.db_path)
        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(
            world_snapshot(loaded),
            world_snapshot(world),
        )
        self.assertEqual(
            loaded.rng.getstate(),
            world.rng.getstate(),
        )

        with sqlite_connection(self.db_path) as conn:
            intervention_rows = conn.execute(
                "SELECT COUNT(*) FROM interventions"
            ).fetchone()[0]
            response_rows = conn.execute(
                "SELECT COUNT(*) FROM intervention_responses"
            ).fetchone()[0]

        self.assertEqual(intervention_rows, 1)
        self.assertEqual(response_rows, 1)

    def test_faith_attribution_history_survives_restart(self):
        world = World(seed=1947, population=2)
        target = world.agents[0]
        target.traits["discipline"] = 1.0
        target.traits["risk_tolerance"] = 1.0
        target.stress = 0.0
        target.prayers.append(
            Prayer(
                agent_id=target.id,
                desire_type="employment",
                intensity=1.0,
                related_goal="find_job",
                timestamp=0,
            )
        )
        world.create_intervention(
            kind="dream",
            target_id=target.id,
            theme="an open office door",
            suggested_action="job_hunt",
            strength=1.0,
        )
        world.day = 1
        world.resolve_interventions()
        target.events.append(
            Event(
                day=1,
                kind="career",
                description="Found a job paying 30/day",
                significance=0.94,
            )
        )
        world.resolve_daily_attributions()

        save_world(world, self.db_path)
        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(world_snapshot(loaded), world_snapshot(world))

        with sqlite_connection(self.db_path) as conn:
            attribution_rows = conn.execute(
                "SELECT COUNT(*) FROM attributions"
            ).fetchone()[0]

        self.assertEqual(attribution_rows, 1)

    def test_active_intervention_continuation_matches_restart(self):
        def make_world():
            world = World(seed=1947, population=2)
            target = world.agents[0]
            target.traits["discipline"] = 1.0
            target.traits["risk_tolerance"] = 1.0
            target.stress = 0.0
            world.create_intervention(
                kind="dream",
                target_id=target.id,
                theme="mastering a difficult craft",
                suggested_action="train",
                strength=1.0,
                duration=7,
            )
            return world

        uninterrupted = make_world()
        uninterrupted.run(4)

        interrupted = make_world()
        interrupted.run(1)
        save_world(interrupted, self.db_path)
        resumed = load_world(self.db_path)
        resumed.run(3)

        self.assertEqual(
            world_snapshot(resumed),
            world_snapshot(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )

    def test_schema5_defaults_to_empty_perception_state(self):
        world = World(seed=1947)
        save_world(world, self.db_path)

        with sqlite_connection(self.db_path) as conn:
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

        with sqlite_connection(self.db_path) as conn:
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

        with sqlite_connection(self.db_path) as conn:
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

        with sqlite_connection(self.db_path) as conn:
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

        with sqlite_connection(self.db_path) as conn:
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
        expected_prayer_count = sum(
            len(agent.prayers)
            for agent in world.agents
        )
        expected_attribution_count = sum(
            len(agent.attributions)
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

        with sqlite_connection(
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

            prayer_rows = conn.execute(
                """
                SELECT COUNT(*)
                FROM prayers
                """
            ).fetchone()[0]

            attribution_rows = conn.execute(
                """
                SELECT COUNT(*)
                FROM attributions
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

        self.assertEqual(
            prayer_rows,
            expected_prayer_count,
        )

        self.assertEqual(
            attribution_rows,
            expected_attribution_count,
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
        with sqlite_connection(
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
