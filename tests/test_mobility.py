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
from unittest.mock import patch



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
from playing_god.core.world import World

class MobilityTests(unittest.TestCase):

    def test_tired_agent_goes_home(self):
        agent = SimpleNamespace(
            energy=0.20,
            stress=0.20,
            goal="advance_career",
            employed=True,
        )

        destination = choose_destination(agent, "work")

        self.assertEqual(destination, "home")

    def test_stressed_agent_goes_to_park(self):
        agent = SimpleNamespace(
            energy=0.80,
            stress=0.90,
            goal="advance_career",
            employed=True,
        )

        destination = choose_destination(agent, "work")

        self.assertEqual(destination, "park")

    def test_normal_agent_goes_to_work(self):
        agent = SimpleNamespace(
            energy=0.80,
            stress=0.20,
            goal="advance_career",
            employed=True,
        )

        destination = choose_destination(agent, "work")

        self.assertEqual(destination, "work")

    def test_socially_tired_agent_cancels_social_trip(self):
        agent = SimpleNamespace(
            energy=0.80,
            social_energy=0.20,
            stress=0.20,
            goal="build_relationships",
            employed=True,
        )

        destination = choose_destination(agent, "socialize")

        self.assertEqual(destination, "home")

    def test_socializing_spends_only_social_energy(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "cafe"
        target.current_location = "work"
        actor.energy = 0.80
        actor.social_energy = 0.80

        world.act(actor, "socialize")

        self.assertEqual(actor.energy, 0.80)
        self.assertLess(actor.social_energy, 0.80)


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

    def test_travel_pays_route_costs(self):
        world_map = WorldMap()
        world_map.add_location(Location("home", "home", 0, 0))
        world_map.add_location(Location("work", "work", 1, 0))
        world_map.add_road(
            Road(
                "home",
                "work",
                distance=1,
                travel_time=5,
                energy_cost=0.04,
                money_cost=2.5,
            )
        )
        agent = SimpleNamespace(
            current_location="home",
            destination=None,
            energy=0.80,
            money=100.0,
        )

        result = travel(agent, world_map, "work")

        self.assertAlmostEqual(result.energy_cost, 0.04)
        self.assertAlmostEqual(result.money_cost, 2.5)
        self.assertAlmostEqual(agent.energy, 0.76)
        self.assertAlmostEqual(agent.money, 97.5)

    def test_world_run_moves_for_selected_activity(self):
        world = World(seed=1947, population=2)

        with patch(
            "playing_god.core.world.choose",
            return_value="train",
        ):
            world.run(1)

        for agent in world.agents:
            self.assertEqual(agent.current_location, "school")
            self.assertTrue(
                any(
                    event.kind == "travel"
                    and "for train" in event.description
                    for event in agent.events
                )
            )

    def test_strong_relationship_redirects_social_travel_to_visit(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "home"
        target.current_location = "park"
        actor.relationships[target.id] = 0.30
        target.relationships[actor.id] = 0.30
        world.social.update_relationship(
            actor.id,
            target.id,
            familiarity=0.30,
        )
        world.social.update_relationship(
            target.id,
            actor.id,
            familiarity=0.30,
        )
        world.sync_social_affinities()

        world.move_for_action(actor, "socialize")

        self.assertEqual(actor.current_location, "park")
        self.assertIn(target, world.exposed_people(actor))
        self.assertIn(
            f"to visit {target.name}",
            actor.events[-1].description,
        )

    def test_weak_relationship_uses_normal_social_destination(self):
        world = World(seed=1947, population=2)
        actor, target = world.agents
        actor.current_location = "home"
        target.current_location = "park"

        world.move_for_action(actor, "socialize")

        self.assertEqual(actor.current_location, "cafe")
    

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
