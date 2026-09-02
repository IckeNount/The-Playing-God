from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.civilization import (
    PEER_TRAIN_ACTION_ID,
    PEER_TRAIN_KNOWLEDGE_ID,
    AgentKnowledgeRecord,
    AgentKnowledgeState,
    CivilizationState,
    KnowledgeEntry,
    activate_peer_training_affordance,
    knowledge_signature,
    validate_civilization_links,
)
from playing_god.core.events import Event
from playing_god.core.institution import validate_school_links
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    PersistenceError,
    load_world,
    save_world,
)
from tests.test_development import (
    prepare_family,
    progress_to,
    set_upbringing,
)
from tests.test_peer_training import actionable_world


PRIMITIVE_IDS = (
    "demonstration",
    "feedback",
    "shared_practice",
)


def add_knowledge(world: World, discoverer) -> None:
    world.day = 2
    attempt_index = len(discoverer.events)
    discoverer.events.append(Event(
        day=1,
        kind="discovery_attempted",
        description="Combined peer-learning primitives",
        significance=0.60,
    ))
    validation_index = len(discoverer.events)
    discoverer.events.append(Event(
        day=2,
        kind="discovery_validated",
        description="Validated peer-training knowledge",
        significance=0.85,
    ))
    world.civilization = activate_peer_training_affordance(
        CivilizationState(knowledge=(KnowledgeEntry(
            id=PEER_TRAIN_KNOWLEDGE_ID,
            signature=knowledge_signature(
                PRIMITIVE_IDS,
                PEER_TRAIN_ACTION_ID,
            ),
            origin_agent_id=discoverer.id,
            origin_event_index=attempt_index,
            discoverer_ids=(discoverer.id,),
            primitive_ids=PRIMITIVE_IDS,
            action_id=PEER_TRAIN_ACTION_ID,
            creation_day=2,
        ),))
    )
    discoverer.knowledge = AgentKnowledgeState(records=(
        AgentKnowledgeRecord(
            day=2,
            knowledge_id=PEER_TRAIN_KNOWLEDGE_ID,
            source_id=discoverer.id,
            route="discovery",
            response="accept",
            variant_id=None,
            causal_parent_agent_id=discoverer.id,
            causal_parent_event_index=validation_index,
        ),
    ))


def school_evidence_world(*, evidence_days: int) -> World:
    world = actionable_world()
    teacher, learner = world.agents
    teacher.current_location = "school"
    learner.current_location = "school"
    for day in range(3, 3 + evidence_days):
        world.day = day
        world.act(teacher, PEER_TRAIN_ACTION_ID)
    return world


def family_world(*, evidence_days: int) -> tuple[World, object]:
    world = World(seed=71, population=4, reproduction_enabled=True)
    first, second, child = prepare_family(world)
    set_upbringing(
        world,
        child,
        (first, second),
        supported=True,
    )
    teacher, learner = world.agents[2:4]
    add_knowledge(world, teacher)
    teacher.skill = 0.65
    learner.skill = 0.20
    teacher.energy = 0.80
    learner.energy = 0.80
    teacher.current_location = "school"
    learner.current_location = "school"
    for source, target in ((teacher, learner), (learner, teacher)):
        world.social.add_relationship(
            source.id,
            target.id,
            affinity=0.40,
            trust=0.70,
            familiarity=0.80,
        )
    for day in range(3, 3 + evidence_days):
        world.day = day
        world.act(teacher, PEER_TRAIN_ACTION_ID)
    return world, child


class InstitutionalAdoptionTests(unittest.TestCase):
    def test_unknown_unobserved_or_insufficient_evidence_does_not_adopt(self):
        unknown = World(seed=1947, population=2)
        for agent in unknown.agents:
            agent.current_location = "school"
        for day in (3, 4, 5):
            unknown.day = day
            unknown.act(unknown.agents[0], PEER_TRAIN_ACTION_ID)

        unobserved = actionable_world()
        for day in (3, 4, 5):
            unobserved.day = day
            unobserved.act(
                unobserved.agents[0],
                PEER_TRAIN_ACTION_ID,
            )

        insufficient = school_evidence_world(evidence_days=2)
        same_day = school_evidence_world(evidence_days=0)
        for _ in range(3):
            same_day.act(same_day.agents[0], PEER_TRAIN_ACTION_ID)

        self.assertEqual(unknown.school.knowledge_evidence, ())
        self.assertIsNone(unknown.school.knowledge_adoption)
        self.assertEqual(unobserved.school.knowledge_evidence, ())
        self.assertIsNone(unobserved.school.knowledge_adoption)
        self.assertEqual(len(insufficient.school.knowledge_evidence), 2)
        self.assertIsNone(insufficient.school.knowledge_adoption)
        self.assertEqual(len(same_day.school.knowledge_evidence), 1)
        self.assertIsNone(same_day.school.knowledge_adoption)

    def test_adoption_is_causal_and_changes_only_later_school_opportunity(self):
        non_adopted, baseline_child = family_world(evidence_days=2)
        adopted, later_child = family_world(evidence_days=3)

        self.assertIsNone(non_adopted.school.knowledge_adoption)
        adoption = adopted.school.knowledge_adoption
        self.assertIsNotNone(adoption)
        self.assertEqual(adoption.day, 5)
        self.assertEqual(adoption.evidence_count, 3)
        self.assertEqual(
            (adoption.origin_agent_id, adoption.origin_event_index),
            (
                adopted.civilization.knowledge[0].origin_agent_id,
                adopted.civilization.knowledge[0].origin_event_index,
            ),
        )

        progress_to(non_adopted, 6)
        progress_to(adopted, 6)

        self.assertFalse(any(
            record.route == "school"
            for record in baseline_child.knowledge.records
        ))
        school_records = [
            record
            for record in later_child.knowledge.records
            if record.route == "school"
        ]
        self.assertEqual(len(school_records), 1)
        self.assertGreaterEqual(school_records[0].day, adoption.day)
        self.assertNotIn(
            later_child.id,
            adopted.civilization.knowledge[0].discoverer_ids,
        )
        validate_civilization_links(
            adopted.civilization,
            adopted.agents,
            current_day=adopted.day,
            school=adopted.school,
        )
        validate_school_links(
            adopted.school,
            adopted.civilization,
            adopted.agents,
            current_day=adopted.day,
        )

    def test_broken_school_evidence_is_rejected(self):
        world = school_evidence_world(evidence_days=3)
        first = world.school.knowledge_evidence[0]
        world.school.knowledge_evidence = (
            replace(first, teacher_event_index=len(world.agents[0].events)),
            *world.school.knowledge_evidence[1:],
        )

        with self.assertRaisesRegex(
            ValueError,
            "Invalid school evidence link",
        ):
            validate_school_links(
                world.school,
                world.civilization,
                world.agents,
                current_day=world.day,
            )
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                PersistenceError,
                "Invalid school links",
            ):
                save_world(world, Path(directory) / "world.db")

    def test_adoption_is_deterministic_persistent_and_schema21_defaults_empty(self):
        first = school_evidence_world(evidence_days=3)
        second = school_evidence_world(evidence_days=3)
        self.assertEqual(asdict(first.school), asdict(second.school))
        self.assertEqual(
            [asdict(agent) for agent in first.agents],
            [asdict(agent) for agent in second.agents],
        )
        self.assertEqual(first.rng.getstate(), second.rng.getstate())

        with TemporaryDirectory() as directory:
            path = Path(directory) / "world.db"
            save_world(first, path)
            loaded = load_world(path)
            save_world(loaded, path)
            reloaded = load_world(path)

            self.assertEqual(reloaded.school, first.school)
            self.assertEqual(sum(
                event.kind == "institution_adoption"
                for agent in reloaded.agents
                for event in agent.events
            ), 1)

            legacy_path = Path(directory) / "legacy.db"
            legacy = World(seed=8, population=2)
            expected_rng = legacy.rng.getstate()
            save_world(legacy, legacy_path)
            with closing(sqlite3.connect(legacy_path)) as conn, conn:
                conn.execute(
                    "ALTER TABLE world_state DROP COLUMN school_json"
                )
                conn.execute(
                    "UPDATE world_state SET schema_version = 21 WHERE id = 1"
                )
            migrated = load_world(legacy_path)
            self.assertEqual(migrated.school.knowledge_evidence, ())
            self.assertIsNone(migrated.school.knowledge_adoption)
            self.assertEqual(migrated.rng.getstate(), expected_rng)
            save_world(migrated, legacy_path)
            with closing(sqlite3.connect(legacy_path)) as conn:
                version = conn.execute(
                    "SELECT schema_version FROM world_state WHERE id = 1"
                ).fetchone()[0]

        self.assertEqual(version, 22)


if __name__ == "__main__":
    unittest.main()
