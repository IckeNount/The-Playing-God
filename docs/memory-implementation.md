# THE PLAYING GOD — Layered Coding-Agent Memory Implementation

**Purpose:** Reduce repeated codebase analysis, preserve architectural reasoning across coding-agent sessions, and keep token usage proportional to the task.

**Status:** Supporting engineering infrastructure for the thesis project.  
**Scope:** Coding-agent memory + retrieval now; CI/CD, DevOps, and MLOps only where justified later.

---

## 1. Core Principle

The coding agent must not re-read or re-analyze the whole repository every session.

Use progressive retrieval:

```text
RULES
→ PROJECT MAP
→ STRUCTURAL GRAPH
→ EXACT SYMBOLS
→ ENGINEERING MEMORY
→ SOURCE + TESTS
```

Memory helps the agent navigate and recover rationale.

```text
Source code + Git + tests = current truth.
```

Never allow stale memory to override the repository.

---

## 2. Layered Memory System

### M1 — Constitution

Create:

```text
AGENTS.md
```

Keep compact.

Contains only stable information:

```text
project identity
thesis boundary
stable design laws
coding-agent operating rules
testing policy
token/resource policy
overengineering restrictions
memory navigation rules
```

Do not store implementation history here.

---

### M2 — Project Map

Create:

```text
docs/PROJECT_MAP.md
```

Purpose:

```text
show what each subsystem owns
identify major entry points
show important interfaces
describe dependency direction
```

Example:

```text
core/          simulation engine
spatial/       location + mobility
social/        exposure + interaction + relationships
persistence/   SQLite state + event persistence
experiments/   reproducible and counterfactual runs
analysis/      metrics and research outputs
```

Do not duplicate source documentation.

---

### M3 — Structural Code Memory

Integrate:

```text
Graphify
+
Serena / LSP-level symbol retrieval
```

Responsibilities:

```text
Graphify
→ module relations
→ dependency graph
→ calls / imports
→ architectural structure

Serena
→ definitions
→ exact symbols
→ references
→ callers
→ targeted code retrieval
```

Preferred retrieval flow:

```text
task
→ PROJECT_MAP subsystem
→ Graphify structural query
→ Serena symbol/reference query
→ open minimum necessary source
```

Avoid whole-repository embeddings for ordinary code navigation.

---

### M4 — Engineering Episodic Memory

Create:

```text
.agent/
└── memory/
    ├── CURRENT.md
    ├── decisions/
    ├── failures/
    └── milestones.jsonl
```

#### CURRENT.md

Contains only current working context:

```text
current phase / milestone
recent completed work
active architectural concern
known failing test or blocker
next logical task
```

Keep it disposable and short.

#### Persistent events

Record only significant engineering events:

```text
architecture decision
important bug and root cause
failed implementation worth avoiding
new invariant
schema change
research assumption
milestone completion
major dependency introduction/removal
```

Example:

```yaml
type: architecture_decision
area: mobility
decision: movement remains event-driven
reason: preserve determinism and weak-hardware performance
avoid:
  - per-frame NPC decision loops
affected:
  - src/playing_god/spatial/
  - tests/test_mobility.py
commit: abc123
```

Do not log routine file reads, searches, minor edits, or agent chatter.

---

### M5 — Semantic Memory

Add only when M1–M4 are insufficient.

Possible indexed material:

```text
architecture decisions
project briefs
research notes
important bugs
design rationale
major experiment findings
```

Use semantic retrieval for questions such as:

```text
Why was frame-based simulation rejected?
Which previous decision relates to discovery validation?
Where did we define the historical technology-gating rule?
```

Do not treat embeddings as source-of-truth state.

---

## 3. Coding-Agent Session Protocol

Every implementation session should follow:

```text
1. Read AGENTS.md.
2. Read .agent/memory/CURRENT.md.
3. Identify target subsystem through PROJECT_MAP.md.
4. Query structural memory only if needed.
5. Query exact symbols/references before opening large files.
6. Read only source required for the task.
7. Implement the smallest valid change.
8. Run focused tests first.
9. Run broader regression tests only when boundaries changed.
10. Update engineering memory only if something significant changed.
11. Leave CURRENT.md with the next useful state.
```

The agent must prefer retrieval over rediscovery.

---

## 4. Token and Resource Policy

### Context policy

```text
small bootstrap context
→ retrieve only task-relevant architecture
→ retrieve only task-relevant code
→ discard unrelated context
```

### Agent rules

- Do not scan the entire repository without a concrete reason.
- Do not reopen files already summarized unless source verification is required.
- Do not create documentation for trivial code.
- Do not duplicate knowledge across AGENTS.md, PROJECT_MAP.md, and episodic memory.
- Do not introduce a new database, framework, service, or agent-memory platform unless an existing layer fails measurably.
- Prefer deterministic local tooling.
- Keep the system usable on weak hardware.

---

## 5. Testing Policy

Every memory-related implementation must remain secondary to simulation correctness.

Minimum tests:

```text
focused unit tests
existing regression suite
memory parser / schema tests if structured memory is introduced
Git diff sanity check
```

Memory tooling must never change simulation outcomes.

If a memory integration fails or is unavailable:

```text
coding agent
→ falls back to PROJECT_MAP
→ targeted source search
→ source + tests remain fully functional
```

No memory layer may become a runtime dependency of the simulated world.

---

## 6. Minimal CI/CD Layer

Consider after the memory layers stabilize.

Recommended CI:

```text
Pull Request
↓
ruff / formatting check
↓
pytest focused + regression
↓
determinism test
↓
SQLite save/load round-trip
↓
short simulation smoke run
↓
merge allowed
```

Long simulation regressions should run on a scheduled or release workflow rather than every tiny commit.

Possible later CD only when there is something real to deploy:

```text
API / dashboard / experiment service
→ Docker image
→ GitHub Actions
→ versioned container artifact
```

Do not create deployment infrastructure for a local-only thesis engine.

---

## 7. Future DevOps

Introduce only when operational requirements exist.

Possible progression:

```text
Docker
→ reproducible runtime

GitHub Actions
→ automated validation / delivery

Container registry
→ versioned deployable artifacts

Cloud runner
→ simulations too large for local hardware
```

Avoid until justified:

```text
Kubernetes
Terraform
microservices
distributed queues
complex observability stacks
```

---

## 8. Future MLOps

MLOps begins only when the project produces actual trained models or reusable datasets.

Potential flow:

```text
simulation
→ dataset
→ feature/version definition
→ training
→ evaluation
→ model artifact
```

Recommended first addition:

```text
MLflow
```

Track:

```text
world seed
Git commit
simulation config
schema version
dataset version
model parameters
metrics
artifacts
```

Add DVC only if datasets/models become too large or important for normal Git workflows.

ML tooling must remain optional. The simulation must still function with no model server and no API key.

---

## 9. Reproducibility Metadata

Every important simulation or ML experiment should eventually record:

```yaml
run_id:
git_commit:
world_seed:
config_hash:
schema_version:
dependency_lock_hash:
simulation_days:
experiment_type:
metrics:
```

Target invariant:

```text
same code
+ same seed
+ same config
+ same schema
→ reproducible run
```

This is part of the thesis methodology, not merely DevOps hygiene.

---

## 10. Overengineering Guardrails

Do not implement a layer merely because it sounds production-grade.

A new infrastructure component must answer:

```text
What measurable problem exists now?
Why can the current stack not solve it?
What is the smallest implementation that solves it?
What new maintenance cost does it introduce?
Does it improve thesis reproducibility, agent efficiency, or research validity?
```

If those answers are weak, defer it.

---

## 11. Implementation Order

```text
M1  AGENTS.md
↓
M2  PROJECT_MAP.md
↓
M3  Graphify + Serena
↓
M4  engineering episodic memory
↓
M5  semantic retrieval only if needed
↓
CI reproducibility guardrails
↓
MLflow when ML experiments exist
↓
Docker/CD when deployment exists
↓
DVC/cloud infrastructure only when scale demands it
```

Do not implement every future layer in one milestone.

---

## 12. Acceptance Criteria

The memory system succeeds when:

```text
new coding-agent session
→ understands current project state without full repo scan
→ locates relevant subsystem quickly
→ retrieves exact code selectively
→ recovers important historical decisions
→ avoids previously rejected approaches
→ performs focused implementation
→ verifies changes through tests
→ leaves concise state for the next session
```

Desired outcome:

```text
less repo re-analysis
less token consumption
less architectural drift
fewer repeated mistakes
more reproducible development
```

---

## Thesis Compass

This is supporting infrastructure, not the research subject.

**The Playing God remains a Master of Computer Engineering thesis about a reproducible artificial society in which autonomous agents, social and spatial interactions, persistent state, causal history, evolving civilization, and sparse intervention produce measurable divergent trajectories.**

The layered coding-agent memory system solves a separate engineering problem:

```text
growing research codebase
→ repeated agent rediscovery
→ token waste + inconsistent decisions

layered persistent memory
→ selective retrieval
→ preserved engineering rationale
→ faster and more reliable thesis development
```

---

## Canonical Engineering Pattern

```text
RULES
= what must remain true

MAP
= where systems belong

GRAPH
= how systems connect

SYMBOLS
= exact code relevant now

EPISODES
= why important decisions happened

SEMANTIC MEMORY
= retrieve older meaning when exact lookup is insufficient

GIT + TESTS
= current truth

CI
= continuously verify truth

MLOPS
= reproduce data/model experiments when ML exists

DEVOPS
= operate/deploy the system only when operation becomes necessary
```

**Build memory to reduce rediscovery, not to create another system that itself needs remembering.**
