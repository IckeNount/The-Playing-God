# The Playing God

**A reproducible artificial-society and counterfactual-history simulation for a Master of Computer Engineering thesis.**

The Playing God explores how autonomous artificial individuals develop divergent lives through the interaction of internal state, resources, relationships, geography, memory, uncertainty, and sparse external intervention.

Rather than scripting stories, the project builds a causal simulation engine and asks whether complex histories can emerge from a relatively small set of understandable computational mechanisms.

> **The developer defines the possibility space. The agents create the history inside it.**

---

## Research Question

> How do small differences in artificial agents, social conditions, environmental constraints, historical events, and indirect interventions propagate through a simulated society and produce different long-term trajectories?

The project is designed as an **experimental platform**, not as a claim to accurately reproduce human psychology, consciousness, or real-world history.

---

## Core Model

```text
AGENT
= traits
+ capabilities
+ needs
+ state
+ goals
+ resources
+ memory
+ relationships
+ beliefs

DECISION
= state
+ context
+ expected outcomes
+ uncertainty

LIFE
= decisions
→ events
→ consequences
→ memories
→ changed state
→ future decisions

SOCIETY
= agents
+ relationships
+ geography
+ institutions
+ economy
+ information

HISTORY
= causal events
+ feedback loops
+ path dependence

GOD
= sparse indirect intervention
```

The simulation engine decides **what happens**.

Optional generative AI may later decide **how those events are expressed in language**.

---

## Current State

### Phase 1 — Ten Invisible Humans ✅

- deterministic seeded worlds
- autonomous NPC agents
- traits and behavioral drives
- needs and goals
- weighted stochastic decisions
- evolving state
- structured life events
- divergent trajectories

### Phase 2 — Persistent World ✅

- SQLite persistence
- save / load
- deterministic continuation
- persistent agents
- relationships
- event history
- world metadata

### Phase 3 — Social World ✅

- explicit social relationships
- multidimensional social state
- cross-agent effects
- social graph inspection
- interaction-driven state changes

### Phase 4 — Spatial Mobility & Encounters 🚧

Implemented foundations include:

- locations and roads
- weighted spatial graph
- route calculation
- destination selection
- travel state
- exposure detection
- interaction resolution

Current integration work is connecting movement, co-location, encounters, social consequences, and persistence into one continuous world lifecycle.

---

## Spatial Causality

Relationships are intended to emerge from actual opportunities for contact rather than appearing randomly.

```text
need / goal / obligation
        ↓
destination
        ↓
movement
        ↓
co-location
        ↓
exposure
        ↓
interaction
        ↓
familiarity
        ↓
relationship
        ↓
social history
```

This makes geography part of the causal simulation rather than merely a visualization layer.

---

## Determinism & Counterfactuals

Every world is initialized with a deterministic seed.

```text
Seed 1947
+ no intervention
→ baseline history
```

The same world can later be rerun with a controlled change:

```text
Seed 1947
+ intervention at Day 100
→ alternative history
```

Comparing the resulting trajectories allows the project to study **counterfactual effects and butterfly-like propagation** without confusing intervention effects with unrelated random initialization.

---

## Architecture

```text
src/playing_god/
├── core/
│   ├── agent.py
│   ├── decision.py
│   ├── events.py
│   ├── exposure.py
│   ├── mobility.py
│   ├── rng.py
│   ├── social.py
│   ├── spatial.py
│   └── world.py
│
├── persistence/
│   └── sqlite_store.py
│
└── visualization/
    └── social_graph.py

scripts/
├── run_simulation.py
├── inspect_agent.py
└── show_social_graph.py

tests/
docs/
```

The simulation core is intentionally kept independent from future renderers, LLM providers, cloud infrastructure, and game engines.

---

## Run a World

Create a deterministic universe and simulate 365 days:

```bash
python3 scripts/run_simulation.py \
  --seed 1947 \
  --days 365 \
  --report
```

Continue an existing universe:

```bash
python3 scripts/run_simulation.py \
  --load data/worlds/world_1947.db \
  --days 30 \
  --report
```

Generated SQLite worlds are local runtime state and are not committed to the repository.

---

## Tests

Run the test suite from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Reproducibility tests protect an important research invariant:

> A seeded simulation should produce reproducible results, and a persisted restart should continue consistently with an uninterrupted run.

---

## Design Laws

1. Simulation before visualization.
2. Emergence before scripted content.
3. Important outcomes must be causally traceable.
4. Randomness selects among plausible possibilities rather than inventing impossible ones.
5. Relationships require causal exposure.
6. Events form history rather than disposable logs.
7. Counterfactual experiments must remain reproducible.
8. Prefer understandable algorithms before opaque models.
9. The simulation must work without an LLM API.
10. Weak hardware remains a supported target.
11. NPCs may evolve civilization-level possibilities, but not rewrite the simulation kernel.
12. Scientific claims remain narrower than the fictional world.

---

## Long-Term Direction

The thesis core may eventually support:

```text
perception
→ belief
→ intervention
→ counterfactual comparison

individual development
→ generations
→ cultural inheritance
→ institutions
→ discoveries
→ artificial history
```

Potential later systems include:

- belief and faith
- indirect player intervention
- institutions
- economy
- migration
- collective behavior
- generations and inheritance
- cultural transmission
- technological discovery
- causal event graphs
- counterfactual timeline comparison
- lightweight ML analysis
- optional generative language
- 2D visualization

These are research directions, not claims about the current implementation.

---

## What This Project Is Not

The Playing God is not primarily:

```text
an LLM swarm
a chatbot world
a city-building game
a real-world prediction engine
a consciousness simulator
a claim to model human psychology accurately
```

It is primarily:

> **A reproducible computational laboratory for studying how autonomous artificial lives interact to create social and historical trajectories, and how small interventions can redirect those trajectories.**

---

## Thesis Boundary

Psychology, morality, belief, attraction, status, culture, and social behavior inside the simulation are computational abstractions.

The project does not claim to:

- predict specific real people
- diagnose psychological conditions
- prove or simulate consciousness
- prove supernatural causation
- reproduce real societies exactly
- predict real historical events

The research target is the **behavior of the computational system itself**.

---

## Documentation

The `docs/` directory preserves the evolving research architecture, project briefs, subsystem boundaries, implementation decisions, and future phase definitions.

Start with:

```text
docs/PROJECT_MAP.md
docs/the-playing-god-master-agent-brief-v0.3.md
```

---

## License

Licensed under the **Apache License 2.0**.

See [`LICENSE`](LICENSE).

---

## Final Principle

> **Do not simulate everything. Define a small set of causal mechanisms clearly enough that unexpected lives and histories can emerge from their interaction.**

First, make the invisible people live.

Then observe what kind of world they create.
