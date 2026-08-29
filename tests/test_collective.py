from __future__ import annotations

import random
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from playing_god.core.collective import (
    MAX_PARTICIPATION_AGE_DAYS,
    PARTICIPATION_STATUS,
    participation_pressure,
)
from playing_god.core.decision import choose, scores
from playing_god.core.economy import EconomyState
from playing_god.core.information import EMPLOYMENT_STATUS
from playing_god.core.perception import Observation, receive_observation
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world


class CollectiveActionTests(unittest.TestCase):
    def make_threshold_world(self):
        world = World(seed=1947, population=3)
        subject, source, recipient = world.agents

        for trait in recipient.traits:
            recipient.traits[trait] = 0.0
        for sin in recipient.sins:
            recipient.sins[sin] = 0.0
        for other_id in recipient.relationships:
            recipient.relationships[other_id] = 0.0

        recipient.traits["risk_tolerance"] = 0.60
        recipient.money = 130
        recipient.employed = False
        recipient.stress = 0.20
        recipient.energy = 1.0
        recipient.social_energy = 1.0
        recipient.current_location = "home"

        world.sync_social_affinities()
        return world, subject, source, recipient

    def test_participation_is_unavailable_below_threshold(self):
        world, _, _, recipient = self.make_threshold_world()

        pressure = participation_pressure(recipient, world.social)

        self.assertFalse(pressure.eligible)
        self.assertEqual(scores(recipient)["participate"], -99)

    def test_empty_collective_snapshot_has_zero_metrics(self):
        world = World(seed=1947, population=3)
        before_agents = deepcopy(world.agents)
        before_rng = world.rng.getstate()

        snapshot = world.collective_snapshot()

        self.assertEqual(snapshot.participant_ids, ())
        self.assertEqual(snapshot.participants, 0)
        self.assertEqual(snapshot.participation_rate, 0.0)
        self.assertIsNone(snapshot.first_participant_day)
        self.assertEqual(snapshot.peak_participants, 0)
        self.assertEqual(snapshot.cascade_depth, 0)
        self.assertEqual(world.agents, before_agents)
        self.assertEqual(world.rng.getstate(), before_rng)

    def test_trusted_information_can_push_agent_over_threshold(self):
        world, subject, source, recipient = self.make_threshold_world()
        before = world.participation_pressure(recipient)

        world.social.update_relationship(
            recipient.id,
            source.id,
            trust=0.75,
        )
        receive_observation(
            recipient,
            Observation(
                day=world.day,
                kind=EMPLOYMENT_STATUS,
                subject_id=subject.id,
                value="unemployed",
                source_id=source.id,
                reliability=1.0,
            ),
        )

        after = world.participation_pressure(recipient)

        self.assertFalse(before.eligible)
        self.assertEqual(before.trusted_information, 0.0)
        self.assertTrue(after.eligible)
        self.assertEqual(after.trusted_information, 1.0)

    def test_eligible_agent_joins_only_after_normal_selection_and_travel(self):
        world, subject, source, recipient = self.make_threshold_world()
        world.social.update_relationship(
            recipient.id,
            source.id,
            trust=0.75,
        )
        receive_observation(
            recipient,
            Observation(
                day=world.day,
                kind=EMPLOYMENT_STATUS,
                subject_id=subject.id,
                value="unemployed",
                source_id=source.id,
                reliability=1.0,
            ),
        )
        pressure = world.participation_pressure(recipient)

        action = choose(
            recipient,
            random.Random(0),
            participation_utility=pressure.score,
        )
        self.assertEqual(action, "participate")

        world.move_for_action(recipient, action)
        world.act(recipient, action)

        self.assertEqual(recipient.current_location, "park")
        self.assertEqual(recipient.actions["participate"], 1)
        event = recipient.events[-1]
        self.assertEqual(event.kind, "participation")
        self.assertEqual(event.location, "park")
        self.assertIn("trusted information: 1.000", event.description)

    def test_high_personal_pressure_does_not_force_participation(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]

        for trait in agent.traits:
            agent.traits[trait] = 0.0
        for sin in agent.sins:
            agent.sins[sin] = 0.0
        for other_id in agent.relationships:
            agent.relationships[other_id] = 0.0

        agent.traits["risk_tolerance"] = 1.0
        agent.money = -260
        agent.employed = False
        agent.stress = 0.70
        agent.energy = 0.30
        agent.social_energy = 0.30
        agent.current_location = "home"
        world.sync_social_affinities()

        pressure = world.participation_pressure(agent)
        action = choose(
            agent,
            random.Random(0),
            participation_utility=pressure.score,
        )

        self.assertTrue(pressure.eligible)
        self.assertGreater(pressure.personal_pressure, 0.90)
        self.assertEqual(action, "rest")

        world.move_for_action(agent, action)
        world.act(agent, action)

        self.assertEqual(agent.current_location, "home")
        self.assertEqual(agent.actions["participate"], 0)

    def test_direct_action_call_cannot_bypass_threshold_or_location(self):
        world, _, _, recipient = self.make_threshold_world()

        world.act(recipient, "participate")

        self.assertEqual(recipient.actions["participate"], 0)
        self.assertFalse(
            any(
                event.kind == "participation"
                for event in recipient.events
            )
        )

    def test_participation_does_not_become_known_without_interaction(self):
        world, actor, _, observer = self.make_threshold_world()
        world.day = 1
        actor.current_location = "park"
        observer.current_location = "home"
        world.record(
            actor,
            "participation",
            "Joined the public gathering",
            0.68,
            location="park",
        )

        world.resolve_daily_interactions()

        self.assertFalse(
            any(
                observation.kind == PARTICIPATION_STATUS
                for observation in observer.observations
            )
        )
        self.assertEqual(
            world.participation_pressure(
                observer
            ).social_confirmation,
            0.0,
        )

    def test_phase6_chain_is_inspectable_and_survives_restart(self):
        world = World(seed=1947, population=3)
        actor, near_threshold, low_pressure = world.agents
        world.day = 1

        for agent in world.agents:
            for trait in agent.traits:
                agent.traits[trait] = 0.0
            for sin in agent.sins:
                agent.sins[sin] = 0.0
            for other_id in agent.relationships:
                agent.relationships[other_id] = 0.0
            agent.traits["sociability"] = 1.0
            agent.energy = 1.0
            agent.social_energy = 1.0
            agent.current_location = "park"

        actor.traits["risk_tolerance"] = 1.0
        actor.money = -260
        actor.employed = True
        actor.stress = 1.0

        near_threshold.traits["risk_tolerance"] = 0.60
        near_threshold.money = 130
        near_threshold.employed = False
        near_threshold.stress = 0.20

        low_pressure.traits["risk_tolerance"] = 0.0
        low_pressure.money = 260
        low_pressure.employed = False
        low_pressure.stress = 0.0

        world.sync_social_affinities()
        world.economy = EconomyState(job_capacity=1)
        world.social.update_relationship(
            near_threshold.id,
            actor.id,
            trust=0.75,
        )
        world.social.update_relationship(
            low_pressure.id,
            actor.id,
            trust=0.75,
        )

        before_near = world.participation_pressure(near_threshold)
        before_low = world.participation_pressure(low_pressure)
        world.act(actor, "participate")
        interactions = world.resolve_daily_interactions()
        after_near = world.participation_pressure(near_threshold)
        after_low = world.participation_pressure(low_pressure)

        self.assertEqual(len(interactions), 3)
        self.assertFalse(before_near.eligible)
        self.assertFalse(before_low.eligible)
        self.assertEqual(after_near.social_confirmation, 1.0)
        self.assertEqual(after_low.social_confirmation, 1.0)
        self.assertEqual(after_near.trusted_information, 0.25)
        self.assertTrue(after_near.eligible)
        self.assertFalse(after_low.eligible)

        world.day = 2
        world.act(actor, "participate")
        near_threshold.current_location = "home"
        after_near = world.participation_pressure(near_threshold)
        action = choose(
            near_threshold,
            random.Random(0),
            participation_utility=after_near.score,
        )
        self.assertEqual(action, "participate")
        world.move_for_action(near_threshold, action)
        world.act(near_threshold, action)

        self.assertEqual(actor.actions["participate"], 2)
        self.assertEqual(near_threshold.actions["participate"], 1)
        self.assertEqual(low_pressure.actions["participate"], 0)

        economy = world.economic_snapshot()
        collective = world.collective_snapshot()
        trace = world.participation_trace(near_threshold.id)

        self.assertEqual(economy.job_capacity, 1)
        self.assertEqual(economy.vacancies, 0)
        self.assertEqual(economy.unemployed_count, 2)
        self.assertEqual(
            collective.participant_ids,
            (actor.id, near_threshold.id),
        )
        self.assertEqual(collective.participants, 2)
        self.assertEqual(collective.participation_rate, 0.666667)
        self.assertEqual(collective.first_participant_day, 1)
        self.assertEqual(collective.peak_participants, 2)
        self.assertEqual(collective.cascade_depth, 1)

        self.assertEqual(trace.agent_id, near_threshold.id)
        self.assertEqual(trace.participation_day, 2)
        self.assertGreater(trace.personal_pressure, 0.0)
        self.assertEqual(trace.social_confirmation, 1.0)
        self.assertEqual(trace.trusted_information, 0.25)
        self.assertTrue(trace.threshold_passed)
        self.assertEqual(trace.decision, "participate")
        self.assertIsNotNone(trace.movement_event_index)
        self.assertIn("for participate", trace.movement)
        self.assertEqual(trace.influencer_ids, (actor.id,))
        self.assertEqual(len(trace.social_evidence_ids), 1)
        self.assertEqual(
            len(trace.trusted_information_evidence_ids),
            1,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "phase6.db"
            save_world(world, database)
            loaded = load_world(database)

        self.assertEqual(
            loaded.economic_snapshot(),
            economy,
        )
        self.assertEqual(
            loaded.collective_snapshot(),
            collective,
        )
        self.assertEqual(
            loaded.participation_trace(near_threshold.id),
            trace,
        )

        world.run(1)
        loaded.run(1)

        self.assertEqual(
            [asdict(agent) for agent in loaded.agents],
            [asdict(agent) for agent in world.agents],
        )
        self.assertEqual(
            loaded.collective_snapshot(),
            world.collective_snapshot(),
        )
        self.assertEqual(
            loaded.economic_snapshot(),
            world.economic_snapshot(),
        )
        self.assertEqual(loaded.rng.getstate(), world.rng.getstate())

    def test_old_participation_evidence_stops_confirming(self):
        world, actor, _, observer = self.make_threshold_world()
        world.day = 1
        world.social.update_relationship(
            observer.id,
            actor.id,
            trust=0.75,
        )
        world.record(
            actor,
            "participation",
            "Joined the public gathering",
            0.68,
            location="park",
        )
        actor.current_location = "park"
        observer.current_location = "park"
        actor.traits["sociability"] = 1.0
        observer.traits["sociability"] = 1.0
        actor.social_energy = 1.0
        observer.social_energy = 1.0

        world.resolve_daily_interactions()
        current = world.participation_pressure(observer)
        world.day += MAX_PARTICIPATION_AGE_DAYS + 1
        stale = world.participation_pressure(observer)

        self.assertGreater(current.social_confirmation, 0.0)
        self.assertEqual(stale.social_confirmation, 0.0)


if __name__ == "__main__":
    unittest.main()
