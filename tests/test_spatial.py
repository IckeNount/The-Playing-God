import unittest

from playing_god.core.spatial import Location, Road
from playing_god.core.spatial import (
    Location,
    Road,
    WorldMap,
    create_default_world_map,
)

class SpatialModelTests(unittest.TestCase):

    def test_location(self):
        shrine = Location(
            id="shrine",
            kind="shrine",
            x=5.0,
            y=8.0,
        )

        self.assertEqual(shrine.id, "shrine")
        self.assertEqual(shrine.kind, "shrine")

    def test_road(self):
        road = Road(
            source="home_01",
            target="shrine",
            distance=4.5,
            travel_time=30,
            energy_cost=0.2,
        )

        self.assertEqual(road.source, "home_01")
        self.assertEqual(road.target, "shrine")
        self.assertEqual(road.travel_time, 30)


    def test_world_map_finds_fastest_route(self):
        world_map = WorldMap()

        world_map.add_location(
            Location("home", "home", 0, 0)
        )
        world_map.add_location(
            Location("market", "market", 5, 0)
        )
        world_map.add_location(
            Location("shrine", "shrine", 10, 0)
        )

        world_map.add_road(
            Road("home", "market", 5, 10)
        )
        world_map.add_road(
            Road("market", "shrine", 5, 10)
        )
        world_map.add_road(
            Road("home", "shrine", 8, 30)
        )

        route = world_map.find_route(
            "home",
            "shrine",
        )

        self.assertEqual(
            route,
            ["home", "market", "shrine"],
        )

    def test_default_map_supports_daily_destinations(self):
        world_map = create_default_world_map()

        self.assertEqual(
            set(world_map.locations),
            {
                "home",
                "work",
                "market",
                "school",
                "park",
                "cafe",
                "shrine",
            },
        )
        self.assertEqual(
            world_map.find_route("home", "work"),
            ["home", "market", "work"],
        )
        self.assertEqual(
            world_map.find_route("home", "shrine"),
            ["home", "cafe", "park", "shrine"],
        )

if __name__ == "__main__":
    unittest.main()
