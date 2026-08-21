from __future__ import annotations

import math

import matplotlib.pyplot as plt


def _agent_positions(world_map, agents) -> dict[str, tuple[float, float]]:
    by_location: dict[str, list] = {}

    for agent in agents:
        if agent.current_location in world_map.locations:
            by_location.setdefault(
                agent.current_location,
                [],
            ).append(agent)

    positions = {}

    for location_id, occupants in by_location.items():
        location = world_map.locations[location_id]
        ordered = sorted(occupants, key=lambda agent: agent.id)

        for index, agent in enumerate(ordered):
            angle = 2 * math.pi * index / max(1, len(ordered))
            radius = 0.16 if len(ordered) > 1 else 0.0
            positions[agent.id] = (
                location.x + radius * math.cos(angle),
                location.y + radius * math.sin(angle),
            )

    return positions


def draw_spatial_map(
    world_map,
    agents,
    *,
    route: list[str] | None = None,
    day: int | None = None,
    ax=None,
):
    """Draw current spatial state without changing the simulation."""
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5))

    for source, target in world_map.graph.edges:
        start = world_map.locations[source]
        end = world_map.locations[target]
        ax.plot(
            [start.x, end.x],
            [start.y, end.y],
            color="#94a3b8",
            linewidth=1.5,
            zorder=1,
        )

    if route:
        unknown = [
            location_id
            for location_id in route
            if location_id not in world_map.locations
        ]
        if unknown:
            raise ValueError(
                f"Unknown route location: {unknown[0]}"
            )

        route_locations = [
            world_map.locations[location_id]
            for location_id in route
        ]
        ax.plot(
            [location.x for location in route_locations],
            [location.y for location in route_locations],
            color="#f97316",
            linewidth=3,
            zorder=2,
        )

    locations = list(world_map.locations.values())
    ax.scatter(
        [location.x for location in locations],
        [location.y for location in locations],
        s=420,
        color="#e2e8f0",
        edgecolor="#334155",
        zorder=3,
    )

    for location in locations:
        ax.text(
            location.x,
            location.y,
            location.id,
            ha="center",
            va="center",
            fontsize=8,
            zorder=4,
        )

    agent_positions = _agent_positions(world_map, agents)
    visible_agents = [
        agent
        for agent in agents
        if agent.id in agent_positions
    ]

    ax.scatter(
        [agent_positions[agent.id][0] for agent in visible_agents],
        [agent_positions[agent.id][1] for agent in visible_agents],
        s=50,
        color="#2563eb",
        edgecolor="white",
        linewidth=0.7,
        zorder=5,
    )

    for agent in visible_agents:
        x, y = agent_positions[agent.id]
        ax.annotate(
            agent.name,
            (x, y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            zorder=6,
        )

    title = "The Playing God — Spatial Debug Map"
    if day is not None:
        title += f" — Day {day}"

    ax.set_title(title)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.figure.tight_layout()
    return ax


def show_spatial_map(world, route: list[str] | None = None) -> None:
    draw_spatial_map(
        world.world_map,
        world.agents,
        route=route,
        day=world.day,
    )
    plt.show()
