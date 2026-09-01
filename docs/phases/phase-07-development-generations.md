# THE PLAYING GOD — PHASE 7
## Development, Adaptive Cognition, Reproduction & Generations

**Document revision:** v1.0.0
**Prepared:** 2026-08-30
**Project:** The Playing God
**Project type:** Master of Computer Engineering thesis / artificial-life and artificial-society simulation
**Status:** APPROVED — IMPLEMENTATION IN PROGRESS
**Execution gate:** Human-approved 2026-08-31. Implement one numbered milestone at a time.
**Canonical destination:** `docs/phases/phase-07-development-generations.md`

---

# 0. Document Role

This document is the Phase 7 project-manager implementation brief for the coding agent.

It defines:

- why Phase 7 exists;
- the computer-engineering problem it addresses;
- the boundary between hard-coded priors and learned behavior;
- the role of lightweight ML/RL before reproduction;
- the Phase 7 subphase order;
- what each subphase must prove;
- what each subphase must not expand into;
- persistence and reproducibility expectations;
- weak-hardware constraints;
- testing and anti-overengineering policy;
- the Phase 7 exit condition;
- what is deliberately deferred to later phases.

It intentionally does **not** prescribe:

- exact class names;
- exact module names;
- folder restructuring;
- private helper functions;
- SQL table names;
- specific model hyperparameters;
- line-by-line coding steps;
- exact test file names;
- framework choices when the existing code can satisfy the requirement.

Codex owns implementation details.

Codex does **not** own research-scope expansion.

---

# 1. Thesis Anchor

## Computer Engineering identity

**The Playing God is a Master of Computer Engineering thesis project.**

The simulated world is the experimental medium. The engineering problem remains:

> **How can a resource-constrained computer system generate, persist, adapt, reproduce, inspect, and experimentally compare long-term emergent behavior in autonomous artificial agents without relying on continuous LLM inference or manually scripted stories?**

Phase 7 focuses this problem on **development through time**:

> **How can fixed priors, learned behavior, social experience, family conditions, institutions, and cultural transmission combine to produce reproducible but divergent developmental trajectories across generations?**

The project direction remains:

```text
autonomous individuals
→ persistent lives
→ causal social contact
→ society
→ adaptive behavior
→ development
→ generations
→ culture
→ discovery
→ artificial history
→ cognitive interior research
```

Phase 7 is not merely:

```text
add babies
add family trees
add ML
```

The phase must demonstrate:

```text
initial potential
+
lived experience
+
social environment
+
learned adaptation
+
historical context
↓
developed individual
```

The core thesis value is the **causal separation of what an NPC begins with from what the NPC becomes**.

---

# 2. Phase 7 Objective

## Purpose

Replace fully formed, mostly hard-coded adult NPCs with agents whose later state is increasingly explained by:

- inherited or initialized priors;
- personal experience;
- online adaptation;
- upbringing;
- relationships;
- institutions;
- resources and opportunity;
- cultural exposure;
- aging and lifecycle events.

## Phase 7 canonical sequence

```text
7.0  Adaptive Cognition Foundation
↓
7A   Founder Prehistory
↓
7B   Family / Reproduction Foundation
↓
7C   Child Development
↓
7D   Household / Inheritance / Lifecycle
↓
7E   Cultural Transmission
↓
7F   Ouroboros Foundation — conditional, only when enough generational data exists
```

## Core Phase 7 exit condition

Phase 7 is complete when the system can demonstrate, under reproducible seeds, that:

```text
two agents may begin with similar priors
+
experience different developmental histories
+
learn different behavioral tendencies
+
inherit / receive different resources and culture
↓
become measurably different adults
```

and:

```text
later-generation adults
are products of simulated history
rather than arbitrary adult initialization
```

The system must still function without an LLM API and without GPU-dependent training.

---

# 3. The Critical Separation: Priors, State, Memory, Policy, Culture

Phase 7 must prevent several concepts from collapsing into one giant "personality" object.

Conceptually:

```text
PRIORS
= starting biases / capacities

STATE
= what is currently happening to the NPC

MEMORY
= what happened to the NPC

LEARNED POLICY
= what experience taught the NPC tends to work

CULTURE / BELIEF
= information and norms acquired from others and institutions

LANGUAGE
= how structured internal reality may optionally be expressed
```

## 3.1 Priors are not destiny

Examples of plausible priors:

```text
threat sensitivity
novelty seeking
reward sensitivity
self-regulation potential
learning rate
memory capacity
social inference potential
spatial / motor aptitude
```

A prior may bias learning or action selection.

It must not directly encode a completed life outcome.

Avoid:

```text
born_criminal = true
future_artist = 0.91
will_be_rich = true
```

Prefer:

```text
potential
× exposure
× practice
× opportunity
× environment
× feedback
× chance
→ developed capability / tendency
```

## 3.2 Learned policy is not inherited memory

A child may receive bounded priors and environmental conditions from parents.

A child must not directly inherit:

```text
parent Q-values
parent personal memories
parent-specific trust scores
parent-specific learned fear of an individual
parent's exact behavioral policy
```

Those belong to lived experience.

Cultural information may be transmitted separately through observable social mechanisms.

## 3.3 The world remains authoritative

Learning changes how an NPC chooses among valid possibilities.

Learning must not bypass:

- physical constraints;
- resource constraints;
- institution rules;
- world legality/invariants;
- valid action requirements;
- causal event rules.

The learned component is a **decision influence**, not a second simulation engine.

---

# 4. Phase 7.0 — Adaptive Cognition Foundation

## Purpose

Introduce the smallest useful learning mechanism before reproduction so later agents can become behaviorally different because of what happened to them.

This is the bridge from:

```text
state
→ programmer-defined scoring
→ action
```

toward:

```text
state
+ priors
+ experience
+ learned preference
→ action
```

This subphase is intentionally lightweight.

It is **not** a deep-learning phase.

---

## 7.0.0 — Establish the Learning Boundary

### Goal

Define where learning is allowed to influence existing decision behavior without replacing the verified simulation engine.

The implementation must preserve the current causal pipeline:

```text
world context
→ valid candidate actions
→ constraints
→ decision mechanism
→ action
→ consequence
→ event / state update
```

Learning may influence:

```text
preference among valid actions
```

Learning may not invent:

```text
physically impossible actions
resources that do not exist
relationships that never formed
knowledge the NPC never received
institutional permissions that were not granted
```

### Required outcome

Codex must be able to explain, using the actual implementation:

```text
what information becomes a learning context/state
what action choice is being learned
what consequence becomes feedback
what remains controlled by deterministic world rules
```

No large new architecture is required merely to formalize this explanation.

### Non-goals

Do not add yet:

```text
deep neural policies
PPO
DQN
SAC
Dreamer
large world models
multi-agent deep RL frameworks
RLlib
large Gym abstractions
GPU pipelines
MLOps platforms
experiment tracking services
```

### Completion condition

The codebase has a clear, minimal boundary where a learning strategy can influence existing valid action choice without becoming the source of world truth.

### Implementation record — 2026-08-31

**7.0.0 complete.** `decision.choose()` now accepts an action-keyed
`learned_preferences` input after deriving the valid candidate set. Learned
and intervention adjustments can change relative preference only among those
already-valid actions; neither can resurrect an unavailable action.

The boundary is deliberately narrow:

- learning context/state is derived upstream from information explicitly
  available to the NPC and translated into action-keyed preferences;
- the learned choice is preference among existing action names;
- feedback is derived downstream from consequences produced by normal world
  execution, not by the chooser;
- `scores()`, `World.move_for_action()`, and `World.act()` retain authority over
  eligibility, physical/resource/institution constraints, and consequences.

Milestone 7.0.1 owns the first concrete context representation, consequence
feedback rule, and online update. No learned state or persistence migration was
introduced in 7.0.0.

---

## 7.0.1 — First Online Learner: Contextual Adaptation

### Goal

Give NPCs a lightweight mechanism that can learn:

> under situations like this, which available action has historically produced better outcomes for me?

The default research direction is a **contextual-bandit-class mechanism** or an equivalently simple online learner.

The exact representation and algorithm are Codex's implementation responsibility as long as they remain:

- inspectable;
- deterministic under the approved seed/control scheme;
- CPU-friendly;
- small enough to understand and test;
- subordinate to existing world constraints.

### Research behavior to prove

A useful demonstration is:

```text
NPC A and NPC B
start with equivalent or controlled priors
↓
experience different outcomes
↓
their learned action preferences diverge
↓
future decisions diverge in corresponding contexts
```

This is more important than sophisticated model architecture.

### Feedback / reward boundary

Do not create a universal "human happiness score."

Feedback should be derived from existing or clearly justified consequences such as:

- resource improvement/loss;
- goal progress;
- stress or stability changes;
- social consequences;
- capability progress;
- institution access;
- other already modeled outcomes.

If competing objectives exist, preserve their multidimensional character where practical rather than forcing every life outcome into one scientifically meaningless number.

### Non-goals

Do not:

- train a neural network;
- replace current traits;
- rewrite the entire decision engine;
- create hundreds of state buckets because "RL needs states";
- add a generic reward-engine framework;
- claim learned action preference equals intelligence.

### Completion condition

At least one controlled scenario shows that experience changes later action preference and that the change can be inspected.

### Implementation record — 2026-09-01

**7.0.1 complete.** The first learner is a deterministic contextual action-value
table in `core/adaptive.py`:

- context is the NPC's existing current goal, one of five compact state
  summaries already derived by `World.update_goal()`;
- each action observation retains mean money, skill, energy, social-energy,
  stress, reputation, relationship, employment, and job-level consequences;
- feedback is projected only onto the dimension relevant to the current goal,
  rather than collapsed into a universal happiness score;
- the running mean feedback becomes an additive preference bounded to `0.75`;
- updates occur after normal movement/action resolution and consume no RNG.

Adaptive execution is explicitly enabled with
`World(adaptive_cognition=True)`. It remains off for existing and loaded worlds
until 7.0.2 persists the learned table and model setting. The controlled test
holds priors and later decision state equal: an agent admitted to training
learns enough preference to select `train`, while an otherwise equivalent
agent denied by the institution later selects `rest`. Repeated same-seed
adaptive runs remain exact.

No delayed-credit learner, new dependency, or persistence schema was added.

---

## 7.0.2 — Learned-State Persistence & Reproducibility

### Goal

An NPC must not forget learned behavior merely because the process restarts.

Persist only the minimal learned state required by the accepted learning method.

### Required properties

```text
uninterrupted run
≈
save → reload → continue
```

for learned decision behavior under the existing reproducibility contract.

Learned state must remain separate from:

- immutable/baseline priors;
- ordinary episodic events;
- social relationships;
- cultural beliefs.

Do not duplicate the same truth into several persistence representations without a demonstrated need.

### Legacy-world rule

Existing worlds created before adaptive cognition must remain loadable if the current persistence policy already supports version migration.

Legacy agents may begin with empty/untrained adaptive state.

Migration must not fabricate a history they never experienced.

### Completion condition

A split run preserves the NPC's learned behavior consistently and does not silently reset or randomize it.

---

## 7.0.3 — Delayed Consequence Gate

### Purpose

Determine whether the contextual learner is insufficient for behaviors where an action has a cost now but a benefit later.

Example:

```text
training
→ immediate money / time cost
→ capability increase
→ later employment opportunity
→ later income
```

A contextual bandit mainly addresses:

```text
what tends to work in this context?
```

A value-learning method such as **tabular Q-learning** becomes justified when the research problem genuinely requires:

```text
what action now improves expected future state?
```

### Gate

Do not add Q-learning merely because it is a famous RL algorithm.

Add a multi-step learner only if a controlled scenario demonstrates that one-step feedback cannot represent an important Phase 7 developmental behavior.

### If the gate is triggered

The first implementation should remain:

- tabular or otherwise small;
- CPU-first;
- inspectable;
- limited to a small action/state problem;
- deterministic/reproducible under the simulation contract.

### If the gate is not triggered

Record:

```text
Q-learning deferred
reason: no Phase 7 behavior currently requires delayed-credit learning
```

and continue.

### Completion condition

Either:

```text
A) delayed-credit learning is implemented because a concrete behavior requires it
```

or:

```text
B) it is explicitly deferred with evidence that contextual adaptation is sufficient for Phase 7
```

Both are valid outcomes.

---

## Phase 7.0 Exit Condition

Adaptive cognition foundation is complete when:

1. learning influences only valid actions;
2. at least one NPC preference changes from experience;
3. two controlled experience histories can produce different learned behavior;
4. learned state survives persistence where required;
5. seeded runs remain reproducible under the agreed model version;
6. no GPU, continuous LLM, or deep-RL framework is required;
7. Q-learning or more complex RL exists only if a demonstrated problem justified it.

Only then proceed to founder/generational work.

---

# 5. Phase 7A — Founder Prehistory

## Purpose

The current G0 founder adults were initialized as already-formed people.

Do not rerun full childhood simulation for every founder.

Instead, create the smallest causal prehistory required to explain important starting differences.

Concept:

```text
seed
→ compact prior-life conditions/events
→ experiences/exposures
→ G0 starting state
```

## What founder prehistory may explain

Examples:

- starting resources;
- employment status;
- capability exposure;
- important relationships where historically justified;
- selected beliefs;
- selected significant memories;
- learned-policy warm start only when it can be causally derived from generated prehistory.

The objective is **causal plausibility**, not literary biography.

## Constraints

Founder prehistory must be:

- seeded;
- reproducible;
- compact;
- structured;
- inspectable;
- consistent with the current world model;
- cheap enough to generate for many runs.

Do not generate prose biographies as causal state.

An optional LLM may summarize prehistory later, but structured events remain authoritative.

## Non-goals

Do not simulate:

- every childhood day;
- full historical nations;
- entire parental generations before G0;
- detailed medical development;
- school curricula;
- thousands of irrelevant memories.

## Exit condition

The important starting state of G0 adults can be traced to compact generated history rather than appearing as unexplained arbitrary values.

---

# 6. Phase 7B — Family / Reproduction Foundation

## Purpose

Create later-generation agents from world history instead of spawning another arbitrary adult population.

The first reproduction system should be an abstract demographic mechanism, not a biological simulator.

## Required capabilities

The system should support, at minimum:

```text
parent relationship / eligibility context
→ reproduction event when world conditions allow
→ child identity
→ parent-child links
→ birth time
→ starting priors with bounded variation
→ starting environment / dependency context
```

Exact eligibility and demographic rules are implementation/model choices, but must remain explicit and inspectable.

## Inheritance principle

Child priors may depend on:

```text
parent priors
+ bounded variation
+ world / household conditions where justified
```

Do not copy entire parent state.

Do not inherit:

- personal memories;
- learned interpersonal trust;
- exact learned policy;
- occupation;
- adult social status;
- personal grudges;
- arbitrary adult capability values.

## Family structure

Phase 7B needs enough family structure to answer:

```text
who are this child's parents / guardians?
which relationships are genealogical?
what initial environment did the child enter?
```

It does not need a complete sociology of family forms.

## Non-goals

Do not build:

- explicit sexual simulation;
- genetics engines;
- chromosome simulation;
- pregnancy physiology;
- fertility medicine;
- detailed health biology;
- demographic realism for its own sake.

These do not solve the current thesis problem.

## Exit condition

A seeded world can produce a later-generation child whose identity, parent links, and bounded starting priors are causally derived from world state.

---

# 7. Phase 7C — Child Development

## Purpose

Make later NPC state a product of developmental history.

This is the core Phase 7 research layer.

Concept:

```text
starting priors
+
family environment
+
resources
+
relationships
+
institution exposure
+
events
+
practice
+
learning
+
chance
→ developing capability and behavior
```

## Developmental progression

The system needs a lightweight lifecycle representation sufficient to change what an NPC:

- can do;
- is expected/required to do;
- can learn;
- can access;
- can contribute to;
- can remember or understand where relevant.

Exact age boundaries are model details.

Avoid encoding a giant real-world developmental psychology theory.

## Capability expression

A latent capability should become developed only through relevant exposure and history.

Pattern:

```text
aptitude
× exposure
× practice
× opportunity
× feedback
→ developed capability
```

Examples:

```text
learning potential + school access + repeated study
→ skill development

social inference potential + repeated interaction
→ improved social capability
```

No capability is guaranteed merely because its prior is high.

## Adaptive policy integration

The learning mechanism from Phase 7.0 should now accumulate experience through development.

This gives the project a critical distinction:

```text
similar starting priors
≠
identical adult behavior
```

because:

```text
different experience
→ different memories
→ different learned policy
→ different trajectory
```

## Existing systems should matter

Whenever possible, development should reuse already-built causal systems:

- Phase 3 relationships;
- Phase 4 exposure/mobility;
- Phase 5 belief/intervention;
- Phase 6 economy/institutions/information.

Do not create a separate toy childhood world that bypasses the actual society.

## Required research demonstration

A controlled comparison should be possible where:

```text
similar child priors
+
different upbringing / institution access / social exposure
↓
different developed capability or behavior
```

The comparison does not need to be a full Phase 9 research experiment yet.

It only needs to prove the mechanism exists.

## Non-goals

Do not implement:

- validated human developmental psychology;
- detailed educational curricula;
- hundreds of developmental milestones;
- language acquisition models;
- puberty biology;
- child-specific 3D/gameplay systems;
- neural world models.

## Exit condition

A child can reach later life with state and learned behavior that are traceably shaped by the simulated world experienced during development.

---

# 8. Phase 7D — Household, Inheritance & Lifecycle

## Purpose

Make generations sustainable.

Without lifecycle exit and resource continuity, reproduction produces population accumulation rather than generational turnover.

## 7D responsibilities

Introduce the smallest mechanisms necessary for:

- household/dependent resource context;
- basic support between guardians and dependents;
- resource inheritance/transfer at lifecycle transitions where justified;
- aging;
- adulthood/retirement transitions where needed;
- death or other lifecycle exit;
- stable parent/descendant history.

## Household boundary

A household is a resource/social context.

Do not turn it into a new universal institution framework unless the implementation genuinely needs one.

The household system should answer practical questions such as:

```text
who materially supports this dependent NPC?
what resource environment is the NPC developing inside?
what happens to relevant resources after a lifecycle exit?
```

## Mortality boundary

The initial mortality mechanism may remain abstract and age/risk based.

Do not build a medical simulator.

Mortality must not exist merely as arbitrary dramatic storytelling.

It exists to support:

- lifecycle completeness;
- generational turnover;
- inheritance;
- historical loss;
- long-term population stability.

## Population control

Do not hard-code a fixed population ceiling as the primary lifecycle model unless required as a temporary safety guard.

Population should primarily be constrained by causal world conditions such as:

- resources;
- family/household capacity;
- lifecycle;
- reproduction eligibility;
- mortality.

A practical safety cap may exist to protect weak hardware, but it should be clearly identified as an engineering guardrail rather than a simulated social law.

## Exit condition

The simulation can sustain generational turnover without indefinite population accumulation, and important resource/lifecycle transitions remain traceable.

---

# 9. Phase 7E — Cultural Transmission

## Purpose

Separate **what is inherited biologically-like** from **what is inherited socially**.

Later generations should inherit not only starting conditions but also a world containing beliefs, norms, knowledge, institutions, and history created by earlier agents.

Concept:

```text
parents
peers
institutions
social network
information network
historical events
↓
exposure
↓
accept / reject / modify
↓
belief / norm / knowledge state
```

## Transmission routes

Reuse existing causal channels where possible:

- parent/guardian interaction;
- repeated social exposure;
- schools/institutions;
- information diffusion;
- community/relationship influence;
- significant events.

Culture must not teleport directly from "society" into an NPC.

## Critical separation

Do not treat:

```text
parent believes X
```

as equivalent to:

```text
child believes X
```

The child must have a transmission/exposure path.

Likewise:

```text
family norm
≠
genetic prior
```

## Learned policy boundary

A parent may teach or influence a child through social/cultural mechanisms.

Do not directly serialize and copy the parent's adaptive policy into the child.

If a behavior becomes intergenerational, the project should be able to ask whether it persisted through:

```text
shared priors
shared environment
cultural transmission
institutional structure
or repeated independent learning
```

That distinction is research valuable.

## Required demonstration

At least one controlled scenario should show:

```text
earlier generation behavior / belief
→ causal transmission channel
→ later generation internal state or action tendency
```

and another valid path should permit divergence.

## Non-goals

Do not create:

- universal ideology engines;
- hundreds of norm dimensions;
- real-world political labels as personality switches;
- automatic cultural inheritance;
- LLM-generated culture treated as causal truth.

## Exit condition

A later-generation NPC can inherit culture through explicit social/institutional exposure while remaining capable of rejecting, modifying, or diverging from it.

---

# 10. Phase 7F — Ouroboros Foundation

**Status:** CONDITIONAL WITHIN PHASE 7
**Blocking:** No. Core Phase 7 may exit without a mature Ouroboros detector if insufficient generational data exists.

## Purpose

Detect deep-time recurrence rather than manufacture it.

Concept:

```text
earlier agent / trajectory pattern
→ generations pass
→ later candidate pattern
→ similarity measure
→ possible recurrence observation
```

The research question is:

> If two agents or social configurations are structurally similar but live in different historical contexts, do their trajectories converge or diverge?

## First implementation boundary

Prefer structured numeric comparison before semantic or deep models.

Possible comparison categories:

- starting-prior similarity;
- developed-state similarity;
- trajectory-summary similarity;
- social-position similarity;
- broader world-state similarity later.

Exact distance/similarity methods are implementation choices.

## Critical rule

The detector observes recurrence.

It must never:

- modify NPC state to create recurrence;
- spawn a "reincarnated" NPC;
- force matching life events;
- use exact float equality as the recurrence definition;
- claim metaphysical recurrence.

## ML boundary

A basic Ouroboros detector should not require deep learning.

Embeddings or learned representations may be considered later only if structured vectors demonstrably fail to capture an important comparison problem.

## Exit condition

If enough generational data exists, the system can identify structurally similar historical candidates and report their similarities/differences without changing the simulation.

If not enough data exists, record Phase 7F as deferred to Phase 9 analysis rather than manufacturing data merely to complete a checklist.

---

# 11. ML / RL / DL Policy for Phase 7

Phase 7 introduces **adaptive behavior**, not "AI everywhere."

## Required or preferred now

```text
existing weighted/stochastic decision system
+
small online learner
```

Preferred first family:

```text
contextual bandit / equivalent simple online adaptation
```

Conditional:

```text
tabular Q-learning / equivalent value learning
```

only when delayed consequences create a demonstrated need.

## Deferred by default

```text
deep Q networks
PPO
SAC
Dreamer
actor-critic systems
transformer policies
recurrent neural policies
large behavior-cloning pipelines
multi-agent deep RL
world-model training
```

## When a neural network becomes justified

A small neural model may be proposed later if:

1. the current learning state representation becomes measurably unmanageable;
2. a tabular/simple model creates a demonstrated scaling or generalization failure;
3. the target research behavior cannot reasonably be captured by the simpler method;
4. CPU training remains practical or a clear alternative compute plan exists;
5. the change passes human review because it materially changes the project learning architecture.

"Neural networks are more AI" is not justification.

## LLM boundary

The world must still function when:

```text
LLM_API_KEY = null
```

An optional language model may later:

- express dialogue;
- summarize memories;
- narrate biography;
- name events/discoveries;
- generate human-readable explanations from structured state.

It must not silently become:

- the world database;
- the action validator;
- the causal simulation;
- the reproductive mechanism;
- the source of hidden NPC knowledge;
- a continuous per-NPC reasoning loop.

---

# 12. Hardware & Compute Policy

Phase 7 must remain viable on a weak CPU-only development machine.

## Hardware target

```text
single consumer laptop
Intel CPU class hardware
8 GB RAM class hardware
no dedicated GPU required
```

## Compute expectations

The initial adaptive mechanisms should learn online as the simulation runs.

Phase 7 should not require:

```text
multi-day training jobs
GPU clusters
cloud training
distributed rollout workers
large replay buffers
continuous model serving
```

## Performance priority

The expected bottleneck should remain:

```text
number of simulated agent/world interactions
```

rather than:

```text
neural inference per NPC per tick
```

Preserve event-driven simulation.

Do not convert NPC cognition into per-frame inference.

## Scale discipline

Use small controlled populations and short controlled scenarios while validating new mechanisms.

Increase generation count or population only after correctness and runtime are understood.

Do not build performance infrastructure in advance of an actual measured problem.

---

# 13. Reproducibility & Model-Version Policy

Adaptive agents introduce a new risk:

```text
same world state
+
different learning update order
→ different future policy
→ amplified trajectory divergence
```

Therefore Phase 7 must preserve explicit reproducibility discipline.

## Required principles

- approved seeded randomness remains authoritative;
- learning updates must not depend on wall-clock timing;
- iteration/order dependence must be deterministic or explicitly part of the model;
- save/load must preserve required adaptive state;
- no hidden external API response may influence causal truth;
- repeated runs under the same model version/configuration should remain reproducible under the project's existing determinism contract.

## Intentional model changes

A deliberate change to:

- reward/feedback meaning;
- learning algorithm;
- state representation;
- inheritance semantics;
- lifecycle semantics;
- cultural transmission rules;

may legitimately change long-term trajectories.

Do not preserve old narrative fixtures at the cost of keeping an outdated model.

Instead:

```text
document intentional behavior migration
→ update the simulation/model version if the project currently versions behavior
→ update only affected regression expectations
```

Do not confuse:

```text
document revision
```

with:

```text
simulation behavior/model version
```

---

# 14. Anti-Overengineering Policy

This section overrides coding-agent enthusiasm.

## 14.1 Approved brief means implement

Once the human approves this document:

```text
inspect relevant current code
→ implement the current numbered milestone
→ run focused verification
→ report result
```

Do not perform:

```text
review
→ new spec
→ approval request
→ new architecture document
→ new implementation plan
→ another approval request
→ implementation
```

This file is already the approved scope document.

## 14.2 No artificial file-count bureaucracy

There is no arbitrary "must touch exactly N files" rule.

Use the smallest coherent patch that fits the existing architecture.

If a small milestone unexpectedly requires a broad cross-system rewrite, report the architectural reason instead of casually refactoring the whole project.

## 14.3 No speculative abstractions

Do not create generic systems merely because future phases might use them.

Examples to avoid unless a second real use case already requires them:

```text
UniversalLearningEngine
GenericInheritanceFramework
CivilizationPluginSystem
AgentBrainFramework
UniversalRewardRegistry
MLOpsPlatform
ExperimentMicroservice
PolicyServer
ModelRegistry service
```

A concrete mechanism that satisfies the current phase is preferred.

## 14.4 Dependency rule

Before adding a new runtime dependency, Codex must be able to state:

```text
which current Phase 7 requirement cannot be satisfied reasonably with
the standard library or already-installed project dependencies?
```

If that answer is weak, do not add it.

A small ML dependency is acceptable only when it directly enables an approved learning requirement.

Do not preinstall an ecosystem for algorithms that remain deferred.

## 14.5 Refactoring rule

Refactor only when:

- current Phase 7 work is blocked by existing structure;
- correctness is at risk;
- persistence/reproducibility cannot be maintained cleanly;
- the same real behavior is duplicated enough to create an actual maintenance problem.

Do not rewrite working systems for aesthetic consistency.

## 14.6 Documentation rule

Do not create a separate detailed brief for every subphase by default.

This document is sufficient.

A new subphase document is justified only if implementation uncovers a genuine unresolved architectural/research question that cannot safely fit inside this contract.

Do not create retrospectives for completed subphases.

---

# 15. Testing Policy

Testing must prove research behavior, not maximize test count.

## 15.1 Test invariants before stories

Prefer testing:

- valid action constraints remain enforced;
- learning changes preference when experience changes;
- learned state persistence;
- deterministic same-seed behavior;
- bounded inheritance;
- genealogical integrity;
- lifecycle validity;
- cultural transmission requires a causal exposure path;
- no direct parent-memory/policy copying;
- population/resource invariants where applicable.

Avoid tests such as:

```text
NPC Mira must become a teacher on day 912
```

unless that exact event is a deliberately fixed deterministic contract.

## 15.2 Focused first

For each numbered milestone:

1. run the smallest focused tests that prove the new behavior;
2. run relevant existing regression when shared state, persistence, RNG, or major decision behavior changes;
3. run the broader suite at subphase exits or when integration risk justifies it.

Do not create enormous stochastic test runs when a controlled small setup proves the same property.

## 15.3 Do not weaken tests to make new behavior pass

When an old deterministic expectation changes, first classify it:

```text
regression
or
intentional model migration
```

Do not silently refresh fixtures.

## 15.4 Performance verification

Protect weak-hardware viability with a practical sanity check at major Phase 7 exits.

Do not create a benchmarking framework unless a measured regression requires one.

## 15.5 No speculative testing infrastructure

Do not add:

- property-testing frameworks;
- distributed test workers;
- ML experiment trackers;
- benchmark dashboards;
- probabilistic test matrices;

unless an observed defect or research requirement makes them necessary.

---

# 16. Phase 7 Progress Labels

Use these labels for engineering progress:

```text
7.0.0
7.0.1
7.0.2
7.0.3

7A
7B
7C
7D
7E
7F
```

If a subphase genuinely needs multiple implementation checkpoints, Codex may use:

```text
7A.1
7A.2
...
```

but should not manufacture checkpoints merely to imitate process.

These labels are **not document versions**.

Do not confuse:

```text
Phase milestone 7C
```

with:

```text
Phase 7 document revision v1.0.0
```

---

# 17. Document Versioning Policy

Canonical repository file:

```text
docs/phases/phase-07-development-generations.md
```

Do **not** create:

```text
phase-07-v1.md
phase-07-final.md
phase-07-final-final.md
phase-07-new.md
```

The document revision belongs in the header and Git history.

Semantic meaning:

```text
v1.0.0
= first approved Phase 7 scope

v1.x.0
= meaningful scope clarification or added subphase contract
  that does not change the fundamental Phase 7 objective

v1.x.y
= wording, acceptance clarification, corrected ambiguity,
  or non-architectural documentation fix

v2.0.0
= fundamental Phase 7 research/architecture change
  such as replacing the learning model, reordering the phase
  around a new core objective, or redefining generational semantics
```

A code/model version remains separate from this document revision.

---

# 18. Phase 7 Completion Gate

Phase 7 is complete when all core statements below are true.

## Adaptive behavior

- an NPC can change future action preference because of experienced consequences;
- learning remains subordinate to valid world actions/constraints;
- learned state is inspectable enough to explain its effect;
- required learning state survives persistence;
- no deep RL or GPU is required for core completion.

## Founder causality

- important G0 starting conditions can be traced to compact seeded prehistory rather than unexplained arbitrary initialization.

## Reproduction

- later-generation agents can be born from world history;
- parent/guardian relationships are explicit;
- starting priors use bounded inheritance/variation;
- personal memories and exact learned policies are not genetically copied.

## Development

- later agent capability/state changes through exposure, resources, institutions, relationships, events, and learning;
- similar priors under different histories can produce divergent later behavior.

## Lifecycle

- generations can turn over;
- population does not only accumulate forever;
- relevant household/resource/inheritance transitions are traceable.

## Culture

- information/norm/belief transfer uses causal social/institutional channels;
- descendants may adopt, modify, or reject transmitted culture.

## Reproducibility

- seeded Phase 7 behavior satisfies the project's agreed reproducibility contract;
- save/load does not erase essential generational or learned state.

## Ouroboros

Either:

```text
a first non-invasive similarity detector exists because enough data justified it
```

or:

```text
7F is explicitly deferred to Phase 9 because the required dataset does not yet exist
```

The second outcome does not block Phase 7 completion.

---

# 19. Required Phase 7 Demonstration

Before declaring Phase 7 complete, run one compact end-to-end demonstration capable of answering:

```text
Who were this NPC's parents / guardians?

What starting priors did they receive?

What environment did they grow up in?

Which major exposures and institutions shaped them?

What did they learn from their own consequences?

Which beliefs / norms reached them socially?

How did their adult state differ from a comparable agent with a different history?

Can the same seeded experiment be reproduced?
```

The output may be textual/structured.

Do not build a game UI merely for this demonstration.

---

# 20. Phase 7 Non-Goals

Do not allow Phase 7 to expand into:

```text
full genetics
realistic pregnancy physiology
medical simulation
full demographic science
validated human developmental psychology
LLM-powered continuous NPC cognition
large language models per NPC
large local model hosting
deep reinforcement learning
world-model agents
consciousness
sentience claims
self-awareness architecture
open-ended invention
NPC source-code modification
full causal research dashboard
large-scale MLOps
3D generational visualization
```

Relevant destinations:

```text
open-ended invention
→ Phase 8

large experiment/ablation infrastructure
→ Phase 9

world models / self-models / consciousness research
→ Phase 10 human-reviewed research

visual/game polish
→ separate visualization track when justified
```

---

# 21. Bridge to Phase 8

Phase 7 should leave the world in this state:

```text
G0 founders
→ reproduce
→ G1 develops
→ learns
→ receives culture
→ becomes adult
→ changes the society inherited by G2
```

Phase 8 then asks a different question:

> **Can those historically developed agents create new civilization-level capabilities that change what later generations can do?**

Therefore Phase 7 must stop before implementing:

- invention registries;
- dynamic affordance expansion;
- autonomous technology discovery;
- NPC-generated institutions beyond existing Phase 6 mechanisms;
- mutable civilization action spaces.

Those belong to Phase 8.

---

# 22. Computer Engineering Problem Solved by Phase 7

The world-building language may sound biological or sociological.

The engineering result should remain precise.

Phase 7 solves a combination of:

```text
state representation
+
online learning
+
persistent adaptive policy
+
deterministic simulation
+
genealogical data modeling
+
lifecycle state transitions
+
cross-generational information flow
+
causal traceability
+
resource-constrained execution
```

The key achievement is not:

> "NPCs can have children."

It is:

> **The system can generate later autonomous agents whose behavior is a reproducible computational consequence of inherited priors, developmental environment, social history, and learned experience.**

That is the thesis-relevant boundary.

---

# 23. Canonical Phase 7 Pattern

```text
PRIORS
= bounded starting tendencies / capacities

EXPERIENCE
= events + consequences + exposure

ADAPTATION
= experience → learned action preference

DEVELOPMENT
= priors × environment × exposure × practice × learning

GENERATION
= reproduction + bounded inheritance + upbringing

CULTURE
= social / institutional transmission, not genetic copying

LIFE
= state → action → consequence → memory / learning → changed state

HISTORY
= generations modifying the environment inherited by later generations

OUROBOROS
= detect structural recurrence; never force it

LLM
= optional language over structured reality

THESIS
= reproducible causal development of autonomous agents across time
```

---

# 24. Codex Operating Rule for This Phase

After this document is approved, Codex should treat the currently requested milestone as authorized implementation work.

For each milestone:

```text
inspect only relevant current ownership
→ implement smallest coherent solution
→ verify the intended behavior
→ run necessary regression
→ report what changed and what was proven
→ stop
```

Do not invent the next phase.

Do not redesign the project.

Do not write another plan because planning feels productive.

A simulated civilization already provides enough opportunities for unnecessary bureaucracy without the coding agent founding its own.
