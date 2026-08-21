from __future__ import annotations

import json
import unittest

from dataclasses import asdict
from pathlib import Path

from archive.phrase1_main import World as Phase1World
from playing_god.core.world import World


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "phase1_seed_1947.json"
)


def agent_snapshot(agent) -> dict:
    data = asdict(agent)
    data["actions"] = dict(agent.actions)
    return data


def world_snapshot(world: World) -> dict:
    return {
        "seed": world.seed,
        "day": world.day,
        "agents": [
            agent_snapshot(agent)
            for agent in world.agents
        ],
        "social": {
            f"{source_id}->{target_id}": dict(data)
            for source_id, target_id, data
            in world.social.graph.edges(data=True)
        },
    }


def phase1_snapshot(world: Phase1World) -> dict:
    return {
        "seed": world.seed,
        "day": world.day,
        "agents": [
            agent_snapshot(agent)
            for agent in world.agents
        ],
    }


class ReproducibilityTests(unittest.TestCase):

    # ---------------------------------------------------------
    # TEST 1
    # A fresh seed=1947 world is reproducible.
    # ---------------------------------------------------------

    def test_seed_1947_is_reproducible(self):
        world_a = World(seed=1947)
        world_b = World(seed=1947)

        world_a.run(365)
        world_b.run(365)

        self.assertEqual(
            world_snapshot(world_a),
            world_snapshot(world_b),
        )

        self.assertEqual(
            world_a.rng.getstate(),
            world_b.rng.getstate(),
        )

    # ---------------------------------------------------------
    # Stronger version of TEST 1:
    # initial state must also be reproducible.
    # ---------------------------------------------------------

    def test_seed_1947_initial_state_is_reproducible(self):
        world_a = World(seed=1947)
        world_b = World(seed=1947)

        self.assertEqual(
            world_snapshot(world_a),
            world_snapshot(world_b),
        )

        self.assertEqual(
            world_a.rng.getstate(),
            world_b.rng.getstate(),
        )

    # ---------------------------------------------------------
    # TEST 6
    # Different seeds create different universes.
    # ---------------------------------------------------------

    def test_different_seeds_create_different_universes(self):
        world_a = World(seed=1947)
        world_b = World(seed=1948)

        world_a.run(365)
        world_b.run(365)

        self.assertNotEqual(
            world_snapshot(world_a),
            world_snapshot(world_b),
        )

    # ---------------------------------------------------------
    # Phase-1 regression:
    # The archived Phase-1 engine must reproduce its frozen fixture.
    # ---------------------------------------------------------

    def test_archived_phase1_matches_frozen_fixture(self):
        if not FIXTURE_PATH.exists():
            self.fail(
                "Missing Phase-1 fixture: "
                f"{FIXTURE_PATH}"
            )

        expected = json.loads(
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

        world = Phase1World(
            seed=1947,
            population=10,
        )

        world.run(365)

        actual = phase1_snapshot(world)

        self.assertEqual(
            expected,
            actual,
            msg=(
                "The archived Phase-1 engine no longer "
                "matches its frozen seed=1947 fixture."
            ),
        )

    # ---------------------------------------------------------
    # Split execution must equal one uninterrupted execution,
    # even before SQLite is involved.
    # ---------------------------------------------------------

    def test_split_run_matches_uninterrupted_run(self):
        uninterrupted = World(
            seed=1947
        )

        uninterrupted.run(365)

        split = World(
            seed=1947
        )

        split.run(120)
        split.run(245)

        self.assertEqual(
            split.day,
            365,
        )

        self.assertEqual(
            world_snapshot(uninterrupted),
            world_snapshot(split),
        )

        self.assertEqual(
            uninterrupted.rng.getstate(),
            split.rng.getstate(),
        )


if __name__ == "__main__":
    unittest.main()
