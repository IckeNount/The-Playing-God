# Current Engineering State

**Updated:** 2026-08-21

## Current milestone

The coding-agent memory foundation (M1/M2/M4) is installed. Phase 4 now has weighted locations and roads, Dijkstra routing, direct travel with structured event data, node-based co-location exposure, seeded interaction resolution, and persisted agent spatial state.

## Recent completed work

- Added stable coding-agent rules and a retrieval-first session protocol.
- Mapped current subsystem ownership, entry points, focused tests, and dependency boundaries.
- Added concise episodic decision/failure memory without introducing a runtime dependency or external service.
- Existing standalone location, routing, mobility, exposure, and interaction tests pass. These components are not yet connected to daily world progression.
- SQLite schema version 3 persists `current_location` and `destination`; version 1/2 worlds load with backward-compatible `home`/`None` defaults.

## Active architectural concern

Phase 4 components are not yet an end-to-end causal system because `World.run()` does not invoke mobility or exposure. `choose_destination()` also uses 0–100 energy/stress thresholds while real `Agent` values are normalized to 0–1; correct that mismatch before integration. Preserve seeded RNG order and save/load equivalence.

## Known failures and blockers

- Full suite after spatial persistence: 36 tests run, 35 pass, 1 fails. `test_phase2_matches_phase1_seed_1947_fixture` compares a frozen fixture that lacks the newer `current_location` and `destination` agent fields included by `asdict()`.
- Persistence tests emit unclosed-SQLite `ResourceWarning` messages. They do not currently fail the suite but should be diagnosed separately.
- This workspace has no `.git` directory, so Git history, diffs, commits, and commit-linked memory are unavailable until repository metadata is restored or initialized deliberately.

## Next logical task

Correct destination utility to use real normalized agent state, provide a small fixed weighted map, and connect deterministic need/goal/obligation-driven travel to daily world progression. Add exposure and encounter consequences only after movement is causal and reproducible. Resolve the frozen-fixture contract explicitly rather than silently regenerating it.
