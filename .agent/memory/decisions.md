# Engineering Decisions and Failures

Record only durable rationale or failures future agents would otherwise rediscover. Source and tests remain current truth.

## 2026-08-21 — Keep coding-agent memory repository-native

**Area:** coding-agent-memory

**Decision:** Use four small Markdown entry points—`AGENTS.md`, `docs/PROJECT_MAP.md`, `CURRENT.md`, and this file—for the initial M1/M2/M4 memory foundation.

**Reason:** The repository is small enough for targeted text retrieval. Manual, dependency-free memory solves session rediscovery without creating a second application to maintain.

**Rejected for now:** Custom schemas, record classes, validation frameworks, ID machinery, a large CLI, semantic/vector storage, Graphify/Serena integration, and separate infrastructure databases. Reconsider only after a measurable retrieval or consistency problem appears.

**Affected:** `AGENTS.md`, `docs/PROJECT_MAP.md`, `.agent/memory/`

## Existing invariant — deterministic simulation truth

**Area:** core-simulation, persistence

**Decision:** Causal randomness comes from the world's seeded RNG, and a saved/reloaded continuation must equal an uninterrupted run.

**Reason:** Reproducibility and causal traceability are thesis requirements. Coding-agent memory may explain this invariant but must never participate in runtime behavior.

**Avoid:** Global randomness, hidden LLM decisions, or memory-derived simulation state.

**Affected:** `src/playing_god/core/rng.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_reproducibility.py`, `tests/test_persistence.py`

## 2026-08-21 — Persist only current agent spatial state first

**Area:** spatial-mobility, persistence

**Decision:** SQLite schema version 3 adds `current_location` and nullable `destination` to the existing `agents` table. Version 1/2 databases load with `home` and `None` defaults and migrate on their next save.

**Reason:** Agent position must survive restarts before movement can join the daily world loop. These are the only Phase 4 spatial fields currently represented by `Agent`.

**Rejected for now:** Separate location, road, position, travel-event, or encounter tables before those concepts have an integrated runtime owner.

**Affected:** `src/playing_god/persistence/sqlite_store.py`, `tests/test_persistence.py`

## Existing invariant — preserve legacy affinity during social expansion

**Area:** social

**Decision:** `Agent.relationships` remains the signed affinity consumed by existing Phase-2 behavior; `SocialGraph` adds explicit relationship dimensions and is rebuilt from agent state.

**Reason:** This allows richer social modeling without silently changing established decision behavior.

**Avoid:** Treating the NetworkX graph as a drop-in replacement before all consumers and persistence paths have an intentional migration.

**Affected:** `src/playing_god/core/agent.py`, `src/playing_god/core/social.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`

## 2026-08-21 — Integrate one event-driven movement per daily action

**Area:** spatial-mobility, core-simulation

**Decision:** Each NPC selects its existing daily action, chooses a destination from normalized needs plus that action/goal, and travels by Dijkstra route before applying the action. New and loaded worlds rebuild the same six-location fixed map.

**Reason:** This adds causal movement without frame loops or new RNG draws and provides the physical state required for later exposure detection.

**Rejected for now:** Procedural maps, frame-based movement, A*, and calibrated default money/energy travel costs. The travel engine accounts for edge costs, but the V1 shared map keeps them neutral until research assumptions justify values.

**Compatibility:** Travel events are excluded from the legacy 30-event crisis window, and the frozen Phase-1 fixture compares a non-spatial projection. This prevents logging frequency from changing prior causal behavior.

**Affected:** `src/playing_god/core/spatial.py`, `src/playing_god/core/mobility.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_spatial.py`, `tests/test_mobility.py`, `tests/test_reproducibility.py`

## 2026-08-21 — Exposure creates familiarity before relationships

**Area:** spatial-mobility, social

**Decision:** After all daily movement, node co-location creates exposures. A deterministic RNG derived from world seed and day resolves those opportunities, and each successful interaction adds `0.04` familiarity in both directions.

**Reason:** A separate day-derived stream keeps encounters reproducible across restarts without perturbing the established core RNG sequence. Familiarity records repeated contact while deferring stronger relationship semantics.

**Rejected for now:** Interaction without co-location, instant friendship, new encounter tables, and per-interaction long-term event logging. `last_exposures` and `last_interactions` support current-day inspection; cumulative familiarity persists in the existing relationship schema.

**Compatibility:** `Agent.relationships` remains authoritative affinity and is mirrored into `SocialGraph` before encounter updates, eliminating pre-save/load graph drift.

**Affected:** `src/playing_god/core/exposure.py`, `src/playing_god/core/world.py`, `tests/test_exposure.py`, `tests/test_persistence.py`, `tests/test_reproducibility.py`

## 2026-08-22 — Gate autonomous relationship actions by familiar exposure

**Area:** social, spatial-mobility

**Decision:** `socialize`, `help`, and `compete` select targets only from current co-location exposures, and both directed familiarity values must be at least `0.22` before stronger effects occur. A social outing may still consume the actor's ordinary outing resources when no familiar target is available, but it cannot alter another NPC.

**Reason:** Three successful `0.04` familiarity gains from the `0.10` baseline are required before ordinary interaction can become a stronger relationship event. This implements stranger → recognized stranger → acquaintance without instant friendship.

**Compatibility:** Causal targeting intentionally supersedes modern Phase-1 trajectory compatibility. The frozen fixture now tests `archive/phrase1_main.py`; the current engine retains independent deterministic, split-run, and save/load contracts.

**Affected:** `src/playing_god/core/world.py`, `tests/test_social.py`, `tests/test_reproducibility.py`

## 2026-08-22 — Let strong ties create visit movement

**Area:** spatial-mobility, social

**Decision:** A `socialize` or `help` trip may redirect from the normal cafe destination to the current location of the strongest mutually familiar positive tie. Both familiarity values must be at least `0.34` and both affinities at least `0.18`.

**Reason:** This closes the Phase 4 bidirectional loop: movement creates encounters, repeated encounters create relationships, and relationships change later movement. Deterministic strongest-tie selection avoids extra RNG draws.

**Constraints:** Low energy or high stress still selects home/park before a visit is considered. Visits use the same fixed graph, Dijkstra route, spatial state, and travel event path as ordinary movement; the target may still move later, so a visit opportunity does not guarantee interaction.

**Affected:** `src/playing_god/core/world.py`, `tests/test_mobility.py`

## 2026-08-22 — Store successful encounters in ordinary events

**Area:** social, persistence

**Decision:** Each successful interaction appends a reciprocal `interaction` event with nullable `target_id` and `location`. SQLite schema version 4 adds those fields to the existing append-only events table; schema version 3 records load with null context and migrate on save.

**Reason:** This preserves inspectable who/where history across restarts with two nullable fields and no new runtime subsystem. Only realized interactions are durable; exposures remain current-day opportunities.

**Compatibility:** Interaction events are excluded from the legacy crisis lookback so added logging frequency cannot change crisis timing. Existing event constructors and older databases default the new fields to `None`.

**Affected:** `src/playing_god/core/events.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_exposure.py`, `tests/test_persistence.py`

## 2026-08-22 — Separate physical and social energy without new randomness

**Area:** core-simulation, spatial-mobility, social, persistence

**Decision:** Keep legacy `Agent.energy` as physical energy with an explicit `physical_energy` alias, and add a separately bounded `social_energy`. Social energy affects social-action scores, social-trip cancellation, encounter probability, conversation cost, and rest/daily recovery; physical travel and work continue using physical energy.

**Reason:** This implements the Phase 4 separation law while preserving the existing energy API and RNG sequence. New agents initialize both energies from the same existing draw, then causal activity makes them diverge.

**Compatibility:** SQLite schema version 5 persists social energy. Version 1–4 worlds default it to their stored physical energy and migrate on save. Split-run, save/load, and seeded determinism remain tested.

**Affected:** `src/playing_god/core/agent.py`, `src/playing_god/core/decision.py`, `src/playing_god/core/exposure.py`, `src/playing_god/core/mobility.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`

## 2026-08-22 — Keep the spatial debug map read-only

**Area:** visualization, spatial-mobility

**Decision:** Render fixed location coordinates, roads, deterministic NPC offsets, optional route highlighting, and day labels from existing world state. The renderer accepts data and returns a Matplotlib axis; only the CLI calls `show()`.

**Reason:** This satisfies Phase 4 path-debugging requirements without placing frame state, interpolation, plotting dependencies, or mutation inside the simulation loop.

**Rejected:** Browser UI, 3D/game rendering, continuous animation, procedural layout, and renderer-owned position state.

**Affected:** `src/playing_god/visualization/spatial_map.py`, `scripts/show_spatial_map.py`, `tests/test_spatial_visualization.py`
