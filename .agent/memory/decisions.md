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

## Known failure — Phase-1 fixture shape mismatch

**Area:** tests-fixtures

**Observed:** `test_phase2_matches_phase1_seed_1947_fixture` fails because current `Agent` snapshots include `current_location` and `destination`, while the frozen Phase-1 JSON fixture does not.

**Why retained:** The failure predates the memory foundation and represents an unresolved compatibility-contract decision, not a memory regression.

**Avoid:** Regenerating the fixture merely to make the test green. Decide whether the contract should compare only Phase-1 fields or intentionally version the fixture.

**Affected:** `src/playing_god/core/agent.py`, `tests/test_reproducibility.py`, `tests/fixtures/phase1_seed_1947.json`
