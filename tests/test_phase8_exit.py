from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.civilization import (
    PEER_TRAIN_ACTION_ID,
    validate_civilization_links,
    validate_discovery_links,
)
from playing_god.core.civilization_metrics import (
    build_phase8_metrics,
    compare_phase8_metrics,
)
from playing_god.core.counterfactual import (
    snapshot_agents,
    snapshot_phase8,
)
from playing_god.core.institution import validate_school_links
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_discovery import eligible_world
from tests.test_institutional_adoption import school_evidence_world


def prepare_prefork_world() -> World:
    world = World(seed=1, population=3)
    discoverer, adopter, learner = world.agents
    for agent in world.agents:
        agent.age = 30
        agent.family = replace(agent.family, dependent=False)
        agent.energy = 0.90

    discoverer.skill = 0.80
    discoverer.money = 200.0
    discoverer.stress = 0.10
    discoverer.traits["discipline"] = 1.0
    discoverer.traits["risk_tolerance"] = 1.0
    discoverer.traits["sociability"] = 1.0
    discoverer.social_energy = 1.0
    adopter.skill = 0.60
    adopter.traits["empathy"] = 1.0
    adopter.traits["sociability"] = 1.0
    adopter.social_energy = 1.0
    adopter.current_location = "cafe"
    learner.skill = 0.10
    learner.social_energy = 1.0
    learner.current_location = "home"

    for source, target, familiarity in (
        (discoverer, adopter, 0.70),
        (adopter, discoverer, 0.70),
        (adopter, learner, 0.90),
        (learner, adopter, 0.90),
    ):
        source.relationships[target.id] = 0.40
        world.social.add_relationship(
            source.id,
            target.id,
            affinity=0.40,
            trust=0.90,
            familiarity=familiarity,
        )

    world.day = 1
    discoverer.current_location = world.school.location
    world.act(discoverer, "train")
    world.day = 2
    world.move_for_action(discoverer, "rest")
    world.act(discoverer, "train")
    world.day = 3
    world.act(discoverer, "train")
    return world


def trigger_discovery(world: World) -> None:
    discoverer = world.agents[0]
    world.day = 4
    world.act(discoverer, "train")
    world.day = 5
    attempt = world.attempt_discovery(discoverer.id)
    if attempt is None or attempt.outcome != "validated":
        raise AssertionError("Controlled discovery did not validate.")


def take_counterfactual_fork(world: World) -> None:
    discoverer = world.agents[0]
    world.day = 4
    world.move_for_action(discoverer, "train")
    world.act(discoverer, "train")
    world.day = 5
    if world.attempt_discovery(discoverer.id) is not None:
        raise AssertionError("Counterfactual unexpectedly attempted discovery.")


def complete_history(world: World) -> None:
    discoverer, adopter, learner = world.agents
    world.day = 6
    world.move_for_action(discoverer, "socialize")
    world.resolve_daily_interactions()
    world.day = 7
    world.move_for_action(learner, "socialize")
    world.act(adopter, PEER_TRAIN_ACTION_ID)


def assert_valid_phase8(test: unittest.TestCase, world: World) -> None:
    validate_discovery_links(world.agents, current_day=world.day)
    validate_civilization_links(
        world.civilization,
        world.agents,
        current_day=world.day,
        school=world.school,
    )
    validate_school_links(
        world.school,
        world.civilization,
        world.agents,
        current_day=world.day,
    )
    test.assertEqual(world.day, 7)


class Phase8ExitTests(unittest.TestCase):
    def test_controlled_fork_proves_the_complete_causal_chain_and_metrics(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "prefork.db"
            prefix = prepare_prefork_world()
            save_world(prefix, path)
            discovery = load_world(path)
            counterfactual = load_world(path)

        before_snapshot = snapshot_phase8(discovery)
        before_agents = snapshot_agents(discovery)
        before_rng = discovery.rng.getstate()
        self.assertEqual(before_snapshot, snapshot_phase8(counterfactual))
        self.assertEqual(before_agents, snapshot_agents(counterfactual))
        self.assertEqual(before_rng, counterfactual.rng.getstate())

        trigger_discovery(discovery)
        take_counterfactual_fork(counterfactual)
        complete_history(discovery)
        complete_history(counterfactual)

        discoverer, adopter, learner = discovery.agents
        counterfactual_learner = counterfactual.agents[2]
        fork_event_index = len(before_agents[0].events)
        self.assertEqual(
            discovery.agents[0].events[fork_event_index].day,
            4,
        )
        self.assertEqual(
            counterfactual.agents[0].events[fork_event_index].day,
            4,
        )
        self.assertEqual(
            discoverer.discovery.pressures[0].recognized_day,
            4,
        )
        self.assertEqual(discoverer.discovery.attempts[0].outcome, "validated")
        self.assertEqual(adopter.knowledge.records[0].route, "social")
        self.assertEqual(adopter.knowledge.records[0].response, "accept")
        self.assertAlmostEqual(
            learner.skill - counterfactual_learner.skill,
            0.006,
        )
        self.assertEqual(counterfactual.civilization.knowledge, ())
        self.assertEqual(counterfactual.civilization.affordances, ())
        self.assertIsNone(
            counterfactual.peer_training_utility(
                counterfactual.agents[1]
            )
        )

        metrics_before = build_phase8_metrics(discovery)
        state_before = snapshot_phase8(discovery)
        agents_before = snapshot_agents(discovery)
        rng_before = discovery.rng.getstate()
        comparison = compare_phase8_metrics(discovery, counterfactual)

        self.assertEqual(metrics_before.problem_recognition_day, 4)
        self.assertEqual(metrics_before.attempt_count, 1)
        self.assertEqual(metrics_before.successful_attempt_count, 1)
        self.assertEqual(metrics_before.rejected_attempt_count, 0)
        self.assertEqual(metrics_before.validation_day, 5)
        self.assertEqual(metrics_before.recognition_to_validation_days, 1)
        self.assertEqual(metrics_before.exposed_agent_count, 1)
        self.assertEqual(metrics_before.adopting_agent_count, 2)
        self.assertEqual(metrics_before.affordance_first_use_day, 7)
        self.assertIsNone(metrics_before.institution_adoption_day)
        self.assertEqual(
            dict(comparison.skill_deltas)[learner.id],
            0.006,
        )
        self.assertEqual(comparison.opportunity_count_delta, 2)
        rejected = eligible_world(5)
        rejected.attempt_discovery(rejected.agents[0].id)
        self.assertEqual(
            build_phase8_metrics(rejected).rejected_attempt_count,
            1,
        )
        self.assertEqual(
            build_phase8_metrics(
                school_evidence_world(evidence_days=3)
            ).institution_adoption_day,
            5,
        )
        self.assertEqual(snapshot_phase8(discovery), state_before)
        self.assertEqual(snapshot_agents(discovery), agents_before)
        self.assertEqual(discovery.rng.getstate(), rng_before)
        self.assertNotEqual(
            snapshot_phase8(discovery),
            snapshot_phase8(counterfactual),
        )
        assert_valid_phase8(self, discovery)
        assert_valid_phase8(self, counterfactual)

    def test_same_seed_and_save_reload_continuation_are_exact(self):
        uninterrupted = prepare_prefork_world()
        repeated = prepare_prefork_world()
        trigger_discovery(uninterrupted)
        trigger_discovery(repeated)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "split.db"
            save_world(repeated, path)
            resumed = load_world(path)
            complete_history(resumed)

        complete_history(uninterrupted)
        fresh_repeat = prepare_prefork_world()
        trigger_discovery(fresh_repeat)
        complete_history(fresh_repeat)

        self.assertEqual(
            snapshot_phase8(resumed),
            snapshot_phase8(uninterrupted),
        )
        self.assertEqual(
            snapshot_agents(resumed),
            snapshot_agents(uninterrupted),
        )
        self.assertEqual(
            resumed.rng.getstate(),
            uninterrupted.rng.getstate(),
        )
        self.assertEqual(
            build_phase8_metrics(resumed),
            build_phase8_metrics(uninterrupted),
        )
        self.assertEqual(
            snapshot_phase8(fresh_repeat),
            snapshot_phase8(uninterrupted),
        )
        self.assertEqual(
            snapshot_agents(fresh_repeat),
            snapshot_agents(uninterrupted),
        )
        self.assertEqual(
            fresh_repeat.rng.getstate(),
            uninterrupted.rng.getstate(),
        )
        assert_valid_phase8(self, resumed)
        assert_valid_phase8(self, uninterrupted)


if __name__ == "__main__":
    unittest.main()
