# Current Engineering State

**Updated:** 2026-08-22

## Current milestone

The coding-agent memory foundation (M1/M2/M4) is installed. Phase 4 is complete by the master brief's exit condition: the deterministic simulation can explain location, travel motive/route, possible exposure, actual interaction, repeated-contact relationship change, and relationship-driven movement, with a separate lightweight path renderer.

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

## Active architectural concern

Phase 5's perception boundary is not implemented: agents still consume world truth directly, with no distinct observation, perception, or belief state. The V0.2.4 brief internally calls this build sequence Phase 4, while the canonical master brief labels it Phase 5; follow the master phase numbering and the V0.2.4 subsystem order.

## Known failures and blockers

- Full suite after the Phase 4 spatial debug map: 53 tests pass.
- Persistence tests emit unclosed-SQLite `ResourceWarning` messages. They do not currently fail the suite but should be diagnosed separately.

## Next logical task

Begin Phase 5 with the smallest offline perception/belief foundation from V0.2.4: keep world truth, received observations, and agent belief state distinct before changing decisions or adding prayer/intervention behavior.
