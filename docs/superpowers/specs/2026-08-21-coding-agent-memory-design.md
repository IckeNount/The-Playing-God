# Coding-Agent Memory Foundation Design

**Date:** 2026-08-21

**Status:** Approved design

## Purpose

Implement the repository-native foundation described by `docs/memory-implementation.md` so a new coding-agent session can recover stable project rules, locate the relevant subsystem, retrieve current engineering context, and preserve significant decisions without scanning the full repository.

This milestone implements M1 (constitution), M2 (project map), and M4 (engineering episodic memory). M3 external structural tools, M5 semantic retrieval, CI/CD, DevOps, and MLOps remain deferred until a measurable need justifies them.

## Constraints

- Source code, tests, and Git—when Git metadata exists—remain the current truth.
- Memory must never be imported by or become a runtime dependency of the simulation.
- The implementation uses only the Python standard library.
- Retrieval remains deterministic and usable on weak hardware.
- Memory records cover only significant engineering events, not routine activity.
- Existing simulation behavior is outside this change and must not be altered.

## Architecture

### M1: Constitution

Create `AGENTS.md` as the compact bootstrap document for coding agents. It contains the thesis boundary, permanent design laws, operating rules, testing commands, resource constraints, and the required memory navigation sequence. It points to detailed project and episodic memory instead of duplicating them.

### M2: Project map

Create `docs/PROJECT_MAP.md` from the current repository. Each subsystem section states its ownership, entry points, important interfaces, tests, and dependency direction. The map also identifies planned phase boundaries without claiming that unimplemented systems exist.

The map is optimized for targeted retrieval: `scripts/memory.py context <area>` can select a named subsystem section without loading the entire map.

### M4: Episodic engineering memory

Create the following structure:

```text
.agent/memory/
├── CURRENT.md
├── README.md
├── decisions/
├── failures/
└── milestones.jsonl
```

`CURRENT.md` contains only the current phase, recent completed work, active concern, known failures or blockers, and next logical task. It records the pre-existing Phase-1 fixture mismatch and SQLite resource warnings found during baseline verification.

Decision and failure records are individual JSON objects. Milestones are append-only JSON Lines. All structured records share these fields:

```text
id          stable category-prefixed identifier
type        architecture_decision | failure | milestone
date        ISO 8601 calendar date
area        project-map subsystem key
summary     concise description of the significant event
affected    non-empty list of repository-relative paths
```

Architecture decisions additionally require `decision`, `reason`, and `avoid`. Failures additionally require `failure`, `root_cause`, `resolution`, and `avoid`. Milestones require no category-specific fields beyond the shared fields. `avoid` is a list and may be empty only when no rejected approach exists.

## Command-Line Interface

Create `scripts/memory.py` with four command families:

- `context [area]` prints `AGENTS.md`, `CURRENT.md`, and either the requested project-map section or the project-map index.
- `search <query>` performs case-insensitive literal search across repository memory artifacts and reports repository-relative file names with line numbers.
- `validate [--root PATH]` verifies required paths, structured record schemas, unique IDs, JSON/JSONL syntax, and repository-relative affected paths.
- `record decision|failure|milestone ...` validates a record before writing it. Decisions and failures use an ID-derived JSON filename and refuse to overwrite an existing record. Milestones append exactly one JSON object and newline.

The CLI discovers the project root from its own location by default. `--root` allows tests to operate on isolated temporary repositories.

## Data Flow

At session start, the agent reads `AGENTS.md`, then `CURRENT.md`, then uses the project map to identify the target area. The CLI provides this compact bootstrap through `context`. Exact source retrieval continues through targeted `rg` and direct file inspection because Graphify and Serena are not part of this milestone.

When significant work occurs, `record` creates a validated episodic entry. `validate` provides a deterministic health check. Memory never writes to simulation source, SQLite world files, or runtime state.

## Error Handling

- Missing required memory paths produce a descriptive validation error and nonzero exit status.
- Malformed JSON, malformed JSON Lines, unknown record types, missing fields, duplicate IDs, invalid dates, and absolute or parent-traversing affected paths are rejected.
- `context` rejects unknown project-map areas and lists valid keys.
- `record` creates required category directories when the rest of the memory foundation exists, but refuses to overwrite an existing decision or failure.
- A memory-tooling failure leaves normal source search, tests, and simulation execution available.

## Testing

Add `tests/test_memory.py` using `unittest` and temporary directories. Tests cover:

- validation of a complete memory tree;
- reporting missing required files;
- rejecting malformed and schema-invalid structured records;
- detecting duplicate record IDs;
- retrieving only the requested project-map section;
- finding memory text with file and line information;
- recording each event category;
- refusing decision/failure overwrite;
- preserving valid JSON Lines after multiple milestone appends.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.test_memory -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/memory.py validate
python3 scripts/run_simulation.py --seed 81947 --days 2 --db /tmp/playing-god-memory-smoke.db
```

The full regression suite currently has one known pre-existing failure: `test_phase2_matches_phase1_seed_1947_fixture`. SQLite resource warnings also appear in persistence tests. This milestone records those facts and does not change their behavior.

## Acceptance Criteria

- A new session can obtain rules, current state, and a relevant subsystem map without scanning the whole repository.
- Significant decisions, failures, and milestones have deterministic local storage with schema validation.
- Focused retrieval works without external services or dependencies.
- Invalid memory fails clearly and cannot change simulation outcomes.
- Memory tests pass, existing regression results do not worsen, validation succeeds, and the simulation smoke run succeeds.

## Deferred Work

- Graphify and Serena integration awaits available tooling and a demonstrated navigation bottleneck.
- Semantic indexing awaits evidence that literal episodic retrieval is insufficient.
- CI/CD awaits a Git repository and stabilized memory workflow.
- MLflow, DVC, containers, cloud infrastructure, and deployment remain outside the current thesis-support milestone.
