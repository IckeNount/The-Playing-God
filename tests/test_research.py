from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.causal_history import HistoricalEventReference
from playing_god.core.counterfactual import snapshot_agents, snapshot_phase8
from playing_god.core.events import Event
from playing_god.core.research import (
    MAX_EPISODES,
    MAX_TRAJECTORY_SUBJECTS,
    RESEARCH_PACKET_ANALYSIS_VERSION,
    RESEARCH_QUERY_ANALYSIS_VERSION,
    build_counterfactual_research_packet,
    query_causal_history,
    query_historical_episodes,
    query_trajectory_comparison,
)
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    SCHEMA_VERSION,
    load_world,
    save_world,
)
from tests.test_history import connected_history
from tests.test_phase8_exit import (
    complete_history,
    prepare_prefork_world,
    take_counterfactual_fork,
    trigger_discovery,
)


def controlled_fork() -> tuple[World, World, World, World]:
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
        world.economic_snapshot(),
        world.school_snapshot(),
        tuple(world.interventions),
        tuple(world.intervention_responses),
        world.rng.getstate(),
    )


class ResearchQueryTests(unittest.TestCase):
    def test_episode_query_is_repeatable_filtered_bounded_and_read_only(self):
        world = connected_history()
        state_before = observed_state(world)

        first = query_historical_episodes(world, max_episodes=1)
        repeated = query_historical_episodes(world, max_episodes=1)

        self.assertEqual(first, repeated)
        self.assertEqual(first.provenance.analysis_version, "research-query-v1")
        self.assertEqual(first.provenance.schema_version, SCHEMA_VERSION)
        self.assertEqual(first.total_matching_episodes, 2)
        self.assertEqual(len(first.episodes), 1)
        self.assertTrue(first.truncated)
        subject = query_historical_episodes(
            world,
            subject_agent_id=world.agents[3].id,
            start_day=2,
            end_day=2,
        )
        self.assertEqual(subject.total_matching_episodes, 1)
        self.assertEqual(
            subject.episodes[0].source_event_references,
            (HistoricalEventReference(world.agents[3].id, 0),),
        )
        self.assertEqual(observed_state(world), state_before)

    def test_causal_query_respects_bounds_and_rejects_missing_reference(self):
        world = controlled_fork()[2]
        recognition = world.agents[0].discovery.pressures[0]
        root = HistoricalEventReference(
            world.agents[0].id,
            recognition.recognition_event_index,
        )
        state_before = observed_state(world)

        result = query_causal_history(
            world,
            root,
            direction="descendants",
            max_depth=1,
            max_nodes=2,
        )

        self.assertEqual(result.trace.configured_max_depth, 1)
        self.assertEqual(result.trace.configured_max_nodes, 2)
        self.assertLessEqual(len(result.trace.nodes), 2)
        self.assertTrue(result.trace.truncated)
        self.assertEqual(observed_state(world), state_before)
        with self.assertRaisesRegex(ValueError, "Unknown historical event"):
            query_causal_history(
                world,
                HistoricalEventReference("missing", 0),
                direction="ancestors",
            )

    def test_missing_and_legacy_evidence_is_qualified_not_fabricated(self):
        baseline = World(seed=14, population=1)
        comparison = World(seed=14, population=1)

        result = query_trajectory_comparison(baseline, comparison)
        school_access = next(
            item
            for item in result.comparison.component_results
            if item.path == "subjects.0.development.school_access_rate"
        )

        self.assertFalse(school_access.baseline.available)
        self.assertFalse(school_access.comparison.available)
        self.assertEqual(
            school_access.baseline.reason,
            "no developmental checkpoint observed in this window",
        )
        self.assertIsNone(school_access.normalized_distance)

        legacy = World(seed=16, population=1)
        legacy.agents[0].events.clear()
        legacy.agents[0].events.append(Event(
            day=1,
            kind="peer_training",
            description="Legacy peer training without a parent reference",
            significance=0.50,
        ))
        legacy.day = 1
        trace = query_causal_history(
            legacy,
            HistoricalEventReference(legacy.agents[0].id, 0),
            direction="ancestors",
        ).trace
        self.assertEqual(trace.edges, ())
        self.assertEqual(len(trace.unresolved_references), 1)
        self.assertEqual(
            trace.unresolved_references[0].reason,
            "knowledge_parent_event_unavailable",
        )

        too_large = World(
            seed=15,
            population=MAX_TRAJECTORY_SUBJECTS + 1,
        )
        with self.assertRaisesRegex(ValueError, "select a subset"):
            query_trajectory_comparison(too_large, too_large)

    def test_counterfactual_packet_is_compact_explainable_and_read_only(self):
        worlds = controlled_fork()
        states_before = tuple(observed_state(world) for world in worlds)

        packet = build_counterfactual_research_packet(
            *worlds,
            fork_day=3,
            max_episodes_per_branch=1,
            max_components=3,
            max_causal_traces=1,
        )

        self.assertEqual(
            packet.analysis_version,
            RESEARCH_PACKET_ANALYSIS_VERSION,
        )
        self.assertTrue(packet.valid_controlled_pair)
        self.assertEqual(packet.first_observed_divergence.day, 4)
        self.assertEqual(packet.trajectory_aggregate_distance, 0.11565277777777777)
        self.assertEqual(
            dict(packet.phase8_metrics.skill_deltas)["npc_003"],
            0.006,
        )
        self.assertLessEqual(len(packet.baseline_episodes), 1)
        self.assertLessEqual(len(packet.counterfactual_episodes), 1)
        self.assertLessEqual(len(packet.trajectory_components), 3)
        self.assertLessEqual(len(packet.causal_evidence), 1)
        self.assertTrue(packet.selection.trajectory_components_truncated)
        self.assertIn(
            "research packet truncated trajectory components",
            packet.qualification_warnings,
        )
        self.assertTrue(packet.source_event_references)
        self.assertTrue(all(
            reference in packet.source_event_references
            for episode in packet.baseline_episodes
            for reference in episode.source_event_references
        ))
        self.assertEqual(
            packet.explanation,
            "First observed divergence appears on day 4 in "
            "authoritative event evidence.",
        )
        self.assertEqual(
            tuple(observed_state(world) for world in worlds),
            states_before,
        )

    def test_fresh_and_save_reload_packets_are_exact(self):
        worlds = controlled_fork()
        expected = build_counterfactual_research_packet(
            *worlds,
            fork_day=3,
        )
        fresh = build_counterfactual_research_packet(
            *controlled_fork(),
            fork_day=3,
        )

        with TemporaryDirectory() as directory:
            loaded = []
            for index, world in enumerate(worlds):
                path = Path(directory) / f"research-{index}.db"
                save_world(world, path)
                loaded.append(load_world(path))
        reloaded = build_counterfactual_research_packet(
            *loaded,
            fork_day=3,
        )

        self.assertEqual(fresh, expected)
        self.assertEqual(reloaded, expected)
        self.assertEqual(reloaded.packet_id, expected.packet_id)

    def test_invalid_query_bounds_windows_subjects_and_directions_fail(self):
        world = connected_history()
        for limit in (0, MAX_EPISODES + 1, True):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    query_historical_episodes(world, max_episodes=limit)
        with self.assertRaisesRegex(ValueError, "observed day"):
            query_historical_episodes(world, end_day=world.day + 1)
        with self.assertRaisesRegex(ValueError, "Unknown research subject"):
            query_historical_episodes(world, subject_agent_id="missing")
        with self.assertRaisesRegex(ValueError, "Unknown causal trace direction"):
            query_causal_history(
                world,
                HistoricalEventReference(world.agents[0].id, 0),
                direction="both",
            )
        with self.assertRaises(ValueError):
            query_causal_history(
                world,
                HistoricalEventReference(world.agents[0].id, 0),
                direction="ancestors",
                max_depth=True,
            )
        with self.assertRaises(ValueError):
            build_counterfactual_research_packet(
                *controlled_fork(),
                fork_day=3,
                max_components=0,
            )

    def test_query_analysis_version_is_separate_from_packet_version(self):
        self.assertEqual(RESEARCH_QUERY_ANALYSIS_VERSION, "research-query-v1")
        self.assertEqual(
            RESEARCH_PACKET_ANALYSIS_VERSION,
            "research-packet-v1",
        )


if __name__ == "__main__":
    unittest.main()
