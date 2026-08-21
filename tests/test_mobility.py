# import unittest

# from playing_god.core.mobility import choose_destination


# class MobilityTests(unittest.TestCase):

#     def test_tired_agent_goes_home(self):
#         agent = self.make_agent()

#         agent.energy = 20

#         destination = choose_destination(agent)

#         self.assertEqual(destination, "home")

#     def test_stressed_agent_goes_to_park(self):
#         agent = self.make_agent()

#         agent.energy = 80
#         agent.stress = 90

#         destination = choose_destination(agent)

#         self.assertEqual(destination, "park")

import unittest
from types import SimpleNamespace



from playing_god.core.mobility import (
    choose_destination,
    travel,
    travel_event_data,
    TravelResult,
)

from playing_god.core.spatial import (
    Location,
    Road,
    WorldMap,
)

class MobilityTests(unittest.TestCase):

    def test_tired_agent_goes_home(self):
        agent = SimpleNamespace(
            energy=20,
            stress=20,
        )

        destination = choose_destination(agent)

        self.assertEqual(destination, "home")

    def test_stressed_agent_goes_to_park(self):
        agent = SimpleNamespace(
            energy=80,
            stress=90,
        )

        destination = choose_destination(agent)

        self.assertEqual(destination, "park")

    def test_normal_agent_goes_to_work(self):
        agent = SimpleNamespace(
            energy=80,
            stress=20,
        )

        destination = choose_destination(agent)

        self.assertEqual(destination, "work")


    def test_agent_can_travel(self):
        world_map = WorldMap()

        world_map.add_location(
            Location("home", "home", 0, 0)
        )
        world_map.add_location(
            Location("market", "market", 5, 0)
        )
        world_map.add_location(
            Location("work", "work", 10, 0)
        )

        world_map.add_road(
            Road(
                "home",
                "market",
                distance=5,
                travel_time=10,
            )
        )

        world_map.add_road(
            Road(
                "market",
                "work",
                distance=5,
                travel_time=15,
            )
        )

        agent = SimpleNamespace(
            current_location="home",
            destination=None,
        )

        result = travel(
            agent,
            world_map,
            "work",
        )

        self.assertEqual(
            result.route,
            ["home", "market", "work"],
        )

        self.assertEqual(
            result.travel_time,
            25,
        )

        self.assertEqual(
            agent.current_location,
            "work",
        )

        self.assertIsNone(
            agent.destination,
        )
    

    def test_travel_creates_event_data(self):
        result = TravelResult(
            start="home",
            destination="work",
            route=["home", "market", "work"],
            travel_time=25,
        )

        event = travel_event_data(
            "npc_001",
            result,
        )

        self.assertEqual(event["kind"], "travel")
        self.assertEqual(event["agent_id"], "npc_001")
        self.assertEqual(event["from_location"], "home")
        self.assertEqual(event["to_location"], "work")
        self.assertEqual(
            event["route"],
            ["home", "market", "work"],
        )


if __name__ == "__main__":
    unittest.main()