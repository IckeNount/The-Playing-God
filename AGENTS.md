# Playing God Coding-Agent Rules

## Project identity

The Playing God is a Master of Computer Engineering thesis and deterministic artificial-society simulator. The research goal is to generate, persist, inspect, reproduce, and compare long-term emergent behavior on modest hardware. Supporting infrastructure must remain secondary to simulation validity.

## Stable design laws

- Simulation before spectacle; causal mechanisms before scripted outcomes.
- Reproducibility before realism. The same code, seed, configuration, and schema must produce the same result.
- The simulation must work without an LLM API. LLMs may explain or express outcomes but never silently decide causal truth.
- Keep the full universe out of LLM context. Retrieve only the state needed for the task.
- Prefer deterministic, inspectable, local mechanisms and minimal dependencies.
- Preserve verified behavior unless an intentional migration is approved.
- Agents may evolve possibilities inside the world but may not rewrite the immutable simulation kernel.
- Make scientific claims narrower than the fictional world; do not infer consciousness, souls, free will, or supernatural causation from behavior.
- Stop when the current phase objective is met. Do not improve unrelated systems.

## Source of truth and memory order

Source code, tests, and Git (when available) are current truth. Memory is navigation and rationale; stale memory never overrides the repository.

At the start of implementation work:

1. Read this file.
2. Read `.agent/memory/CURRENT.md`.
3. Use `docs/PROJECT_MAP.md` to identify the owning subsystem and focused tests.
4. Use targeted symbol or text search before opening large files.
5. Read only the source needed for the change.

After meaningful work, update only the state or rationale future agents would otherwise rediscover: the current milestone, an important decision or rejected approach, a known blocker/root cause, and the next logical task. Do not log routine searches, reads, minor edits, or agent chatter.

## Direct execution

For low-risk, reversible work affecting roughly five files or fewer, proceed from an approved brief directly to focused inspection, implementation, focused tests, necessary regression tests, memory update, and one final human review. Do not add specs, implementation plans, architecture proposals, or approval checkpoints unless risk or material ambiguity requires them.

## Verification

- Tests use `unittest`; the package uses a `src` layout.
- Focused test: `PYTHONPATH=src python3 -m unittest tests.test_<area> -v`
- Full regression: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- Simulation entry point: `python3 scripts/run_simulation.py`
- Run focused tests first. Run the full suite when a subsystem boundary or shared state changes.
- Memory tooling and documents must never be imported by the simulation or change simulation outcomes.
- Browser visual checks are opt-in and run only when explicitly requested.

## Scope and resource policy

- Do not scan the full repository without a concrete reason.
- Do not duplicate detailed knowledge across this file, `PROJECT_MAP.md`, and episodic memory.
- Do not introduce databases, services, frameworks, semantic indexes, containers, or deployment infrastructure without a measured need the current stack cannot meet.
- Keep the system usable on weak hardware and avoid speculative abstractions.
- The canonical long-term vision is `docs/ROADMAP.md`; `docs/STATUS.md` records current progress, and `docs/phases/` refines individual milestones.
- Documents under `docs/research/` preserve human-review-gated directions. They do not authorize implementation or change the current phase unless `docs/STATUS.md` explicitly says so.
