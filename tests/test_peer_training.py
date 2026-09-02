from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, replace
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.adaptive import (
    capture_state,
    consequence_between,
    learn,
)
from playing_god.core.civilization import (
    PEER_TRAIN_ACTION_ID,
    PEER_TRAIN_AFFORDANCE,
    PEER_TRAIN_EFFECTS,
    activate_peer_training_affordance,
)
from playing_god.core.decision import choose, scores
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_knowledge_diffusion import add_discoverer_knowledge


class PeakChoiceRandom:
    def __init__(self) -> None:
        self.population: list[str] = []

    def choices(
        self,
        population: list[str],
        *,
        weights: list[float],
        k: int,
    ) -> list[str]:
        self.population = population
        winner = max(
            range(len(population)),
            key=weights.__getitem__,
        )
        return [population[winner]]


def actionable_world(*, adaptive: bool = False) -> World:
    world = World(
        seed=1947,
        population=2,
        adaptive_cognition=adaptive,
    )
    add_discoverer_knowledge(world)
    world.civilization = activate_peer_training_affordance(
        world.civilization
    )
    teacher, learner = world.agents
    teacher.skill = 0.65
    learner.skill = 0.20
    teacher.energy = 0.80
    learner.energy = 0.80
    teacher.current_location = "market"
    learner.current_location = "market"
    for source, target in ((teacher, learner), (learner, teacher)):
        world.social.add_relationship(
            source.id,
            target.id,
            affinity=0.40,
            trust=0.70,
            familiarity=0.80,
        )
    world.day = 3
    return world


class PeerTrainingTests(unittest.TestCase):
    def test_adopted_affordance_is_selectable_and_executes_bounded_effects(self):
        world = actionable_world(adaptive=True)
        teacher, learner = world.agents
        eligibility = world.peer_training_eligibility(
            teacher.id,
            learner.id,
        )
        chooser = PeakChoiceRandom()

        action = choose(
            teacher,
            chooser,
            peer_training_utility=world.peer_training_utility(teacher),
            learned_preferences={PEER_TRAIN_ACTION_ID: 100.0},
        )
        before = (
            teacher.energy,
            learner.energy,
            learner.skill,
            teacher.money,
            learner.money,
            teacher.current_location,
        )
        world.move_for_action(teacher, action)
        world.act(teacher, action)

        self.assertTrue(eligibility.eligible)
        self.assertEqual(action, PEER_TRAIN_ACTION_ID)
        self.assertIn(PEER_TRAIN_ACTION_ID, chooser.population)
        self.assertEqual(teacher.energy, before[0] - 0.06)
        self.assertEqual(learner.energy, before[1] - 0.04)
        self.assertEqual(
            learner.skill,
            before[2] + PEER_TRAIN_EFFECTS[0].amount,
        )
        self.assertLess(PEER_TRAIN_EFFECTS[0].amount, 0.009)
        self.assertEqual((teacher.money, learner.money), before[3:5])
        self.assertEqual(teacher.current_location, before[5])
        self.assertEqual(world.school.admissions_used, 0)
        self.assertEqual(teacher.events[-1].kind, "peer_training")
        self.assertEqual(teacher.events[-1].target_id, learner.id)
        self.assertIn(
            eligibility.knowledge_id,
            teacher.events[-1].description,
        )
        self.assertIn(
            f"{eligibility.knowledge_parent_agent_id}:"
            f"{eligibility.knowledge_parent_event_index}",
            teacher.events[-1].description,
        )
        learned = learner.adaptive_values["improve_skill"]["train"]
        self.assertEqual(learned.observations, 1)
        self.assertGreater(learned.mean_feedback, 0.0)

    def test_direct_execution_revalidates_each_required_precondition(self):
        baseline = World(seed=1947, population=2)
        teacher, learner = baseline.agents
        baseline_state = asdict(teacher), asdict(learner)

        baseline.act(teacher, PEER_TRAIN_ACTION_ID)

        self.assertEqual((asdict(teacher), asdict(learner)), baseline_state)
        self.assertNotIn(PEER_TRAIN_ACTION_ID, scores(teacher))

        cases = (
            ("knowledge", lambda world: setattr(
                world.agents[0],
                "knowledge",
                type(world.agents[0].knowledge)(),
            )),
            ("teacher_skill", lambda world: setattr(
                world.agents[0], "skill", 0.20
            )),
            ("relationship", lambda world: [
                world.social.add_relationship(
                    source.id,
                    target.id,
                    affinity=0.0,
                    trust=0.0,
                    familiarity=0.10,
                )
                for source, target in (
                    (world.agents[0], world.agents[1]),
                    (world.agents[1], world.agents[0]),
                )
            ]),
            ("co_location", lambda world: setattr(
                world.agents[1], "current_location", "home"
            )),
            ("teacher_energy", lambda world: setattr(
                world.agents[0], "energy", 0.05
            )),
            ("learner_energy", lambda world: setattr(
                world.agents[1], "energy", 0.03
            )),
        )
        for blocker, mutate in cases:
            with self.subTest(blocker=blocker):
                world = actionable_world()
                teacher, learner = world.agents
                mutate(world)
                eligibility = world.peer_training_eligibility(
                    teacher.id,
                    learner.id,
                )
                before = asdict(teacher), asdict(learner)

                world.act(teacher, PEER_TRAIN_ACTION_ID)

                self.assertIn(blocker, eligibility.blockers)
                self.assertEqual(
                    (asdict(teacher), asdict(learner)),
                    before,
                )

    def test_missing_registry_affordance_removes_counterfactual_action(self):
        available = actionable_world()
        unavailable = actionable_world()
        unavailable.civilization = replace(
            unavailable.civilization,
            knowledge=(),
            affordances=(),
        )
        available_teacher = available.agents[0]
        unavailable_teacher = unavailable.agents[0]

        self.assertIsNotNone(
            available.peer_training_utility(available_teacher)
        )
        self.assertIsNone(
            unavailable.peer_training_utility(unavailable_teacher)
        )
        self.assertEqual(
            available_teacher.knowledge,
            unavailable_teacher.knowledge,
        )
        self.assertIn(
            "registry",
            unavailable.peer_training_eligibility(
                unavailable_teacher.id,
                unavailable.agents[1].id,
            ).blockers,
        )

    def test_same_seed_repeats_selection_outcome_and_event_order(self):
        worlds = [actionable_world() for _ in range(2)]
        actions = []
        for world in worlds:
            teacher = world.agents[0]
            action = choose(
                teacher,
                world.rng,
                peer_training_utility=world.peer_training_utility(
                    teacher
                ),
                learned_preferences={PEER_TRAIN_ACTION_ID: 100.0},
            )
            actions.append(action)
            world.act(teacher, action)

        self.assertEqual(
            actions,
            [PEER_TRAIN_ACTION_ID, PEER_TRAIN_ACTION_ID],
        )
        self.assertEqual(
            [asdict(agent) for agent in worlds[0].agents],
            [asdict(agent) for agent in worlds[1].agents],
        )
        self.assertEqual(
            worlds[0].rng.getstate(),
            worlds[1].rng.getstate(),
        )

    def test_restart_and_schema20_migration_preserve_availability(self):
        world = actionable_world(adaptive=True)
        teacher = world.agents[0]
        before = capture_state(teacher)
        world.act(teacher, PEER_TRAIN_ACTION_ID)
        learn(
            teacher,
            "improve_skill",
            PEER_TRAIN_ACTION_ID,
            consequence_between(before, capture_state(teacher)),
        )
        expected_values = teacher.adaptive_values
        expected_rng = world.rng.getstate()

        with TemporaryDirectory() as directory:
            path = Path(directory) / "world.db"
            save_world(world, path)
            with closing(sqlite3.connect(path)) as conn, conn:
                data = json.loads(conn.execute(
                    "SELECT civilization_json FROM world_state WHERE id = 1"
                ).fetchone()[0])
                data["affordances"] = []
                conn.execute(
                    "UPDATE world_state SET schema_version = 20, "
                    "civilization_json = ? WHERE id = 1",
                    (json.dumps(data, sort_keys=True),),
                )
            loaded = load_world(path)

            self.assertEqual(
                loaded.civilization.affordances,
                (PEER_TRAIN_AFFORDANCE,),
            )
            self.assertTrue(loaded.peer_training_eligibility(
                loaded.agents[0].id,
                loaded.agents[1].id,
            ).eligible)
            self.assertEqual(
                loaded.agents[0].adaptive_values,
                expected_values,
            )
            self.assertEqual(loaded.rng.getstate(), expected_rng)
            save_world(loaded, path)
            reloaded = load_world(path)
            with closing(sqlite3.connect(path)) as conn:
                version = conn.execute(
                    "SELECT schema_version FROM world_state WHERE id = 1"
                ).fetchone()[0]

        self.assertEqual(version, 22)
        self.assertEqual(
            reloaded.civilization.affordances,
            (PEER_TRAIN_AFFORDANCE,),
        )


if __name__ == "__main__":
    unittest.main()
