from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.adaptive import ActionValue
from playing_god.core.causal_history import HistoricalEventReference
from playing_god.core.counterfactual import snapshot_agents, snapshot_phase8
from playing_god.core.counterfactual_history import (
    COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION,
    compare_counterfactual_histories,
)
from playing_god.core.events import Event
from playing_god.core.history import resolve_source_event
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_phase8_exit import (
    complete_history,
    prepare_prefork_world,
    take_counterfactual_fork,
    trigger_discovery,
)


def controlled_fork():
    baseline_prefix = prepare_prefork_world()
    counterfactual_prefix = prepare_prefork_world()
    baseline = prepare_prefork_world()
    counterfactual = prepare_prefork_world()
    trigger_discovery(baseline)
    take_counterfactual_fork(counterfactual)
    complete_history(baseline)
    complete_history(counterfactual)
    return baseline_prefix, counterfactual_prefix, baseline, counterfactual


def observed_state(world: World) -> tuple:
    return (
        snapshot_agents(world),
        snapshot_phase8(world),
        world.rng.getstate(),
        tuple(world.interventions),
        tuple(world.intervention_responses),
    )


class CounterfactualHistoricalComparisonTests(unittest.TestCase):
    def test_phase8_fork_exposes_divergence_metrics_episodes_and_chain(self):
        worlds = controlled_fork()
        states_before = tuple(observed_state(world) for world in worlds)

        comparison = compare_counterfactual_histories(
            *worlds,
            fork_day=3,
        )

        self.assertEqual(
            comparison.analysis_version,
            COUNTERFACTUAL_HISTORY_ANALYSIS_VERSION,
        )
        self.assertTrue(comparison.valid_controlled_pair)
        self.assertTrue(comparison.pre_fork.trajectory.equivalent)
        self.assertTrue(
            comparison.pre_fork.trajectory.source_signatures_equal
        )
        self.assertTrue(comparison.diverged)
        first = comparison.first_observed_divergence
        self.assertEqual(first.day, 4)
        self.assertEqual(first.basis, "authoritative_event")
        self.assertEqual(
            first.event_differences[0].difference.baseline.kind,
            "institution",
        )
        self.assertEqual(
            first.event_differences[0].difference.intervention.kind,
            "travel",
        )
        self.assertGreater(
            comparison.post_fork_trajectory.aggregate_distance,
            0.0,
        )
        self.assertIn(
            "subjects.2.skill",
            first.trajectory_component_paths,
        )
        self.assertEqual(
            dict(comparison.phase8_metrics.skill_deltas)["npc_003"],
            0.006,
        )
        self.assertEqual(
            comparison.phase8_metrics.discovery.attempt_count,
            1,
        )
        self.assertEqual(
            comparison.phase8_metrics.counterfactual.attempt_count,
            0,
        )
        self.assertTrue(any(
            "peer_training" in episode.event_kinds
            for episode in comparison.baseline_episodes
        ))
        self.assertFalse(any(
            "discovery_attempted" in episode.event_kinds
            for episode in comparison.counterfactual_episodes
        ))

        explicit_baseline = [
            item
            for item in comparison.causal_evidence
            if item.branch == "baseline"
            and item.explicit_path_available
        ]
        traced_events = {
            resolve_source_event(worlds[2], node.reference).kind
            for item in explicit_baseline
            for node in item.trace.nodes
        }
        self.assertIn("problem_pressure_recognized", traced_events)
        self.assertIn("discovery_validated", traced_events)
        self.assertIn("knowledge_exposed", traced_events)
        self.assertIn("peer_training", traced_events)
        self.assertTrue(all(
            "causal path unavailable" in note
            for note in comparison.causal_path_notes
        ))
        self.assertEqual(
            tuple(observed_state(world) for world in worlds),
            states_before,
        )

    def test_repeated_fresh_and_save_reload_comparisons_are_exact(self):
        worlds = controlled_fork()
        expected = compare_counterfactual_histories(*worlds, fork_day=3)
        repeated = compare_counterfactual_histories(
            *controlled_fork(),
            fork_day=3,
        )

        with TemporaryDirectory() as directory:
            loaded = []
            for index, world in enumerate(worlds):
                path = Path(directory) / f"branch-{index}.db"
                save_world(world, path)
                loaded.append(load_world(path))

        reloaded = compare_counterfactual_histories(
            *loaded,
            fork_day=3,
        )

        self.assertEqual(repeated, expected)
        self.assertEqual(reloaded, expected)

    def test_invalid_pre_fork_history_is_qualified(self):
        worlds = list(controlled_fork())
        prefix = worlds[1]
        prefix.agents[0].events[-1] = replace(
            prefix.agents[0].events[-1],
            description="Different pre-fork history",
        )

        comparison = compare_counterfactual_histories(
            *worlds,
            fork_day=3,
        )

        self.assertFalse(comparison.valid_controlled_pair)
        self.assertIn(
            "pre_fork_agent_snapshot_mismatch",
            comparison.pre_fork.qualification_reasons,
        )
        self.assertIn(
            "pre_fork_trajectory_mismatch",
            comparison.pre_fork.qualification_reasons,
        )
        self.assertIn(
            "pre_fork_agent_snapshot_mismatch",
            comparison.qualification_warnings,
        )

    def test_identical_and_empty_post_fork_histories_do_not_diverge(self):
        empty_worlds = tuple(prepare_prefork_world() for _ in range(4))
        empty = compare_counterfactual_histories(
            *empty_worlds,
            fork_day=3,
        )

        self.assertTrue(empty.valid_controlled_pair)
        self.assertFalse(empty.diverged)
        self.assertIsNone(empty.post_fork_trajectory)
        self.assertIsNone(empty.first_observed_divergence)

        baseline_prefix = prepare_prefork_world()
        counterfactual_prefix = prepare_prefork_world()
        baseline = prepare_prefork_world()
        counterfactual = prepare_prefork_world()
        for world in (baseline, counterfactual):
            trigger_discovery(world)
            complete_history(world)
        identical = compare_counterfactual_histories(
            baseline_prefix,
            counterfactual_prefix,
            baseline,
            counterfactual,
            fork_day=3,
        )

        self.assertTrue(identical.valid_controlled_pair)
        self.assertFalse(identical.diverged)
        self.assertTrue(identical.post_fork_trajectory.equivalent)
        self.assertEqual(
            identical.post_fork_trajectory.aggregate_distance,
            0.0,
        )

    def test_unlinked_divergence_reports_causal_path_unavailable(self):
        prefix = World(seed=44, population=1)
        other_prefix = World(seed=44, population=1)
        baseline = World(seed=44, population=1)
        counterfactual = World(seed=44, population=1)
        baseline.day = 1
        counterfactual.day = 1
        baseline.agents[0].events.append(Event(
            day=1,
            kind="unlinked_change",
            description="Observed without explicit causal ancestry",
            significance=0.40,
        ))

        comparison = compare_counterfactual_histories(
            prefix,
            other_prefix,
            baseline,
            counterfactual,
            fork_day=0,
        )

        self.assertTrue(comparison.valid_controlled_pair)
        self.assertTrue(comparison.diverged)
        self.assertEqual(
            comparison.first_observed_divergence.day,
            1,
        )
        self.assertTrue(comparison.causal_path_notes)
        self.assertFalse(any(
            item.explicit_path_available
            for item in comparison.causal_evidence
        ))

    def test_missing_component_remains_qualified_and_not_zero(self):
        prefix = World(seed=45, population=1)
        other_prefix = World(seed=45, population=1)
        baseline = World(seed=45, population=1)
        counterfactual = World(seed=45, population=1)
        baseline.day = 1
        counterfactual.day = 1
        baseline.agents[0].adaptive_values = {
            "improve_skill": {
                "train": ActionValue(
                    observations=1,
                    mean_feedback=0.0,
                ),
            },
        }

        comparison = compare_counterfactual_histories(
            prefix,
            other_prefix,
            baseline,
            counterfactual,
            fork_day=0,
        )

        result = next(
            item
            for item in comparison.post_fork_trajectory.component_results
            if item.path == "subjects.0.adaptive.train_mean_feedback"
        )
        self.assertTrue(result.baseline.available)
        self.assertEqual(result.baseline.value, 0.0)
        self.assertFalse(result.comparison.available)
        self.assertIsNone(result.normalized_distance)
        self.assertIn(
            "subjects.0.adaptive.train_mean_feedback: "
            "source completeness differs",
            comparison.qualification_warnings,
        )
        self.assertEqual(
            comparison.first_observed_divergence.basis,
            "trajectory_endpoint",
        )
        self.assertEqual(
            comparison.causal_path_notes,
            (
                "observed divergence, causal path unavailable: "
                "no differing source event",
            ),
        )

    def test_mismatched_agents_windows_and_fork_days_are_rejected(self):
        changed_configuration = list(controlled_fork())
        changed_configuration[2].economy = replace(
            changed_configuration[2].economy,
            job_capacity=(
                changed_configuration[2].economy.job_capacity + 1
            ),
        )
        qualified = compare_counterfactual_histories(
            *changed_configuration,
            fork_day=3,
        )
        self.assertFalse(qualified.valid_controlled_pair)
        self.assertFalse(qualified.baseline_continuity_valid)
        self.assertIn(
            "baseline_configuration_changed_after_prefix",
            qualified.qualification_warnings,
        )

        worlds = list(controlled_fork())
        worlds[3].day = 6
        with self.assertRaisesRegex(ValueError, "same analysis end day"):
            compare_counterfactual_histories(*worlds, fork_day=3)

        with self.assertRaisesRegex(ValueError, "matching agent identities"):
            compare_counterfactual_histories(
                World(seed=1, population=1),
                World(seed=1, population=2),
                World(seed=1, population=1),
                World(seed=1, population=1),
                fork_day=0,
            )

        valid = tuple(World(seed=1, population=1) for _ in range(4))
        for fork_day in (-1, True):
            with self.subTest(fork_day=fork_day):
                with self.assertRaises(ValueError):
                    compare_counterfactual_histories(
                        *valid,
                        fork_day=fork_day,
                    )

        with self.assertRaisesRegex(ValueError, "cannot end before"):
            compare_counterfactual_histories(
                *valid,
                fork_day=1,
            )


if __name__ == "__main__":
    unittest.main()
