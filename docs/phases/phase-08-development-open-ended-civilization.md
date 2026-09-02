# THE PLAYING GOD — PHASE 8 DEVELOPMENT PLAN

## Controlled Open-Ended Civilization

**Document role:** Approved implementation brief for Codex

**Project:** The Playing God

**Phase:** 8

**Status:** Ready for step-by-step implementation after Phase 7

**Canonical vision:** V0.2 + V0.2.2 + V0.2.3

**Supersedes:** The legacy V0.1 label `Phase 8 — Generative Language`

---

## 0. Authority and Execution Rule

This document is the implementation authority for Phase 8.

Codex must implement the named subphase directly when instructed to proceed. Do not create another specification, architecture proposal, approval loop, or implementation plan unless the repository reveals a genuine conflict that would materially change the approved behavior.

Execution pattern:

```text
user approves / says proceed
→ inspect only the relevant current code
→ implement the current subphase
→ run focused tests
→ run the full suite at milestone boundaries
→ commit the completed subphase
→ report outcome, evidence, and next subphase
```

Do not implement later subphases early. Do not enlarge the scope while "preparing" for them.

Prefer reversible slices touching roughly five files or fewer. Persistence work may naturally cross more files; if so, keep the change cohesive and explain the reason in the completion report instead of generating another plan.

---

## 1. Phase 8 Decision

The original V0.1 roadmap called Phase 8 **Generative Language**. That label is now obsolete for the current development sequence.

V0.2.2 introduced the more important dependency:

```text
agents develop
→ reproduce
→ transmit culture
→ discover capabilities
→ alter later possibilities
```

Phase 7 completed the first three steps. Therefore the current Phase 8 is:

> **A controlled runtime extension layer in which agents can discover, validate, transmit, adopt, and institutionalize one new civilization-level capability without modifying the simulation kernel.**

Generative language remains a later optional presentation layer. It is not deleted from the long-term vision, but it is not part of this phase.

---

## 2. Computer Engineering and Thesis Relevance

Phase 8 is not primarily about making NPCs look clever or adding an invention mechanic.

It addresses this computer-engineering problem:

> **How can a deterministic multi-agent system permit agent-driven expansion of its runtime action space while preserving safety boundaries, causal traceability, persistence, reproducibility, and bounded computational cost?**

The engineering contribution is the boundary between a fixed simulation kernel and an evolvable civilization layer:

```text
IMMUTABLE KERNEL
clock + RNG + invariants + causal rules + validator
                  │
                  ▼
CONTROLLED CIVILIZATION API
registries + bounded effect vocabulary + persistence
                  │
                  ▼
AGENT-DRIVEN HISTORY
problem → experiment → discovery → diffusion → adoption
                  │
                  ▼
CHANGED POSSIBILITY SPACE
later agents can perform an action that was previously unavailable
```

This extends the thesis from observing different lives inside one fixed world to studying how historical actors can change the conditions inherited by later actors.

Phase 8 must remain a research mechanism, not a generic game technology tree.

---

## 3. Starting Baseline

Phase 8 begins from the completed Phase 7 state:

- Phase 7 completion commit: `551841d docs: close phase 7 recurrence gate`.
- Phase 7E cultural transmission commit: `b7d7912 feat: add causal cultural transmission`.
- Schema is currently v17.
- Full suite is currently 197 passing tests.
- Development, reproduction, family history, inheritance, adaptive learning state, institutional training access, and cultural transmission exist.
- Cultural transmission uses guardian, school, and social-information routes.
- Responses are deterministic accept, modify, or reject outcomes.
- Counterfactual snapshots include cultural history.
- Recurrence/Ouroboros detection is deferred to Phase 9 because current worlds contain no adult descendant generation or G2 evidence.

Before the first Phase 8 mutation, Codex must verify the current repository state rather than blindly assuming these numbers still match. A changed test count is acceptable if all existing tests pass and the change is explained by intervening work.

Phase 8 does not require artificial G2 worlds, recurrence fixtures, or longer generation probes.

---

## 4. Phase Goal

At Phase 8 completion, one controlled world must demonstrate this complete causal chain:

```text
repeated training access problem
→ affected agent observes sufficient evidence
→ eligible agent spends resources on an experiment
→ existing primitives are recombined into a candidate procedure
→ world validator accepts or rejects the candidate
→ successful knowledge initially belongs only to the discoverer/group
→ knowledge spreads through causal exposure routes
→ adopters gain a new bounded action affordance
→ an institution may adopt the validated procedure
→ later training opportunity changes
→ save/reload and same-seed replay preserve the same history
→ a counterfactual without the discovery retains the old possibility space
```

The reference vertical slice is a **peer-training procedure**:

- Existing problem: formal/institutional training can be denied, unaffordable, or inaccessible.
- Existing foundations: skill practice, feedback, relationships, schools, information exposure, money, energy, time, and stress.
- Candidate idea: combine demonstration, shared practice, and feedback into a peer-training procedure.
- New affordance: an agent who knows the validated procedure may help another agent train outside formal institutional access.
- Required trade-off: lower formal access/money requirement, but non-zero time and energy cost and bounded skill progress. It must not dominate formal training in every case.

This is a proving fixture for the engine, not a permanent claim that peer training is the only possible discovery.

The implementation must be data-driven enough that the discovery is not encoded as a dedicated `invent_peer_training()` branch. However, Phase 8 does not build a universal invention language.

---

## 5. Core Architecture Contract

### 5.1 Immutable kernel

NPCs and discovery data must never modify:

```text
simulation clock
seed or RNG semantics
engine source code
database schema definitions at runtime
causal-link rules
validation code
numeric safety bounds
persistence invariants
```

### 5.2 Evolvable civilization layer

The controlled mutable layer may contain:

```text
world knowledge
validated procedures
agent knowledge possession
knowledge exposure and adoption
bounded action affordances
institutional adoption state
causal discovery history
```

### 5.3 Bounded effect vocabulary

A discovery may only produce effects already allowed by engine-owned effect operations.

For the Phase 8 slice, the whitelist should be no larger than required to express:

```text
resource cost
time / energy / stress change
bounded skill progress
knowledge exposure / adoption
action availability
institutional availability
```

Discovery records contain structured data. They do not contain Python, SQL, prompts, executable expressions, arbitrary class paths, or user-defined callbacks.

### 5.4 World orchestration boundary

`world.py` may coordinate the phase but must not absorb all registry, discovery, validation, diffusion, and affordance logic.

Desired responsibility split:

```text
world orchestration
→ requests problem/discovery processing
→ receives deterministic domain results
→ applies approved state transitions
→ records causal events

civilization domain
→ owns registry models and lookup
→ derives problem pressure
→ evaluates discovery eligibility
→ creates and validates candidates
→ resolves exposure/adoption
→ returns bounded effects

persistence
→ serializes and restores civilization state
→ validates referential integrity
```

Do not perform a broad rewrite of `world.py` because of its line count. Extract only the seams Phase 8 requires, preserving current behavior and tests.

If equivalent module boundaries already exist, reuse them. File names are not part of the research result.

---

## 6. Minimum Domain Records

Codex should adapt names to existing conventions, but the model must represent these concepts explicitly.

### Base primitive definition

An engine-owned possibility from which candidates may be composed.

Minimum meaning:

```text
stable primitive id
category / tags
capabilities supplied
requirements
bounded cost or effect metadata where relevant
```

Base primitives are defined by developers as part of the physics of possibility. Agents do not invent or mutate the validator itself.

### Problem pressure

A compact causal summary of repeated evidence, not an omniscient complaint generated from global state.

Minimum meaning:

```text
problem kind
affected agent or group
first and latest evidence day
bounded occurrence count / severity
causal evidence event ids
resolved or unresolved state
```

### Discovery attempt

Minimum meaning:

```text
stable attempt id
day
proposer agent/group ids
problem reference
ordered/canonical primitive ids
costs paid
eligibility inputs
validation result
success or rejection reason
causal parent ids
```

### Knowledge entry

Minimum meaning:

```text
stable knowledge id
canonical discovery signature
origin attempt
discoverer/group
validated action/effect specification
creation day
status
```

### Agent knowledge state

Minimum meaning:

```text
agent id
knowledge id
source / route
exposure day
response: accept, modify, or reject where reused
effective adopted variant, if any
causal parent
```

### Affordance definition or unlock

Minimum meaning:

```text
stable action id
source knowledge id
preconditions
bounded costs
whitelisted effects
who may use it
availability state
```

Do not duplicate existing event, institution, action, culture, or agent-knowledge models if they already provide the needed semantics.

---

## 7. Determinism and Causality Laws

Every Phase 8 transition must satisfy all of the following:

1. Stable iteration order is explicit. Never rely on set order, dict construction accidents, SQLite row order without `ORDER BY`, or Python hash behavior.
2. Any stochastic discovery outcome uses the world's existing seeded RNG policy. Do not create independent unseeded randomness.
3. Structural validation is pure and deterministic. Randomness may influence whether an eligible experiment succeeds, but it must never make an invalid candidate legal.
4. Canonical signatures prevent duplicate discoveries regardless of primitive input ordering.
5. Every important Phase 8 event has causal parents that exist and precede it.
6. A discovery cannot be known, adopted, used, or institutionalized before it is validated.
7. An agent cannot learn a discovery without a causal exposure route.
8. A new action cannot execute unless its source knowledge and preconditions are satisfied.
9. Rejected attempts remain part of history; they must not mutate the registry or unlock the action.
10. Save/reload must not re-run an already resolved attempt, re-emit events, duplicate adoption, or alter RNG continuation.

Recommended significant event kinds, adapted to current naming conventions:

```text
problem_pressure_recognized
discovery_attempted
discovery_rejected
discovery_validated
knowledge_exposed
knowledge_adopted
affordance_unlocked
institution_adopted_discovery
```

Do not emit a noisy event every day merely because pressure still exists.

---

## 8. Phase Sequence

| Subphase | Name | Main proof |
|---|---|---|
| 8.0 | Entry Boundary | Phase 7 remains unchanged and the Phase 8 seam is identified |
| 8A | Civilization Registries | The world can represent primitives, knowledge, and bounded affordances |
| 8B | Problem Pressure | Discovery begins from causal repeated evidence |
| 8C | Experiment and Validation | Eligible agents can pay costs and produce accepted or rejected candidates |
| 8D | Knowledge Diffusion | Validated knowledge spreads through real exposure, not omniscience |
| 8E | Affordance Expansion | Adoption makes one previously impossible action available |
| 8F | Institutionalization | A validated procedure can change later institutional opportunity |
| 8G | Counterfactual Exit Gate | Replay, persistence, causal integrity, and changed futures are proven |

Each subphase below is an implementation milestone and should end in one cohesive commit.

---

# PHASE 8.0 — Entry Boundary and Behavior-Preserving Seam

## Objective

Prepare the smallest architecture boundary required for Phase 8 without changing simulation outcomes.

## Required work

1. Verify the current clean baseline, schema version, and full suite.
2. Locate current ownership of:
   - action availability and execution;
   - skill improvement and training costs;
   - institutional training approval/denial;
   - cultural/information transmission;
   - event creation and causal links;
   - snapshots, counterfactual forks, persistence, and validation;
   - world tick/day orchestration.
3. Produce a short responsibility map in the completion report, not a new planning document.
4. Extract only a clearly necessary Phase 8 domain seam if adding the feature directly would otherwise place unrelated logic into `world.py`.
5. Preserve byte-for-byte or semantic equivalence of existing deterministic fixtures, using the repository's existing comparison style.

## Do not

- Refactor the entire world orchestrator.
- Rename unrelated models or event kinds.
- Introduce Phase 8 tables or mechanics before their owner is clear.
- Add abstractions with only hypothetical future consumers.
- Change the RNG call order.

## Focused proof

- Existing deterministic replay fixture remains identical.
- Existing save/reload equivalence remains identical.
- Existing counterfactual snapshot behavior remains identical.
- Full pre-Phase-8 suite passes.

## Exit criteria

```text
✓ Phase 7 behavior unchanged
✓ Phase 8 domain owner identified
✓ world.py remains orchestration-focused for the new feature
✓ no speculative framework added
✓ full suite green
```

---

# PHASE 8A — Civilization Registries and Base Primitives

## Objective

Create the minimum persistent representation for engine-defined primitives, validated knowledge, and knowledge-backed action affordances.

## Required behavior

1. Define the minimum structured records from Section 6, reusing existing models where possible.
2. Seed only the primitives required by the peer-training vertical slice.
3. Store primitive definitions separately from per-world discoveries if the current persistence architecture distinguishes definitions from mutable state.
4. Give each world an initially empty validated-knowledge set except for explicitly defined baseline knowledge.
5. Provide deterministic registry lookup, canonical ordering, duplicate prevention, and integrity validation.
6. Add persistence only for mutable world-specific state. Do not persist derivable duplication without a proven need.
7. Increment the schema only if persistent shape changes. Starting from v17 suggests v18, but Codex must follow the actual repository migration sequence rather than force this number.
8. Old supported saves must load with the correct empty/default civilization state according to existing migration policy.

## Registry laws

```text
primitive exists before use
knowledge points to one valid origin
affordance points to validated knowledge
all effect operations are whitelisted
all numeric values are finite and bounded
ids and signatures are stable
```

## Focused tests

- New world receives the expected minimal primitives in deterministic order.
- Empty world has no peer-training knowledge or affordance.
- Duplicate/corrupt registry entries are rejected.
- Registry state survives save/reload.
- Legacy persistence fixture loads with safe defaults.

## Exit criteria

```text
✓ minimal registry model exists
✓ no action is unlocked merely by registry creation
✓ persistence and migration are valid
✓ definitions cannot execute arbitrary behavior
✓ focused tests pass
```

---

# PHASE 8B — Causal Problem Pressure and Discovery Eligibility

## Objective

Make discovery respond to repeated experienced constraints rather than random invention rolls or omniscient world inspection.

## Reference signal

Use existing training outcomes as evidence:

```text
training request
→ institutional denial, unaffordable cost, or inaccessible opportunity
→ affected agent experiences no skill progress
→ repeated evidence accumulates
→ bounded problem pressure becomes recognizable
```

The exact qualifying training outcomes must reuse current semantics. Do not invent a second training denial system.

## Required behavior

1. Derive pressure from existing causal events or action results visible to the affected agent/group.
2. Accumulate a bounded count/severity without creating unbounded histories inside agent state.
3. Retain causal evidence references.
4. Define a clear threshold for recognition and keep it in one named policy/configuration location.
5. Eligibility must require:
   - recognized unresolved pressure;
   - relevant developed capability/skill or reasoning threshold already present in the model;
   - possession/exposure to required base primitives;
   - enough time/energy/resources to attempt experimentation;
   - any existing age or action constraints that logically apply.
6. Agents without experience or causal information must not receive the signal.
7. Problem recognition alone does not guarantee an attempt or success.

## Anti-shortcut rules

- Do not scan the entire database and assign all problems to all agents.
- Do not add `wants_to_invent` as a free-floating random trait.
- Do not allow the developer fixture to fire on a fixed day.
- Do not treat one denial as a civilization-wide crisis unless the threshold explicitly supports it.
- Do not introduce a generic goal-planning engine.

## Focused tests

- Repeated qualifying evidence crosses the threshold on the expected day.
- Insufficient evidence does not create recognized pressure.
- A bystander without exposure does not gain the problem signal.
- Pressure evidence has valid causal parents.
- Same seed and inputs produce identical eligibility.
- Save/reload preserves recognized/unresolved pressure without duplicating it.

## Exit criteria

```text
✓ discovery has a causal reason to begin
✓ recognition depends on experienced evidence
✓ thresholds are bounded and inspectable
✓ no candidate or affordance exists yet
✓ focused tests pass
```

---

# PHASE 8C — Experimentation, Candidate Composition, and Validation

## Objective

Allow an eligible agent or small group to spend resources on a structured discovery attempt that can succeed or fail under world constraints.

## Required causal chain

```text
recognized problem
+ eligible proposer
+ possessed base primitives
+ available resources
→ attempt
→ immediate cost
→ canonical candidate
→ structural validation
→ seeded outcome resolution
→ rejected attempt OR validated knowledge
```

## Candidate model

The candidate should identify:

```text
problem addressed
primitives recombined
proposed bounded action/effect template
requirements
costs/trade-offs
proposer and evidence
```

For Phase 8, candidate generation may choose from a tiny engine-defined composition space. It does not need natural-language ideation, program synthesis, embeddings, or a universal recipe DSL.

## Validator responsibilities

The engine-owned validator must reject a candidate when:

- a primitive is unknown or not possessed;
- evidence/problem linkage is missing;
- effect operations are outside the whitelist;
- costs or effects are non-finite, negative where forbidden, or outside bounds;
- requirements are impossible or circular;
- the canonical discovery already exists;
- an affordance references unknown state;
- causal ordering is invalid.

An eligible and structurally valid attempt may still fail because the experiment outcome is insufficient. That outcome may use existing seeded randomness after deterministic score construction.

## Cost law

Every resolved attempt—successful or rejected—must have a visible cost paid at attempt time. Rejection must not refund the world unless a current general rule already supports recovery.

Minimum costs should reuse existing time/energy/money/stress semantics. Do not create a new resource model.

## Successful result

On success:

- create exactly one validated knowledge entry;
- attach it to the discoverer/group only;
- record origin and causal parents;
- do not make the new action globally available yet.

## Focused tests

- Ineligible proposer cannot attempt and pays no attempt cost.
- Eligible failed attempt pays cost, records rejection, and creates no knowledge.
- Structurally invalid candidate is rejected deterministically.
- Controlled successful attempt creates one knowledge entry with provenance.
- Primitive order cannot create duplicate signatures.
- Same seed resolves the same outcome and event order.
- Save/reload cannot re-resolve or duplicate the attempt.

## Exit criteria

```text
✓ attempts have causes and costs
✓ invalid candidates cannot mutate civilization
✓ success creates knowledge, not global magic
✓ failure remains causally observable
✓ kernel remains immutable
✓ focused tests pass
```

---

# PHASE 8D — Knowledge Possession, Exposure, and Diffusion

## Objective

Make validated knowledge spread through Phase 7's causal transmission infrastructure rather than becoming instant global truth.

## Required behavior

1. The discoverer/group initially possesses the knowledge.
2. Other agents require a valid route such as:
   - direct social-information exposure;
   - school/institution exposure after institutional adoption;
   - guardian exposure only where current developmental rules permit it.
3. Reuse Phase 7E accept/modify/reject response semantics where compatible.
4. A modified variant must remain inside validator bounds and retain lineage to the original knowledge. Phase 8 does not support variants that silently create a second unvalidated effect.
5. Rejection records exposure history but grants no affordance.
6. Repeated exposure must follow the current cultural-history policy and must not emit duplicate adoption.
7. Distance, relationship, institution, or information access must matter wherever the existing transmission system already makes them causal.

## Important distinction

```text
validated in world registry ≠ known by every agent
exposed ≠ adopted
adopted ≠ successfully used
```

## Focused tests

- Discoverer knows the discovery immediately after validation.
- Unexposed agent does not know it.
- Valid social exposure produces deterministic accept/modify/reject behavior.
- Rejected exposure does not unlock the action.
- Modified adoption preserves lineage and effect bounds.
- Save/reload preserves knowledge history and prevents duplicate exposure/adoption events.
- Counterfactual snapshot includes the new knowledge history.

## Exit criteria

```text
✓ knowledge is local before it diffuses
✓ diffusion reuses causal Phase 7 routes
✓ exposure and adoption are distinct
✓ no global broadcast shortcut exists
✓ focused tests pass
```

---

# PHASE 8E — Bounded Action-Space Expansion

## Objective

Prove that adopted knowledge changes what an agent can actually do, not merely what a history record says.

## Reference affordance

Validated peer-training knowledge may unlock a bounded peer-training action when:

```text
teacher knows/adopts procedure
+ learner is causally present/connected under current interaction rules
+ teacher has sufficient relevant skill
+ both satisfy time/energy constraints
+ learner consents/qualifies under existing action rules
→ peer-training action becomes selectable
```

## Required trade-off

Peer training must not be a universally superior replacement for school/formal training.

The reference balance should express:

```text
lower money or institutional-access requirement
+ non-zero teacher and learner time/energy cost
+ bounded skill progress
+ possible lower efficiency or reliability than formal training
+ relationship/exposure dependency
```

Reuse existing feedback and adaptive-learning signals. Do not create a second skill progression system.

## Required behavior

1. Before discovery/adoption, the action is absent or ineligible—not merely hidden in UI.
2. Registry data is converted into an action only through engine-owned bounded execution logic.
3. The action chooser may consider the new affordance using current scoring/selection rules. Do not replace the decision engine.
4. Execution validates preconditions again at action time.
5. Effects use the whitelisted operations and current numeric bounds.
6. Events identify the source knowledge and causal exposure/adoption history.
7. If the knowledge entry is unavailable in a counterfactual fork, the action cannot appear.

## Focused tests

- Baseline agent without knowledge cannot select or execute peer training.
- Adopted knowledge plus satisfied preconditions makes the action available.
- Missing teacher skill, relationship/exposure, time, or energy blocks execution as appropriate.
- Successful action has immediate costs and bounded skill progress.
- The new action does not bypass institutional denial by pretending formal approval occurred; it is a distinct causal route.
- Same seed produces identical selection, outcome, and causal event order.
- Save/reload preserves action availability without duplicating the registry entry.

## Exit criteria

```text
✓ possibility space genuinely expands
✓ expansion is knowledge-dependent
✓ execution remains bounded by kernel rules
✓ action has real trade-offs
✓ existing learning system receives the result
✓ focused tests pass
```

---

# PHASE 8F — Institutional Adoption and Inherited Opportunity

## Objective

Allow one existing institution to adopt a validated procedure after sufficient evidence, changing opportunity for later agents without granting the institution unrestricted agency.

## Required behavior

1. Reuse an existing school/training institution. Do not add a new institution type for this proof.
2. Institutional adoption requires inspectable evidence such as:
   - validated knowledge exists;
   - minimum adoption or successful-use evidence exists;
   - the institution has causal exposure to the knowledge;
   - existing policy/state permits adoption;
   - any bounded resource requirement is met.
3. Adoption is a state transition under engine rules, not an LLM decision.
4. Institutional rejection or non-adoption remains possible.
5. Adoption changes future opportunity only from its adoption day onward.
6. It must not rewrite past denials or retroactively teach agents.
7. Later eligible agents may encounter the adopted procedure through the institution's existing information/training path.
8. Preserve lineage from institution adoption to the original discovery attempt and evidence.

## Scope boundary

This subphase proves one institutionalization route. It does not create generic laws, governments, markets, religions, scientific academies, technology eras, or autonomous organization design.

## Focused tests

- Institution cannot adopt unknown or unvalidated knowledge.
- Insufficient evidence does not trigger adoption.
- Controlled evidence triggers adoption on the expected day.
- Opportunity before adoption remains unchanged.
- Opportunity after adoption changes through the institution's existing route.
- Institutional adoption survives save/reload.
- Same seed preserves adoption day and causal history.

## Exit criteria

```text
✓ discovery can become institutional state
✓ adoption has evidence and lineage
✓ later opportunity changes prospectively
✓ no new institution framework is created
✓ focused tests pass
```

---

# PHASE 8G — Persistence, Counterfactual Proof, Metrics, and Exit Gate

## Objective

Prove the complete Phase 8 chain as reproducible artificial history and close the phase without expanding into a second discovery domain.

## Required controlled experiment

Create one bounded integration scenario with a baseline and counterfactual fork.

### Discovery world

```text
training access problem accumulates
→ eligible attempt occurs
→ peer-training procedure validates
→ knowledge diffuses
→ at least one second agent adopts it
→ new peer-training action executes
→ optional school adoption occurs if the fixture naturally supports it
→ later skill opportunity/outcome changes
```

### Counterfactual world

Use the same seed and pre-intervention history, then remove or alter one causal input at the approved fork boundary, such as:

```text
the key problem evidence
OR the discovery attempt opportunity
OR the exposure that enables adoption
```

Expected result:

```text
history is identical before the fork
→ discovery chain is absent or delayed afterward
→ peer-training affordance is unavailable where knowledge is absent
→ later training trajectory differs for a traceable reason
```

Do not force the desired macro outcome through direct state editing after the fork.

## Required metrics

Add only compact research-facing outputs needed to inspect this phase:

```text
problem recognition day
attempt count
success / rejection count
validation day
time from recognized problem to validation
number of exposed and adopting agents
affordance first-use day
institution adoption day, if any
skill/opportunity delta versus counterfactual
```

Metrics must be derived from authoritative state/events where practical. Do not build a dashboard.

## Required verification

1. Same-seed fresh runs produce identical Phase 8 state and event history.
2. Continuous run equals save/reload continuation.
3. Snapshot/fork contains all Phase 8 state required for independent continuation.
4. Baseline and counterfactual histories are identical before the fork.
5. All new causal references resolve and are temporally valid.
6. Duplicate registry signatures, attempts, knowledge possession, adoption, and events are rejected or prevented.
7. Legacy saves continue to load according to supported migration policy.
8. Full suite passes.
9. Record a small performance comparison against the Phase 7 baseline if a benchmark harness already exists. Do not add a benchmarking framework solely for this item.

## Phase 8 exit criteria

```text
✓ one problem-driven discovery can succeed or fail
✓ validation protects the immutable kernel
✓ successful discovery creates structured knowledge
✓ knowledge spreads only through causal exposure
✓ adoption unlocks one bounded new action
✓ one existing institution can adopt the procedure
✓ later opportunity can differ because history changed
✓ same seed reproduces the discovery history
✓ save/reload equals continuous execution
✓ counterfactual divergence begins only after the fork
✓ causal history is valid
✓ no API key or LLM is required
✓ weak-hardware viability is preserved
✓ full test suite passes
✓ Phase 8 is documented and committed
```

---

## 9. Testing Policy

Tests must prove causal behavior, not maximize count.

For each subphase, prefer the smallest set covering:

```text
one successful path
one blocked or rejected path
one determinism/persistence invariant where state changes
one causal-integrity assertion where events are added
```

Use focused tests during implementation. Run the full suite at the end of every committed subphase or whenever shared core behavior changes.

Do not add:

- exhaustive combinations of every trait and threshold;
- hundreds of near-duplicate numeric boundary tests;
- artificial multi-generation or G2 fixtures;
- property-testing dependencies unless a real bug class justifies them;
- tests that mock away the problem → attempt → validation → diffusion chain;
- fragile assertions over internal implementation details when observable state is sufficient;
- performance tests with timing thresholds likely to vary across machines;
- a second reference discovery merely to claim genericity.

Manual probes are acceptable for exploratory evidence, but any rule required for Phase 8 acceptance must have an automated regression test.

---

## 10. Persistence and Migration Policy

1. Persist only state required to continue deterministically.
2. Use the repository's existing transaction and migration patterns.
3. Never silently drop Phase 8 history when loading.
4. Never rebuild resolved attempts in a way that consumes RNG again.
5. Validate foreign references for discoverers, agents, institutions, causal events, knowledge, and affordances.
6. Use stable serialized ordering for collection-like fields.
7. Old supported worlds receive safe empty/default civilization state; they do not retroactively invent peer training.
8. Counterfactual snapshots must include problem pressure, attempts, knowledge registry, agent knowledge history, affordance state, and institutional adoption.
9. Bump schema versions only when persistent representation changes, not for logic-only edits.

---

## 11. Performance Policy

Phase 8 remains Python-first.

No Rust migration is authorized. No performance rewrite is justified without measured evidence.

Implementation should avoid:

- scanning all events for every agent every day;
- pairwise all-agent diffusion checks when existing exposure routes already identify candidates;
- repeated reconstruction of registry indexes;
- unbounded problem evidence lists;
- large JSON blobs duplicated across agents;
- semantic similarity models for duplicate discovery detection;
- repeated database writes when no Phase 8 state changed.

Prefer:

```text
event-driven updates
bounded counters
canonical signatures
indexed lookups
existing exposure candidates
compact structured records
```

Optimization beyond these rules requires profiling.

---

## 12. Explicit Non-Goals

Phase 8 must not implement:

```text
LLM-generated discoveries
LLM dialogue, diaries, prayers, or narration
embeddings or vector databases
semantic duplicate detection
deep learning
Q-learning or a new RL policy
source-code generation or execution
arbitrary SQL/data mutation by NPCs
plugin or scripting systems
a general-purpose DSL
a complete technology tree
multiple discovery domains
scientific theory simulation
new religions, ideologies, laws, markets, or political systems
new institution types
procedural world generation
3D or frontend visualization
Rust migration
distributed services
G2 acceleration or artificial adult descendants
Ouroboros/recurrence detection
consciousness claims or Phase 10 architecture
```

If any of these becomes necessary to finish a listed acceptance criterion, stop and report the architectural contradiction instead of silently expanding scope.

---

## 13. Completion Report Template for Codex

At the end of each subphase, report only:

```text
Phase 8X is complete.

- Commit: <hash and message>
- Implemented: <compact behavior summary>
- Causal proof: <what controlled test demonstrates>
- Persistence/schema: <change or no change>
- Tests: <focused and full-suite result>
- Scope guard: <important deferred/non-goal preserved>
- Worktree: <clean or explain remaining user changes>
- Next: <next named subphase; awaits user instruction>
```

Do not restate the entire plan after every milestone.

---

## 14. Phase 8 Research Output

Once complete, the world should be able to answer:

```text
What recurring constraint motivated the discovery?
Which agent or group recognized it, and from what evidence?
What did the experiment cost?
Why did the validator accept or reject it?
Who initially knew the result?
Through which causal routes did it spread?
Who adopted, modified, or rejected it?
Which new action became possible?
Did an institution adopt it?
Which later opportunity changed?
What happened in the same seeded world without the key causal input?
```

These answers—not the number of invention types—are the success measure.

---

## Final Phase Principle

```text
developer defines the physics of possibility
agents encounter historically caused problems
agents recombine permitted primitives
validator protects the kernel
knowledge spreads through causal exposure
adoption expands bounded affordances
later agents inherit a changed world
```

> **Phase 8 succeeds when civilization changes because of traceable agent history while the engine remains sovereign, deterministic, persistent, and reproducible.**
