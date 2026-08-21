from dataclasses import dataclass
import networkx as nx


@dataclass(frozen=True)
class Location:
    id: str
    kind: str
    x: float
    y: float


@dataclass(frozen=True)
class Road:
    source: str
    target: str
    distance: float
    travel_time: float
    energy_cost: float = 0.0
    money_cost: float = 0.0
    danger: float = 0.0


class WorldMap:
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.locations: dict[str, Location] = {}

    def add_location(self, location: Location) -> None:
        self.locations[location.id] = location
        self.graph.add_node(location.id)

    def add_road(self, road: Road) -> None:
        if road.source not in self.locations:
            raise ValueError(f"Unknown location: {road.source}")

        if road.target not in self.locations:
            raise ValueError(f"Unknown location: {road.target}")

        self.graph.add_edge(
            road.source,
            road.target,
            distance=road.distance,
            travel_time=road.travel_time,
            energy_cost=road.energy_cost,
            money_cost=road.money_cost,
            danger=road.danger,
        )

    def find_route(
        self,
        start: str,
        destination: str,
    ) -> list[str]:
        return nx.shortest_path(
            self.graph,
            source=start,
            target=destination,
            weight="travel_time",
            method="dijkstra",
        )


def create_default_world_map() -> WorldMap:
    """Build the small fixed map shared by deterministic worlds."""
    world_map = WorldMap()

    for location in (
        Location("home", "home", 0, 0),
        Location("market", "market", 2, 0),
        Location("work", "work", 4, 0),
        Location("cafe", "cafe", 0, 2),
        Location("park", "park", 2, 2),
        Location("school", "school", 4, 2),
    ):
        world_map.add_location(location)

    for road in (
        Road("home", "market", 2, 8),
        Road("market", "work", 2, 8),
        Road("home", "cafe", 2, 6),
        Road("cafe", "park", 2, 5),
        Road("market", "park", 2, 5),
        Road("park", "school", 2, 6),
        Road("school", "work", 2, 6),
        Road("market", "school", 3, 10),
    ):
        world_map.add_road(road)

    return world_map
