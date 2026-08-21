from playing_god.core.agent import Agent
from dataclasses import dataclass

from playing_god.core.spatial import WorldMap

def choose_destination(agent: Agent) -> str:
    if agent.energy < 30:
        return "home"

    if agent.stress > 70:
        return "park"

    return "work"

@dataclass
class TravelResult:
    start: str
    destination: str
    route: list[str]
    travel_time: float


def travel(
    agent,
    world_map: WorldMap,
    destination: str,
) -> TravelResult:
    start = agent.current_location

    route = world_map.find_route(
        start,
        destination,
    )

    travel_time = 0.0

    for source, target in zip(route, route[1:]):
        edge = world_map.graph[source][target]
        travel_time += edge["travel_time"]

    agent.destination = destination
    agent.current_location = destination
    agent.destination = None

    return TravelResult(
        start=start,
        destination=destination,
        route=route,
        travel_time=travel_time,
    )

def travel_event_data(
    agent_id: str,
    result: TravelResult,
) -> dict:
    return {
        "kind": "travel",
        "agent_id": agent_id,
        "from_location": result.start,
        "to_location": result.destination,
        "route": result.route,
        "travel_time": result.travel_time,
        "significance": 0.1,
    }