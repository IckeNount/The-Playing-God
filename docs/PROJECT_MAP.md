# Playing God Project Map

Use this map to find the owning subsystem before opening source. It describes the repository as it exists now; planned phases are listed separately and are not implemented claims.

## Dependency direction

```text
scripts
  -> persistence
       -> core world + agent + events + RNG + social graph
  -> visualization
       -> social graph

core world
  -> agent + decision + events + RNG + social graph + mobility + spatial map

exposure
  -> agent spatial state
  -> daily interaction opportunities in core world
```

Simulation code must not depend on `.agent/`, memory documents, or coding-agent tooling.

## `core-simulation` — agents, decisions, and world evolution

**Owns:** deterministic population creation, mutable agent state, goals, action selection and effects, daily progression, event recording, aging, and text reports.

**Entry points:**

- `src/playing_god/core/world.py` — `World`, including `run()`, `act()`, and `report()`.
- `src/playing_god/core/agent.py` — `Agent`, stable trait/sin keys, normalization.
- `src/playing_god/core/decision.py` — action scores and seeded weighted selection.
- `src/playing_god/core/events.py` — structured per-agent `Event`.
- `src/playing_god/core/rng.py` — RNG construction and persistence-safe state serialization.

**Focused tests:** `tests/test_reproducibility.py`.

**Important boundary:** All causal randomness must use the world's seeded RNG. Avoid global randomness and changes to RNG call order unless the resulting determinism migration is intentional and tested.

## `social` — relationships and contact

**Owns:** directed multidimensional relationships, social-event effects, co-location exposure detection, and probabilistic interaction resolution.

**Entry points:**

- `src/playing_god/core/social.py` — `SocialGraph` and social event effects.
- `src/playing_god/core/exposure.py` — `Exposure`, `Interaction`, detection, and resolution.
- `src/playing_god/visualization/social_graph.py` — optional NetworkX graph inspection.
- `scripts/show_social_graph.py` — manual visualization entry point.

**Focused tests:** `tests/test_social.py`, `tests/test_exposure.py`.

**Important boundary:** `Agent.relationships` remains the legacy signed affinity used by current decisions. `SocialGraph` adds dimensions and is rebuilt from agents; changing one representation does not automatically make the other the source of truth.

## `spatial-mobility` — places, routes, and travel

**Owns:** location/road models, shortest-time routing, destination selection, travel state changes, and travel-event payloads.

**Entry points:**

- `src/playing_god/core/spatial.py` — `Location`, `Road`, and `WorldMap`.
- `src/playing_god/core/mobility.py` — destination choice, travel, and event data.
- `src/playing_god/visualization/spatial_map.py` — read-only fixed-map, NPC-position, and route renderer.
- `scripts/show_spatial_map.py` — persisted-world spatial visualization entry point.
- Agent location fields live in `src/playing_god/core/agent.py`.

**Focused tests:** `tests/test_spatial.py`, `tests/test_mobility.py`, `tests/test_exposure.py`, `tests/test_spatial_visualization.py`.

**Current state:** The full movement → exposure → interaction → relationship → visit movement loop participates in `World.run()`, successful encounters retain who/where context, physical/social energy are separate, and the optional renderer inspects locations, roads, NPC positions, and supplied routes without mutating the world.

## `persistence` — durable world state

**Owns:** SQLite schema/versioning, save/load, schema migration, validation, RNG continuation, agent state, relationship dimensions, and immutable event history.

**Entry points:**

- `src/playing_god/persistence/sqlite_store.py` — `save_world()`, `load_world()`, schema version 5, and persistence errors.
- `scripts/run_simulation.py` — create/load/run/save command line workflow.
- `scripts/inspect_agent.py` — manual persisted-agent inspection.

**Focused tests:** `tests/test_persistence.py`, plus split-run checks in `tests/test_reproducibility.py`.

**Important boundary:** A persisted restart must match an uninterrupted seeded run. Schema changes require an explicit migration and round-trip/continuation coverage.

## `tests-fixtures` — behavioral contracts

**Owns:** deterministic and persistence regression expectations.

**Entry points:**

- `tests/fixtures/phase1_seed_1947.json` — frozen Phase-1 structured snapshot.
- `tests/fixtures/report_1947.txt` — frozen report output.
- `tests/test_reproducibility.py` — seed and split-run contracts.

Fixtures are contracts, not generated output to refresh casually. Determine whether code or fixture intent is wrong before updating either.

## `research-docs` — thesis direction and phase intent

**Owns:** project vision, permanent research constraints, milestone definitions, and accepted future directions. These documents guide scope but do not override implemented source and tests.

**Entry points:**

- `docs/the-playing-god-master-agent-brief-v0.3.md` — canonical long-term handoff.
- `docs/the-playing-god-project-brief-v0.2.3-spatial-mobility.md` — spatial/mobility requirements.
- `docs/the-playing-god-project-brief-v0.2.4-perception-belief-intervention.md` — perception, prayer, and intervention direction.
- `docs/memory-implementation.md` — coding-agent memory principles and staged infrastructure.

## `coding-agent-memory` — navigation and rationale

**Owns:** stable agent rules, this subsystem map, concise current state, and significant engineering decisions/failures.

**Entry points:** `AGENTS.md`, `.agent/memory/CURRENT.md`, `.agent/memory/decisions.md`.

**Important boundary:** This layer is manually maintained, dependency-free supporting infrastructure. It is not simulation state, a runtime dependency, or an exhaustive activity log.

## Planned but not implemented

Phase 4 satisfies the master brief's exit condition. The next research-facing integration is Phase 5 perception/belief/intervention, beginning with distinct world truth, observation, perception, and belief state from V0.2.4. Later phases cover society and institutions, generations, culture, discovery, and recursive simulation. External code graphs, semantic memory, CI/CD, MLOps, containers, and cloud infrastructure remain deferred until an actual bottleneck or operational requirement exists.
