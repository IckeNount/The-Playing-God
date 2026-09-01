from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from playing_god.core.culture import (
    CULTURAL_NORM,
    SCHOOL_NORM_SUBJECT,
    SCHOOL_SOURCE_ID,
)
from playing_god.core.perception import belief_key
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world


def make_family(seed: int = 71):
    world = World(
        seed=seed,
        population=2,
        reproduction_enabled=True,
        adaptive_cognition=True,
    )
    first, second = world.agents
    for parent in (first, second):
        parent.age = 30
        parent.money = 500.0
        parent.stress = 0.10
        parent.current_location = "home"
    first.employed = True
    first.relationships[second.id] = 0.50
    second.relationships[first.id] = 0.50
    for source, target in ((first, second), (second, first)):
        world.social.add_relationship(
            source.id,
            target.id,
            affinity=0.50,
            trust=0.70,
            familiarity=0.80,
        )
    world.express_cultural_norm(
        first.id,
        "mutual_aid",
        "support",
    )
    with patch(
        "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
        1.0,
    ):
        child = world.resolve_reproduction()[0]
    return world, first, second, child


def progress_to(world: World, child, age: int) -> None:
    for current_age in range(child.age + 1, age + 1):
        world.day = child.family.birth_day + current_age * 365
        world.resolve_development()


class CulturalTransmissionTests(unittest.TestCase):

    def test_birth_does_not_copy_parent_culture_or_policy(self):
        world, parent, _, child = make_family()

        self.assertIn(
            belief_key(CULTURAL_NORM, "mutual_aid"),
            parent.beliefs,
        )
        self.assertEqual(child.beliefs, {})
        self.assertEqual(child.observations, [])
        self.assertEqual(child.culture.records, ())
        self.assertEqual(child.adaptive_values, {})

    def test_guardian_exposure_causes_later_generation_acceptance(self):
        world, parent, _, child = make_family()
        rng_state = world.rng.getstate()

        progress_to(world, child, 1)

        records = [
            record
            for record in child.culture.records
            if record.subject_id == "mutual_aid"
        ]
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.source_id, parent.id)
        self.assertEqual(record.route, "guardian")
        self.assertEqual(record.response, "accept")
        self.assertEqual(record.resulting_value, "support")
        self.assertEqual(
            child.beliefs[
                belief_key(CULTURAL_NORM, "mutual_aid")
            ].value,
            "support",
        )
        self.assertEqual(
            child.observations[-1].information_id,
            parent.observations[0].information_id,
        )
        self.assertEqual(world.rng.getstate(), rng_state)

    def test_same_priors_can_modify_or_reject_guardian_norm(self):
        modified, _, _, modified_child = make_family()
        rejected, _, _, rejected_child = make_family()
        self.assertEqual(modified_child.traits, rejected_child.traits)
        self.assertEqual(modified_child.sins, rejected_child.sins)

        modified_child.traits["empathy"] = 0.50
        rejected_child.traits["empathy"] = 0.0
        parent_id = modified_child.family.guardian_ids[0]
        modified.social.add_relationship(
            modified_child.id,
            parent_id,
            affinity=0.0,
            trust=0.20,
            familiarity=0.10,
        )
        rejected.social.add_relationship(
            rejected_child.id,
            parent_id,
            affinity=0.0,
            trust=0.0,
            familiarity=0.0,
        )

        progress_to(modified, modified_child, 1)
        progress_to(rejected, rejected_child, 1)

        modified_record = modified_child.culture.records[0]
        rejected_record = rejected_child.culture.records[0]
        self.assertEqual(modified_record.response, "modify")
        self.assertEqual(modified_record.resulting_value, "uncertain")
        self.assertEqual(rejected_record.response, "reject")
        self.assertNotIn(
            belief_key(CULTURAL_NORM, "mutual_aid"),
            rejected_child.beliefs,
        )
        self.assertTrue(any(
            observation.subject_id == "mutual_aid"
            for observation in rejected_child.observations
        ))

    def test_school_access_is_an_explicit_institutional_route(self):
        world, parent, _, child = make_family()
        parent.beliefs.clear()
        parent.observations.clear()
        world.rebuild_information_index()

        progress_to(world, child, 6)

        school_records = [
            record
            for record in child.culture.records
            if record.route == "school"
        ]
        self.assertEqual(len(school_records), 1)
        self.assertEqual(school_records[0].source_id, SCHOOL_SOURCE_ID)
        self.assertEqual(school_records[0].response, "accept")
        self.assertEqual(
            child.beliefs[
                belief_key(CULTURAL_NORM, SCHOOL_NORM_SUBJECT)
            ].value,
            "support",
        )
        self.assertTrue(child.development.records[-1].school_access)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "school-world.db"
            save_world(world, path)
            loaded = load_world(path)
        loaded_child = loaded.agents[-1]
        self.assertEqual(
            asdict(loaded_child.culture),
            asdict(child.culture),
        )

    def test_social_contact_moves_norm_through_information_identity(self):
        world = World(seed=1947, population=2)
        source, recipient = world.agents
        for agent in world.agents:
            agent.traits["sociability"] = 1.0
            agent.social_energy = 1.0
            agent.current_location = "market"
        world.social.add_relationship(
            recipient.id,
            source.id,
            affinity=0.50,
            trust=0.90,
            familiarity=0.90,
        )
        origin = world.express_cultural_norm(
            source.id,
            "mutual_aid",
            "support",
        )
        world.day = 1

        world.resolve_daily_interactions()

        records = [
            record
            for record in recipient.culture.records
            if record.route == "social"
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].response, "accept")
        self.assertEqual(records[0].information_id, origin.information_id)
        snapshot = world.diffusion_snapshot(origin.information_id)
        self.assertEqual(snapshot.reached_agent_count, 2)
        self.assertEqual(snapshot.informed_agent_count, 2)

    def test_cultural_history_and_continuation_survive_restart(self):
        uninterrupted, _, _, uninterrupted_child = make_family()
        split, _, _, split_child = make_family()
        progress_to(uninterrupted, uninterrupted_child, 2)
        progress_to(split, split_child, 1)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "world.db"
            save_world(split, path)
            loaded = load_world(path)
            loaded_child = loaded.agents[-1]
            progress_to(loaded, loaded_child, 2)

        self.assertEqual(
            asdict(loaded_child.culture),
            asdict(uninterrupted_child.culture),
        )
        self.assertEqual(
            loaded_child.beliefs,
            uninterrupted_child.beliefs,
        )
        self.assertEqual(
            loaded.rng.getstate(),
            uninterrupted.rng.getstate(),
        )


if __name__ == "__main__":
    unittest.main()
