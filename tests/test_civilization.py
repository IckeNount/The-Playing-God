from __future__ import annotations

import sqlite3
import tempfile
import unittest

from contextlib import closing
from dataclasses import replace
from pathlib import Path

from playing_god.core.civilization import (
    BASE_PRIMITIVES,
    AffordanceDefinition,
    AgentKnowledgeRecord,
    AgentKnowledgeState,
    BoundedEffect,
    CivilizationState,
    KnowledgeEntry,
    adopted_knowledge_ids,
    affordance_definition,
    base_primitive,
    knowledge_entry,
    knowledge_signature,
    validate_civilization_state,
)
from playing_god.core.decision import scores
from playing_god.core.events import Event
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    PersistenceError,
    WorldLoadError,
    load_world,
    save_world,
)


KNOWLEDGE_ID = "knowledge:peer_training"
ACTION_ID = "peer_train"
PRIMITIVE_IDS = (
    "demonstration",
    "feedback",
    "shared_practice",
)


def add_valid_registry(world: World) -> None:
    world.day = 2
    discoverer = world.agents[0]
    origin_event_index = len(discoverer.events)
    discoverer.events.append(
        Event(
            day=1,
            kind="discovery_attempted",
            description="Combined peer-learning primitives",
            significance=0.60,
        )
    )
    validation_event_index = len(discoverer.events)
    discoverer.events.append(
        Event(
            day=2,
            kind="discovery_validated",
            description="Validated peer-training knowledge",
            significance=0.80,
        )
    )

    entry = KnowledgeEntry(
        id=KNOWLEDGE_ID,
        signature=knowledge_signature(PRIMITIVE_IDS, ACTION_ID),
        origin_agent_id=discoverer.id,
        origin_event_index=origin_event_index,
        discoverer_ids=(discoverer.id,),
        primitive_ids=PRIMITIVE_IDS,
        action_id=ACTION_ID,
        creation_day=2,
    )
    affordance = AffordanceDefinition(
        id=ACTION_ID,
        source_knowledge_id=KNOWLEDGE_ID,
        preconditions=(
            "adult",
            "co_located",
            "knowledge_adopted",
            "learner_energy",
            "relationship",
            "teacher_energy",
            "teacher_skill",
        ),
        costs=(
            BoundedEffect("consume_energy", "learner", 0.04),
            BoundedEffect("consume_energy", "teacher", 0.06),
        ),
        effects=(
            BoundedEffect("increase_skill", "learner", 0.006),
        ),
    )
    world.civilization = CivilizationState(
        knowledge=(entry,),
        affordances=(affordance,),
    )
    discoverer.knowledge = AgentKnowledgeState(records=(
        AgentKnowledgeRecord(
            day=2,
            knowledge_id=KNOWLEDGE_ID,
            source_id=discoverer.id,
            route="discovery",
            response="accept",
            variant_id=None,
            causal_parent_agent_id=discoverer.id,
            causal_parent_event_index=validation_event_index,
        ),
    ))


class CivilizationRegistryTests(unittest.TestCase):
    def test_new_world_has_only_canonical_base_primitives(self):
        world = World(seed=1947, population=2)

        self.assertEqual(world.base_primitives, BASE_PRIMITIVES)
        self.assertEqual(
            tuple(item.id for item in world.base_primitives),
            PRIMITIVE_IDS,
        )
        self.assertEqual(world.civilization, CivilizationState())
        self.assertTrue(all(
            agent.knowledge == AgentKnowledgeState()
            for agent in world.agents
        ))
        self.assertNotIn(ACTION_ID, scores(world.agents[0]))

    def test_lookup_and_signature_are_deterministic(self):
        world = World(seed=8, population=1)
        add_valid_registry(world)

        self.assertEqual(
            knowledge_signature(
                tuple(reversed(PRIMITIVE_IDS)),
                ACTION_ID,
            ),
            knowledge_signature(PRIMITIVE_IDS, ACTION_ID),
        )
        self.assertEqual(
            base_primitive("feedback"),
            BASE_PRIMITIVES[1],
        )
        self.assertEqual(
            knowledge_entry(world.civilization, KNOWLEDGE_ID),
            world.civilization.knowledge[0],
        )
        self.assertEqual(
            affordance_definition(world.civilization, ACTION_ID),
            world.civilization.affordances[0],
        )
        self.assertEqual(
            adopted_knowledge_ids(world.agents[0].knowledge),
            (KNOWLEDGE_ID,),
        )

    def test_duplicate_signature_is_rejected(self):
        world = World(seed=8, population=1)
        add_valid_registry(world)
        original = world.civilization.knowledge[0]
        duplicate = replace(original, id="knowledge:peer_training_copy")

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate or unordered knowledge registry",
        ):
            validate_civilization_state(CivilizationState(
                knowledge=(original, duplicate),
                affordances=world.civilization.affordances,
            ))

    def test_unknown_primitive_and_effect_are_rejected(self):
        world = World(seed=8, population=1)
        add_valid_registry(world)
        entry = world.civilization.knowledge[0]
        affordance = world.civilization.affordances[0]

        with self.assertRaisesRegex(
            ValueError,
            "Invalid validated knowledge entry",
        ):
            validate_civilization_state(CivilizationState(
                knowledge=(replace(
                    entry,
                    primitive_ids=("unknown_primitive",),
                    signature=knowledge_signature(
                        ("unknown_primitive",),
                        ACTION_ID,
                    ),
                ),),
                affordances=(affordance,),
            ))

        with self.assertRaisesRegex(
            ValueError,
            "Invalid bounded civilization effect",
        ):
            validate_civilization_state(CivilizationState(
                knowledge=(entry,),
                affordances=(replace(
                    affordance,
                    effects=(BoundedEffect(
                        "run_python",
                        "learner",
                        0.1,
                    ),),
                ),),
            ))


class CivilizationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "world.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registry_and_agent_knowledge_survive_restart(self):
        world = World(seed=27, population=2)
        add_valid_registry(world)
        expected_rng_state = world.rng.getstate()

        save_world(world, self.db_path)
        loaded = load_world(self.db_path)

        self.assertEqual(loaded.civilization, world.civilization)
        self.assertEqual(
            loaded.agents[0].knowledge,
            world.agents[0].knowledge,
        )
        self.assertEqual(loaded.base_primitives, BASE_PRIMITIVES)
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

    def test_schema17_loads_empty_state_and_migrates_to_18(self):
        world = World(seed=31, population=2)
        save_world(world, self.db_path)
        expected_rng_state = world.rng.getstate()

        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "ALTER TABLE world_state "
                "DROP COLUMN civilization_json"
            )
            conn.execute(
                "ALTER TABLE agents DROP COLUMN knowledge_json"
            )
            conn.execute(
                "UPDATE world_state SET schema_version = 17 "
                "WHERE id = 1"
            )

        loaded = load_world(self.db_path)

        self.assertEqual(loaded.civilization, CivilizationState())
        self.assertTrue(all(
            agent.knowledge == AgentKnowledgeState()
            for agent in loaded.agents
        ))
        self.assertEqual(loaded.base_primitives, BASE_PRIMITIVES)
        self.assertEqual(loaded.rng.getstate(), expected_rng_state)

        save_world(loaded, self.db_path)
        with closing(sqlite3.connect(self.db_path)) as conn:
            schema_version = conn.execute(
                "SELECT schema_version FROM world_state WHERE id = 1"
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

        self.assertEqual(schema_version, 18)
        self.assertIn("civilization_json", world_columns)
        self.assertIn("knowledge_json", agent_columns)

    def test_corrupt_registry_and_agent_knowledge_fail_clearly(self):
        world = World(seed=41, population=1)
        save_world(world, self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "UPDATE world_state SET civilization_json = '[]' "
                "WHERE id = 1"
            )
        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid civilization state",
        ):
            load_world(self.db_path)

        save_world(world, self.db_path)
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "UPDATE agents SET knowledge_json = '[]' "
                "WHERE id = ?",
                (world.agents[0].id,),
            )
        with self.assertRaisesRegex(
            WorldLoadError,
            "Invalid knowledge state",
        ):
            load_world(self.db_path)

    def test_save_rejects_broken_origin_link(self):
        world = World(seed=51, population=1)
        add_valid_registry(world)
        world.agents[0].events.clear()

        with self.assertRaisesRegex(
            PersistenceError,
            "Invalid civilization links",
        ):
            save_world(world, self.db_path)


if __name__ == "__main__":
    unittest.main()
