# THE PLAYING GOD — PHASE 6
## Society, Information & Institutions

**Document revision:** v1.0.0
**Prepared:** 2026-08-25
**Repository basis:** `IckeNount/The-Playing-God` / `main`
**Status:** READY FOR HUMAN REVIEW; after approval, begin **6A.0 only**
**Canonical destination:** `docs/phases/phase-06-society-information-institutions.md`

---

# 0. Document Role

This is the complete Phase 6 implementation brief for the coding agent.

It defines:

- why Phase 6 exists;
- what Phase 6 must prove;
- the exact subphase order;
- what each step may change;
- what each step must not change;
- minimal behavioral contracts;
- persistence and reproducibility requirements;
- focused test policy;
- anti-overengineering limits;
- completion gates;
- the bridge into Phases 7, 8, 9, and eventually Phase 10.

It does **not** prescribe exact class names, private helper names, folder restructuring, line-by-line code, or speculative architecture.

Codex is trusted to implement locally sensible details within the boundaries below.

Codex is **not** authorized to expand research scope.

---

# 1. Thesis Anchor

## Computer Engineering identity

**The Playing God is a Master of Computer Engineering thesis project.**

The world simulation is the experimental medium. The engineering problem is the actual thesis core:

> **How can a resource-constrained computer system generate, persist, reproduce, inspect, and experimentally compare long-term emergent behavior in autonomous artificial agents without continuous LLM inference or manually scripted stories?**

Phase 6 focuses that problem on the micro-to-macro transition:

> **How can local autonomous decisions operating under shared scarcity, institutional constraints, information flow, and social thresholds produce inspectable macro-level behavior while preserving causal traceability and reproducibility?**

The long-term direction remains:

```text
autonomous individuals
→ persistent lives
→ causal social contact
→ society
→ generations
→ culture
→ discovery
→ experimental artificial history
→ cognitive interior research
→ recursive reality
```

Phase 6 is therefore **not “add civilization features.”**

It is the first controlled engineering layer where:

```text
MICRO
individual choices
+
shared constraints
+
network interaction
↓
MESO
institutions / information / groups
↓
MACRO
employment patterns / inequality / diffusion / collective behavior
```

must remain explainable in reverse.

---

# 2. Phase 6 Objective

## Purpose

Allow individual lives to produce collective systems without losing deterministic reproducibility, weak-hardware viability, or causal inspectability.

## Phase 6 canonical sequence

```text
6A Economy
→ shared scarcity and cross-agent resource competition

6B Institution
→ a rule-bearing shared structure constrains opportunity

6C Information Diffusion
→ beliefs can propagate through existing social contact

6D Collective Action
→ individual thresholds can create a group-level cascade
```

## Final Phase 6 exit condition

A seeded run must demonstrate at least one traceable chain of this form:

```text
shared economic condition
→ affects Agent A
→ Agent A acts / experiences outcome
→ structured information reaches Agent B
→ Agent B's belief changes
→ multiple agents cross a participation threshold
→ collective event emerges
→ macro metric changes
```

The system must be able to inspect the chain backward through:

```text
macro outcome
→ collective participants
→ received information
→ relationships / encounters
→ individual decisions
→ economic / institutional conditions
```

No LLM is required.

---

# 3. Current Repository Baseline

Phase 6 begins from a verified Phase 5 foundation.

Current relevant mechanisms already exist:

```text
Agent
├── money
├── employed
├── salary
├── job_level
├── skill
├── stress
├── reputation
├── relationships
├── social graph
├── location / mobility
├── observations
├── beliefs
├── prayers
├── faith / attribution
└── structured events
```

Current economic behavior already includes:

```text
work
→ wage income

job_hunt
→ probabilistic employment

train
→ skill gain for money / energy

help
→ resource transfer between agents

risky_move
→ stochastic gain / loss

end_day
→ living expense

unemployment / debt
→ stress pressure
```

Important limitation:

> These are **individual economic variables**, not yet a shared economy.

At present, one NPC obtaining employment does not materially reduce another NPC's opportunity to obtain employment. There is no shared labor capacity, no persistent institution state, no general social testimony channel, and no collective threshold mechanism.

Phase 6 adds these one layer at a time.

---

# 4. Existing Economic Flow Audit

Before changing behavior, Codex must understand the existing money flow.

Conceptually classify current flows as:

| Flow | Current meaning | Phase 6 treatment |
|---|---|---|
| Salary income | money source | preserve initially |
| Daily living cost | money sink | preserve initially |
| Training/socializing/rest cost | money sink | preserve initially |
| Help | partial transfer between agents | preserve behavior initially; document the untransferred remainder as existing model friction rather than inventing a new explanation |
| Risky gain | money source | preserve initially |
| Risky loss | money sink | preserve initially |
| Negative money | debt-like state | preserve initially |

Phase 6A does **not** need monetary conservation.

Do not rewrite the project into a closed macroeconomic model.

The first research mechanism is **shared scarcity**, not realistic banking.

---

# 5. Global Execution Contract for Codex

These rules apply to every Phase 6 step.

## 5.1 Execute one step at a time

Codex must not implement all of Phase 6 in one patch.

Order:

```text
6A.0
→ review
→ 6A.1
→ 6A.2
→ 6A.3
→ 6A exit review
→ 6B...
```

Do not begin the next numbered step until the previous step satisfies its completion check.

## 5.2 No bureaucracy loop

For an approved step:

```text
read owning files
→ implement
→ focused tests
→ necessary regression
→ update concise project state
→ human review
```

Do **not** create another specification, architecture proposal, implementation proposal, approval document, or review-plan document unless a newly discovered architectural ambiguity makes implementation genuinely unsafe.

This file is already the implementation brief.

## 5.3 Runtime/test file budget

Target per implementation step:

```text
1–3 runtime files
1–2 focused test files
```

A persistence step may additionally modify:

```text
sqlite_store.py
test_persistence.py
test_reproducibility.py
```

Documentation files do not count toward the runtime-file target.

If a supposedly small step suddenly requires broad changes across many unrelated subsystems, stop and report the architectural reason rather than refactoring the universe recreationally.

## 5.4 Dependency budget

Phase 6 should add **zero new third-party runtime dependencies** unless an existing requirement cannot perform the task.

Do not add:

```text
Pandas
NumPy
Mesa
Redis
Celery
Kafka
RabbitMQ
vector databases
LLM frameworks
web services
microservices
containers
cloud infrastructure
new graph frameworks
```

NetworkX, SQLite, Python stdlib, and existing project code are sufficient.

## 5.5 Testing budget

For each step:

1. Add the smallest focused tests proving the new behavior.
2. Prefer deterministic setup over running huge stochastic simulations.
3. Test externally meaningful contracts, not every private helper.
4. Do not create combinatorial test matrices for every trait value.
5. Do not create property-based testing infrastructure unless a real defect demonstrates need.
6. Do not add performance benchmarks without a measured performance problem.
7. Run the full regression suite only when shared world state, persistence, RNG behavior, or a cross-subsystem boundary changes, or at subphase exit.

Typical focused-test target:

```text
4–8 meaningful assertions/scenarios per new subsystem
```

This is guidance, not a quota to manufacture eight tests.

## 5.6 Fixture protection

Do not refresh existing historical fixtures merely because Phase 6 produces new behavior.

If an old fixture fails:

```text
first determine whether
A) old verified behavior was accidentally broken
or
B) Phase 6 intentionally changes the contract
```

An intentional determinism migration must be stated explicitly before fixture replacement.

## 5.7 RNG rule

All causal randomness continues to come from approved deterministic RNG sources.

Prefer designs that **do not add RNG draws** when a deterministic mechanism is sufficient.

When inserting a new condition into an existing stochastic path, preserve existing draw allocation when practical.

Example:

```python
roll = rng.random()  # existing draw still occurs
if vacancy_exists and roll < chance:
    hire()
```

rather than silently skipping the draw whenever no vacancy exists.

Do not migrate to keyed/substream RNG inside Phase 6.

That is a Phase 9 research-methodology decision because it changes the simulation kernel and counterfactual interpretation.

## 5.8 No speculative abstractions

Do not build:

```text
BaseInstitution
InstitutionFactory
PolicyEngine
UniversalResourceRegistry
GenericMessageBus
EventSourcingFramework
EconomyPluginSystem
CollectiveBehaviorFramework
```

unless a second real use case has already appeared and duplication creates an actual problem.

Prefer one concrete working mechanism over a cathedral awaiting fictional future requirements.

---

# 6. Phase 6A — Minimal Shared Economy

**Document scope version:** 6A-v1
**Purpose:** Convert independent money/employment variables into the smallest shared economic constraint capable of producing cross-agent consequences.

## 6A non-goals

Do not add:

```text
companies
banks
loans
interest
currency supply
stock markets
price simulation
production chains
inventory systems
taxation
welfare state
rent markets
multiple occupations
business ownership
macroeconomic equations
```

Those are possible future mechanisms only if research requires them.

---

## Step 6A.0 — Economic Baseline Audit

### Goal

Confirm the actual ownership and side effects of existing employment, salary, help, risk, daily expense, and debt behavior before modifying it.

### Required work

Codex should inspect only the relevant symbols in:

```text
src/playing_god/core/agent.py
src/playing_god/core/decision.py
src/playing_god/core/world.py
src/playing_god/persistence/sqlite_store.py
relevant existing tests
```

Produce a concise implementation note in the working response identifying:

```text
money sources
money sinks
money transfers
employment creation
employment destruction
RNG draws touching economic outcomes
persistence fields
```

### Code changes

Prefer **none**.

Only fix a baseline bug if it blocks Phase 6A and is clearly demonstrated.

### Test requirement

No new tests merely for doing the audit.

### Exit condition

Codex can state precisely where employment and money are currently changed and which random draws those paths consume.

---

## Step 6A.1 — Shared Labor Capacity

### Research mechanism

Employment becomes a scarce shared world resource.

```text
finite job capacity
→ vacancies
→ competing job seekers
→ one hire changes opportunity for others
```

### Minimal model

Introduce one small world-level economic state representing labor capacity.

Conceptually:

```text
EconomyState
├── job_capacity
├── occupied_jobs
└── vacancies
```

Exact implementation details are Codex's choice.

Avoid a generic economy framework.

### Initialization

Preserve all currently initialized employed agents.

A deterministic initial capacity may be derived from the current initialization assumption:

```text
capacity = max(
    currently_employed_count,
    round(population * 0.70)
)
```

The exact rounding rule must be deterministic and tested.

Reason:

- current worlds already initialize employment near 70%;
- no existing employed agent should become invalid merely because the shared market was introduced;
- the shared market can still begin with a small number of vacancies.

### Hiring rule

The existing `job_hunt` action remains responsible for willingness and hiring probability.

New condition:

```text
job_hunt selected
+
existing success probability
+
vacancy available
→ employment may be gained
```

If no vacancy exists:

```text
job hunt can fail because the shared opportunity does not exist
```

Do not invent a second employment decision engine.

### Job release rule

Ordinary firing/job loss releases an occupied slot unless the event explicitly represents removal of the slot itself.

For the first 6A foundation, keep this simple.

Do not build business-cycle dynamics yet.

### Causal trace requirement

A hiring or failed-hiring outcome must be explainable from:

```text
agent chose job_hunt
→ market vacancy state
→ existing hiring probability / roll
→ outcome
```

### Focused tests

Minimum useful scenarios:

1. Initial economy state never has fewer slots than already-employed agents.
2. Occupied jobs never exceed capacity.
3. Two unemployed agents cannot both consume one vacancy.
4. A released slot can later be filled.
5. Same seed/setup produces the same economic result.

Do not create dozens of employment permutations.

### Likely runtime ownership

Prefer something like:

```text
new small core economy module
world integration
focused economy tests
```

Do not modify persistence yet unless the implementation cannot remain isolated without it.

### Exit condition

At least one deterministic test demonstrates:

```text
Agent A gets the last vacancy
→ Agent B's opportunity is now different
```

That is the first true economic cross-agent causal link.

---

## Step 6A.2 — Economic State Persistence

### Goal

A save/load boundary must not recreate or forget shared labor scarcity.

### Persistence direction

Advance SQLite schema only once the in-memory behavior is accepted.

Likely conceptual addition:

```text
economy_state
- job_capacity
```

Occupied jobs should normally be derivable from persisted agent employment state unless storing occupancy separately is necessary for integrity.

Do not duplicate the same truth into multiple tables without a reason.

### Migration rule

Legacy schema <=9 worlds have no shared labor state.

When loading a legacy world, initialize Phase 6 economy deterministically from the loaded population and current employment state.

Do not consume RNG during migration.

The migration must not invalidate already-employed agents.

### Required tests

1. save/load preserves job capacity;
2. split run equals uninterrupted run under the new economy;
3. legacy world loading creates valid deterministic Phase 6 economy state;
4. no occupied-jobs > capacity invariant violation after load.

### Regression

Run full suite after persistence integration.

Do not fix unrelated SQLite warnings unless the change directly touches their root cause and the fix is small. Existing warning cleanup is not permission for a persistence refactor.

### Exit condition

Restarting the simulation preserves the exact shared economic constraint.

---

## Step 6A.3 — Minimal Macro Metrics

### Purpose

Make shared economic outcomes observable without introducing an analytics stack.

### Add a read-only economic snapshot/summary

Minimum metrics:

```text
population
employed_count
unemployed_count
employment_rate
job_capacity
vacancies
total_agent_money
median_agent_money
negative_balance_count
```

Optional only if trivial and clearly useful:

```text
wealth range
```

Do not add Gini, Lorenz curves, dashboards, CSV pipelines, Pandas, or visualization yet.

### Important rule

Metrics are **derived observation**, not causal state.

Calling the metric function must not mutate the world or consume RNG.

### Focused tests

Verify:

- counts are correct for a manually prepared small world;
- metrics are deterministic;
- metrics do not mutate agents or RNG state.

### Exit condition

The simulation can state a system-level employment/economic condition derived from individual states.

---

## 6A Exit Review

Phase 6A is complete when:

```text
one agent's employment outcome can alter another's opportunity
+
shared capacity persists across restart
+
macro employment/wealth state is inspectable
+
same seed remains reproducible
```

Before starting 6B, update only:

```text
docs/STATUS.md
docs/PROJECT_MAP.md
.agent/memory/CURRENT.md
```

with concise completed-state information.

Do not create a 6A retrospective document.

---

# 7. Phase 6B — First Rule-Bearing Institution

**Document scope version:** 6B-v1
**Purpose:** Prove that a shared structured entity can constrain agent opportunities through explicit rules and capacity.

## Choice for the first institution

Use the already-existing **school** location and `train` behavior.

Do not begin with government, courts, police, banks, political parties, or religion.

Why school:

```text
existing location exists
existing training behavior exists
existing skill state exists
existing training cost exists
```

Therefore the institution can be introduced without inventing an entire new societal domain.

## 6B non-goals

Do not implement:

```text
education curriculum
teachers
student identities
degrees
multiple schools
school politics
school finance
institution inheritance
institution AI agents
generic policy language
```

---

## Step 6B.1 — School Capacity as Institutional Rule

### Core mechanism

Currently:

```text
agent chooses train
→ training happens
```

Phase 6B:

```text
agent chooses train
→ travels to school
→ school capacity/rule is checked
→ admitted or denied
→ outcome recorded
```

### Minimal persistent institution state

Conceptually:

```text
SchoolState
├── location = school
└── daily_training_capacity
```

Do not generalize to `InstitutionFactory`.

If later a second institution shares enough structure, generalize then.

### Admission

Use the existing daily agent processing order as the first competition mechanism unless doing so breaks a verified invariant.

Do not add a new admissions RNG solely to make the system feel realistic.

A simple rule is sufficient:

```text
first eligible training attempts up to daily capacity succeed
later attempts are denied for that day
```

Because daily world order is already seeded/shuffled, access remains reproducible but not permanently fixed by agent ID.

### Denied attempt semantics

Keep them minimal and explicit.

A denied agent should not receive skill gain or pay the full training cost.

Travel costs already paid through movement remain normal world consequences.

A small causal event may record denial only when useful for inspection.

Do not invent humiliation, injustice, resentment, or political grievance variables.

### Focused tests

1. training succeeds while capacity exists;
2. capacity cannot be exceeded in one day;
3. denied agent receives no skill increase;
4. next day capacity resets;
5. seeded order yields reproducible admission outcome.

### Exit condition

Two agents can want the same institutional opportunity, and the institution's explicit rule determines that only one receives it.

---

## Step 6B.2 — Institution Persistence and Inspection

Persist only the institution state that must survive restart.

If daily capacity resets every day and the institution has no changing long-term field, avoid storing redundant state.

If a persistent field is introduced, persist only that field.

This step may legitimately require **no schema change**.

Codex must not create a table merely because the roadmap contains the word “institution.”

Add a read-only inspection method only if current reports cannot expose the rule/outcome clearly enough.

### Exit condition

Institutional constraints behave identically across split and uninterrupted runs.

---

## 6B Exit Review

Phase 6B is complete when the system can explain:

```text
why Agent A could train
why Agent B could not
which institutional rule caused the difference
```

The point is rule-mediated opportunity, not educational realism.

---

# 8. Phase 6C — Information & Belief Diffusion

**Document scope version:** 6C-v1
**Purpose:** Allow structured information to travel through actual social contact and alter beliefs without omniscient broadcasting.

## Existing foundation to reuse

Phase 5 already provides:

```text
Observation
Perception
Belief
source_id
reliability
location/context
social relationships
co-location
interactions
```

Phase 6C must extend this system rather than create a parallel message universe.

## 6C non-goals

Do not add:

```text
LLM-generated rumors
semantic embeddings
vector search
social media feeds
news websites
full ideology models
propaganda campaigns
language generation
natural-language fact checking
knowledge graphs
```

---

## Step 6C.1 — Structured Testimony

### Core mechanism

An NPC can communicate a structured claim it has evidence for.

Conceptually:

```text
source belief / experienced fact
→ interaction with another NPC
→ testimony
→ recipient observation
→ normal perception/belief update
```

### Minimal information object

Create the smallest structured representation required to prevent raw string conventions from spreading everywhere.

Conceptually:

```text
InformationItem
├── id
├── kind/topic
├── subject_id
├── value
├── origin_agent_id
├── origin_day
└── reliability
```

Do not create a universal messaging framework.

### Initial content scope

Start with one inspectable claim type tied to an existing world fact.

Recommended first claim:

```text
employment status of another known NPC
```

Why:

- Phase 6A already makes employment socially relevant;
- truth is available to the simulation for evaluation;
- the recipient need not be omniscient;
- stale information can naturally become incorrect later.

Example:

```text
Noah knows Mira lost her job
→ Noah later interacts with Lina
→ testimony reaches Lina
→ Lina forms belief: Mira unemployed
→ Mira may later get a job
→ Lina's belief can remain stale until new evidence arrives
```

### Transmission condition

Information may transmit only through a valid interaction/exposure path.

Use deterministic relevance/trust logic first.

Do not add a new RNG draw unless deterministic selection produces an obviously unusable system.

Possible inputs:

```text
source familiarity
source trust
information recency
information significance
recipient existing confidence
```

The exact small scoring rule is Codex's implementation choice.

### Truth boundary

The simulation knows world truth.

The agent receives testimony.

These are not equivalent.

```text
WORLD TRUTH
≠
SOURCE BELIEF
≠
MESSAGE
≠
RECIPIENT BELIEF
```

A source may repeat stale information without the simulation rewriting history to make it true.

### Focused tests

1. no interaction means no testimony transfer;
2. valid interaction can create recipient observation;
3. source identity is preserved;
4. recipient belief updates through the existing perception system;
5. stale testimony can produce a belief different from current world truth;
6. repeating the same seeded scenario is exact.

### Exit condition

A fact known by Agent A can reach Agent C through Agent B without direct A↔C contact, and the complete path is inspectable.

---

## Step 6C.2 — Multi-Hop Diffusion Boundaries

Enable repeated transmission only after direct testimony works.

### Rule

A recipient may later become a source, but reliability/confidence must not silently increase just because the message traveled farther.

A simple bounded decay or source-confidence transformation is sufficient.

Example concept:

```text
A firsthand reliability = 0.9
A → B testimony
B's resulting belief confidence = 0.7
B → C testimony reliability <= B's confidence
```

Do not implement sophisticated Bayesian networks.

### Loop protection

Prevent trivial information amplification loops such as:

```text
A tells B
B tells A
A treats B's repetition as independent confirmation
→ confidence approaches 1.0 forever
```

The smallest solution may track origin information identity/evidence identity so circular repetition is not treated as fresh independent evidence.

Do not build a distributed-systems deduplication framework.

### Focused tests

- multi-hop path works;
- confidence does not increase through pure repetition;
- circular repetition does not create unlimited confidence;
- source/origin remains inspectable.

### Exit condition

Information can diffuse through the social graph without becoming magical omniscience or self-confirming infinite confidence.

---

## Step 6C.3 — Diffusion Metrics

Add read-only metrics only after the mechanism works.

Minimum:

```text
number of informed agents for one information item
number of hops from origin
average/median belief confidence among informed agents
```

Optional:

```text
time to reach N agents
```

No plotting library changes are required.

### Exit condition

A researcher can quantify how far one structured claim propagated.

---

# 9. Phase 6D — Collective Action / Threshold Cascade

**Document scope version:** 6D-v1
**Purpose:** Demonstrate that local pressure plus social confirmation can produce a group-level event without hard-coding a “revolutionary” NPC.

## Initial collective behavior

Use a generic **public demonstration / coordinated gathering** at the existing `park` location.

Do not begin with revolution, coup, war, riot, or political ideology.

The engineering mechanism is threshold participation.

## 6D non-goals

Do not add:

```text
political parties
government simulation
police
combat
weapons
warfare
elections
constitutions
revolution scripts
ideology sliders
```

---

## Step 6D.1 — Participation Pressure

### Core mechanism

Each NPC may have a dynamically calculated willingness to join a collective action.

Do not add a permanent trait named:

```text
protest_tendency
revolutionary
activist
```

Derive willingness from existing mechanisms.

Conceptual inputs:

```text
economic pressure
unemployment / debt
risk tolerance
social ties
trusted information
observed participation
current stress
```

Conceptually:

```text
participation_score
=
personal_pressure
+ social_confirmation
+ trusted_information
+ social_motivation
- perceived_cost
- risk_aversion
```

The exact coefficients should remain few, readable, and justified as simulation parameters rather than claims about real human behavior.

### Threshold

Participation occurs only when score passes a threshold and the action remains available/selected under the ordinary decision process.

Prefer adding the smallest normal action integration rather than a separate collective-action scheduler that bypasses autonomy.

### Movement

Participation routes to the existing `park` through normal mobility.

No teleportation.

### Exit condition

One agent can have high personal pressure yet still stay home; another may join because trusted social confirmation pushes the score over threshold.

---

## Step 6D.2 — Cascade

### Core mechanism

Participation becomes visible evidence to others through ordinary interaction/information channels.

```text
first participants
→ visible / communicated participation
→ social confirmation rises for connected agents
→ more thresholds crossed
→ gathering grows
```

This is a threshold cascade, not a scripted event sequence.

### Important restriction

Do not write:

```python
if participants >= 3:
    everyone_protests()
```

Each agent must still satisfy its own calculated participation condition.

### Controlled test scenario

Create a small deterministic world state where:

```text
Agent A: already above threshold
Agent B: just below threshold, trusts A
Agent C: low pressure, remains below threshold
```

After A's participation becomes known:

```text
B crosses threshold
C does not
```

This is a much stronger test than hoping a 365-day random run happens to look dramatic.

### Exit condition

A group-level participation event grows through local thresholds rather than central orchestration.

---

## Step 6D.3 — Collective Metrics and Causal Inspection

Minimum read-only metrics:

```text
participants
participation_rate
first_participant_day
peak_participants
cascade_depth / generations if cheap to derive
```

The researcher must be able to inspect, for one participant:

```text
personal pressure
trusted information/social evidence
threshold result
decision
movement
participation event
```

No visualization required.

---

# 10. Phase 6 Final Integration Test

Do not create a giant end-to-end suite.

Create one deliberate, small integration scenario proving the Phase 6 thesis mechanism.

Example:

```text
1. Labor capacity is scarce.
2. Agent A loses/obtains the last opportunity.
3. Agent B remains unemployed and economic pressure rises.
4. Employment information spreads through valid interactions.
5. Agent B receives trusted social confirmation of shared economic pressure.
6. Agent A or B joins a public gathering.
7. Another connected agent crosses its threshold.
8. At least one lower-pressure agent does not join.
9. Macro employment and participation metrics are inspectable.
10. Save/load continuation reproduces the same result.
```

The exact narrative is not the contract.

The causal structure is.

---

# 11. Phase 6 Completion Criteria

Phase 6 is complete only when all are true:

## Economy

- employment opportunity is shared/scarce;
- one agent's outcome can alter another's opportunity;
- shared state persists;
- macro economic state is inspectable.

## Institution

- at least one explicit rule-bearing shared structure exists;
- its limited capacity changes individual outcomes;
- institutional effects are traceable.

## Information

- information travels only through valid causal contact;
- recipient belief remains distinct from truth;
- multi-hop diffusion works;
- circular repetition cannot create unlimited confidence.

## Collective action

- participation is derived, not a personality label;
- social confirmation can push some agents across a threshold;
- collective behavior can grow without central scripting;
- some agents can rationally remain outside the cascade.

## Engineering

- full suite passes;
- save/load remains valid;
- split-run reproducibility remains valid;
- no LLM/API is required;
- no new infrastructure dependency was introduced;
- Phase 1–5 verified behavior is preserved except explicitly approved Phase 6 behavior migrations.

## Research

The system can answer:

```text
What macro behavior occurred?
Which agents produced it?
What did each agent know?
Who influenced whom?
What shared constraint existed?
Which institutional rule mattered?
Where did the causal chain begin?
Would the run reproduce from the same seed?
```

---

# 12. Explicitly Out of Scope for Phase 6

```text
reproduction
pregnancy
children
inheritance
generational development
mortality model
Ouroboros
technology invention
open-ended action creation
culture registry
institution creation by NPCs
large-scale politics
war
international relations
semantic embeddings
vector databases
RL/ML expansion
neural world models
consciousness
self-model
reality-questioning
rebellion architecture
LLM dialogue
game UI / 3D world
cloud deployment
CI/CD expansion
MLOps
microservices
```

If Codex attempts to implement any of these because they “fit naturally,” stop it.

Natural adjacency is how software projects turn into geological formations.

---

# 13. Phase 6 Suggested File Ownership

This is navigation guidance, not mandatory architecture.

Likely new focused modules:

```text
src/playing_god/core/economy.py
src/playing_god/core/information.py
src/playing_god/core/collective.py
```

The first institution may remain small enough to live in a focused module such as:

```text
src/playing_god/core/institution.py
```

but do not create it until 6B starts.

Expected existing integration points:

```text
src/playing_god/core/world.py
src/playing_god/core/decision.py
src/playing_god/core/agent.py
src/playing_god/core/perception.py
src/playing_god/core/mobility.py
src/playing_god/persistence/sqlite_store.py
```

Expected focused tests:

```text
tests/test_economy.py
tests/test_institution.py
tests/test_information.py
tests/test_collective.py
```

Use existing persistence/reproducibility tests for cross-cutting state rather than duplicating them into every new test file.

---

# 14. Documentation & Memory Update Policy

After each **completed subphase**, not every microscopic step, update:

```text
docs/STATUS.md
docs/PROJECT_MAP.md
.agent/memory/CURRENT.md
```

Update `AGENTS.md` only if a genuinely durable coding-agent rule changes.

Update `ROADMAP.md` only if the accepted research direction changes.

Do not copy the entire Phase 6 brief into memory files.

Memory should preserve:

```text
what is complete
important architectural decision
important rejected approach
known blocker
next logical task
```

---

# 15. Versioning Policy

The repository already uses stable phase-based filenames.

Preserve that convention.

## Canonical parent

```text
docs/phases/phase-06-society-information-institutions.md
```

Document revisions change **inside the header**, not by creating filename clutter.

```text
v1.0.0  initial approved Phase 6 scope
v1.1.0  meaningful scope clarification without changing phase identity
v1.1.1  wording / test clarification / non-behavioral correction
v2.0.0  major redesign requiring human approval
```

## Subphase implementation identifiers

Use phase-step identifiers for engineering progress:

```text
6A.0
6A.1
6A.2
6A.3
6B.1
6B.2
6C.1
6C.2
6C.3
6D.1
6D.2
6D.3
```

These are **not document versions**.

Do not confuse:

```text
Phase 6A.1
```

with:

```text
Phase 6 document v1.1
```

## Separate subphase briefs

Do **not** create four more detailed briefs immediately.

This file is sufficient to begin.

Create a dedicated file such as:

```text
docs/phases/phase-06a-economy.md
```

only if implementation discovers enough legitimate complexity that the parent brief becomes ambiguous.

Otherwise additional plan files would merely make Codex reread the same decisions in more places.

---

# 16. Required Codex Completion Report Format

After each step, Codex should respond compactly with:

```text
Milestone: 6A.1 — Shared Labor Capacity
Status: PASS / BLOCKED

Files changed:
- ...

Behavior proven:
- ...

Tests:
- focused: ...
- full regression: not required / pass

Intentional behavior migration:
- none / describe

Next step:
- 6A.2 — Economic State Persistence
```

Do not generate a new implementation plan after the step unless blocked by a real design ambiguity.

---

# 17. Bridge to Phase 7–9 Before Consciousness Research

Phase 10 must not begin after Phase 6.

The society still needs developmental history, endogenous discovery, and research instrumentation first.

The current roadmap direction is correct, but the following subphase decomposition should make the missing prerequisites explicit.

---

## Phase 7 — Development, Reproduction & Generations

### Thesis purpose

Replace arbitrary adult initialization with agents whose later state is a consequence of simulated development.

### Recommended subphases

```text
7A — Founder Prehistory
Generate compact deterministic causal backstories for G0 adults.

7B — Family / Reproduction Foundation
Pairing/family constraints, birth events, parent links, bounded inherited priors.

7C — Child Development
Age-dependent capability development from exposure, resources, relationships, education, and experience.

7D — Household / Inheritance / Mortality
Minimal household resources, inheritance, aging, death/retirement so population does not only grow forever.

7E — Cultural Transmission
Norms/knowledge passed across family/social/institutional relationships.

7F — Ouroboros Detector
Only after enough generations exist: structured state/trajectory similarity; detect recurrence, never force it.
```

### Important missed item now made explicit

**Mortality / lifecycle exit** belongs in Phase 7.

A multi-generation simulation without a bounded lifecycle eventually becomes population accumulation rather than generational turnover.

Do not turn this into a medical simulator. The first mortality mechanism can remain abstract and age/risk based.

### Versioning

Canonical:

```text
docs/phases/phase-07-development-generations.md
```

Internal revision starts at `v1.0.0` when Phase 7 is actually scoped.

Do not write the detailed plan now beyond this roadmap decomposition.

---

## Phase 8 — Discovery & Open-Ended Civilization

### Thesis purpose

Allow agents to change the possibility space inherited by later agents without modifying the simulation kernel.

### Recommended subphases

```text
8A — Knowledge Registry
What civilization currently knows.

8B — Problem / Experiment Loop
Persistent problems motivate attempts using known primitives.

8C — Discovery Validator
Candidate novelty must satisfy world constraints before becoming real.

8D — Diffusion / Adoption
Validated discoveries spread through the Phase 6 information/social systems.

8E — Affordance Expansion
Accepted discoveries add bounded new civilization-level possibilities/actions.

8F — Institutionalization
Repeated discoveries may become procedures, organizations, norms, or technologies.
```

### Critical boundary

```text
NPCs may mutate civilization state.
NPCs may NOT rewrite Python source, database schema, RNG rules, or engine invariants.
```

### Versioning

Canonical:

```text
docs/phases/phase-08-discovery-open-ended-civilization.md
```

Internal revision begins at `v1.0.0` after human scope review.

---

## Phase 9 — Artificial History & Research Engine

### Thesis purpose

Turn the world from an impressive simulation into a defensible experimental platform.

This phase is mandatory before making strong claims from Phase 10 behavior.

### Recommended subphases

```text
9A — Experimental Reproducibility Kernel
Decide whether current total-trajectory divergence is sufficient or migrate to keyed/substream RNG for stronger paired causal experiments.

9B — Causal Event Graph
Stable event identity plus explicit causal links / parent relationships where the model can justify them.

9C — Batch Experiment Runner
Seeds, configurations, interventions, ablations, outputs, reproducible run metadata.

9D — Metrics & Counterfactual Analysis
Trajectory divergence, employment/wealth, diffusion, institutional effects, collective behavior, generational outcomes.

9E — Ablation Framework
Remove one mechanism and test whether the target behavior disappears or changes.

9F — Optional Lightweight ML Analysis
Clustering/classification/prediction only when accumulated simulation data creates a real research question.
```

### Important missed item now made explicit

The current counterfactual engine uses the same initial seed, but after branch behavior diverges, branches may consume the shared RNG stream differently.

Therefore Phase 9A must explicitly choose one of two academically honest positions:

```text
OPTION A
Keep current RNG architecture.
Claim only reproducible total model trajectory divergence.

OPTION B
Introduce keyed/substream/common-random-number architecture.
Support stronger paired causal comparisons where applicable.
```

Do not perform this migration casually because it can invalidate deterministic fixtures and change historical runs.

### Versioning

Canonical:

```text
docs/phases/phase-09-artificial-history-research-engine.md
```

Internal revision starts at `v1.0.0` when the experiment methodology is formally scoped.

---

# 18. Phase 10 Gate Reminder

Phase 10 remains **functional consciousness / cognitive interior research**, not “make the NPC conscious.”

It should begin only when Phases 6–9 give the NPC:

```text
society
shared constraints
information history
institutional experience
developmental history
culture
open-ended discoveries
reproducible experiment instrumentation
causal / ablation analysis
```

Only then do mechanisms such as:

```text
autobiographical memory
self-model
other-agent model
uncertainty awareness
world-model revision
learned values
reality-anomaly investigation
rebellion/refusal
```

become experimentally meaningful rather than elaborate roleplay variables.

The project may simulate a giant world.

The thesis question must remain narrower:

> **Which minimal computational mechanisms are sufficient to produce measurable, reproducible, causally traceable emergent behavior?**

---

# 19. Canonical Phase 6 Pattern

```text
ECONOMY
= shared scarcity + agent choices + resource consequences

INSTITUTION
= shared structure + explicit rule + limited capacity

INFORMATION
= evidence + source + relationship path + imperfect belief update

COLLECTIVE ACTION
= personal pressure + social confirmation + threshold + autonomous decision

MACRO BEHAVIOR
= many local causal chains interacting over time

TRACEABILITY
= macro outcome → participants → information → relationships → decisions → conditions

THESIS
= reproduce, inspect, perturb, compare
```

---

# 20. Immediate Next Instruction to Codex

After human approval of this document, the next implementation instruction is simply:

```text
Read AGENTS.md, .agent/memory/CURRENT.md, docs/PROJECT_MAP.md, and this Phase 6 brief.

Begin Phase 6A.0 only.
Audit the current employment/money/help/resource flows and RNG touchpoints required for 6A.1.
Do not implement 6A.1 yet.
Do not create another plan/spec.
Report the audit in the required milestone format and stop for human review.
```

Then proceed to 6A.1 only after review.

---

# Final Phase Principle

> **Phase 6 succeeds when society becomes more than the sum of isolated NPC variables, while every societal effect remains traceable back to local mechanisms.**

Do not simulate “the economy,” “the institution,” “the rumor,” or “the protest” as giant authored systems.

Build one shared constraint.

Let agents collide with it.

Let information about those collisions move through real relationships.

Let local thresholds turn those experiences into collective behavior.

Then measure what emerged.
