from __future__ import annotations

import networkx as nx


RELATIONSHIP_FIELDS = (
    "trust",
    "familiarity",
    "attraction",
    "hostility",
    "respect",
    
)

SOCIAL_EVENT_EFFECTS = {
    "help": {
        "actor_to_target": {
            "familiarity": 0.03,
            "respect": 0.02,
        },
        "target_to_actor": {
            "trust": 0.12,
            "familiarity": 0.05,
            "respect": 0.08,
        },
    },

    "argue": {
        "actor_to_target": {
            "trust": -0.05,
            "familiarity": 0.02,
            "hostility": 0.08,
            "respect": -0.03,
        },
        "target_to_actor": {
            "trust": -0.08,
            "familiarity": 0.02,
            "hostility": 0.10,
            "respect": -0.05,
        },
    },

    "insult": {
        "actor_to_target": {
            "hostility": 0.04,
            "respect": -0.02,
        },
        "target_to_actor": {
            "trust": -0.10,
            "hostility": 0.15,
            "respect": -0.10,
        },
    },

    "betray": {
        "actor_to_target": {
            "familiarity": 0.03,
        },
        "target_to_actor": {
            "trust": -0.35,
            "hostility": 0.30,
            "respect": -0.20,
        },
    },
}

def clamp(value: float) -> float:
    """Clamp a normal relationship dimension to 0.0–1.0."""
    return max(0.0, min(1.0, value))


def clamp_signed(value: float) -> float:
    """Clamp signed affinity to -1.0–1.0."""
    return max(-1.0, min(1.0, value))


class SocialGraph:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    @classmethod
    def from_agents(cls, agents) -> "SocialGraph":
        """
        Build the Phase-3 graph from existing Phase-2 Agent.relationships.

        Important:
        Agent.relationships remains the source of existing Phase-2 behavior.
        """
        social = cls()

        # Every NPC becomes a graph node.
        for agent in agents:
            social.add_agent(agent.id)

        # Existing Phase-2 relationship floats become "affinity".
        for agent in agents:
            for target_id, affinity in agent.relationships.items():
                social.add_relationship(
                    agent.id,
                    target_id,
                    affinity=affinity,
                )

        return social

    def add_agent(self, agent_id: str) -> None:
        self.graph.add_node(agent_id)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        *,
        affinity: float = 0.0,
        trust: float = 0.25,
        familiarity: float = 0.10,
        attraction: float = 0.0,
        hostility: float = 0.0,
        respect: float = 0.25,
    ) -> None:
        self.graph.add_edge(
            source_id,
            target_id,
            affinity=clamp_signed(affinity),
            trust=clamp(trust),
            familiarity=clamp(familiarity),
            attraction=clamp(attraction),
            hostility=clamp(hostility),
            respect=clamp(respect),
        )

    def get_relationship(
        self,
        source_id: str,
        target_id: str,
    ) -> dict[str, float] | None:
        if not self.graph.has_edge(source_id, target_id):
            return None

        return dict(self.graph[source_id][target_id])

    def update_relationship(
        self,
        source_id: str,
        target_id: str,
        **changes: float,
    ) -> None:
        if not self.graph.has_edge(source_id, target_id):
            self.add_relationship(source_id, target_id)

        relationship = self.graph[source_id][target_id]

        for field, amount in changes.items():
            if field == "affinity":
                relationship[field] = clamp_signed(
                    relationship[field] + amount
                )
                continue

            if field not in RELATIONSHIP_FIELDS:
                raise ValueError(
                    f"Unknown relationship field: {field}"
                )

            relationship[field] = clamp(
                relationship[field] + amount
            )

    def set_affinity(
        self,
        source_id: str,
        target_id: str,
        affinity: float,
    ) -> None:
        """Set authoritative affinity without additive float drift."""
        if not self.graph.has_edge(source_id, target_id):
            self.add_relationship(source_id, target_id)

        self.graph[source_id][target_id]["affinity"] = clamp_signed(
            affinity
        )

    def social_neighbors(self, agent_id: str) -> list[str]:
        return list(self.graph.successors(agent_id))

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def relationship_count(self) -> int:
        return self.graph.number_of_edges()

    def apply_social_event(
        self,
        actor_id: str,
        target_id: str,
        event_type: str,
    ) -> None:
        """
        Apply relationship consequences from a social interaction.

        actor_id:
            NPC performing the action.

        target_id:
            NPC receiving the action.

        event_type:
            help, argue, insult, betray
        """

        if actor_id == target_id:
            raise ValueError("An NPC cannot perform a social event on itself.")

        effects = SOCIAL_EVENT_EFFECTS.get(event_type)

        if effects is None:
            raise ValueError(
                f"Unknown social event type: {event_type}"
            )

        # How the actor's feelings toward the target change.
        self.update_relationship(
            actor_id,
            target_id,
            **effects["actor_to_target"],
        )

        # How the target's feelings toward the actor change.
        self.update_relationship(
            target_id,
            actor_id,
            **effects["target_to_actor"],
        )
