from __future__ import annotations

import unittest

from playing_god.core.counterfactual import (
    ScheduledIntervention,
    compare_counterfactual,
    snapshot_agents,
)
from playing_god.core.world import World


class CounterfactualTests(unittest.TestCase):
    def schedule(self, **overrides) -> ScheduledIntervention:
        values = {
            "day": 0,
            "kind": "dream",
            "target_id": "npc_001",
            "theme": "an open office door",
            "suggested_action": "job_hunt",
            "strength": 1.0,
            "duration": 14,
        }
        values.update(overrides)
        return ScheduledIntervention(**values)

    def test_empty_schedule_produces_identical_branches(self):
        comparison = compare_counterfactual(
            seed=1947,
            days=30,
        )

        self.assertFalse(comparison.diverged)
        self.assertIsNone(comparison.first_divergence_day)
        self.assertEqual(comparison.agent_differences, ())
        self.assertEqual(
            snapshot_agents(comparison.baseline_world),
            snapshot_agents(comparison.intervention_world),
        )
        self.assertEqual(
            comparison.baseline_world.rng.getstate(),
            comparison.intervention_world.rng.getstate(),
        )

    def test_intervention_produces_traceable_trajectory_divergence(self):
        comparison = compare_counterfactual(
            seed=1947,
            days=60,
            schedule=(self.schedule(),),
        )

        self.assertTrue(comparison.diverged)
        self.assertEqual(comparison.first_divergence_day, 1)
        self.assertIn("npc_001", comparison.affected_agent_ids)
        target_difference = next(
            difference
            for difference in comparison.agent_differences
            if difference.agent_id == "npc_001"
        )
        self.assertIsNotNone(
            target_difference.first_event_difference
        )
        self.assertEqual(
            target_difference.first_event_difference.day,
            1,
        )
        self.assertIn("events", target_difference.changed_fields)
        self.assertEqual(len(comparison.created_interventions), 1)
        self.assertEqual(len(comparison.intervention_responses), 1)
        self.assertEqual(
            comparison.baseline_world.interventions,
            [],
        )

    def test_baseline_branch_matches_an_ordinary_same_seed_run(self):
        comparison = compare_counterfactual(
            seed=1947,
            days=60,
            schedule=(self.schedule(),),
        )
        standalone = World(seed=1947)
        standalone.run(60)

        self.assertEqual(
            snapshot_agents(comparison.baseline_world),
            snapshot_agents(standalone),
        )
        self.assertEqual(
            comparison.baseline_world.rng.getstate(),
            standalone.rng.getstate(),
        )

    def test_repeated_comparison_is_exactly_reproducible(self):
        schedule = (
            self.schedule(),
            self.schedule(
                day=20,
                kind="opportunity",
                target_id="npc_003",
                theme="a public training workshop",
                suggested_action="train",
                location="market",
                duration=10,
            ),
        )

        first = compare_counterfactual(
            seed=1947,
            days=90,
            schedule=schedule,
        )
        second = compare_counterfactual(
            seed=1947,
            days=90,
            schedule=schedule,
        )

        self.assertEqual(first, second)
        self.assertEqual(
            snapshot_agents(first.baseline_world),
            snapshot_agents(second.baseline_world),
        )
        self.assertEqual(
            snapshot_agents(first.intervention_world),
            snapshot_agents(second.intervention_world),
        )
        self.assertEqual(
            first.baseline_world.rng.getstate(),
            second.baseline_world.rng.getstate(),
        )
        self.assertEqual(
            first.intervention_world.rng.getstate(),
            second.intervention_world.rng.getstate(),
        )

    def test_schedule_input_is_normalized_by_day(self):
        later = self.schedule(day=10)
        earlier = self.schedule(
            day=2,
            target_id="npc_003",
            suggested_action="train",
        )

        comparison = compare_counterfactual(
            seed=1947,
            days=20,
            schedule=(later, earlier),
        )

        self.assertEqual(
            tuple(item.day for item in comparison.schedule),
            (2, 10),
        )
        self.assertEqual(
            tuple(
                intervention.created_day
                for intervention in comparison.created_interventions
            ),
            (2, 10),
        )

    def test_schedule_must_fit_inside_comparison_window(self):
        with self.assertRaises(ValueError):
            compare_counterfactual(
                seed=1947,
                days=10,
                schedule=(self.schedule(day=10),),
            )

    def test_invalid_target_is_rejected_by_world_rules(self):
        with self.assertRaises(ValueError):
            compare_counterfactual(
                seed=1947,
                days=10,
                schedule=(
                    self.schedule(target_id="missing"),
                ),
            )

    def test_snapshotting_does_not_mutate_worlds(self):
        comparison = compare_counterfactual(
            seed=1947,
            days=10,
            schedule=(self.schedule(),),
        )
        baseline_rng = comparison.baseline_world.rng.getstate()
        intervention_rng = (
            comparison.intervention_world.rng.getstate()
        )

        snapshot_agents(comparison.baseline_world)
        snapshot_agents(comparison.intervention_world)

        self.assertEqual(
            comparison.baseline_world.rng.getstate(),
            baseline_rng,
        )
        self.assertEqual(
            comparison.intervention_world.rng.getstate(),
            intervention_rng,
        )


if __name__ == "__main__":
    unittest.main()
