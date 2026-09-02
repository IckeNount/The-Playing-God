from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from playing_god.core.civilization import (
    PEER_TRAIN_ACTION_ID,
    PEER_TRAIN_KNOWLEDGE_ID,
    AgentKnowledgeRecord,
    AgentKnowledgeState,
    CivilizationState,
    KnowledgeEntry,
    adopted_knowledge_ids,
    knowledge_signature,
    knowledge_variant_id,
    validate_civilization_links,
)
from playing_god.core.counterfactual import snapshot_agents
from playing_god.core.decision import scores
from playing_god.core.events import Event
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world


PRIMITIVE_IDS = (
    "demonstration",
    "feedback",
    "shared_practice",
)


def add_discoverer_knowledge(world: World) -> None:
    world.day = 2
    discoverer = world.agents[0]
    attempt_event_index = len(discoverer.events)
    discoverer.events.append(Event(
        day=1,
        kind="discovery_attempted",
        description="Combined peer-learning primitives",
        significance=0.60,
    ))
    validation_event_index = len(discoverer.events)
    discoverer.events.append(Event(
        day=2,
        kind="discovery_validated",
        description="Validated peer-training knowledge",
        significance=0.85,
    ))
    world.civilization = CivilizationState(knowledge=(KnowledgeEntry(
        id=PEER_TRAIN_KNOWLEDGE_ID,
        signature=knowledge_signature(
            PRIMITIVE_IDS,
            PEER_TRAIN_ACTION_ID,
        ),
        origin_agent_id=discoverer.id,
        origin_event_index=attempt_event_index,
        discoverer_ids=(discoverer.id,),
        primitive_ids=PRIMITIVE_IDS,
        action_id=PEER_TRAIN_ACTION_ID,
        creation_day=2,
    ),))
    discoverer.knowledge = AgentKnowledgeState(records=(
        AgentKnowledgeRecord(
            day=2,
            knowledge_id=PEER_TRAIN_KNOWLEDGE_ID,
            source_id=discoverer.id,
            route="discovery",
            response="accept",
            variant_id=None,
            causal_parent_agent_id=discoverer.id,
            causal_parent_event_index=validation_event_index,
        ),
    ))


def expose_socially(
    *,
    empathy: float,
    trust: float,
    familiarity: float,
) -> World:
    world = World(seed=1947, population=2)
    add_discoverer_knowledge(world)
    source, recipient = world.agents
    for agent in world.agents:
        agent.current_location = "market"
        agent.traits["sociability"] = 1.0
        agent.social_energy = 1.0
    recipient.traits["empathy"] = empathy
    world.social.add_relationship(
        recipient.id,
        source.id,
        affinity=0.0,
        trust=trust,
        familiarity=familiarity,
    )
    world.day = 4
    world.resolve_daily_interactions()
    return world


class KnowledgeDiffusionTests(unittest.TestCase):
    def test_social_contact_adopts_locally_and_snapshots_history(self):
        world = World(seed=1947, population=3)
        add_discoverer_knowledge(world)
        source, recipient, bystander = world.agents
        source.current_location = "market"
        recipient.current_location = "market"
        bystander.current_location = "home"
        for agent in (source, recipient):
            agent.traits["sociability"] = 1.0
            agent.social_energy = 1.0
        world.social.add_relationship(
            recipient.id,
            source.id,
            affinity=0.50,
            trust=0.90,
            familiarity=0.90,
        )
        world.day = 4

        world.resolve_daily_interactions()

        record = recipient.knowledge.records[0]
        self.assertEqual(record.route, "social")
        self.assertEqual(record.response, "accept")
        self.assertEqual(
            adopted_knowledge_ids(recipient.knowledge),
            (PEER_TRAIN_KNOWLEDGE_ID,),
        )
        self.assertEqual(bystander.knowledge, AgentKnowledgeState())
        self.assertEqual(
            [event.kind for event in recipient.events[-2:]],
            ["knowledge_exposed", "knowledge_adopted"],
        )
        self.assertEqual(
            snapshot_agents(world)[1].knowledge,
            recipient.knowledge,
        )
        self.assertNotIn(PEER_TRAIN_ACTION_ID, scores(recipient))
        validate_civilization_links(
            world.civilization,
            world.agents,
            current_day=world.day,
        )

    def test_response_is_deterministic_and_rejection_does_not_adopt(self):
        modified = expose_socially(
            empathy=0.50,
            trust=0.20,
            familiarity=0.10,
        )
        repeated = expose_socially(
            empathy=0.50,
            trust=0.20,
            familiarity=0.10,
        )
        rejected = expose_socially(
            empathy=0.0,
            trust=0.0,
            familiarity=0.0,
        )

        modified_record = modified.agents[1].knowledge.records[0]
        rejected_record = rejected.agents[1].knowledge.records[0]
        self.assertEqual(
            modified.agents[1].knowledge,
            repeated.agents[1].knowledge,
        )
        self.assertEqual(modified_record.response, "modify")
        self.assertEqual(
            modified_record.variant_id,
            knowledge_variant_id(
                PEER_TRAIN_KNOWLEDGE_ID,
                modified.agents[1].id,
            ),
        )
        self.assertEqual(
            modified_record.knowledge_id,
            PEER_TRAIN_KNOWLEDGE_ID,
        )
        self.assertEqual(modified.civilization.affordances, ())
        self.assertEqual(rejected_record.response, "reject")
        self.assertEqual(
            adopted_knowledge_ids(rejected.agents[1].knowledge),
            (),
        )
        self.assertFalse(any(
            event.kind == "knowledge_adopted"
            for event in rejected.agents[1].events
        ))
        self.assertNotIn(
            PEER_TRAIN_ACTION_ID,
            scores(rejected.agents[1]),
        )

    def test_restart_preserves_history_without_duplicate_social_adoption(self):
        world = expose_socially(
            empathy=1.0,
            trust=0.90,
            familiarity=0.90,
        )
        recipient_id = world.agents[1].id

        with TemporaryDirectory() as directory:
            path = Path(directory) / "world.db"
            save_world(world, path)
            loaded = load_world(path)
            loaded.day = 5
            loaded.resolve_daily_interactions()
            save_world(loaded, path)
            reloaded = load_world(path)

        recipient = next(
            agent for agent in reloaded.agents
            if agent.id == recipient_id
        )
        self.assertEqual(len(recipient.knowledge.records), 1)
        self.assertEqual(sum(
            event.kind == "knowledge_adopted"
            for event in recipient.events
        ), 1)

    def test_guardian_exposure_uses_the_annual_development_route(self):
        world = World(
            seed=71,
            population=2,
            reproduction_enabled=True,
        )
        first, second = world.agents
        for parent in (first, second):
            parent.age = 30
            parent.money = 500.0
            parent.stress = 0.10
            parent.current_location = "home"
        first.employed = True
        first.relationships[second.id] = 0.50
        second.relationships[first.id] = 0.50
        for source, target in ((first, second), (second, first)):
            world.social.add_relationship(
                source.id,
                target.id,
                affinity=0.50,
                trust=0.70,
                familiarity=0.80,
            )
        with patch(
            "playing_god.core.world.REPRODUCTION_DAILY_CHANCE",
            1.0,
        ):
            child = world.resolve_reproduction()[0]
        add_discoverer_knowledge(world)
        world.day = child.family.birth_day + 365

        world.resolve_development()

        records = [
            record
            for record in child.knowledge.records
            if record.route == "guardian"
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_id, first.id)
        validate_civilization_links(
            world.civilization,
            world.agents,
            current_day=world.day,
        )

    def test_broken_exposure_event_is_rejected_by_integrity_check(self):
        world = expose_socially(
            empathy=1.0,
            trust=0.90,
            familiarity=0.90,
        )
        recipient = world.agents[1]
        record = recipient.knowledge.records[0]
        recipient.events[record.causal_parent_event_index] = replace(
            recipient.events[record.causal_parent_event_index],
            target_id="npc_missing",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Invalid knowledge exposure link",
        ):
            validate_civilization_links(
                world.civilization,
                world.agents,
                current_day=world.day,
            )


if __name__ == "__main__":
    unittest.main()
