# Phase 6 Exit Closure Plan

**Plan revision:** `v2.0.0-minimal`
**Phase label:** `Phase 6 — Exit Closure`
**Execution:** Inline only; no subagents
**Status:** Implemented and verified

## Goal

Close the four verified Phase 6 review gaps without starting Phase 7 or adding speculative architecture.

## Anti-overengineering rules

- Use existing models, events, persistence, and visualization dependencies.
- Add no framework, service, scheduler, dependency, generic provenance system, or RNG draw.
- Keep SQLite schema version 11 unless a failing test proves a migration is unavoidable.
- Change only files required by a failing test or confirmed broken command.
- One focused test per defect; retain the existing full-suite check.

## Implementation

### 1. Freeze participation traces

Files: `src/playing_god/core/collective.py`, `src/playing_god/core/world.py`, `tests/test_collective.py`

- Record the evidence and influencer identifiers used when participation is decided, using the existing persisted participation event format.
- Build later traces and cascade depth from that recorded decision-time data, not current trust values.
- Test that changing trust after participation does not change the trace or collective snapshot.

### 2. Prove the real scarcity chain

File: `tests/test_collective.py`

- Update the Phase 6 integration scenario so an agent actually attempts a job hunt when no vacancy exists.
- Verify the failed attempt produces unemployment evidence, trusted diffusion, selective participation, SQLite reload equality, and deterministic continuation.

### 3. Repair persistence cleanup

Files: `src/playing_god/persistence/sqlite_store.py`, `tests/test_persistence.py`

- Explicitly close SQLite connections after save/load; the connection context manager commits or rolls back but does not close.
- Verify repeated save/load operations produce no resource warnings.

### 4. Restore the existing social graph command

Files: `scripts/show_social_graph.py` and, only if required, `src/playing_god/visualization/social_graph.py`

- Replace the nonexistent `SQLiteStore` usage with the existing `load_world()` function.
- Keep the current NetworkX/Matplotlib visualization; do not build a frontend in Phase 6 closure.
- Add a lightweight non-browser check that the command imports and accepts a database path.

## Verification and release gate

- Run the focused collective, persistence, and visualization checks.
- Run the full test suite, compilation check, and whitespace/diff check.
- Update `docs/STATUS.md`, `docs/PROJECT_MAP.md`, and `.agent/memory/CURRENT.md` only after all checks pass.
- Label the completed implementation `phase-6-closed` (release/tag naming), while keeping this plan revision `v2.0.0-minimal`.
- Phase 7 remains untouched until the human exit review accepts these results.

## Done means

Historical traces remain unchanged, the scarcity cascade is exercised end-to-end, database handles close cleanly, the existing graph viewer runs, and all tests pass.
