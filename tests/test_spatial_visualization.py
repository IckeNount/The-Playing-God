from __future__ import annotations

import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from playing_god.core.world import World
from playing_god.visualization.spatial_map import draw_spatial_map


class SpatialVisualizationTests(unittest.TestCase):

    def tearDown(self) -> None:
        plt.close("all")

    def test_draws_world_without_mutating_simulation(self):
        world = World(seed=1947, population=2)
        world.agents[0].current_location = "market"
        world.agents[1].current_location = "market"
        before = [
            (agent.id, agent.current_location)
            for agent in world.agents
        ]

        ax = draw_spatial_map(
            world.world_map,
            world.agents,
            day=world.day,
        )

        after = [
            (agent.id, agent.current_location)
            for agent in world.agents
        ]
        labels = {text.get_text() for text in ax.texts}

        self.assertEqual(before, after)
        self.assertIn("market", labels)
        self.assertIn(world.agents[0].name, labels)
        self.assertIn("Day 0", ax.get_title())

    def test_highlights_a_route(self):
        world = World(seed=1947, population=1)
        base_road_count = world.world_map.graph.number_of_edges()

        ax = draw_spatial_map(
            world.world_map,
            world.agents,
            route=["home", "market", "work"],
        )

        self.assertEqual(len(ax.lines), base_road_count + 1)
        self.assertEqual(ax.lines[-1].get_color(), "#f97316")


if __name__ == "__main__":
    unittest.main()
