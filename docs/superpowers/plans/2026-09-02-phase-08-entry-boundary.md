# Phase 8.0 Entry Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open Phase 8 with a verified, behavior-preserving ownership boundary and no speculative runtime machinery.

**Architecture:** Keep the current simulation kernel unchanged. Record the approved milestone in repository status and engineering memory, while assigning future civilization registries and validation to a focused domain module only when 8A introduces real models.

**Tech Stack:** Python 3, `unittest`, SQLite, Markdown, Git.

## Global Constraints

- Preserve the current RNG call order and all Phase 7 behavior.
- Do not add Phase 8 runtime models, tables, actions, or abstractions during 8.0.
- Treat `src/playing_god/core/world.py` as orchestration, not the future owner of registry and validation logic.
- Keep recurrence detection deferred to Phase 9.
- Stop before Phase 8A.

---

### Task 1: Record and verify the Phase 8 entry boundary

**Files:**

- Modify: `docs/STATUS.md`
- Modify: `.agent/memory/CURRENT.md`
- Verify: `src/playing_god/core/decision.py`
- Verify: `src/playing_god/core/institution.py`
- Verify: `src/playing_god/core/culture.py`
- Verify: `src/playing_god/core/world.py`
- Verify: `src/playing_god/persistence/sqlite_store.py`
- Verify: `src/playing_god/core/counterfactual.py`

**Interfaces:**

- Consumes: the approved `docs/phases/phase-08-development-open-ended-civilization.md` brief and the Phase 7 implementation at commit `551841d`.
- Produces: repository status declaring Phase 8 active with 8.0 complete, plus a durable ownership decision for the first code-bearing milestone, 8A.

- [x] **Step 1: Update the canonical status**

  Set the current phase to `Phase 8 — In Progress`, state that 8.0 verified the schema-v17 and 197-test baseline, and add a Phase 8 progress table marking only 8.0 complete while 8A–8G remain planned.

- [x] **Step 2: Update concise engineering memory**

  Record that the Phase 8 brief is approved, 8.0 changed no runtime behavior, and 8A should introduce the smallest concrete civilization-domain owner rather than an empty framework.

- [x] **Step 3: Run focused behavior-preservation tests**

  Run:

  ```bash
  PYTHONPATH=src python3 -m unittest tests.test_reproducibility tests.test_persistence tests.test_counterfactual -v
  ```

  Expected: all focused tests pass with no fixture or snapshot changes.

- [x] **Step 4: Run the full pre-Phase-8 regression suite**

  Run:

  ```bash
  PYTHONPATH=src python3 -m unittest discover -s tests -q
  ```

  Expected: `Ran 197 tests` followed by `OK`.

- [x] **Step 5: Verify and commit the milestone**

  Run:

  ```bash
  git diff --check
  git status --short
  ```

  Review only the two milestone-state files and this execution record, then commit them with:

  ```bash
  git add docs/STATUS.md .agent/memory/CURRENT.md docs/superpowers/plans/2026-09-02-phase-08-entry-boundary.md
  git commit -m "docs: open phase 8 entry boundary"
  ```
