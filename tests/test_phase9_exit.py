from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import unittest

from playing_god.core.causal_history import HistoricalEventReference
from playing_god.core.counterfactual import snapshot_agents, snapshot_phase8
from playing_god.core.history import resolve_source_event
from playing_god.core.research import (
    build_counterfactual_research_packet,
    query_causal_history,
    query_historical_episodes,
    query_trajectory_comparison,
)
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_phase8_exit import (
    complete_history,
    prepare_prefork_world,
    take_counterfactual_fork,
    trigger_discovery,
)
from tests.test_trajectory import developmental_world


def controlled_fork() -> tuple:
    baseline_prefix = prepare_prefork_world()
    counterfactual_prefix = prepare_prefork_world()
    baseline = prepare_prefork_world()
    counterfactual = prepare_prefork_world()
    trigger_discovery(baseline)
    take_counterfactual_fork(counterfactual)
    complete_history(baseline)
    complete_history(counterfactual)
    return baseline_prefix, counterfactual_prefix, baseline, counterfactual


def authoritative_state(world) -> tuple:
    return (
        snapshot_agents(world),
        snapshot_phase8(world),
        world.economic_snapshot(),
        world.school_snapshot(),
        tuple(world.interventions),
        tuple(world.intervention_responses),
        tuple(world.information_items),
        world.rng.getstate(),
    )


class Phase9ExitTests(unittest.TestCase):
    def test_integrated_counterfactual_research_workflow_is_exact(self):
        worlds = controlled_fork()
        baseline = worlds[2]
        counterfactual = worlds[3]
        states_before = tuple(authoritative_state(world) for world in worlds)
        started = perf_counter()

        episodes = query_historical_episodes(
            baseline,
            subject_agent_id=baseline.agents[0].id,
            start_day=4,
            end_day=7,
            max_episodes=6,
        )
        pressure = baseline.agents[0].discovery.pressures[0]
        recognition = HistoricalEventReference(
            baseline.agents[0].id,
            pressure.recognition_event_index,
        )
        causal = query_causal_history(
            baseline,
            recognition,
            direction="descendants",
            max_depth=8,
            max_nodes=64,
        )
        trajectory = query_trajectory_comparison(
            baseline,
            counterfactual,
            baseline_start_day=4,
            comparison_start_day=4,
        )
        packet = build_counterfactual_research_packet(
            *worlds,
            fork_day=3,
        )
        elapsed = perf_counter() - started

        self.assertTrue(packet.valid_controlled_pair)
        self.assertEqual(packet.first_observed_divergence.day, 4)
        self.assertEqual(
            packet.first_observed_divergence.basis,
            "authoritative_event",
        )
        self.assertEqual(
            packet.trajectory_aggregate_distance,
            0.11565277777777777,
        )
        self.assertEqual(
            trajectory.comparison.aggregate_distance,
            packet.trajectory_aggregate_distance,
        )
        self.assertEqual(
            dict(packet.phase8_metrics.skill_deltas)["npc_003"],
            0.006,
        )
        self.assertEqual(packet.phase8_metrics.discovery.attempt_count, 1)
        self.assertEqual(packet.phase8_metrics.counterfactual.attempt_count, 0)
        self.assertTrue(episodes.episodes)
        self.assertTrue(all(
            reference in packet.source_event_references
            for episode in packet.baseline_episodes
            for reference in episode.source_event_references
        ))
        causal_kinds = {
            resolve_source_event(baseline, node.reference).kind
            for node in causal.trace.nodes
        }
        self.assertIn("problem_pressure_recognized", causal_kinds)
        self.assertIn("discovery_validated", causal_kinds)
        self.assertIn("knowledge_exposed", causal_kinds)
        self.assertIn("peer_training", causal_kinds)
        self.assertLessEqual(len(episodes.episodes), 6)
        self.assertLessEqual(len(causal.trace.nodes), 64)
        self.assertLessEqual(len(packet.baseline_episodes), 6)
        self.assertLessEqual(len(packet.counterfactual_episodes), 6)
        self.assertLessEqual(len(packet.trajectory_components), 12)
        self.assertLessEqual(len(packet.causal_evidence), 8)
        self.assertLess(elapsed, 5.0)
        self.assertEqual(
            tuple(authoritative_state(world) for world in worlds),
            states_before,
        )

        fresh = build_counterfactual_research_packet(
            *controlled_fork(),
            fork_day=3,
        )
        with TemporaryDirectory() as directory:
            loaded = []
            for index, world in enumerate(worlds):
                path = Path(directory) / f"phase9-exit-{index}.db"
                save_world(world, path)
                loaded.append(load_world(path))
        reloaded = build_counterfactual_research_packet(
            *loaded,
            fork_day=3,
        )
        self.assertEqual(fresh, packet)
        self.assertEqual(reloaded, packet)
        self.assertEqual(reloaded.packet_id, packet.packet_id)

    def test_secondary_developmental_comparison_uses_same_surface(self):
        supported, supported_child = developmental_world(supported=True)
        constrained, constrained_child = developmental_world(supported=False)
        states_before = (
            authoritative_state(supported),
            authoritative_state(constrained),
        )

        result = query_trajectory_comparison(
            supported,
            constrained,
            baseline_agent_ids=(supported_child.id,),
            comparison_agent_ids=(constrained_child.id,),
        )
        components = {
            item.path: item
            for item in result.comparison.component_results
        }

        self.assertEqual(supported_child.traits, constrained_child.traits)
        self.assertEqual(supported_child.sins, constrained_child.sins)
        self.assertGreater(result.comparison.aggregate_distance, 0.0)
        self.assertGreater(
            components["subjects.0.skill"].normalized_distance,
            0.0,
        )
        self.assertGreater(
            components[
                "subjects.0.development.school_access_rate"
            ].normalized_distance,
            0.0,
        )
        self.assertTrue(
            components[
                "subjects.0.adaptive.train_mean_feedback"
            ].baseline.available
        )
        self.assertFalse(
            components[
                "subjects.0.adaptive.train_mean_feedback"
            ].comparison.available
        )
        self.assertEqual(
            (
                authoritative_state(supported),
                authoritative_state(constrained),
            ),
            states_before,
        )

    def test_research_observer_does_not_change_future_execution(self):
        observed = prepare_prefork_world()
        control = prepare_prefork_world()
        packet_before = build_counterfactual_research_packet(
            observed,
            observed,
            observed,
            observed,
            fork_day=3,
        )
        query_historical_episodes(observed, max_episodes=4)
        query_trajectory_comparison(observed, observed)
        first_reference = HistoricalEventReference(
            observed.agents[0].id,
            0,
        )
        query_causal_history(
            observed,
            first_reference,
            direction="descendants",
            max_depth=2,
            max_nodes=8,
        )

        self.assertTrue(packet_before.valid_controlled_pair)
        trigger_discovery(observed)
        trigger_discovery(control)
        complete_history(observed)
        complete_history(control)

        self.assertEqual(
            authoritative_state(observed),
            authoritative_state(control),
        )


if __name__ == "__main__":
    unittest.main()
