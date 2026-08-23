from __future__ import annotations

import unittest

from playing_god.core.events import Event
from playing_god.core.prayer import Prayer, prayer_need
from playing_god.core.world import World


class FaithTests(unittest.TestCase):
    def add_prayer(
        self,
        agent,
        *,
        desire_type="employment",
        intensity=1.0,
        timestamp=0,
    ) -> None:
        agent.prayers.append(
            Prayer(
                agent_id=agent.id,
                desire_type=desire_type,
                intensity=intensity,
                related_goal="find_job",
                timestamp=timestamp,
            )
        )

    def add_event(
        self,
        agent,
        *,
        kind,
        description,
        significance=0.90,
    ) -> None:
        agent.events.append(
            Event(
                day=1,
                kind=kind,
                description=description,
                significance=significance,
            )
        )

    def test_faith_starts_neutral_and_skepticism_is_complement(self):
        agent = World(seed=1947, population=1).agents[0]

        self.assertEqual(agent.faith, 0.5)
        self.assertEqual(agent.skepticism, 0.5)

        agent.faith = 1.4
        agent.normalize()
        self.assertEqual(agent.faith, 1.0)
        self.assertEqual(agent.skepticism, 0.0)

    def test_prayer_and_perceived_stimulus_can_support_miracle(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        agent.traits["discipline"] = 1.0
        agent.traits["risk_tolerance"] = 1.0
        agent.stress = 0.0
        self.add_prayer(agent)
        world.create_intervention(
            kind="dream",
            target_id=agent.id,
            theme="an open office door",
            suggested_action="job_hunt",
            strength=1.0,
        )
        world.day = 1
        world.resolve_interventions()
        self.add_event(
            agent,
            kind="career",
            description="Found a job paying 30/day",
            significance=0.94,
        )
        rng_state = world.rng.getstate()

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "miracle")
        self.assertEqual(attribution.prayer_timestamp, 0)
        self.assertEqual(
            attribution.intervention_id,
            "intervention_000001",
        )
        self.assertGreater(attribution.faith_after, 0.5)
        self.assertEqual(agent.faith, attribution.faith_after)
        self.assertEqual(world.rng.getstate(), rng_state)

    def test_clear_personal_effort_increases_skepticism(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        agent.traits["discipline"] = 1.0
        agent.traits["ambition"] = 1.0
        world.day = 1
        self.add_event(
            agent,
            kind="growth",
            description="Reached skilled-worker level",
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "personal_effort")
        self.assertLess(attribution.faith_after, 0.5)
        self.assertGreater(agent.skepticism, 0.5)

    def test_risky_failure_can_be_attributed_to_coincidence(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        world.day = 1
        self.add_event(
            agent,
            kind="misfortune",
            description="A risky move failed: -64",
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "coincidence")
        self.assertLess(agent.faith, 0.5)

    def test_identifiable_social_help_does_not_become_miracle(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        self.add_prayer(
            agent,
            desire_type="security",
        )
        world.day = 1
        self.add_event(
            agent,
            kind="support",
            description="Received material help from Noah",
            significance=0.55,
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "social_help")
        self.assertEqual(attribution.faith_after, 0.5)

    def test_institutional_cause_outweighs_supernatural_attribution(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        world.day = 1
        self.add_event(
            agent,
            kind="career",
            description="Lost job in workplace downsizing",
            significance=0.95,
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "institutional")
        self.assertLess(agent.faith, 0.5)

    def test_negative_outcome_after_stimulus_can_mean_manipulation(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        agent.traits["discipline"] = 1.0
        agent.traits["risk_tolerance"] = 1.0
        agent.stress = 0.0
        world.create_intervention(
            kind="dream",
            target_id=agent.id,
            theme="an urgent deadline",
            suggested_action="work",
            strength=1.0,
        )
        world.day = 1
        world.resolve_interventions()
        self.add_event(
            agent,
            kind="career",
            description="Lost their job",
            significance=0.96,
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(attribution.cause, "manipulation")
        self.assertLess(agent.faith, 0.5)

    def test_perceived_stimulus_remains_evidence_after_expiry(self):
        world = World(seed=1947, population=2)
        agent = world.agents[0]
        agent.traits["discipline"] = 1.0
        agent.traits["risk_tolerance"] = 1.0
        agent.stress = 0.0
        self.add_prayer(agent)
        world.create_intervention(
            kind="dream",
            target_id=agent.id,
            theme="an open office door",
            suggested_action="job_hunt",
            strength=1.0,
            duration=1,
        )
        world.day = 1
        world.resolve_interventions()
        world.day = 2
        agent.events.append(
            Event(
                day=2,
                kind="career",
                description="Found a job paying 30/day",
                significance=0.94,
            )
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertEqual(
            attribution.intervention_id,
            "intervention_000001",
        )
        self.assertEqual(attribution.cause, "miracle")

    def test_prior_faith_changes_ambiguous_causal_interpretation(self):
        faithful_world = World(seed=1947, population=1)
        skeptical_world = World(seed=1947, population=1)

        for world, faith in (
            (faithful_world, 0.9),
            (skeptical_world, 0.1),
        ):
            agent = world.agents[0]
            agent.faith = faith
            agent.traits["discipline"] = 0.2
            agent.traits["ambition"] = 0.2
            self.add_prayer(agent)
            world.day = 1
            self.add_event(
                agent,
                kind="career",
                description="Found a job paying 30/day",
            )

        faithful = faithful_world.resolve_daily_attributions()[0]
        skeptical = skeptical_world.resolve_daily_attributions()[0]

        self.assertEqual(faithful.cause, "miracle")
        self.assertEqual(skeptical.cause, "coincidence")

    def test_stale_prayer_is_not_used_as_evidence(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        agent.traits["discipline"] = 1.0
        agent.traits["ambition"] = 1.0
        self.add_prayer(agent, timestamp=1)
        world.day = 40
        agent.events.append(
            Event(
                day=40,
                kind="career",
                description="Found a job paying 30/day",
                significance=0.94,
            )
        )

        attribution = world.resolve_daily_attributions()[0]

        self.assertIsNone(attribution.prayer_timestamp)
        self.assertNotEqual(attribution.cause, "miracle")

    def test_outcome_is_attributed_only_once(self):
        world = World(seed=1947, population=1)
        agent = world.agents[0]
        world.day = 1
        self.add_event(
            agent,
            kind="growth",
            description="Reached skilled-worker level",
        )

        first = world.resolve_daily_attributions()
        second = world.resolve_daily_attributions()

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(len(agent.attributions), 1)

    def test_faith_modestly_increases_future_prayer_utility(self):
        agent = World(seed=1947, population=1).agents[0]
        agent.goal = "improve_skill"
        agent.faith = 0.0
        skeptical_score = prayer_need(agent)
        agent.faith = 1.0
        faithful_score = prayer_need(agent)

        self.assertAlmostEqual(
            faithful_score - skeptical_score,
            0.30,
        )


if __name__ == "__main__":
    unittest.main()
