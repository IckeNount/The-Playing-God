from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.causal_history import (
    CAUSAL_TRACE_ANALYSIS_VERSION,
    ExplicitCausalReference,
    HistoricalEventReference,
    trace_causal_ancestors,
    trace_causal_descendants,
)
from playing_god.core.counterfactual import (
    snapshot_agents,
    snapshot_phase8,
)
from playing_god.core.events import Event
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_history import connected_history
from tests.test_phase8_exit import (
    complete_history,
    prepare_prefork_world,
    trigger_discovery,
)


def completed_discovery_history() -> World:
    world = prepare_prefork_world()
    trigger_discovery(world)
    complete_history(world)
    return world


def event_reference(
    world: World,
    agent_index: int,
    kind: str,
    *,
    description_prefix: str | None = None,
) -> HistoricalEventReference:
    agent = world.agents[agent_index]
    event_index = next(
        index
        for index, event in enumerate(agent.events)
        if event.kind == kind
        and (
            description_prefix is None
            or event.description.startswith(description_prefix)
        )
    )
    return HistoricalEventReference(agent.id, event_index)


class CausalHistoryTraceTests(unittest.TestCase):
    def test_discovery_chain_is_traversable_backward_without_association(self):
        world = completed_discovery_history()
        root = event_reference(
            world,
            1,
            "peer_training",
            description_prefix="Peer-trained",
        )

        trace = trace_causal_ancestors(world, root)
        references = {item.reference for item in trace.nodes}

        self.assertEqual(trace.direction, "ancestors")
        self.assertEqual(trace.root, root)
        self.assertEqual(trace.causal_depth, 5)
        self.assertEqual(trace.provenance.analysis_version,
                         CAUSAL_TRACE_ANALYSIS_VERSION)
        self.assertIn(event_reference(
            world,
            0,
            "discovery_validated",
        ), references)
        self.assertIn(event_reference(
            world,
            0,
            "problem_pressure_recognized",
        ), references)
        self.assertIn(event_reference(
            world,
            1,
            "interaction",
        ), references)
        self.assertNotIn(event_reference(
            world,
            0,
            "travel",
            description_prefix="Travelled home -> cafe",
        ), references)
        self.assertNotIn(event_reference(
            world,
            1,
            "knowledge_adopted",
        ), references)
        self.assertFalse(trace.unresolved_references)
        self.assertFalse(trace.corrupt)
        self.assertFalse(trace.truncated)

    def test_descendant_trace_preserves_peer_training_branch(self):
        world = completed_discovery_history()
        discoverer = world.agents[0]
        denial = HistoricalEventReference(
            discoverer.id,
            discoverer.discovery.pressures[0].evidence[0].event_index,
        )
        teacher_training = event_reference(
            world,
            1,
            "peer_training",
            description_prefix="Peer-trained",
        )
        learner_training = event_reference(
            world,
            2,
            "peer_training",
        )
        exposure = event_reference(world, 1, "knowledge_exposed")

        trace = trace_causal_descendants(world, denial)

        self.assertIn(teacher_training, {
            item.reference for item in trace.nodes
        })
        self.assertIn(learner_training, {
            item.reference for item in trace.nodes
        })
        self.assertIn(
            ExplicitCausalReference(
                exposure,
                teacher_training,
                "knowledge_adoption_to_peer_training",
            ),
            trace.edges,
        )
        self.assertIn(
            ExplicitCausalReference(
                exposure,
                learner_training,
                "knowledge_adoption_to_peer_training",
            ),
            trace.edges,
        )
        self.assertNotIn(
            ExplicitCausalReference(
                teacher_training,
                learner_training,
                "knowledge_adoption_to_peer_training",
            ),
            trace.edges,
        )
        self.assertEqual(trace.branch_count, 1)
        self.assertEqual(trace.causal_depth, 5)

    def test_episode_or_participant_association_does_not_create_edges(self):
        world = connected_history()
        root = HistoricalEventReference(world.agents[2].id, 0)

        trace = trace_causal_ancestors(world, root)

        self.assertEqual(
            trace.nodes,
            (type(trace.nodes[0])(depth=0, reference=root),),
        )
        self.assertEqual(trace.edges, ())
        self.assertEqual(trace.reachable_count, 0)

    def test_missing_and_legacy_references_are_explicit_gaps(self):
        legacy = World(seed=4, population=1)
        legacy.agents[0].events.clear()
        legacy.agents[0].events.append(Event(
            day=1,
            kind="peer_training",
            description="Legacy peer training without a parent reference",
            significance=0.50,
        ))
        legacy_root = HistoricalEventReference(legacy.agents[0].id, 0)

        legacy_trace = trace_causal_ancestors(legacy, legacy_root)

        self.assertEqual(len(legacy_trace.unresolved_references), 1)
        self.assertIsNone(
            legacy_trace.unresolved_references[0].cause
        )
        self.assertEqual(
            legacy_trace.unresolved_references[0].reason,
            "knowledge_parent_event_unavailable",
        )

        broken = prepare_prefork_world()
        trigger_discovery(broken)
        agent = broken.agents[0]
        attempt = agent.discovery.attempts[0]
        agent.discovery = replace(
            agent.discovery,
            attempts=(replace(attempt, resolution_event_index=999),),
        )
        attempted = HistoricalEventReference(
            agent.id,
            attempt.attempt_event_index,
        )

        broken_trace = trace_causal_descendants(broken, attempted)

        self.assertEqual(len(broken_trace.unresolved_references), 1)
        gap = broken_trace.unresolved_references[0]
        self.assertEqual(gap.cause, attempted)
        self.assertEqual(
            gap.effect,
            HistoricalEventReference(agent.id, 999),
        )
        self.assertEqual(gap.reason, "referenced_event_unavailable")

    def test_cycle_is_reported_without_infinite_traversal(self):
        world = prepare_prefork_world()
        trigger_discovery(world)
        agent = world.agents[0]
        attempt = agent.discovery.attempts[0]
        agent.discovery = replace(
            agent.discovery,
            attempts=(replace(
                attempt,
                resolution_event_index=attempt.attempt_event_index,
            ),),
        )
        root = HistoricalEventReference(
            agent.id,
            attempt.attempt_event_index,
        )

        trace = trace_causal_descendants(world, root)

        self.assertTrue(trace.corrupt)
        self.assertEqual(len(trace.cycle_edges), 1)
        self.assertEqual(trace.nodes[0].reference, root)
        self.assertLessEqual(len(trace.nodes), trace.configured_max_nodes)

    def test_depth_and_node_limits_report_boundaries(self):
        world = completed_discovery_history()
        agent = world.agents[0]
        denial = HistoricalEventReference(
            agent.id,
            agent.discovery.pressures[0].evidence[0].event_index,
        )

        depth_limited = trace_causal_descendants(
            world,
            denial,
            max_depth=2,
        )
        node_limited = trace_causal_descendants(
            world,
            denial,
            max_nodes=2,
        )

        self.assertTrue(depth_limited.truncated)
        self.assertEqual(depth_limited.causal_depth, 2)
        self.assertEqual(
            {item.reason for item in depth_limited.boundaries},
            {"max_depth"},
        )
        self.assertTrue(node_limited.truncated)
        self.assertEqual(len(node_limited.nodes), 2)
        self.assertEqual(
            {item.reason for item in node_limited.boundaries},
            {"max_nodes"},
        )

    def test_tracing_is_repeatable_read_only_and_restart_exact(self):
        world = completed_discovery_history()
        repeat = completed_discovery_history()
        root = event_reference(
            world,
            1,
            "peer_training",
            description_prefix="Peer-trained",
        )
        agents_before = snapshot_agents(world)
        phase8_before = snapshot_phase8(world)
        rng_before = world.rng.getstate()

        first = trace_causal_ancestors(world, root)
        second = trace_causal_ancestors(world, root)
        repeated_world = trace_causal_ancestors(repeat, root)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "causal-history.db"
            save_world(world, path)
            loaded = load_world(path)
        loaded_trace = trace_causal_ancestors(loaded, root)

        self.assertEqual(first, second)
        self.assertEqual(first, repeated_world)
        self.assertEqual(first, loaded_trace)
        self.assertEqual(snapshot_agents(world), agents_before)
        self.assertEqual(snapshot_phase8(world), phase8_before)
        self.assertEqual(world.rng.getstate(), rng_before)

    def test_unknown_roots_and_invalid_bounds_are_rejected(self):
        world = completed_discovery_history()
        unknown = HistoricalEventReference("missing", 0)
        with self.assertRaisesRegex(ValueError, "Unknown historical event"):
            trace_causal_ancestors(world, unknown)

        root = event_reference(world, 0, "discovery_validated")
        for kwargs in (
            {"max_depth": -1},
            {"max_nodes": 0},
            {"max_nodes": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    trace_causal_descendants(world, root, **kwargs)


if __name__ == "__main__":
    unittest.main()
