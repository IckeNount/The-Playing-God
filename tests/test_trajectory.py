from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.counterfactual import snapshot_agents, snapshot_phase8
from playing_god.core.development import ADULT_AGE
from playing_god.core.trajectory import (
    build_trajectory_signature,
    compare_trajectories,
    compare_trajectory_signatures,
)
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_development import prepare_family, progress_to, set_upbringing
from tests.test_phase8_exit import (
    complete_history,
    prepare_prefork_world,
    take_counterfactual_fork,
    trigger_discovery,
)


def developmental_world(*, supported: bool) -> tuple[World, object]:
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
    progress_to(world, ADULT_AGE)
    return world, child


def result_by_path(comparison):
    return {
        item.path: item
        for item in comparison.component_results
    }


class HistoricalTrajectoryComparisonTests(unittest.TestCase):
    def test_identical_trajectories_are_equivalent_and_read_only(self):
        baseline = prepare_prefork_world()
        comparison_world = prepare_prefork_world()
        baseline_state = (
            snapshot_phase8(baseline),
            snapshot_agents(baseline),
            baseline.rng.getstate(),
        )
        comparison_state = (
            snapshot_phase8(comparison_world),
            snapshot_agents(comparison_world),
            comparison_world.rng.getstate(),
        )

        comparison = compare_trajectories(baseline, comparison_world)

        self.assertTrue(comparison.equivalent)
        self.assertEqual(comparison.aggregate_distance, 0.0)
        self.assertTrue(comparison.source_signatures_equal)
        self.assertEqual(comparison.component_differences, ())
        self.assertEqual(
            baseline_state,
            (
                snapshot_phase8(baseline),
                snapshot_agents(baseline),
                baseline.rng.getstate(),
            ),
        )
        self.assertEqual(
            comparison_state,
            (
                snapshot_phase8(comparison_world),
                snapshot_agents(comparison_world),
                comparison_world.rng.getstate(),
            ),
        )

    def test_same_prior_development_exposes_opportunity_and_skill_divergence(self):
        supported, supported_child = developmental_world(supported=True)
        constrained, constrained_child = developmental_world(supported=False)
        before_supported = asdict(supported_child)
        before_constrained = asdict(constrained_child)
        supported_rng = supported.rng.getstate()
        constrained_rng = constrained.rng.getstate()

        comparison = compare_trajectories(
            supported,
            constrained,
            baseline_agent_ids=(supported_child.id,),
            comparison_agent_ids=(constrained_child.id,),
        )
        components = result_by_path(comparison)

        self.assertEqual(supported_child.traits, constrained_child.traits)
        self.assertEqual(supported_child.sins, constrained_child.sins)
        self.assertFalse(comparison.equivalent)
        self.assertGreater(comparison.aggregate_distance, 0.0)
        self.assertGreater(
            components["subjects.0.skill"].normalized_distance,
            0.0,
        )
        school_access = components[
            "subjects.0.development.school_access_rate"
        ]
        self.assertTrue(school_access.baseline.available)
        self.assertTrue(school_access.comparison.available)
        self.assertGreater(school_access.baseline.value, 0.0)
        self.assertEqual(school_access.comparison.value, 0.0)
        learned = components[
            "subjects.0.adaptive.train_mean_feedback"
        ]
        self.assertTrue(learned.baseline.available)
        self.assertFalse(learned.comparison.available)
        self.assertIn(
            "source completeness differs",
            comparison.qualification_warnings[0],
        )
        self.assertEqual(asdict(supported_child), before_supported)
        self.assertEqual(asdict(constrained_child), before_constrained)
        self.assertEqual(supported.rng.getstate(), supported_rng)
        self.assertEqual(constrained.rng.getstate(), constrained_rng)

    def test_phase8_fork_is_equivalent_before_and_divergent_after(self):
        discovery = prepare_prefork_world()
        counterfactual = prepare_prefork_world()

        before = compare_trajectories(discovery, counterfactual)
        self.assertTrue(before.equivalent)
        self.assertEqual(before.aggregate_distance, 0.0)

        trigger_discovery(discovery)
        take_counterfactual_fork(counterfactual)
        complete_history(discovery)
        complete_history(counterfactual)
        after = compare_trajectories(
            discovery,
            counterfactual,
            baseline_start_day=4,
            comparison_start_day=4,
        )
        differences = {
            item.path
            for item in after.component_differences
        }

        self.assertFalse(after.equivalent)
        self.assertGreater(after.aggregate_distance, 0.0)
        self.assertFalse(after.source_signatures_equal)
        self.assertIn("world.civilization", differences)
        self.assertIn("subjects.0.discovery", differences)
        self.assertIn("subjects.2.skill", differences)
        self.assertIn("subjects.2.events.kind_frequencies", differences)
        self.assertEqual(after.baseline_window.start_day, 4)
        self.assertEqual(after.baseline_window.end_day, 7)

    def test_normalization_bounds_money_and_preserves_missing_from_zero(self):
        baseline = World(seed=9, population=1)
        comparison_world = World(seed=9, population=1)
        baseline.agents[0].money = 0.0
        comparison_world.agents[0].money = 1_000_000.0
        baseline.agents[0].skill = 0.0
        comparison_world.agents[0].skill = 1.0

        comparison = compare_trajectories(baseline, comparison_world)
        components = result_by_path(comparison)

        self.assertEqual(
            components["subjects.0.money"].normalized_distance,
            1.0,
        )
        self.assertEqual(
            components["subjects.0.skill"].normalized_distance,
            1.0,
        )
        missing = components[
            "subjects.0.development.school_access_rate"
        ]
        self.assertFalse(missing.baseline.available)
        self.assertIsNone(missing.normalized_distance)
        self.assertLessEqual(comparison.aggregate_distance, 1.0)

    def test_windows_are_explicit_and_incompatible_durations_are_rejected(self):
        first = prepare_prefork_world()
        second = prepare_prefork_world()
        first_signature = build_trajectory_signature(first, start_day=0)
        second_signature = build_trajectory_signature(second, start_day=1)

        with self.assertRaisesRegex(ValueError, "equal day counts"):
            compare_trajectory_signatures(first_signature, second_signature)
        with self.assertRaisesRegex(ValueError, "endpoint"):
            build_trajectory_signature(first, end_day=2)

    def test_same_seed_and_save_reload_signatures_are_exact(self):
        uninterrupted = prepare_prefork_world()
        fresh = prepare_prefork_world()
        trigger_discovery(uninterrupted)
        trigger_discovery(fresh)
        complete_history(uninterrupted)
        complete_history(fresh)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "trajectory.db"
            save_world(uninterrupted, path)
            reloaded = load_world(path)

        expected = build_trajectory_signature(uninterrupted)

        self.assertEqual(build_trajectory_signature(fresh), expected)
        self.assertEqual(build_trajectory_signature(reloaded), expected)
        self.assertTrue(compare_trajectories(uninterrupted, reloaded).equivalent)
        self.assertEqual(reloaded.rng.getstate(), uninterrupted.rng.getstate())


if __name__ == "__main__":
    unittest.main()
