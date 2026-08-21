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