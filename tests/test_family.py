from __future__ import annotations

import unittest

from dataclasses import asdict, replace
from unittest.mock import patch

from playing_god.core.family import INHERITANCE_VARIATION
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


class FamilyFoundationTests(unittest.TestCase):

    def test_seeded_world_can_produce_later_generation_child(self):
        world = World(
            seed=65,
            population=2,
            reproduction_enabled=True,
        )
        first, second = prepare_eligible_pair(world)
        world.day = 1

        child = world.attempt_reproduction(first.id, second.id)

        self.assertIsNotNone(child)
        self.assertEqual(child.family.generation, 1)
        self.assertEqual(child.family.birth_day, 1)

    def test_eligibility_is_inspectable_and_ineligible_attempt_uses_no_rng(self):
        world = World(
            seed=1947,
            population=2,
            reproduction_enabled=True,
        )
        first, second = world.agents
        before = world.rng.getstate()

        eligibility = world.reproduction_eligibility(
            first.id,
            second.id,
        )
        child = world.attempt_reproduction(first.id, second.id)

        self.assertFalse(eligibility.eligible)
        self.assertTrue(eligibility.reasons)
        self.assertIsNone(child)
        self.assertEqual(world.rng.getstate(), before)

    def test_seeded_birth_creates_child_links_context_and_bounded_priors(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        first, second = prepare_eligible_pair(world)
        world.day = 12

        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            births = world.resolve_reproduction()

        self.assertEqual(len(births), 1)
        child = births[0]
        self.assertEqual(child.family.generation, 1)
        self.assertEqual(child.family.birth_day, 12)
        self.assertTrue(child.family.dependent)
        self.assertEqual(
            child.family.parent_ids,
            (first.id, second.id),
        )
        self.assertEqual(
            child.family.guardian_ids,
            (first.id, second.id),
        )
        self.assertIn(child.id, first.family.child_ids)
        self.assertIn(child.id, second.family.child_ids)

        context = child.family.birth_context
        self.assertIsNotNone(context)
        self.assertEqual(context.day, 12)
        self.assertEqual(context.location, "home")
        self.assertEqual(context.household_money, 800.0)
        self.assertEqual(context.employed_guardians, 1)
        self.assertEqual(context.guardian_stress, 0.20)
        self.assertEqual(context.mutual_affinity, 0.50)
        self.assertEqual(context.mutual_trust, 0.70)
        self.assertEqual(context.mutual_familiarity, 0.80)

        for key, value in child.traits.items():
            parent_mean = (
                first.traits[key] + second.traits[key]
            ) / 2
            self.assertLessEqual(
                abs(value - parent_mean),
                INHERITANCE_VARIATION,
            )
        for key, value in child.sins.items():
            parent_mean = (
                first.sins[key] + second.sins[key]
            ) / 2
            self.assertLessEqual(
                abs(value - parent_mean),
                INHERITANCE_VARIATION,
            )

        self.assertFalse(child.employed)
        self.assertEqual(child.skill, 0.0)
        self.assertEqual(child.adaptive_values, {})
        self.assertEqual(child.founder_prehistory, [])
        self.assertTrue(any(
            event.kind == "birth"
            for event in child.events
        ))

    def test_dependent_child_does_not_act_or_interact(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        prepare_eligible_pair(world)
        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            child = world.resolve_reproduction()[0]

        birth_events = list(child.events)
        birth_location = child.current_location
        world.move_for_action(child, "work")
        world.act(child, "rest")
        world.end_day(child)
        world.run(1)

        self.assertEqual(dict(child.actions), {})
        self.assertEqual(child.money, 0.0)
        self.assertEqual(child.events, birth_events)
        self.assertEqual(child.current_location, birth_location)
        self.assertTrue(all(
            child.id not in {
                exposure.agent_a,
                exposure.agent_b,
            }
            for exposure in world.last_exposures
        ))

    def test_close_family_is_never_eligible(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        first, second = prepare_eligible_pair(world)
        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            child = world.resolve_reproduction()[0]

        child.age = 25
        child.family = replace(child.family, dependent=False)
        child.money = 400.0
        child.employed = True
        child.stress = 0.20
        child.relationships[first.id] = 0.50
        first.relationships[child.id] = 0.50
        world.social.add_relationship(
            child.id,
            first.id,
            affinity=0.50,
            trust=0.70,
            familiarity=0.80,
        )
        world.social.add_relationship(
            first.id,
            child.id,
            affinity=0.50,
            trust=0.70,
            familiarity=0.80,
        )

        eligibility = world.reproduction_eligibility(
            first.id,
            child.id,
        )

        self.assertFalse(eligibility.eligible)
        self.assertIn("close_family", eligibility.reasons)

    def test_same_seed_birth_is_exact(self):
        first_world = World(
            seed=83,
            population=2,
            reproduction_enabled=True,
        )
        second_world = World(
            seed=83,
            population=2,
            reproduction_enabled=True,
        )
        prepare_eligible_pair(first_world)
        prepare_eligible_pair(second_world)

        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            first_world.resolve_reproduction()
            second_world.resolve_reproduction()

        self.assertEqual(
            [asdict(agent) for agent in first_world.agents],
            [asdict(agent) for agent in second_world.agents],
        )
        self.assertEqual(
            first_world.rng.getstate(),
            second_world.rng.getstate(),
        )


if __name__ == "__main__":
    unittest.main()
