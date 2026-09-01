from __future__ import annotations

import unittest

from dataclasses import asdict
from unittest.mock import patch

from playing_god.core.development import ADULT_AGE
from playing_god.core.world import World


def prepare_family(world: World):
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
    with patch(
        "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
        1.0,
    ):
        child = world.resolve_reproduction()[0]
    return first, second, child


def set_upbringing(
    world: World,
    child,
    guardians,
    *,
    supported: bool,
) -> None:
    for index, guardian in enumerate(guardians):
        guardian.money = 500.0 if supported else 0.0
        guardian.employed = supported and index == 0
        guardian.stress = 0.10 if supported else 0.90
        world.social.add_relationship(
            guardian.id,
            child.id,
            affinity=0.45,
            trust=0.90 if supported else 0.10,
            familiarity=0.90 if supported else 0.10,
        )


def progress_to(world: World, age: int) -> None:
    child = world.agents[-1]
    birth_day = child.family.birth_day
    for current_age in range(child.age + 1, age + 1):
        world.day = birth_day + current_age * 365
        world.resolve_development()


class ChildDevelopmentTests(unittest.TestCase):

    def make_world(self, *, supported: bool) -> tuple[World, object]:
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
            adaptive_cognition=True,
        )
        first, second, child = prepare_family(world)
        set_upbringing(
            world,
            child,
            (first, second),
            supported=supported,
        )
        return world, child

    def test_similar_priors_diverge_through_upbringing_and_school_access(self):
        supported, supported_child = self.make_world(supported=True)
        constrained, constrained_child = self.make_world(supported=False)

        self.assertEqual(
            supported_child.traits,
            constrained_child.traits,
        )
        self.assertEqual(
            supported_child.sins,
            constrained_child.sins,
        )

        progress_to(supported, ADULT_AGE)
        progress_to(constrained, ADULT_AGE)

        self.assertFalse(supported_child.family.dependent)
        self.assertFalse(constrained_child.family.dependent)
        self.assertTrue(any(
            record.school_access
            for record in supported_child.development.records
        ))
        self.assertFalse(any(
            record.school_access
            for record in constrained_child.development.records
        ))
        self.assertGreater(supported_child.skill, constrained_child.skill)
        self.assertEqual(constrained_child.skill, 0.0)
        self.assertIn(
            "train",
            supported_child.adaptive_values["improve_skill"],
        )
        self.assertEqual(constrained_child.adaptive_values, {})

    def test_child_actions_remain_blocked_until_age_eighteen(self):
        world, child = self.make_world(supported=True)
        progress_to(world, ADULT_AGE - 1)

        world.act(child, "rest")
        self.assertTrue(child.family.dependent)
        self.assertEqual(dict(child.actions), {})

        progress_to(world, ADULT_AGE)
        world.act(child, "rest")

        self.assertFalse(child.family.dependent)
        self.assertEqual(child.age, ADULT_AGE)
        self.assertEqual(child.actions["rest"], 1)

    def test_development_is_exact_and_consumes_no_rng(self):
        first, first_child = self.make_world(supported=True)
        second, second_child = self.make_world(supported=True)
        first_rng = first.rng.getstate()
        second_rng = second.rng.getstate()

        progress_to(first, 8)
        progress_to(second, 8)

        self.assertEqual(
            asdict(first_child.development),
            asdict(second_child.development),
        )
        self.assertEqual(first_child.skill, second_child.skill)
        self.assertEqual(first.rng.getstate(), first_rng)
        self.assertEqual(second.rng.getstate(), second_rng)

    def test_development_occurs_only_on_birth_anniversary(self):
        world, child = self.make_world(supported=True)
        birth_day = child.family.birth_day
        world.day = birth_day + 364

        self.assertEqual(world.resolve_development(), [])
        self.assertEqual(child.age, 0)

        world.day += 1
        self.assertEqual(world.resolve_development(), [child])
        self.assertEqual(world.resolve_development(), [])
        self.assertEqual(child.age, 1)
        self.assertEqual(len(child.development.records), 1)
        self.assertEqual(
            child.development.records[0].stage,
            "early_childhood",
        )

    def test_anniversary_progression_matches_across_split_world_runs(self):
        uninterrupted, uninterrupted_child = self.make_world(
            supported=True
        )
        split, split_child = self.make_world(supported=True)
        uninterrupted.reproduction_enabled = False
        split.reproduction_enabled = False

        uninterrupted.run(365)
        split.run(180)
        split.run(185)

        self.assertEqual(
            [asdict(agent) for agent in split.agents],
            [asdict(agent) for agent in uninterrupted.agents],
        )
        self.assertEqual(split.rng.getstate(), uninterrupted.rng.getstate())
        self.assertEqual(split_child.age, 1)
        self.assertEqual(uninterrupted_child.age, 1)


if __name__ == "__main__":
    unittest.main()
