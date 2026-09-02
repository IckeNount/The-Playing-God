from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from playing_god.core.counterfactual import (
    snapshot_agents,
    snapshot_phase8,
)
from playing_god.core.events import Event
from playing_god.core.history import (
    ExplicitCausalReference,
    HistoricalEventReference,
    extract_historical_episodes,
    resolve_source_event,
)
from playing_god.core.world import World
from playing_god.persistence.sqlite_store import load_world, save_world
from tests.test_phase8_exit import prepare_prefork_world, trigger_discovery


def connected_history(seed: int = 91) -> World:
    world = World(seed=seed, population=4)
    for agent in world.agents:
        agent.events.clear()

    first, second, third, unrelated = world.agents
    first.events.append(Event(
        day=1,
        kind="institution",
        description="A: access was denied",
        significance=0.40,
        target_id=second.id,
    ))
    second.events.append(Event(
        day=2,
        kind="problem_pressure_recognized",
        description="B: a shared problem became visible",
        significance=0.65,
        target_id=third.id,
    ))
    third.events.append(Event(
        day=3,
        kind="discovery_attempted",
        description="C: the connected response began",
        significance=0.80,
    ))
    unrelated.events.append(Event(
        day=2,
        kind="prayer",
        description="D: nearby in time but unrelated",
        significance=0.95,
    ))
    world.day = 3
    return world


class HistoricalEpisodeTests(unittest.TestCase):
    def test_participant_chain_excludes_unrelated_chronology(self):
        world = connected_history()

        episodes = extract_historical_episodes(world)

        self.assertEqual(len(episodes), 2)
        connected = next(
            item
            for item in episodes
            if len(item.source_event_references) == 3
        )
        unrelated = next(
            item
            for item in episodes
            if len(item.source_event_references) == 1
        )
        self.assertEqual(connected.start_day, 1)
        self.assertEqual(connected.end_day, 3)
        self.assertEqual(
            connected.participating_agent_ids,
            tuple(sorted(agent.id for agent in world.agents[:3])),
        )
        self.assertEqual(
            connected.source_event_references,
            tuple(
                HistoricalEventReference(agent.id, 0)
                for agent in world.agents[:3]
            ),
        )
        self.assertEqual(
            connected.event_kinds,
            (
                "discovery_attempted",
                "institution",
                "problem_pressure_recognized",
            ),
        )
        self.assertEqual(connected.magnitude, 0.80)
        self.assertEqual(connected.explicit_causal_references, ())
        self.assertEqual(
            unrelated.source_event_references,
            (HistoricalEventReference(world.agents[3].id, 0),),
        )
        source = resolve_source_event(
            world,
            connected.source_event_references[1],
        )
        self.assertIs(source, world.agents[1].events[0])

    def test_extraction_is_repeatable_and_does_not_mutate_world(self):
        world = connected_history()
        agents_before = snapshot_agents(world)
        phase8_before = snapshot_phase8(world)
        rng_before = world.rng.getstate()

        first = extract_historical_episodes(world)
        second = extract_historical_episodes(world)

        self.assertEqual(first, second)
        self.assertEqual(snapshot_agents(world), agents_before)
        self.assertEqual(snapshot_phase8(world), phase8_before)
        self.assertEqual(world.rng.getstate(), rng_before)
        self.assertEqual(world.day, 3)

    def test_fresh_same_seed_and_save_reload_extract_identically(self):
        first = connected_history(seed=14)
        repeat = connected_history(seed=14)
        expected = extract_historical_episodes(first)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.db"
            save_world(first, path)
            loaded = load_world(path)

        self.assertEqual(extract_historical_episodes(repeat), expected)
        self.assertEqual(extract_historical_episodes(loaded), expected)
        self.assertEqual(loaded.rng.getstate(), first.rng.getstate())

    def test_existing_discovery_indices_remain_explicit_causal_links(self):
        world = prepare_prefork_world()
        trigger_discovery(world)
        discoverer = world.agents[0]
        attempt = discoverer.discovery.attempts[0]

        episodes = extract_historical_episodes(world)
        attempt_reference = HistoricalEventReference(
            discoverer.id,
            attempt.attempt_event_index,
        )
        episode = next(
            item
            for item in episodes
            if attempt_reference in item.source_event_references
        )

        self.assertIn(
            ExplicitCausalReference(
                cause=HistoricalEventReference(
                    discoverer.id,
                    attempt.pressure_recognition_event_index,
                ),
                effect=attempt_reference,
                relation="recognition_to_discovery_attempt",
            ),
            episode.explicit_causal_references,
        )
        self.assertIn(
            ExplicitCausalReference(
                cause=attempt_reference,
                effect=HistoricalEventReference(
                    discoverer.id,
                    attempt.resolution_event_index,
                ),
                relation="discovery_attempt_to_resolution",
            ),
            episode.explicit_causal_references,
        )
        self.assertLess(
            len(episode.explicit_causal_references),
            len(episode.source_event_references) - 1,
        )

    def test_empty_single_and_legacy_events_are_supported(self):
        world = World(seed=7, population=1)
        world.agents[0].events.clear()
        self.assertEqual(extract_historical_episodes(world), ())

        world.agents[0].events.append(Event(
            day=0,
            kind="legacy",
            description="No target or location metadata",
            significance=0.25,
        ))
        episodes = extract_historical_episodes(world)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].participating_agent_ids, (
            world.agents[0].id,
        ))
        self.assertEqual(episodes[0].explicit_causal_references, ())

    def test_duration_and_event_count_bounds_split_active_history(self):
        world = World(seed=8, population=1)
        agent = world.agents[0]
        agent.events.clear()
        for day in (0, 1, 2, 3, 10):
            agent.events.append(Event(
                day=day,
                kind="work",
                description=f"Worked on day {day}",
                significance=0.30,
            ))

        episodes = extract_historical_episodes(
            world,
            max_day_gap=2,
            max_duration=3,
            max_events=2,
        )

        self.assertEqual(
            tuple(len(item.source_event_references) for item in episodes),
            (2, 2, 1),
        )
        self.assertTrue(all(
            item.end_day - item.start_day <= 3
            for item in episodes
        ))
        self.assertTrue(all(
            len(item.source_event_references) <= 2
            for item in episodes
        ))

    def test_bounds_must_be_explicit_valid_integers(self):
        world = connected_history()
        for kwargs in (
            {"max_day_gap": -1},
            {"max_duration": -1},
            {"max_events": 0},
            {"max_events": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    extract_historical_episodes(world, **kwargs)


if __name__ == "__main__":
    unittest.main()
