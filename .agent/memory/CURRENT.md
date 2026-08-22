# Current Engineering State

**Updated:** 2026-08-22

## Current milestone

Phase 4 is complete. Phase 5A — Perception and Belief is complete at its initial foundation scope: world truth, received observations, interpreted perceptions, and current beliefs are distinct, and relationship-driven visits use the actor's believed location rather than live world truth. Phase 5B — Shrine and Prayer is next.

## Recent completed work

- Added stable coding-agent rules and a retrieval-first session protocol.
- Mapped current subsystem ownership, entry points, focused tests, and dependency boundaries.
- Added concise episodic decision/failure memory without introducing a runtime dependency or external service.
- Focused location, routing, mobility, exposure, and interaction tests pass; exposure/interaction remain standalone.
- SQLite schema version 3 persists `current_location` and `destination`; version 1/2 worlds load with backward-compatible `home`/`None` defaults.
- `World.run()` now moves each NPC once for its selected daily activity without adding RNG draws. The fixed map is rebuilt identically for new and loaded worlds.
- The Phase-1 fixture now verifies a legacy projection, so spatial fields/travel events can evolve while prior non-spatial behavior remains protected.
- After daily movement, co-located pairs become exposures; a world-seed/day-derived RNG resolves interactions, and successful pairs gain familiarity in both graph directions.
- Persistence/reproducibility snapshots now include full social-graph state. Authoritative `Agent.relationships` affinity is synchronized into `SocialGraph` before encounter updates.
- Autonomous `socialize`, `help`, and `compete` actions can target only co-located NPCs whose mutual familiarity is at least `0.22`; familiar help also updates trust/respect through the social graph.
- The frozen Phase-1 fixture now validates the archived Phase-1 engine. Current Phase-4 behavior has separate seeded, split-run, and persistence reproducibility contracts.
- Socialize/help travel can visit the current location of the strongest mutually familiar positive tie (`familiarity >= 0.34`, affinity `>= 0.18` in both directions). Needs still override visits, and the visit uses normal Dijkstra travel.
- Successful interactions now append reciprocal events containing the other agent ID and location. SQLite schema version 4 persists this context; version 3 events load with `None` context and migrate on save.
- `Agent.energy` remains the backward-compatible physical-energy state and `physical_energy` alias; bounded `social_energy` separately affects social decisions, trips, encounter probability, social actions, and recovery. SQLite schema version 5 persists it and defaults older worlds from physical energy without new RNG draws.
- Added a read-only Matplotlib spatial debug map for fixed locations, roads, current NPC positions, optional highlighted routes, and simulation day. `scripts/show_spatial_map.py` loads persisted worlds; renderer tests verify it does not mutate simulation state.
- Successful interactions now give each participant an append-only direct observation of the other's location. Deterministic perception updates a separate belief, which remains stale if truth later changes without new evidence.
- SQLite schema version 6 persists observation histories and current beliefs. Version 1–5 worlds load with empty perception state and migrate on save without consuming RNG draws.
- Strong-tie visits require a positive-confidence location belief. Current beliefs route normally, stale beliefs can cause failed rendezvous, and missing/invalid beliefs fall back to ordinary cafe travel without new RNG draws.
- Documentation now uses stable phase-based names: `docs/ROADMAP.md`, `docs/STATUS.md`, and `docs/phases/phase-XX-*.md`. Superseded versioned vision briefs live under `docs/archive/` and no longer drive phase numbering.

## Active architectural concern

Perception currently covers only direct interaction-derived location evidence. Phase 5B shrine/prayer state and behavior are not implemented.

## Known failures and blockers

- Full suite after belief-driven visit movement: 61 tests pass.
- Persistence tests emit unclosed-SQLite `ResourceWarning` messages. They do not currently fail the suite but should be diagnosed separately.

## Next logical task

Begin Phase 5B: add a shrine as an ordinary world location and the smallest structured, deterministic prayer mechanism before implementing Phase 5C interventions.
