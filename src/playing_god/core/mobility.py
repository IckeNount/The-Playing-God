from dataclasses import dataclass

from playing_god.core.agent import Agent
from playing_god.core.spatial import WorldMap


ACTIVITY_DESTINATIONS = {
    "work": "work",
    "job_hunt": "market",
    "train": "school",
    "socialize": "cafe",
    "help": "cafe",
    "compete": "park",
    "risky_move": "market",
    "pray": "shrine",
    "participate": "park",
    "rest": "home",
}

SOCIAL_ACTIVITIES = {
    "socialize",
    "help",
    "compete",
}

GOAL_DESTINATIONS = {
    "find_job": "market",
    "build_savings": "work",
    "improve_skill": "school",
    "build_relationships": "cafe",
    "advance_career": "work",
}


def choose_destination(
    agent: Agent,
    activity: str | None = None,
) -> str:
    """Choose a plausible destination from needs, intent, and goals."""
    if agent.energy < 0.25:
        return "home"

    if (
        activity in SOCIAL_ACTIVITIES
        and getattr(agent, "social_energy", 1.0) < 0.25
    ):
        return "home"

    if activity == "pray":
        return "shrine"

    if agent.stress > 0.75:
        return "park"

    if activity in ACTIVITY_DESTINATIONS:
        return ACTIVITY_DESTINATIONS[activity]

    destination = GOAL_DESTINATIONS.get(agent.goal)
    if destination is not None:
        return destination

    return "work" if agent.employed else "home"


@dataclass
class TravelResult:
    start: str
    destination: str
    route: list[str]
    travel_time: float
    energy_cost: float = 0.0
    money_cost: float = 0.0


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
    energy_cost = 0.0
    money_cost = 0.0

    for source, target in zip(route, route[1:]):
        edge = world_map.graph[source][target]
        travel_time += edge["travel_time"]
        energy_cost += edge["energy_cost"]
        money_cost += edge["money_cost"]

    if hasattr(agent, "energy"):
        agent.energy -= energy_cost

    if hasattr(agent, "money"):
        agent.money -= money_cost

    agent.destination = destination
    agent.current_location = destination
    agent.destination = None

    return TravelResult(
        start=start,
        destination=destination,
        route=route,
        travel_time=travel_time,
        energy_cost=energy_cost,
        money_cost=money_cost,
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
        "energy_cost": result.energy_cost,
        "money_cost": result.money_cost,
        "significance": 0.1,
    }
