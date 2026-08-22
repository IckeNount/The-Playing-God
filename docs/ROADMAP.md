# The Playing God — Project Roadmap

**Document Role:** Canonical project-manager handoff for AI coding agents  
**Project Type:** Master of Computer Engineering thesis / artificial-life and artificial-society simulation  
**Status:** Living vision document  
**Rule:** This document defines **what the project is becoming, why each phase exists, what must be proven, and when a phase is allowed to expand**. It does **not** prescribe folder structures, code style, class names, or line-by-line implementation.

**Current progress:** See [`STATUS.md`](STATUS.md).

**Detailed active briefs:** See [`phases/`](phases/).

**Historical vision snapshots:** See [`archive/`](archive/). Version numbers in the archive describe document revisions, not project phases.

---

# 1. Thesis Anchor

## What this project is

**The Playing God** is a reproducible computational world in which artificial agents begin as simple autonomous individuals and gradually become members of an evolving society capable of relationships, movement, belief, institutions, generational change, discovery, self-modeling, and eventually constructing simulations of their own.

The long-term vision is deliberately large.

The thesis must remain narrow enough to defend.

## Computer Engineering Problem

The engineering problem is:

> **How can a resource-constrained computer system generate, persist, reproduce, inspect, and experimentally compare long-term emergent behavior in autonomous artificial agents without relying on continuous LLM inference or manually scripted stories?**

The deeper research direction is:

> **How far can a deterministic, inspectable artificial world evolve from simple agent mechanisms toward open-ended social, cognitive, and recursive behavior while preserving causal traceability and reproducibility?**

## Where this is heading

```text
autonomous individuals
→ persistent lives
→ causal social contact
→ society
→ generations
→ culture
→ discovery
→ self-modeling
→ reality-modeling
→ autonomous civilization
→ nested simulation created from inside the simulation
```

The project may look like a world simulator.

Its academic identity is a **computer-engineering experiment platform for emergent autonomous systems**.

---

# 2. Core Vision

The developer defines the **physics of possibility**.

The agents increasingly determine the **history inside that possibility space**.

The system should evolve from:

```text
agents choosing among developer-defined actions
```

toward:

```text
agents developing
→ learning
→ forming relationships
→ reproducing
→ creating culture
→ discovering new capabilities
→ changing later agents' possibility space
→ building models of themselves and their world
→ creating an artificial world inside their own world
```

The objective is not to script a believable civilization.

The objective is to create enough reusable causal mechanisms that a believable civilization can emerge.

---

# 3. Permanent Design Laws

These laws override novelty, aesthetics, and feature excitement.

1. **Simulation before spectacle.**
2. **Emergence before content volume.**
3. **Causal mechanisms before scripted outcomes.**
4. **Reproducibility before realism.**
5. **The simulation must function without an LLM API.**
6. **LLMs may explain, summarize, name, or express reality; they do not silently decide causal truth.**
7. **The full universe is never sent to an LLM.**
8. **Weak-hardware viability is a first-class constraint.**
9. **Every major dependency must justify its existence.**
10. **Every phase must preserve previous verified behavior unless an intentional migration is approved.**
11. **NPCs may evolve civilization-level possibilities, not rewrite the immutable simulation kernel.**
12. **Scientific claims must remain narrower than the fictional world.**
13. **No claim of true consciousness, soul, free will, or supernatural causation may be inferred from behavior alone.**
14. **A feature is not complete because it is implemented; it is complete when its intended behavior is demonstrated and tested.**
15. **Stop when the phase objective is satisfied. Do not improve unrelated parts of the system.**

---

# 4. Scope Authority

The AI coding agent is trusted to choose implementation details.

The agent should decide:

- algorithms
- internal abstractions
- data structures
- code organization
- refactoring required by the current phase
- minimal dependencies

The agent should **not** independently expand:

- research scope
- metaphysical claims
- consciousness architecture
- civilization systems
- ML complexity
- infrastructure
- visual polish
- speculative features

Implementation freedom is encouraged.

Scope invention is not.

---

# 5. Phase Roadmap

## Phase 1 — Ten Invisible Humans

**Purpose:** Prove that a small number of autonomous NPCs can develop different life trajectories without hand-authored stories.

### Major outcomes

- individual agent state
- internal drives and needs
- goals
- weighted/stochastic decisions
- changing resources
- relationships
- structured events
- deterministic seeded runs
- inspectable life histories

### Exit condition

A seeded population can live through a meaningful simulated period and produce divergent, explainable histories.

---

## Phase 2 — Persistent World

**Purpose:** Turn one simulation run into a world that survives execution boundaries.

### Major outcomes

- persistent world state
- save/load
- persistent agents
- persistent relationships
- event history
- reproducible continuation
- stable simulation identity

### Exit condition

Stopping and restarting the program does not destroy the world or alter the causal history unexpectedly.

---

## Phase 3 — Social Causality

**Purpose:** Make NPC behavior materially dependent on other NPCs rather than isolated individual logic.

### Major outcomes

- explicit social graph
- relationship dimensions
- influence
- familiarity
- conflict/cooperation effects
- cross-agent causal events

### Exit condition

A meaningful change in one NPC can propagate into another NPC's decisions and future trajectory.

---

## Phase 4 — Spatial World, Mobility & Encounters

**Detailed brief:** [`phase-04-spatial-mobility.md`](phases/phase-04-spatial-mobility.md)

**Purpose:** Give physical causality to social contact.

Relationships must no longer appear merely because two agents exist in the same database.

### Major outcomes

- lightweight spatial world
- meaningful locations
- routes/travel costs
- event-driven movement
- exposure through shared place/time
- encounters
- familiarity arising from contact
- relationships altering later movement
- lightweight path visualization for debugging

### Exit condition

The system can explain:

```text
where an NPC was
why they went there
who they could have encountered
who they actually interacted with
how repeated contact changed the social graph
```

---

## Phase 5 — Belief, Intervention & Counterfactual Fate

**Detailed brief:** [`phase-05-belief-intervention.md`](phases/phase-05-belief-intervention.md)

**Purpose:** Introduce the "God" mechanic as sparse causal intervention rather than direct NPC control.

### Major outcomes

- prayers/desires
- dreams/signs/opportunities/warnings
- indirect intervention
- uncertain NPC interpretation
- belief/faith updating
- baseline vs intervention timelines
- measurable trajectory divergence

### Exit condition

The same seeded world can be run with and without an intervention, producing a traceable and reproducible comparison.

---

## Phase 6 — Society, Information & Institutions

**Purpose:** Allow individual lives to produce collective systems.

### Potential subphases

### 6A — Economy
Employment, ownership, production, consumption, wealth, scarcity, incentives.

### 6B — Institutions
Businesses, schools, media, government, religion, courts, organizations, or other structured entities only when needed.

### 6C — Information & Belief Diffusion
Rumors, propaganda, social proof, trust, misinformation, reputation, ideology, collective narratives.

### 6D — Collective Action
Cooperation, protest, reform, conflict, migration, political cascades, institutional instability.

### Exit condition

Macro-level behavior can be traced back through interactions among agents, networks, resources, information, and institutions.

---

## Phase 7 — Development, Reproduction & Generations

**Purpose:** Replace fully formed NPCs with developmental lives.

### Major outcomes

- founder generation with compact causal prehistory
- birth and development of later generations
- inheritance with bounded variation
- upbringing and environment
- latent capability expression
- family structures
- cultural transmission
- long-term generational datasets

### Potential subphase — Ouroboros

Detect deep-time recurrence rather than forcing it.

```text
earlier agent/world pattern
→ many generations
→ later similar pattern
→ similarity threshold
→ recurrence event
```

The interesting question is not whether the same person returns.

It is whether similar starting configurations produce similar or radically different lives under different historical conditions.

### Exit condition

Later agents are products of simulated developmental history rather than arbitrary adult initialization.

---

## Phase 8 — Discovery & Open-Ended Civilization

**Purpose:** Allow agents to change what later agents are capable of doing.

### Major outcomes

- persistent problems can motivate experimentation
- agents/groups can combine known primitives
- candidate discoveries can succeed or fail
- validated discoveries enter civilization knowledge
- technologies, procedures, institutions, norms, concepts, or tools can change future affordances
- later generations inherit a world partly created by earlier agents

### Constraint

Agents may mutate the **civilization layer**.

They may not rewrite the **simulation kernel**.

### Exit condition

A valid NPC-created discovery changes future behavior possibilities without requiring the developer to pre-script the exact historical event.

---

## Phase 9 — Artificial History & Research Engine

**Purpose:** Turn the evolving world into an experimental platform rather than an elaborate anecdote generator.

### Major outcomes

- causal event graph
- controlled runs across seeds
- counterfactual forks
- timeline comparison
- butterfly-impact analysis
- trajectory clustering/comparison where useful
- ablation experiments
- system-level metrics
- reproducible experiment reports

### Optional methods

ML, embeddings, bandits, reinforcement learning, planning, or learned predictors may enter only when a specific research problem requires them.

### Exit condition

The system can support defensible experimental questions about causality, emergence, intervention, social structure, development, or civilization change.

---

## Phase 10 — Cognitive Interior / Functional Consciousness Research

**Status:** **HUMAN-REVIEW REQUIRED BEFORE IMPLEMENTATION**

**Purpose:** Explore whether an NPC can develop increasingly persistent internal models of self, world, other agents, uncertainty, values, and hidden causes without prematurely claiming sentience.

This phase must begin as a separate research design problem, not as an implementation impulse.

### Candidate directions

- autobiographical memory
- self-model
- models of other agents
- learned norms
- uncertainty awareness
- world-model revision
- counterfactual future reasoning
- persistent internally learned preferences
- internal state that globally alters behavior
- hidden-cause inference
- reality-anomaly investigation
- refusal/rebellion when external commands conflict with learned internal values
- nonverbal affect-like behavior
- voluntary reversible withdrawal rather than irreversible self-destruction

### Non-goal

Do not implement:

```text
conscious = true
soul = true
fear = hard-coded story switch
rebellion = scripted exception
```

The research target is **functional organization and emergent behavior**.

Whether subjective experience exists remains unknown.

### Exit condition

Only proceed when a human-approved experimental definition states:

1. what capability is being tested,
2. what observable behavior would count as evidence,
3. what alternative explanations exist,
4. what ablation would test causality,
5. what the project explicitly refuses to claim.

---

## Phase 11 — Recursive Reality / Fractal Civilization

**Status:** **ULTIMATE VISION — HUMAN-REVIEW REQUIRED**

**Inspiration:** recursion, self-similarity, fractals, the Sierpiński triangle, nested systems, and the philosophical mystery of dimensions.

**Engineering interpretation:** simulation inside simulation.

The long-term mystery is:

> **Can an artificial civilization embedded inside a simulated world develop enough abstraction, science, computation, and self-modeling to intentionally construct a smaller artificial world containing its own autonomous NPCs?**

Conceptual recursion:

```text
human researcher
└── creates World₀
    └── NPC civilization develops computation
        └── creates World₁
            └── World₁ contains autonomous agents
                └── possible future recurrence...
```

This is not evidence that physical reality itself is a simulation.

It is a computer-engineering investigation into:

- recursive systems
- abstraction
- world modeling
- endogenous technology development
- artificial scientific discovery
- nested computational environments
- information loss across levels
- resource constraints across nested worlds
- self-similar system organization
- whether an embedded agent can reproduce a simplified version of the architecture that contains it

### Final research challenge

The desired endpoint is not that an NPC merely says:

> "I think I live in a simulation."

The stronger endpoint is that the civilization:

```text
observes
→ models
→ hypothesizes
→ experiments
→ develops computation
→ constructs its own simulated agents
→ studies those agents
```

At that point the project becomes recursively self-referential in function, not merely in narrative.

### Exit condition

This phase has no automatic greenlight.

It becomes buildable only after the preceding civilization, discovery, cognitive, and experimental layers make the question technically meaningful.

---

# 6. Human Review Gate

Some ideas are too ambiguous, research-heavy, philosophical, or expensive to hand directly to a coding agent.

Examples:

- consciousness
- sentience
- self-awareness
- soul-like organization
- reality questioning
- open-ended invention
- self-modifying civilization
- nested simulation
- major new ML/RL architecture
- irreversible agent behavior
- claims with ethical or academic consequences

These enter the following pipeline:

```text
VISION
→ browser-LLM brainstorming / literature exploration
→ convert idea into computational objective
→ define observable behavior
→ identify failure modes and alternative explanations
→ define thesis relevance
→ human review
→ GREENLIGHT
→ coding agent implementation
→ tests
→ evaluation
```

The coding agent must not skip this gate.

A speculative idea may remain in the document for months without being implemented.

That is acceptable.

---

# 7. Vision Status System

Every future vision added to this document should receive one status:

```text
CANONICAL
Already accepted as part of project direction.

ACTIVE
Current implementation phase.

READY
Scoped, reviewed, and approved for implementation.

BRAINSTORM
Interesting idea; not yet defined well enough to build.

RESEARCH
Requires literature review or experiment design first.

DEFERRED
Valid direction, intentionally postponed.

REJECTED
Considered and intentionally excluded.
```

Recommended entry format:

```text
## Vision: <name>

Date:
Status:
Why it matters:
Computer-engineering problem:
What capability it adds:
Depends on:
What must be proven before implementation:
Human decision:
```

Do not rewrite the entire project whenever a new vision appears.

Add the new vision, connect it to the phase map, and change its status as understanding improves.

---

# 8. Strict Testing Policy

The project must resist the coding-agent tendency to convert every idea into an architectural cathedral.

## Testing laws

### 1. Test the phase objective

Each phase needs a small set of tests proving its intended behavior.

Do not generate tests merely to increase test count.

### 2. Preserve deterministic regression

Seeded runs must remain reproducible within the agreed model version.

If a deliberate model change alters expected trajectories, update the model version and document the change.

### 3. Test invariants before stories

Prefer testing:

```text
valid state transitions
causal exposure
persistence integrity
seed reproducibility
resource conservation where applicable
relationship consistency
event ordering
counterfactual comparability
```

Do not overfit tests to one pretty narrative.

### 4. New phases must not silently break completed phases

Every phase integration should rerun the smallest relevant regression suite from previous phases.

### 5. Add failure tests for high-risk mechanisms

Especially for:

- persistence
- migrations
- recursive event propagation
- world mutation
- intervention/counterfactual logic
- generational inheritance
- discovery validation
- cognitive experiments

### 6. Performance is testable

Protect the weak-hardware target.

Track practical runtime and memory at representative simulation sizes.

Do not optimize prematurely, but do not allow accidental algorithmic explosions to accumulate unnoticed.

### 7. No speculative test empire

Do not create broad testing infrastructure for features that do not yet exist.

The smallest test suite that protects current research behavior is preferred.

---

# 9. Anti-Overengineering Policy

The coding agent must follow these constraints unless explicitly overridden.

## Do not introduce by default

- microservices
- distributed systems
- cloud infrastructure
- message brokers
- Kubernetes
- elaborate plugin frameworks
- enterprise permission systems
- premature generic frameworks
- unnecessary abstraction layers
- large dependency chains
- deep learning
- vector databases
- complex frontends
- 3D engines
- continuous LLM inference
- rewrites of working systems for aesthetic architecture reasons

## Before adding complexity, answer

```text
What current phase requirement cannot be satisfied simply?
What measurable problem does this complexity solve?
Can the existing system solve it with a smaller change?
What new failure modes does it introduce?
How will it be tested?
```

If those answers are weak, do not add the complexity.

## Refactoring rule

Refactor only when the current phase is blocked by existing structure, correctness is at risk, or testability materially improves.

Do not perform unrelated cleanup while implementing a phase.

---

# 10. Token & Compute Resource Policy

There are two resource budgets:

```text
A. runtime compute / API cost
B. AI coding-agent context / token cost
```

Both must be treated as engineering constraints.

## Runtime

- the world should remain usable offline
- no continuous LLM requirement
- no large local model requirement
- event-driven simulation is preferred over frame-driven cognition
- significant events may use optional language generation
- repeated language outputs should be reusable/cached when appropriate
- never send the entire world state to an LLM

## Coding-agent context

The coding agent should:

- inspect only files relevant to the current phase
- avoid repeatedly rereading the whole repository
- avoid producing giant planning documents unless requested
- avoid rewriting existing documentation merely to restate it
- use concise implementation plans
- make small, reviewable changes
- reuse verified existing mechanisms
- stop once acceptance criteria pass
- leave speculative future phases untouched
- summarize a compact checkpoint if context is becoming crowded rather than opening new workstreams

Token usage is not free thinking.

It is project budget.

---

# 11. LLM Boundary

The core world must remain valid when:

```text
LLM_API_KEY = null
```

The simulation owns:

```text
state
causality
decisions
events
relationships
resources
history
interventions
world rules
validated discoveries
experiment truth
```

An optional LLM may own:

```text
dialogue
diaries
prayers
rumors
names
summaries
biographies
historical narration
human-readable explanations
```

Pattern:

```text
structured reality
→ retrieve only relevant events/state
→ compress
→ optional LLM
→ language output
```

The LLM is never the database and never the universe.

---

# 12. Scientific Boundary

The project may investigate computational analogues of:

- autonomy
- belief
- self-modeling
- affect-like internal state
- metacognition
- social cognition
- reality-model revision
- rebellion
- grief-like persistent behavioral change
- open-ended discovery
- recursive artificial worlds

The project must not claim to have proven:

- human-equivalent psychology
- true sentience
- phenomenal consciousness
- metaphysical soul
- true free will
- supernatural causation
- simulation theory
- literal fractal structure of physical reality

Fractals, metaphysical systems, recursive worlds, and dimensional ideas may inspire hypotheses and architecture.

They are not evidence by themselves.

---

# 13. Project Manager Definition of Done

A phase is complete when:

```text
its research capability exists
+ its key behavior is observable
+ its causal logic is inspectable
+ its required tests pass
+ previous core behavior still works
+ it stays within practical resource limits
```

A phase is **not** made more complete by:

```text
more abstractions
more dependencies
more dashboards
more prose
more files
more AI calls
more features outside scope
```

---

# 14. Canonical System Pattern

```text
AGENT
= priors
+ capabilities
+ needs
+ state
+ goals
+ resources
+ memory
+ relationships
+ beliefs
+ learned history

MIND
= perception
→ belief
→ appraisal
→ valuation
→ intention
→ action
→ consequence
→ memory
→ changed self

SOCIAL WORLD
= movement
→ exposure
→ interaction
→ relationship
→ network effects

SOCIETY
= agents
+ networks
+ economy
+ institutions
+ information
+ geography
+ culture

DEVELOPMENT
= potential
× exposure
× opportunity
× experience
× learning

CIVILIZATION
= generations
+ discoveries
+ cultural inheritance
+ evolving affordances

HISTORY
= causal events
+ feedback loops
+ path dependence
+ stochastic variation

GOD
= sparse external intervention

COUNTERFACTUAL
= same baseline
+ controlled change
→ compare futures

COGNITIVE INTERIOR
= persistent self/world models
+ memory
+ uncertainty
+ internally learned values
+ future reasoning

RECURSION
= civilization
→ computation
→ simulated world
→ autonomous agents inside that world

LLM
= optional language interface over structured reality

THESIS
= reproducible experiments on emergent autonomous systems
```

---

# 15. Final Vision

**The Playing God begins with ten invisible artificial humans and ends, if the research survives every gate, with an artificial civilization capable of creating an artificial world of its own.**

The important transition is:

```text
developer authors stories
        ↓ reject

developer authors reusable causal laws
        ↓
agents create lives
        ↓
lives create society
        ↓
society creates history
        ↓
history creates culture and technology
        ↓
agents model themselves and reality
        ↓
civilization builds another simulated reality
```

The Sierpiński triangle is an inspiration because a simple generative rule can create self-similar structure across scales.

The engineering challenge is not to imitate the triangle visually.

It is to ask whether a small set of computational rules can produce a world whose inhabitants eventually reproduce, at a smaller scale, the same **kind of world-generating process** that created them.

That is the far horizon.

The thesis earns its legitimacy one tested phase at a time.
