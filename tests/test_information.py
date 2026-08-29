from __future__ import annotations

from dataclasses import asdict
import unittest

from playing_god.core.information import (
    EMPLOYMENT_STATUS,
    employment_information_id,
)
from playing_god.core.perception import (
    Observation,
    belief_key,
    receive_observation,
)
from playing_god.core.world import World


class InformationTests(unittest.TestCase):

    def make_world(self) -> tuple[World, object, object, object]:
        world = World(seed=1947, population=3)
        subject, source, recipient = world.agents

        for agent in world.agents:
            agent.traits["sociability"] = 1.0
            agent.social_energy = 1.0
            agent.current_location = "home"

        return world, subject, source, recipient

    def give_firsthand_employment_evidence(
        self,
        world,
        subject,
        source,
        *,
        value: str | None = None,
    ) -> None:
        claim_value = (
            value
            if value is not None
            else (
                "employed"
                if subject.employed
                else "unemployed"
            )
        )
        receive_observation(
            source,
            Observation(
                day=world.day,
                kind=EMPLOYMENT_STATUS,
                subject_id=subject.id,
                value=claim_value,
                source_id=subject.id,
                reliability=1.0,
                location="market",
                information_id=employment_information_id(
                    subject.id,
                    world.day,
                    claim_value,
                ),
                origin_agent_id=subject.id,
                origin_day=world.day,
                hop_count=0,
            ),
        )

    def _testimony_observations(self, recipient, subject, source):
        return [
            observation
            for observation in recipient.observations
            if (
                observation.kind == EMPLOYMENT_STATUS
                and observation.subject_id == subject.id
                and observation.source_id == source.id
            )
        ]

    def test_no_interaction_means_no_testimony_transfer(self):
        world, subject, source, recipient = self.make_world()
        self.give_firsthand_employment_evidence(
            world,
            subject,
            source,
        )
        source.current_location = "market"
        recipient.current_location = "school"
        world.day = 1

        world.resolve_daily_interactions()

        self.assertEqual(
            self._testimony_observations(recipient, subject, source),
            [],
        )
        self.assertEqual(world.information_items, [])

    def test_interaction_transmits_structured_testimony_to_belief(self):
        world, subject, source, recipient = self.make_world()
        self.give_firsthand_employment_evidence(
            world,
            subject,
            source,
        )
        subject.current_location = "home"
        source.current_location = "market"
        recipient.current_location = "market"
        world.day = 1

        interactions = world.resolve_daily_interactions()

        self.assertEqual(len(interactions), 1)
        observations = self._testimony_observations(
            recipient,
            subject,
            source,
        )
        self.assertEqual(len(observations), 1)
        observation = observations[0]
        self.assertGreater(observation.reliability, 0.0)
        self.assertLessEqual(observation.reliability, 1.0)

        item = world.information_items[0]
        self.assertEqual(item.kind, EMPLOYMENT_STATUS)
        self.assertEqual(item.subject_id, subject.id)
        self.assertEqual(item.value, observation.value)
        self.assertEqual(item.origin_agent_id, subject.id)
        self.assertEqual(item.origin_day, 0)
        self.assertEqual(item.reliability, observation.reliability)
        self.assertIn(item.id, source.events[-1].description)
        self.assertIn(item.id, recipient.events[-1].description)

        belief = recipient.beliefs[
            belief_key(EMPLOYMENT_STATUS, subject.id)
        ]
        self.assertEqual(belief.value, observation.value)
        self.assertEqual(
            belief.confidence,
            observation.reliability,
        )

    def test_stale_testimony_does_not_refresh_from_world_truth(self):
        world, subject, source, recipient = self.make_world()
        subject.employed = False
        self.give_firsthand_employment_evidence(
            world,
            subject,
            source,
            value="unemployed",
        )
        subject.employed = True
        source.current_location = "market"
        recipient.current_location = "market"
        world.day = 1

        world.resolve_daily_interactions()

        belief = recipient.beliefs[
            belief_key(EMPLOYMENT_STATUS, subject.id)
        ]
        self.assertTrue(subject.employed)
        self.assertEqual(belief.value, "unemployed")

    def test_fact_reaches_c_through_b_without_a_c_contact(self):
        world, subject, source, recipient = self.make_world()
        subject.current_location = "market"
        source.current_location = "market"
        recipient.current_location = "home"
        world.day = 1

        first_interactions = world.resolve_daily_interactions()

        self.assertEqual(len(first_interactions), 1)
        self.assertIn(
            belief_key(EMPLOYMENT_STATUS, subject.id),
            source.beliefs,
        )

        subject.current_location = "home"
        source.current_location = "market"
        recipient.current_location = "market"
        source.social_energy = 1.0
        recipient.social_energy = 1.0
        world.day = 2

        second_interactions = world.resolve_daily_interactions()

        self.assertEqual(len(second_interactions), 1)
        self.assertEqual(
            len(
                self._testimony_observations(
                    recipient,
                    subject,
                    source,
                )
            ),
            1,
        )
        direct_contacts = [
            event
            for event in recipient.events
            if event.kind == "interaction"
            and event.target_id == subject.id
        ]
        self.assertEqual(direct_contacts, [])

    def test_repeated_seeded_scenario_is_exact(self):
        def scenario():
            world, subject, source, recipient = self.make_world()
            self.give_firsthand_employment_evidence(
                world,
                subject,
                source,
            )
            source.current_location = "market"
            recipient.current_location = "market"
            world.day = 1
            rng_state = world.rng.getstate()

            world.resolve_daily_interactions()

            return (
                [asdict(item) for item in world.information_items],
                [
                    asdict(observation)
                    for observation in recipient.observations
                ],
                {
                    key: asdict(belief)
                    for key, belief in recipient.beliefs.items()
                },
                world.rng.getstate(),
                rng_state,
            )

        first = scenario()
        second = scenario()

        self.assertEqual(first, second)
        self.assertEqual(first[-2], first[-1])

    def test_multi_hop_relay_preserves_origin_and_decays(self):
        world = World(seed=1947, population=4)
        subject, source, relay, recipient = world.agents
        for agent in world.agents:
            agent.traits["sociability"] = 1.0
            agent.social_energy = 1.0

        self.give_firsthand_employment_evidence(
            world,
            subject,
            source,
        )
        evidence_id = source.observations[-1].information_id
        subject.current_location = "home"
        source.current_location = "market"
        relay.current_location = "market"
        recipient.current_location = "school"
        world.day = 1

        world.resolve_daily_interactions()

        first_hop = next(
            observation
            for observation in relay.observations
            if observation.information_id == evidence_id
        )
        subject.current_location = "home"
        source.current_location = "work"
        relay.current_location = "market"
        recipient.current_location = "market"
        relay.social_energy = 1.0
        recipient.social_energy = 1.0
        world.day = 2

        world.resolve_daily_interactions()

        second_hop = next(
            observation
            for observation in recipient.observations
            if observation.information_id == evidence_id
        )
        self.assertEqual(first_hop.source_id, source.id)
        self.assertEqual(second_hop.source_id, relay.id)
        self.assertEqual(second_hop.origin_agent_id, subject.id)
        self.assertEqual(second_hop.origin_day, 0)
        self.assertEqual(second_hop.hop_count, 2)
        self.assertLess(
            second_hop.reliability,
            first_hop.reliability,
        )

    def test_circular_repetition_is_not_new_evidence(self):
        world, subject, source, recipient = self.make_world()
        self.give_firsthand_employment_evidence(
            world,
            subject,
            source,
        )
        evidence_id = source.observations[-1].information_id
        subject.current_location = "home"
        source.current_location = "market"
        recipient.current_location = "market"
        world.day = 1
        world.resolve_daily_interactions()

        source_belief_before = source.beliefs[
            belief_key(EMPLOYMENT_STATUS, subject.id)
        ]
        recipient_belief_before = recipient.beliefs[
            belief_key(EMPLOYMENT_STATUS, subject.id)
        ]
        source_count_before = sum(
            observation.information_id == evidence_id
            for observation in source.observations
        )
        recipient_count_before = sum(
            observation.information_id == evidence_id
            for observation in recipient.observations
        )

        source.current_location = "market"
        recipient.current_location = "market"
        source.social_energy = 1.0
        recipient.social_energy = 1.0
        world.day = 2
        world.resolve_daily_interactions()

        self.assertEqual(
            sum(
                observation.information_id == evidence_id
                for observation in source.observations
            ),
            source_count_before,
        )
        self.assertEqual(
            sum(
                observation.information_id == evidence_id
                for observation in recipient.observations
            ),
            recipient_count_before,
        )
        self.assertEqual(
            source.beliefs[
                belief_key(EMPLOYMENT_STATUS, subject.id)
            ],
            source_belief_before,
        )
        self.assertEqual(
            recipient.beliefs[
                belief_key(EMPLOYMENT_STATUS, subject.id)
            ],
            recipient_belief_before,
        )

    def test_diffusion_snapshot_quantifies_reach_and_confidence(self):
        world = World(seed=1947, population=4)
        subject, source, relay, recipient = world.agents
        information_id = employment_information_id(
            subject.id,
            0,
            "unemployed",
        )
        observations = (
            (
                source,
                Observation(
                    day=0,
                    kind=EMPLOYMENT_STATUS,
                    subject_id=subject.id,
                    value="unemployed",
                    source_id=subject.id,
                    reliability=1.0,
                    information_id=information_id,
                    origin_agent_id=subject.id,
                    origin_day=0,
                    hop_count=0,
                ),
            ),
            (
                relay,
                Observation(
                    day=1,
                    kind=EMPLOYMENT_STATUS,
                    subject_id=subject.id,
                    value="unemployed",
                    source_id=source.id,
                    reliability=0.6,
                    information_id=information_id,
                    origin_agent_id=subject.id,
                    origin_day=0,
                    hop_count=1,
                ),
            ),
            (
                recipient,
                Observation(
                    day=2,
                    kind=EMPLOYMENT_STATUS,
                    subject_id=subject.id,
                    value="unemployed",
                    source_id=relay.id,
                    reliability=0.5,
                    information_id=information_id,
                    origin_agent_id=subject.id,
                    origin_day=0,
                    hop_count=2,
                ),
            ),
        )
        for agent, observation in observations:
            receive_observation(agent, observation)

        agents_before = [asdict(agent) for agent in world.agents]
        rng_before = world.rng.getstate()

        snapshot = world.diffusion_snapshot(information_id)

        self.assertEqual(snapshot.information_id, information_id)
        self.assertEqual(snapshot.kind, EMPLOYMENT_STATUS)
        self.assertEqual(snapshot.subject_id, subject.id)
        self.assertEqual(snapshot.value, "unemployed")
        self.assertEqual(snapshot.origin_agent_id, subject.id)
        self.assertEqual(snapshot.origin_day, 0)
        self.assertEqual(
            snapshot.reached_agent_ids,
            (source.id, relay.id, recipient.id),
        )
        self.assertEqual(snapshot.reached_agent_count, 3)
        self.assertEqual(snapshot.informed_agent_count, 3)
        self.assertEqual(snapshot.max_hops_from_origin, 2)
        self.assertEqual(snapshot.average_belief_confidence, 0.7)
        self.assertEqual(snapshot.median_belief_confidence, 0.6)
        self.assertEqual(
            snapshot,
            world.diffusion_snapshot(information_id),
        )
        self.assertEqual(
            [asdict(agent) for agent in world.agents],
            agents_before,
        )
        self.assertEqual(world.rng.getstate(), rng_before)

    def test_diffusion_snapshot_rejects_unknown_information(self):
        world = World(seed=1947, population=2)

        with self.assertRaises(ValueError) as context:
            world.diffusion_snapshot("unknown-information")

        self.assertIn("Unknown information item", str(context.exception))


if __name__ == "__main__":
    unittest.main()
