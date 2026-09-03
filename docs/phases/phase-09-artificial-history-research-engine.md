# THE PLAYING GOD — PHASE 9
## Artificial History & Research Engine

**Document revision:** v1.0.5
**Prepared:** 2026-09-03
**Project:** The Playing God
**Project type:** Master of Computer Engineering thesis / artificial-life, artificial-society, artificial-history and counterfactual simulation
**Status:** ACTIVE — Phase 9E complete; awaiting authorization for Phase 9F
**Execution gate:** Human-approved execution only. Implement one authorized subphase at a time.
**Canonical destination:** `docs/phases/phase-09-artificial-history-research-engine.md`

---

# 0. Document Role

This document is the canonical Phase 9 project-manager implementation brief for the coding agent.

It defines:

- why Phase 9 exists;
- the Computer Engineering problem it addresses;
- the boundary between simulation truth and research-derived interpretation;
- the Phase 9 subphase order;
- the historical episode model;
- the causal-tracing rules;
- the trajectory-comparison contract;
- the Ouroboros recurrence gate;
- the counterfactual-history comparison contract;
- the read-only research-query boundary;
- provenance, reproducibility, persistence and caching rules;
- weak-hardware constraints;
- testing and anti-overengineering policy;
- Phase 9 exit evidence;
- what remains deferred to Phase 10 and later research.

It intentionally does **not** prescribe:

- exact class names;
- exact module names;
- folder restructuring;
- private helper functions;
- SQL table names;
- CLI command spelling;
- exact numeric similarity formula unless the implementation requires one;
- line-by-line coding steps;
- exact test file names;
- a web dashboard;
- a generic benchmark framework.

Codex owns implementation details.

Codex does **not** own research-scope expansion.

This brief is already the implementation plan. Once approved, Codex should inspect the current code and implement the currently authorized milestone rather than generating another spec-review-approval loop.

---

# 1. Thesis Anchor

## 1.1 Computer Engineering identity

**The Playing God is a Master of Computer Engineering thesis project.**

The simulated world is the experimental medium.

The engineering problem is not:

> How many human-like systems can be added to one fictional world?

The engineering problem is:

> **How can a resource-constrained deterministic multi-agent system preserve, reconstruct, compare and experimentally interrogate long-term causal histories strongly enough to support reproducible research on path dependence, emergence and counterfactual divergence?**

Earlier phases built the mechanisms that generate history.

Phase 9 builds the mechanisms that **study** that history.

The project direction is now:

```text
autonomous agents
→ persistent lives
→ spatial/social causality
→ institutions/information
→ adaptive development
→ generations/culture
→ discovery and expanding affordances
→ artificial history
→ research comparison
→ later cognitive-interior experiments
```

Phase 9 therefore changes the role of the repository.

Before Phase 9:

```text
simulation engine
→ proves individual mechanisms
```

After Phase 9:

```text
simulation engine
→ generates structured histories
→ research engine reconstructs and compares them
→ reproducible evidence can support thesis experiments
```

The central thesis value is no longer merely that unexpected events occur.

It is that the system can answer:

```text
what happened?
when did it happen?
who participated?
which causal links are explicit?
which events belong to the same historical development?
how did one life or world differ from another?
where did a counterfactual fork begin?
which differences propagated afterward?
did a later generation structurally resemble an earlier one?
can another researcher reproduce the same result?
```

---

# 2. Starting State Entering Phase 9

Phase 9 assumes the accepted completion state reported at Phase 8G:

```text
Phase 8G complete
commit: 2b4c890 feat: close phase 8 counterfactual gate

capabilities available:
- complete Phase 8 snapshots
- compact read-only research metrics
- skill/opportunity comparison
- counterfactual-aware trajectory signatures
- explicit Phase 8 discovery/adoption causal evidence
- deterministic same-seed execution
- exact save/reload continuation

schema:
- v22

Phase 8 exit suite:
- 236 tests passed

known controlled counterfactual:
- identical histories fork after day 3
- third denial produces recognition
- day 5 validation
- day 6 social adoption
- day 7 peer training
- learner skill +0.006
- formal access prevents this discovery chain
```

Phase 9 must **reuse** those capabilities.

Do not rebuild Phase 8 snapshots, metrics or trajectory signatures under new names merely because the research phase wants to consume them.

If Phase 9 exposes a limitation in those structures, extend them minimally and document why.

---

# 3. Phase 9 Objective

## 3.1 Purpose

Turn accumulated structured simulation history into a deterministic, read-only research surface.

Phase 9 should make the world capable of supporting:

```text
event history
→ historical episodes
→ causal traces
→ trajectory representations
→ structured similarity
→ recurrence candidates
→ counterfactual divergence
→ compact research evidence
```

The research engine observes the simulation.

It does not become another actor inside the simulation.

## 3.2 Canonical Phase 9 sequence

```text
9.0  Research Contract & Historical Boundary
↓
9A   Deterministic Historical Episode Extraction
↓
9B   Causal History Trace
↓
9C   Historical Trajectory Comparison
↓
9D   Ouroboros Recurrence Gate
↓
9E   Counterfactual Historical Divergence
↓
9F   Read-Only Research Query Surface
↓
9G   Integrated Research Demonstration & Exit Gate
```

The sequence matters.

Do not start with a dashboard.

Do not start with embeddings.

Do not start with a generic causal-inference library.

First establish what counts as historical evidence.

---

# 4. The Critical Separation: Reality, History, Analysis and Narrative

Phase 9 must keep four layers conceptually separate.

```text
SIMULATION REALITY
= authoritative state transitions and structured events

HISTORICAL PROJECTION
= deterministic grouping / tracing over authoritative history

RESEARCH ANALYSIS
= comparison, similarity, metrics and counterfactual measurements

NARRATIVE
= optional human-readable explanation of already-derived evidence
```

## 4.1 Simulation reality is authoritative

The research layer must not alter:

- NPC state;
- resources;
- relationships;
- beliefs;
- policies;
- adaptive learning state;
- locations;
- institutional rules;
- knowledge/discovery registries;
- future action eligibility;
- RNG state;
- event ordering.

A research query must be observational.

Conceptually:

```text
world_before_query
==
world_after_query
```

except for explicitly external output files or non-authoritative analysis caches if later justified.

## 4.2 Historical projection is not causal invention

Two events occurring near one another does not prove one caused the other.

Two events involving the same NPC does not prove causality.

Two similar outcomes do not prove common cause.

Phase 9 must distinguish:

```text
explicit causal relation
```

from:

```text
historical association / grouping relation
```

This distinction is mandatory.

## 4.3 Research analysis is not world truth

A similarity score, trajectory distance or recurrence candidate is an analytical observation.

It must not silently become:

```text
NPC belief
world event
institutional fact
discovery
new affordance
```

unless a later approved phase deliberately creates a mechanism by which agents observe research-like information.

Phase 9 does not do that.

## 4.4 Narrative is optional

The thesis research layer must function when:

```text
LLM_API_KEY = null
```

Optional later language generation may summarize:

- episodes;
- causal traces;
- recurrence candidates;
- counterfactual comparisons;
- research packets.

Structured evidence remains authoritative.

---

# 5. Historical Evidence Model

Phase 9 should use existing identifiers and records wherever possible.

Conceptually, research objects may include the following.

These names are illustrative, not mandatory implementation names.

## 5.1 Historical episode

```text
HistoricalEpisode
- deterministic episode identity
- start_day
- end_day
- ordered source event references
- participant agent IDs
- event kinds
- explicit causal links contained within the episode
- compact derived magnitude/significance
- provenance
```

An episode is a **projection** over events.

It does not own duplicated event truth.

## 5.2 Causal trace

```text
CausalTrace
- root event/reference
- direction: ancestors / descendants / both
- ordered nodes
- explicit causal edges
- depth
- branches
- unresolved boundaries
- provenance
```

A causal trace follows only relations justified by existing structured evidence.

## 5.3 Trajectory comparison

```text
TrajectoryComparison
- subject A
- subject B
- comparison window
- signature/component distances
- matching dimensions
- divergent dimensions
- source snapshots/events
- qualification warnings
- provenance
```

## 5.4 Ouroboros candidate

```text
OuroborosCandidate
- earlier subject
- later subject
- generation separation
- comparison class
- component similarities
- component differences
- historical-context differences
- qualification status
- provenance
```

This is a research observation, not reincarnation.

## 5.5 Counterfactual comparison

```text
CounterfactualComparison
- baseline run/snapshot identity
- fork run/snapshot identity
- fork/intervention point
- shared pre-fork evidence
- first observed post-fork divergence
- metric deltas
- trajectory distance
- explicit downstream causal traces where available
- unattributed differences
- provenance
```

## 5.6 Research packet

At Phase 9F/9G, a compact research packet may compose existing analytical outputs.

```text
ResearchPacket
- world/run identity
- seed
- model/schema context
- requested subject/question
- bounded episodes
- bounded causal evidence
- bounded metrics/comparisons
- provenance
```

It should remain structured and compact.

It is not a giant serialized universe.

---

# 6. Phase 9.0 — Research Contract & Historical Boundary

## Purpose

Freeze the rules that separate:

```text
world execution
```

from:

```text
historical observation
```

before building analysis.

This prevents Phase 9 from turning into a second simulation engine or an analytics kitchen sink.

## Required contract

The implementation/documentation must make these statements true:

1. research/history functions consume no simulation RNG;
2. research/history functions do not call NPC decision logic for new actions;
3. research/history functions do not mutate authoritative world state;
4. derived historical objects reference authoritative records rather than replacing them;
5. causality is reported only when supported by existing explicit evidence;
6. association/grouping is labeled separately from causality;
7. research output is deterministic for identical source history and analysis version;
8. the research layer functions offline;
9. no LLM is required;
10. analysis results do not become NPC/world truth.

## Existing Phase 8 reuse review

Before adding structures, inspect:

- Phase 8 snapshots;
- research metrics;
- skill/opportunity comparison;
- trajectory signatures;
- causal references used by discovery;
- persistence representation;
- existing event identity semantics.

Record which Phase 9 functions can reuse them.

Do not create replacements merely for naming consistency.

### Phase 9.0 implementation record

Phase 9A uses `Agent.events` as the authoritative event stream and preserves
the existing `(agent_id, event_index)` identity already used by persistence and
Phase 8 causal records. Discovery pressure, attempt and resolution indices may
provide explicit causal links; temporal or participant association never does.

Existing Phase 8 structures remain unchanged:

- `snapshot_phase8()` continues to capture mutable civilization state;
- `build_phase8_metrics()` continues to derive bounded discovery/adoption
  measurements;
- counterfactual snapshots and trajectory signatures continue to compare world
  state and execution histories.

Historical episodes have a distinct role: they are immutable, query-time
projections over those authoritative records. The allowed dependency direction
is therefore:

```text
World / Agent.events / existing causal records
→ read-only historical episode extraction
→ immutable derived episodes
```

The history module must not be imported by world execution, call decision
logic, consume simulation RNG, persist duplicate event truth or mutate its
input. Phase 9A adds no database table, schema field, dependency, cache,
simulation behavior or replacement Phase 8 research type.

## Required outcome

Codex can explain:

```text
authoritative source data
→ derived historical representation
→ research comparison
```

and can identify exactly where mutation is forbidden.

## Non-goals

Do not add during 9.0:

- historical episode algorithm;
- new DB tables by default;
- recurrence detector;
- counterfactual runner;
- dashboard;
- CSV warehouse;
- DuckDB;
- vector database;
- embeddings;
- LLM summary;
- causal inference library.

## Completion condition

Phase 9 has a clear read-only research boundary and a documented reuse map for existing Phase 8 research structures.

---

# 7. Phase 9A — Deterministic Historical Episode Extraction

## Purpose

The raw event stream is too granular to serve as the only historical unit.

Phase 9A introduces a compact deterministic projection that groups related events into bounded historical episodes.

Concept:

```text
events
↓
association rules
↓
bounded episode
↓
traceable source references
```

Example:

```text
institutional denial
→ repeated denial
→ recognition pressure
→ validation
→ peer adoption
→ peer training
```

may be observed as one or more related episodes, depending on the accepted grouping rules.

An unrelated event on a similar day must not be absorbed merely because it happened nearby in time.

## 7.1 Episode evidence

An event may be associated with another event because of one or more structured signals such as:

- explicit causal reference;
- shared participant;
- bounded temporal proximity;
- compatible event kinds;
- shared existing information/discovery identity;
- shared institution/location/context identifier already stored by the simulation.

The implementation should prefer strong existing identifiers over vague heuristics.

## 7.2 Association is not causality

An episode may contain:

```text
Event A
Event B
Event C
```

without claiming:

```text
A caused B caused C
```

unless explicit causal evidence exists.

Episode membership means:

> these events form a useful bounded historical unit under the declared grouping rule.

It does not mean:

> every event inside the group caused every later event.

## 7.3 Deterministic identity

Episode identity must be stable for identical source history and algorithm/version.

Do not use:

- wall-clock timestamps;
- random UUID generation;
- process-specific Python hash behavior;
- iteration order from unordered structures.

Prefer stable identity derived from canonical ordered source references and analysis version.

Exact encoding is an implementation choice.

## 7.4 Boundedness requirement

Prevent historical "episode chaining" where one frequently active NPC connects months or years of unrelated events into one giant component.

Grouping must have explicit bounds.

Possible bounds include:

- maximum day gap between adjacent associated events;
- maximum episode duration;
- maximum event count;
- stronger evidence required as gaps grow;
- episode split on long inactive windows.

Exact thresholds belong to the implementation but must be:

- deterministic;
- documented;
- simple enough to explain;
- not tuned to force one desired story.

## 7.5 Ordering

Within an episode, source events must have deterministic order.

Prefer existing authoritative event order/index plus day.

If two events can share a day, preserve the project's existing deterministic event identity/order rule.

## 7.6 Significance / magnitude

If existing event significance or research metrics already provide a valid signal, reuse them.

Do not invent a universal historical importance score that combines unrelated concepts without justification.

If an episode exposes a compact magnitude, it should be transparent, for example:

```text
event count
duration
participant count
max existing significance
sum/mean of an already-defined metric
```

Do not claim historical importance as a scientific property.

## 7.7 Persistence boundary

Historical episodes are derivable.

Default policy:

```text
do not persist authoritative duplicate episode truth
```

unless a measured performance need later justifies caching.

No schema migration is preferred for Phase 9A.

If caching becomes necessary later, see the Phase 9 caching policy.

## Required proving scenario

Construct or reuse a small deterministic history containing:

```text
A → B → C
```

where B/C have explicit causal or participant continuity, plus:

```text
D
```

which is temporally nearby but historically unrelated.

Prove:

1. expected related events are grouped;
2. D is not absorbed merely because of chronology;
3. source event references remain recoverable;
4. explicit causal references remain distinguishable from episode association;
5. repeated extraction is exact;
6. save/reload produces identical extraction;
7. extraction consumes no RNG;
8. extraction does not change world state.

## Edge cases

Cover at least:

- zero events;
- one event;
- events with no causal references;
- unrelated same-day events;
- multiple participants;
- long gap that forces episode split;
- maximum episode bound;
- legacy history lacking newer event metadata.

## Non-goals

Do not add:

- semantic embeddings;
- clustering libraries;
- community detection over all event data;
- topic modeling;
- LLM summaries;
- narrative chapter generation;
- generic event ontology;
- cross-seed benchmarking;
- causal inference from temporal correlation.

## Exit condition

Existing event history can be converted into compact, deterministic, bounded historical episodes while preserving source traceability and epistemic separation between association and causality.

### Phase 9A implementation record

`HistoricalEpisode` is a frozen derived value containing a SHA-256 identity
over its analysis version and canonical source references, day bounds,
participating agent IDs, event kinds, maximum existing event significance, and
the explicit discovery-causal references wholly contained in the episode.

The `episode-v1` association rule processes events in
`(day, agent_id, event_index)` order. An event joins an existing episode only
when it has an explicit discovery link to that episode or shares a participant,
and is within all three fixed bounds: at most three days since the episode's
last event, seven days from its first event, and twelve total events. Candidate
episodes prefer explicit links, then more shared participants, then the most
recent episode, with stable creation order as the final tie-breaker.

The controlled A–B–C/D proof confirms that participant continuity groups A,
B and C while chronology alone cannot absorb D. A separate real discovery
history preserves evidence-to-recognition, recognition-to-attempt and
attempt-to-resolution references without treating every episode association as
causal. Repeated extraction, fresh same-seed construction and save/reload are
identical; source references resolve to authoritative events; world snapshots
and RNG state remain unchanged.

Verification at the exit gate:

- focused Phase 9A tests: 7 passed;
- Phase 9A plus directly affected history/discovery/research tests: 32 passed;
- complete repository suite: 243 passed;
- SQLite schema remains v22.

---

# 8. Phase 9B — Explicit Causal History Trace

## Purpose

Phase 9A tells us:

> which events belong together historically?

Phase 9B asks:

> which explicit causal links can the repository actually prove?

The objective is a read-only causal graph/trace over existing structured references.

Concept:

```text
event
→ explicit cause/reference
→ prior event
→ prior cause
```

and in the opposite direction:

```text
event
→ explicit downstream references
→ consequence branches
```

## 8.1 Causal graph semantics

Nodes:

```text
authoritative historical event/reference
```

Edges:

```text
explicitly supported causal relation
```

Do not create causal edges from:

- temporal order alone;
- same participant alone;
- same location alone;
- similar event kind alone;
- correlation in metrics;
- researcher intuition.

Those signals may help episode grouping but do not establish a causal edge.

## 8.2 Typed relations

If the existing repository already distinguishes relation types, preserve them.

If Phase 9 needs to expose more than one analytical relation, keep causal edges distinct from structural relations.

Conceptually:

```text
CAUSAL
event A → event B

ASSOCIATED
event A ~ event B

CONTAINMENT
episode X contains event A
```

Do not collapse them into one generic "edge."

## 8.3 Ancestor trace

Given an event/reference, support bounded traversal toward known causes.

Return enough data to answer:

```text
what explicit chain led here?
```

A trace should report:

- ordered ancestor nodes;
- causal relation/reference;
- depth;
- missing/unresolved references;
- cycle protection;
- provenance.

## 8.4 Descendant trace

Where reverse indexing is available or cheaply derivable, support bounded traversal toward known downstream consequences.

Return enough data to answer:

```text
what explicitly referenced this event later?
```

Do not infer consequences merely because later metrics changed.

## 8.5 Branches

A cause may have more than one downstream consequence.

The trace must preserve branching.

Avoid flattening:

```text
A → B
A → C
```

into an invented sequence:

```text
A → B → C
```

## 8.6 Cycles and corrupt history

The simulation intends causal history to be valid, but research code must not infinite-loop on malformed data.

Use deterministic cycle detection and either:

- reject invalid causal history; or
- return a bounded trace with an explicit corruption marker,

consistent with existing repository validation style.

Do not silently "fix" causal cycles.

## 8.7 Missing references

Legacy worlds or older event formats may lack references.

A missing reference should be represented honestly:

```text
unknown / unavailable
```

not fabricated.

## 8.8 Research metrics from traces

Allowed compact metrics may include:

```text
causal depth
branch count
reachable ancestor count
reachable descendant count
explicit chain length
```

These are graph properties.

Do not label them "real-world causal strength."

## Required proving scenario

Reuse the Phase 8 discovery chain where possible:

```text
denials
→ recognition
→ validation
→ social adoption
→ peer training
```

Prove:

1. the known explicit chain is traversable;
2. unrelated events do not appear in the causal trace;
3. branch structure is preserved if present;
4. reverse tracing does not invent links;
5. missing/legacy references remain explicit gaps;
6. the trace is deterministic;
7. research traversal consumes no RNG and mutates no world state.

## Non-goals

Do not add:

- Pearl-style causal discovery;
- Bayesian causal inference;
- Granger causality;
- structural equation modeling;
- probability-of-causation claims;
- generic graph database;
- event rewrite/migration merely to make every old event causal.

## Exit condition

The research layer can reconstruct bounded explicit causal ancestry and consequences from the evidence the simulation actually recorded.

### Phase 9B implementation record

`CausalTrace` is an immutable research result containing the root event,
ancestor or descendant direction, breadth-first ordered nodes with depths,
typed explicit edges, unresolved references, cycle edges, configured-limit
boundaries and analysis provenance. It exposes only graph measurements: causal
depth, reachable event count, explicit edge count and downstream branch count.

`causal-trace-v1` derives its forward and reverse indexes at query time from
authoritative `(agent_id, event_index)` references. Current supported evidence
includes problem evidence to recognition, recognition to attempt, attempt to
resolution, uniquely identified knowledge provenance, required social-contact
evidence, recorded peer-training knowledge parents, and existing school
evidence/adoption references. Ambiguous or unavailable event identities become
`UnresolvedCausalReference` values rather than guessed edges.

Traversal uses deterministic breadth-first ordering with default limits of 32
causal hops and 256 nodes. Reaching either limit adds an explicit boundary.
A bounded iterative directed-cycle check marks corruption without repairing the
history or risking an infinite loop. Reverse traversal is derived in memory and
is never persisted.

The Phase 8 proof traces peer training backward through knowledge exposure,
validation, attempt, recognition and the three denial events. Forward tracing
from one denial reaches both peer-training event records as sibling effects of
the same adoption parent; it does not flatten them into a sequence. Nearby
travel, participant overlap, episode membership and the unreferenced
`knowledge_adopted` event create no edges. Legacy missing parents and corrupt
event indices remain visible gaps, while malformed self-causation is explicitly
marked as a cycle.

Verification at the exit gate:

- focused Phase 9B tests: 8 passed;
- combined Phase 9 history tests: 15 passed;
- Phase 9B plus directly affected history/discovery/research tests: 54 passed;
- complete repository suite: 251 passed;
- SQLite schema remains v22.

---

# 9. Phase 9C — Historical Trajectory Comparison

## Purpose

Individual events explain moments.

Trajectory signatures explain longer lives and historical paths.

Phase 8G already provides counterfactual-aware trajectory signatures.

Phase 9C must **canonize and compare** those signatures rather than replace them.

The research question is:

> How structurally similar or different were these two life/world trajectories over a declared window?

## 9.1 Reuse before extension

Inspect the Phase 8 signature first.

Determine whether it already captures enough information for:

- same-agent baseline/fork comparison;
- different-agent life comparison;
- generational comparison later;
- skill/opportunity comparison;
- bounded historical context.

If yes, use it.

If no, add only the missing dimensions required by a Phase 9 research question.

## 9.2 Comparison dimensions

Useful structured dimensions may include already-existing or derivable measures such as:

```text
capability / skill state
employment / opportunity
resource state
stress / energy
relationships / social position
belief / cultural state
institution access
discovery participation
major event-kind frequencies
historical episode profile
generation / age context
```

Do not add dimensions merely because more vectors look scientific.

Every compared feature should answer a real research question.

## 9.3 Normalize incompatible scales

Money, skill, relationship degree and event count live on different scales.

A valid comparison must avoid one numerically large field dominating distance merely because of units.

Possible strategies:

- normalized bounded values;
- per-dimension relative differences;
- category-separated distance;
- transparent weighting.

Exact math is Codex's implementation choice.

The output must remain inspectable.

## 9.4 Preserve components

Prefer:

```text
component distances
+
optional compact aggregate
```

over:

```text
mystery_similarity = 0.837291
```

A researcher should be able to see why two trajectories were considered similar or different.

## 9.5 Comparison window

Trajectory comparison must declare the time basis.

Examples:

```text
birth → age 18
day 0 → day 365
pre-fork day 0 → fork day
post-fork day 4 → day 30
same age window across generations
```

Do not compare a 70-year life with a 3-year childhood as if their event counts were directly equivalent.

## 9.6 Missing dimensions

Legacy worlds may not contain newer fields.

Do not silently substitute zero when zero would mean an observed value.

Distinguish:

```text
observed zero
```

from:

```text
data unavailable
```

A comparison may expose qualification warnings when source completeness differs.

## 9.7 Deterministic signatures

A signature derived from identical source history and algorithm version must be exact.

It must consume no RNG.

## Required demonstrations

At least two controlled comparisons:

### Demonstration A — same-prior developmental divergence

Reuse the Phase 7 controlled adult divergence if practical:

```text
similar/controlled priors
+
different school/opportunity histories
↓
different skill / learned training / trajectory components
```

The comparison should identify the dimensions that differ.

### Demonstration B — identical pre-fork counterfactual histories

Reuse the Phase 8G fork.

Before the fork:

```text
trajectory distance = zero / equivalent under the accepted representation
```

After the fork:

```text
distance becomes non-zero
```

and the output identifies which components changed.

## Non-goals

Do not add:

- deep representation learning;
- autoencoders;
- embedding services;
- vector databases;
- learned metric models;
- universal human-similarity scores;
- demographic stereotyping.

## Exit condition

The project can compare two historical trajectories through an inspectable deterministic representation and explain which structured dimensions produced the observed similarity/divergence.

## 9.8 Implementation record

Phase 9C canonizes the existing Phase 8G compact causal-state tuple rather
than replacing it. `counterfactual.trajectory_signature()` is now the public
name for that representation, with the original private entry point retained
for compatibility. The read-only `trajectory-comparison-v1` projection keeps
the Phase 8G tuple as source provenance and adds only the named components,
availability state, normalization rule and inclusive comparison window needed
for inspectable research comparison.

The representation records separate baseline/comparison windows, source agent
IDs, every component result, optional per-component normalized distance, an
equal-weight arithmetic aggregate over available components, Phase 8G source
signature equality and qualification warnings. A value is represented as
either observed (including observed `0` and observed `None`) or unavailable
with a reason. Missing values are never converted to zero or included in the
aggregate.

The declared window must end at the observed world day because the simulator
does not retain arbitrary past state snapshots. Dated histories are filtered
to the inclusive window. Endpoint fields describe state at that window end.
Untimestamped cumulative action counters are exposed only for day-zero-origin
windows; otherwise they are explicitly unavailable. Comparisons require equal
window lengths and equal subject counts, preventing unequal-duration histories
from being treated as directly comparable while permitting later same-length
windows.

Dimensions remain bounded and question-driven: life/generation context,
capability, resources, opportunity, wellbeing, social position, belief and
culture, event-kind frequencies, institutional/development access, learned
training evidence and Phase 8 civilization participation. `[0, 1]` values use
absolute distance, signed bounded values use half-range distance, unbounded
money/salary/count fields use symmetric relative distance, frequency maps use
normalized absolute count difference, and categorical or structured values
use exact `0/1` distance. Every distance is therefore bounded by one, so money
cannot dominate skill merely because its unit is larger.

The controlled Phase 7 comparison retained identical child traits and sins but
reported non-zero skill (`0.23701961157546333` versus observed `0.0`), school
access rate (`0.6666666666666666` versus observed `0.0`), mean school
opportunity, developmental skill gain, event profile, culture and learned
training evidence. The missing learned value on the constrained path remained
unavailable rather than becoming zero. Its aggregate distance was
`0.16884346811804446` over comparable components.

The Phase 8G fixture compared as exactly equivalent through day 3 with
aggregate distance `0.0`. Over the equal day 4–7 post-fork windows it reported
aggregate distance `0.11565277777777777` and named 20 changed components,
including world civilization state, discoverer discovery/knowledge, adopter
knowledge and learner skill/event profile. Identical fresh same-seed and
save/reload signatures remained exact. All analysis checks preserved agent,
Phase 8 and RNG snapshots.

Verification at the exit gate:

- focused Phase 9C tests: 6 passed;
- Phase 9C plus directly affected counterfactual, development and Phase 8 exit
  tests: 21 passed;
- complete repository suite: 257 passed;
- SQLite schema remains v22.

---

# 10. Phase 9D — Ouroboros Recurrence Gate

## Status

**COMPLETE — OUTCOME B: OUROBOROS OBSERVATION STILL DATA-BLOCKED**

Phase 7F explicitly deferred Ouroboros because the available world history did not contain enough separated adult generations.

Phase 9 revisits it.

The critical rule remains:

> **Detect recurrence. Never manufacture recurrence.**

## 10.1 Research question

```text
earlier agent / trajectory
+
later agent / trajectory
+
different historical context
↓
structural similarity?
↓
similar destiny or divergent destiny?
```

The value is in comparing recurrence of structure against divergence of context and outcome.

It is not a reincarnation mechanic.

## 10.2 Data-readiness gate

Before implementing or running a meaningful recurrence claim, verify that source data contains qualifying comparisons.

Minimum useful evidence should include:

- later-generation adults rather than only children;
- at least two separated generations or another explicitly justified deep-time separation;
- comparable age/life windows;
- enough trajectory history to compare outcomes;
- historical context differences;
- persisted source evidence;
- no hand-picked matching fixture presented as a world finding.

If these conditions are absent, record:

```text
Ouroboros observation still data-blocked
```

and do not fake completion by manufacturing a matching society.

The mathematical comparison utility may be tested with synthetic numeric vectors, but synthetic vectors cannot be reported as discovered recurrence.

## 10.3 Comparison classes

The first bounded implementation may support:

### Type I — Starting/prior recurrence

```text
similar starting priors / latent capacities
```

### Type II — Developed-state recurrence

```text
similar later adult state
```

### Type III — Trajectory recurrence

```text
similar life-course signature
```

### Type IV — Societal/world recurrence

Defer unless Phase 9 evidence clearly justifies it.

A world-state recurrence detector can become a large separate research problem.

Do not add it merely because V0.2.2 names it as a future class.

## 10.4 Structured numeric comparison first

Use the Phase 9C structured representation.

Do not begin with semantic embeddings.

A candidate should expose:

```text
which dimensions match
which dimensions differ
generation gap
age/window comparability
historical-context differences
overall qualification
```

## 10.5 Candidate ranking before binary mythology

Prefer initially:

```text
ranked recurrence candidates
```

over:

```text
OUROBOROS = TRUE
```

If a threshold is used:

- document it;
- keep it deterministic;
- do not tune it against one desired pair;
- expose component distances;
- allow "near but not qualified."

## 10.6 Historical context comparison

A recurrence candidate is more research-interesting when:

```text
agent structure similar
but
historical context materially different
```

Useful context differences may reuse existing measures:

- resource/opportunity;
- institution access;
- culture;
- social position;
- generation;
- discovery/affordance environment.

Do not expand the world just to create context variables for Ouroboros.

## 10.7 No world mutation

A recurrence candidate must never:

- modify either NPC;
- create a supernatural event;
- label an NPC internally as reincarnated;
- change behavior;
- award status/resources;
- trigger belief;
- consume RNG.

## 10.8 No metaphysical claim

The thesis language should remain:

```text
structural recurrence
trajectory similarity
historical recurrence candidate
```

not:

```text
reincarnation discovered
soul recurrence proved
destiny loop confirmed
```

## Required gate outcome

Either:

### Outcome A — data ready

A first structured detector ranks genuine qualifying cross-generational candidates from persisted simulated history and reports similarities/differences without modifying the world.

or:

### Outcome B — data still insufficient

The gate records exactly what data is missing and defers the empirical recurrence claim.

Outcome B does **not** block the rest of Phase 9.

Do not run years of expensive simulation merely to make a checklist green unless the human explicitly approves that research run.

## 10.9 Gate record — 2026-09-03

**Outcome B — Ouroboros observation still data-blocked.**

The live repository audit found exactly two persisted candidate worlds:

```text
data/worlds/world_1947_before_phase3.db
data/worlds/world_1947.db
```

They are schema-v1 and schema-v2 snapshots of seed 1947 at day 365. Each has
ten agents, all generation G0 and all currently adult. Neither has an adult
descendant, a G2-or-later agent, a family link, a development record, a
cultural-transmission record or a knowledge record. Their event history spans
only days 1–365. They therefore provide neither separated adult generations
nor historically distinct, comparable descendant trajectories.

Phase 9C can honestly project both worlds, producing ten subjects and 383
named components per world, but 60 components are explicitly unavailable in
each because the legacy histories contain no development or learned-training
evidence. Missing fields are not treated as observed zero. A recurrence rank
or threshold over these inputs would compare only unrelated G0 founders or
ordinary same-generation resemblance; it could not answer the approved
cross-generational research question.

The audit loaded both databases through the current persistence layer, built
their Phase 9C signatures and compared agent snapshots, RNG state and SHA-256
file hashes before and after analysis. All four read-only checks remained
exact for both worlds. The earlier bounded seven-year probe was not repeated:
its recorded result had G1 children but no adult descendant or G2, and the
brief expressly forbids an expensive run solely to make the gate pass.

No detector, recurrence threshold, synthetic generation, forced fixture,
event, schema field, dependency or simulation behavior was added. The current
structured comparison remains available when a genuinely persisted,
multi-adult-generation dataset exists. Phase 9D is complete through its
approved insufficient-data outcome and does not block Phase 9E.

Exit verification:

- persisted-world readiness audit: 2 of 2 worlds inspected successfully;
- qualifying adult-descendant trajectories: 0;
- qualifying G2-or-later trajectories: 0;
- Phase 9C focused regression: 6 passed;
- SQLite schema remains v22;
- the full repository suite remains reserved for the Phase 9G exit gate under
  Section 19.3.

## Non-goals

Do not add:

- embeddings unless structured comparison demonstrably fails;
- ANN/vector databases;
- deep clustering;
- forced recurrence fixtures reported as findings;
- Type IV civilization recurrence by default;
- reincarnation mechanics;
- metaphysical event generation.

---

# 11. Phase 9E — Counterfactual Historical Divergence

## Purpose

Phase 8G proved one counterfactual fork.

Phase 9E turns that proof into a reusable research comparison.

The key question:

> **Given two histories that share an initial state and diverge after a controlled intervention/condition change, where does measurable divergence begin and how does it propagate through recorded history?**

## 11.1 Inputs

Prefer existing Phase 8 counterfactual artifacts:

- baseline snapshot/history;
- fork/intervention snapshot/history;
- seed;
- shared model/configuration identity;
- fork day/reference;
- trajectory signatures;
- compact research metrics;
- explicit causal references.

Do not create a second fork engine if Phase 8 already provides the required runs.

## 11.2 Pre-fork equivalence

A valid controlled comparison must verify that the compared histories are equivalent under the project's contract before the intervention/fork.

Expose enough evidence to answer:

```text
Were these actually the same history before the treatment?
```

If not, the comparison must be marked invalid or qualified.

## 11.3 First observed divergence

Identify the earliest post-fork difference available from authoritative structured history.

This may be:

- different event;
- different state/snapshot field;
- different action;
- different access outcome;
- different trajectory component.

Label it:

```text
first observed divergence
```

not necessarily:

```text
ultimate cause
```

The treatment/fork is the controlled difference.

Downstream causal claims still require explicit evidence.

## 11.4 Divergence dimensions

Reuse Phase 8 metrics/signatures where possible.

Possible outputs:

```text
skill delta
opportunity/access delta
resource delta
relationship/social delta
belief/culture delta
event/episode delta
discovery/adoption participation
trajectory distance
```

Do not force every world outcome into one scalar.

A compact aggregate distance may coexist with component deltas.

## 11.5 Causal propagation

Where explicit causal references exist, Phase 9B can explain portions of the downstream chain.

Example:

```text
baseline:
formal access
→ no discovery pressure
→ no recognition
→ no validation/adoption/training chain

counterfactual:
denials
→ recognition
→ validation
→ adoption
→ peer training
→ +0.006 skill
```

The research layer may report the explicit chain.

If another difference appears without explicit causal ancestry, report:

```text
observed divergence, causal path unavailable
```

Do not invent the missing chain.

## 11.6 Alignment after divergence

Post-fork event IDs may not align one-to-one.

Do not force brittle event matching.

Use a combination of:

- shared pre-fork identity;
- declared fork point;
- snapshot/signature comparison;
- episode/event-kind evidence;
- explicit causal references.

The exact alignment method should remain simple and explainable.

## 11.7 Butterfly-effect boundary

Phase 9 may measure:

```text
small controlled difference
→ larger downstream trajectory distance
```

But do not declare every divergence a "butterfly effect."

A future thesis metric may define ButterflyImpact formally.

For Phase 9, prefer descriptive measures unless a precise existing definition is implemented.

## Required proving scenario

Use the Phase 8G controlled fork.

Prove:

1. histories are equivalent before the fork;
2. the fork condition is identifiable;
3. the first observed divergence occurs after the fork;
4. the discovery/adoption/training chain is visible where explicit;
5. the learner skill difference is recovered;
6. trajectory distance is zero/equivalent pre-fork and non-zero post-fork;
7. formal access counterfactual lacks the discovery chain;
8. repeated comparison is exact;
9. comparison consumes no RNG and mutates no world.

## Edge cases

Cover at least:

- identical histories with no divergence;
- invalid pair with different pre-fork history;
- divergence with no explicit causal chain;
- missing metric/signature component;
- different analysis window;
- empty post-fork period.

## Non-goals

Do not add:

- Monte Carlo rollouts;
- MCTS;
- automated intervention search;
- treatment-effect estimation across large populations;
- causal inference over observational worlds;
- policy optimization;
- generic experiment platform.

Those may become later thesis experiments only after the deterministic comparison surface is stable.

## Exit condition

The system can produce an inspectable deterministic comparison of a baseline and controlled fork, showing pre-fork equivalence, post-fork divergence, metric/trajectory differences and explicit downstream causal evidence where available.

## 11.8 Implementation record

Phase 9E adds one offline composition,
`counterfactual-history-v1`, rather than a second fork runner. The caller
provides two frozen pre-fork worlds and their two completed branches plus the
declared fork day. The comparison reuses existing `AgentSnapshot` and
`Phase8StateSnapshot` values, Phase 9A `HistoricalEpisode` projections, Phase
9B `CausalTrace` results, Phase 9C trajectory components and Phase 8 metrics.

Pre-fork validation checks the declared day, simulation configuration, agent
and Phase 8 snapshots, Phase 9C signature/source equivalence, episodes,
explicit causal references, RNG state and current economy/school/intervention/
information context. Each completed branch must preserve its prefix event
history and configuration. Mismatches remain named qualifications rather than
being silently accepted as a controlled pair.

Post-fork event comparison aligns only stable `(agent_id, event_index)` source
references after the shared boundary. It reports the earliest differing day
as the **first observed divergence**, not an ultimate cause. Later event IDs
are not force-matched. The result also retains both branches' post-fork
episodes, all Phase 9C component differences and aggregate distance, and the
existing Phase 8 discovery/opportunity/skill metrics.

Phase 9B descendant traces begin only from source events that differ on the
first observed day. A trace with explicit edges is returned unchanged. A
root-only trace or endpoint-only difference is labeled `observed divergence,
causal path unavailable`; chronology and component proximity never create an
edge. Missing Phase 9C observations remain missing and qualified rather than
becoming zero.

The Phase 8G day-3 prefix passed every equivalence check with trajectory
distance `0.0`. The first observed divergence was day 4: the discovery branch
recorded another institutional denial and problem recognition while the
formal-access branch recorded travel and admission. Over days 4–7, trajectory
distance became `0.11565277777777777`. Existing metrics recovered one
validated discovery attempt versus none, and learner `npc_003` retained the
expected `+0.006` skill delta.

The discovery branch's explicit traces connect the denial through recognition,
attempt, validation, accepted knowledge exposure and both peer-training event
branches. Its episodes retain the adoption event. The formal-access branch has
no discovery attempt or discovery/adoption/training chain; its root-only
differences are reported as unavailable causal paths rather than inferred
absence-causes. Repeated fresh and save/reload comparisons are exact, and all
four source worlds retain their snapshots and RNG states.

Exit verification:

- focused Phase 9E tests: 7 passed;
- Phase 9E plus directly affected counterfactual, episode, causal trace,
  trajectory and Phase 8 exit tests: 38 passed;
- SQLite schema remains v22;
- the full repository suite remains reserved for the Phase 9G exit gate under
  Section 19.3.

---

# 12. Phase 9F — Read-Only Research Query Surface

## Purpose

By this point the project has:

```text
episodes
causal traces
trajectory comparisons
possible recurrence candidates
counterfactual comparisons
```

Phase 9F gives researchers a compact way to ask for those results without understanding every internal table.

This is not a generic analytics platform.

It is a narrow research interface over the simulation.

## 12.1 Research questions the interface should support

Conceptually:

```text
show historical episodes for subject/window
trace explicit causes of event X
trace explicit consequences of event X
compare trajectory A with trajectory B
find qualifying recurrence candidates
compare baseline with counterfactual fork
produce compact evidence packet for a subject/experiment
```

Exact Python/API/CLI naming is implementation-owned.

## 12.2 Read-only contract

A research query must not:

- advance the world;
- execute an NPC action;
- update adaptive learning;
- change beliefs;
- mutate discovery state;
- consume RNG;
- save modified world state as a side effect.

If the query writes an export file, that file is external analysis output, not world truth.

## 12.3 Bounded output

Do not return the entire universe by default.

Support explicit bounds such as:

```text
agent
time window
episode count
trace depth
candidate count
metric subset
```

The research surface should protect both:

- weak hardware;
- later LLM/context usage.

## 12.4 Provenance

Every meaningful research result should make it possible to identify its source.

Useful provenance fields may include:

```text
world/run identity
seed
current day / comparison window
schema version
simulation/model version if available
analysis version
source event references
source snapshot/signature references
fork identity when applicable
```

Do not confuse document revision with simulation model version.

## 12.5 Structured first

Preferred output:

```text
typed Python structure / dict / deterministic JSON-compatible data
```

Optional export:

```text
JSON
CSV only where naturally tabular
```

Do not add a database warehouse merely for export.

## 12.6 Explanation boundary

The research layer may produce concise deterministic explanation fields assembled from structured facts.

Example:

```text
"Trajectory divergence first appears on day 4 in institution access."
```

Do not generate speculative prose.

An optional LLM layer may later narrate the packet, but the packet remains sufficient without it.

## 12.7 Research packet

A compact packet for one experiment may include:

```text
experiment identity
baseline/fork metadata
relevant episodes
causal trace
selected trajectory deltas
selected metrics
qualification warnings
source references
```

This becomes useful later for:

- thesis tables;
- case-study narratives;
- visualization;
- optional LLM summaries.

## Required proving scenarios

Prove at least:

1. query same world twice → identical result;
2. query before/after check → authoritative world state unchanged;
3. query does not alter RNG state;
4. bounded trace/episode/candidate limits are respected;
5. invalid/missing references fail clearly;
6. legacy history with missing fields is qualified rather than fabricated;
7. research packet retains source provenance.

## Non-goals

Do not add:

- FastAPI server unless already required by repository architecture;
- React dashboard;
- generic SQL query language;
- BI tooling;
- notebook server;
- vector DB;
- Elasticsearch;
- streaming analytics;
- authentication system;
- cloud storage;
- full benchmark harness.

## Exit condition

A researcher can obtain compact, deterministic, source-traceable history and comparison evidence through a small read-only interface.

---

# 13. Phase 9G — Integrated Research Demonstration & Exit Gate

## Purpose

Prove that Phase 9 is not a pile of unrelated utility functions.

The phase must demonstrate one complete research workflow.

## 13.1 Required integrated experiment

Use the strongest existing controlled scenario rather than inventing a larger story.

Preferred primary case:

```text
Phase 8 denial/discovery counterfactual
```

Research workflow:

```text
load/construct paired deterministic histories
↓
verify pre-fork equivalence
↓
extract relevant historical episode(s)
↓
trace explicit causal chain
↓
compare post-fork trajectories
↓
recover skill/opportunity differences
↓
produce compact counterfactual research packet
↓
repeat from saved/reloaded state
↓
prove exact research output
```

## 13.2 Secondary developmental comparison

Also include one compact Phase 7 developmental case if practical:

```text
similar priors
+
different opportunities/exposures
↓
different adult trajectory
```

This proves the research engine is not hard-coded only around discovery events.

## 13.3 Ouroboros result

At Phase 9 exit record one of:

```text
A) qualifying cross-generational recurrence analysis completed
```

or:

```text
B) data-readiness gate still not satisfied; empirical recurrence remains deferred
```

Outcome B is acceptable.

Do not generate decades of world history solely to avoid writing "insufficient data."

## 13.4 Reproducibility proof

Required:

```text
fresh same-seed research result
==
same-seed repeated result
```

where applicable.

Also:

```text
uninterrupted / in-memory analysis
==
save → reload → analysis
```

for authoritative source histories under the existing persistence contract.

## 13.5 Non-interference proof

Demonstrate that invoking the research engine does not affect later simulation execution.

Strong form:

```text
World A:
simulate → research query → continue

World B:
simulate → no research query → continue

future authoritative states are exact
```

under the same seed/model state.

This proves the observer layer is not accidentally changing the experiment it observes.

## 13.6 Performance sanity

Measure one representative Phase 9 research workflow on a bounded world/history.

Do not build a benchmark suite.

Record enough to know that analysis remains practical on the supported laptop.

If a clear bottleneck appears, optimize only the measured bottleneck.

## 13.7 Full suite policy

The complete repository suite should run at the Phase 9 final exit.

It should not be run after every helper addition.

## Phase 9 exit condition

Phase 9 is complete when:

1. historical episodes are deterministic, bounded and source-traceable;
2. explicit causal ancestry/consequences can be reconstructed without invented causality;
3. trajectory comparison is inspectable and component-based;
4. the Ouroboros gate produces either valid recurrence evidence or an explicit data-blocked result;
5. controlled counterfactual histories can be compared through pre-fork equivalence and post-fork divergence;
6. compact research queries are read-only;
7. provenance is sufficient to trace research outputs back to authoritative simulation data;
8. analysis consumes no simulation RNG;
9. analysis does not change future simulation outcomes;
10. save/reload preserves the source truth needed to reproduce research output;
11. the engine works offline without LLM or GPU;
12. the complete approved repository suite passes.

---

# 14. Persistence & Derived-Data Policy

Phase 9 introduces a common systems-design temptation:

> persist every derived analysis object because it exists.

Do not.

## 14.1 Authoritative vs derived

Authoritative data:

```text
simulation state
events
relationships
agent histories
discovery/culture/lifecycle records
snapshots already accepted as authoritative/approved artifacts
```

Derived Phase 9 data:

```text
episodes
causal traces
similarity results
recurrence candidate rankings
counterfactual comparison summaries
research packets
```

Default:

```text
derive on demand
```

## 14.2 Schema migration rule

A schema migration is justified only when Phase 9 must persist genuinely new authoritative source information.

A schema migration is **not** justified merely to store:

- episode caches;
- trace caches;
- precomputed similarity;
- reports.

Prefer schema v22 through Phase 9 if existing source records are sufficient.

## 14.3 If caching becomes necessary

Only after a measured performance problem.

A cache must be invalidatable from source identity.

Conceptual cache key:

```text
source world/history identity
+
source current day / history version
+
analysis algorithm version
+
query parameters
```

A stale cache must never silently masquerade as current research evidence.

Do not make cache persistence a prerequisite for correctness.

## 14.4 Legacy worlds

Older worlds may lack fields required for newer comparisons.

They should:

- remain loadable under existing migration policy;
- expose available evidence;
- mark unavailable dimensions;
- never fabricate missing historical facts.

---

# 15. Provenance & Reproducibility Policy

Phase 9 turns provenance into a first-class research requirement.

## 15.1 Minimum provenance principle

A research claim should be traceable to:

```text
which world/run?
which seed?
which time window?
which source events/snapshots?
which comparison subjects?
which analysis version?
```

## 15.2 Analysis version

If episode grouping, trajectory representation or similarity semantics change, historical research results may change even when the world does not.

Therefore the analysis mechanism needs some explicit version identity.

This may be:

- code/model version already used by the project;
- a compact analysis-version constant;
- another existing repository mechanism.

Do not build a registry service.

The goal is simply to avoid pretending:

```text
same world
+
changed analysis algorithm
=
same research result
```

## 15.3 Determinism

Phase 9 analysis must not depend on:

- wall-clock time;
- non-deterministic set/dict traversal;
- random tie-breaking;
- external network responses;
- API model output;
- machine-specific floating behavior beyond the project's accepted numeric contract.

When ranking equal candidates, define a deterministic tie-breaker using stable identifiers.

## 15.4 Research reproducibility vs simulation reproducibility

Keep separate:

```text
SIMULATION REPRODUCIBILITY
same seed/model/config → same authoritative history

ANALYSIS REPRODUCIBILITY
same authoritative history + same analysis version/query → same research result
```

Phase 9 must preserve both.

---

# 16. Similarity & Measurement Policy

Phase 9 needs metrics, but metrics can create fake precision surprisingly efficiently.

## 16.1 Prefer interpretable components

Example:

```text
prior distance:       0.08
skill distance:       0.21
resource distance:    0.42
social distance:      0.15
culture distance:     unavailable
trajectory aggregate: 0.23
```

is better than:

```text
same_person_score = 0.8731
```

without explanation.

## 16.2 No universal human-distance metric

A trajectory similarity is a property of the selected computational representation.

It is not a measurement of real psychological identity.

## 16.3 Missing-data discipline

Never conflate:

```text
0.0
```

with:

```text
unknown
```

This matters especially for legacy worlds.

## 16.4 Threshold discipline

For recurrence or classification thresholds:

- document the threshold;
- explain what representation it applies to;
- keep it stable for a declared analysis version;
- do not tune it on the exact pair being reported as a finding.

## 16.5 Statistical expansion later

Phase 9 is primarily deterministic analytical infrastructure.

Large repeated-seed statistical experiments may use it later.

Do not smuggle a full statistics framework into Phase 9 unless an approved thesis experiment requires it.

---

# 17. Hardware & Compute Policy

Phase 9 must remain practical on the project's weak-hardware target.

```text
single consumer laptop
Intel CPU class
8 GB RAM class
no dedicated GPU
offline-capable
```

## 17.1 Analysis should be event-driven / query-driven

Do not continuously recompute history after every simulation event unless a measured requirement demands it.

Preferred:

```text
simulate
→ ask research question
→ derive bounded result
```

## 17.2 Avoid accidental quadratic scans

Potential risk:

```text
all agents
× all agents
× every day
× every historical event
```

For recurrence and trajectory comparison, restrict to eligible subjects and declared windows.

If candidate count grows later, first measure.

Do not add ANN/vector infrastructure in advance.

## 17.3 Long simulation runs are not unit tests

The Phase 7 gate showed that even a seven-year ordinary world can be materially expensive on the target laptop.

Therefore:

- unit tests use compact controlled histories;
- integration tests use bounded scenarios;
- deep-time empirical runs are explicit research jobs, not routine test setup.

## 17.4 No GPU dependency

Nothing in Phase 9 core requires:

- neural embeddings;
- deep clustering;
- GPU model inference;
- distributed compute.

If a later experiment justifies them, that is a separate approval.

---

# 18. Anti-Overengineering Policy

This section overrides coding-agent enthusiasm.

## 18.1 Approved brief means implement

Once the human approves this document:

```text
inspect current code
→ implement authorized Phase 9 milestone
→ run focused proof
→ report
→ stop
```

Do not perform:

```text
review
→ new spec
→ approval request
→ architecture RFC
→ implementation plan
→ approval request
→ implementation
```

This file is the approved implementation contract.

## 18.2 Research engine does not mean analytics platform

Avoid speculative abstractions such as:

```text
UniversalResearchEngine
GenericAnalyticsFramework
HistoricalDataLake
CausalGraphService
ExperimentOrchestrator
MetricPluginRegistry
VectorSearchPlatform
ResearchMicroservice
SimulationWarehouse
```

Use the smallest coherent mechanisms that answer Phase 9 research questions.

## 18.3 No new dependency without a current requirement

Before adding a runtime dependency, Codex must be able to state:

```text
Which approved Phase 9 requirement cannot reasonably be satisfied
with the standard library or dependencies already present?
```

If the answer is weak, do not add it.

NetworkX already exists in the project history and may be reused where it genuinely helps, but do not force every historical operation through it if simpler structures are clearer.

## 18.4 No repository-wide refactor by default

Phase 9 is mostly observational.

That is a feature.

If implementing read-only analysis somehow requires rewriting the simulation kernel, stop and report the architectural reason before proceeding.

## 18.5 Do not duplicate Phase 8 research structures

If Phase 8 already exposes:

```text
snapshot
metric
trajectory signature
```

extend or compose them.

Do not introduce:

```text
Phase9Snapshot2
ResearchMetricV2ButSameThing
NewTrajectorySignature
```

without demonstrated semantic difference.

## 18.6 Documentation rule

Do not create a separate spec per subphase by default.

This document is sufficient.

Update the implementation record under the relevant section after completion if that matches existing repository practice.

---

# 19. Testing Policy

Testing must prove research validity, determinism and non-interference.

It must not maximize test count.

## 19.1 Test the epistemic boundary

High-value tests include:

- association does not become causal edge;
- unrelated chronological events are not absorbed incorrectly;
- explicit causal ancestry is preserved;
- trajectory comparison exposes component differences;
- missing data remains missing rather than zero;
- recurrence does not mutate simulation;
- invalid pre-fork comparison is rejected/qualified;
- research queries consume no RNG;
- research queries do not alter future execution.

## 19.2 Controlled histories before long worlds

Prefer:

```text
small explicit event chain
```

over:

```text
simulate 40 years and hope the right thing happens
```

for correctness tests.

Long worlds belong to empirical research runs, not basic regression.

## 19.3 Focused first

For each authorized subphase:

1. run the smallest tests proving the new invariant;
2. run affected existing tests;
3. run broader relevant suite at subphase exit when integration risk justifies it;
4. run the full repository suite at Phase 9G exit.

## 19.4 Full-suite anti-pattern

Do not run all repository tests after every tiny helper change.

The full suite is valuable as an integration gate, not as a ritual performed every seven minutes to appease the CI gods.

## 19.5 Persistence tests

When a subphase depends only on derivable history and adds no persistence:

- prove save/reload source equivalence;
- do not invent a schema migration test for a migration that does not exist.

If a real schema change occurs, add:

- legacy load;
- migration;
- corrupt-state handling;
- exact restart continuation where relevant.

## 19.6 No test weakening

When expected research output changes:

```text
regression
or
intentional analysis-version change?
```

Classify first.

Do not silently refresh fixtures.

## 19.7 Performance test

Use one practical bounded sanity check at major exit.

Do not build a benchmark framework unless a measured regression demands it.

---

# 20. Phase 9 Progress Labels

Use:

```text
9.0
9A
9B
9C
9D
9E
9F
9G
```

If a subphase genuinely requires a second implementation checkpoint:

```text
9C.1
9C.2
```

is allowed.

Do not manufacture micro-phases merely to generate process.

These labels are not document versions.

---

# 21. Document Versioning Policy

Canonical repository path:

```text
docs/phases/phase-09-artificial-history-research-engine.md
```

Do not create:

```text
phase-09-v2.md
phase-09-final.md
phase-09-final-final.md
phase-09-new.md
```

Document revision belongs in the header and Git history.

Semantic meaning:

```text
v1.0.0
= first approved Phase 9 scope

v1.x.0
= meaningful added/clarified research contract
  without changing Phase 9's fundamental objective

v1.x.y
= wording, acceptance clarification or non-architectural fix

v2.0.0
= fundamental research/architecture change
  such as replacing deterministic history analysis with
  a learned representation as the core mechanism
```

Simulation/model version and analysis version remain separate concepts.

---

# 22. Commit & Execution Policy

Each main subphase should normally end in one coherent commit after its exit proof passes.

Suggested intent:

```text
9.0/9A  feat: add deterministic historical episodes
9B      feat: add explicit causal history tracing
9C      feat: add historical trajectory comparison
9D      feat/docs: add or defer recurrence detection by evidence gate
9E      feat: add counterfactual history comparison
9F      feat: add read-only research queries
9G      docs/test: close phase 9 research gate
```

Exact commit wording is Codex-owned.

Do not split a small coherent subphase into many tiny commits merely to mimic enterprise ceremony.

Do not push unless explicitly authorized.

After each authorized subphase report:

- commit SHA;
- files changed;
- behavior implemented;
- proving evidence;
- tests run;
- schema version;
- determinism/reproducibility result;
- scope guard;
- worktree state;
- next subphase, awaiting instruction.

---

# 23. Phase 9 Completion Gate

Phase 9 is complete when the following are true.

## History

- raw structured events can be projected into bounded historical episodes;
- episodes retain authoritative source references;
- historical association is not mislabeled as causality.

## Causal evidence

- explicit causal ancestry and consequences can be traced;
- branching is preserved;
- missing references are reported honestly;
- chronology alone does not create causal edges.

## Trajectories

- existing Phase 8 trajectory signatures are reused or minimally extended;
- comparisons expose meaningful component differences;
- time windows are explicit;
- missing data is distinguishable from observed zero.

## Ouroboros

Either:

```text
qualifying cross-generational recurrence candidates can be detected
```

or:

```text
the data-readiness gate explicitly defers the empirical recurrence claim
```

No recurrence is manufactured.

## Counterfactual history

- a baseline/fork comparison verifies pre-fork equivalence;
- first observed divergence is identifiable;
- post-fork trajectory/metric differences are measurable;
- explicit causal propagation is shown only where recorded.

## Research surface

- compact read-only queries expose the accepted evidence;
- output is bounded;
- provenance is present;
- no LLM is required.

## Non-interference

- analysis consumes no simulation RNG;
- analysis does not mutate authoritative world state;
- invoking research queries does not change later simulation execution.

## Persistence/reproducibility

- research output is reproducible from identical source history and analysis version;
- save/reload preserves the source truth required to reproduce analysis;
- legacy missing data is not fabricated.

## Compute

- core Phase 9 remains practical on weak CPU-only hardware;
- no GPU/cloud infrastructure is required.

## Integration

- required focused/integration proofs pass;
- final complete repository suite passes.

---

# 24. Required Phase 9 Demonstration

Before declaring Phase 9 complete, produce one compact structured demonstration capable of answering:

```text
Which historical episode contains the discovery chain?

Which source events compose it?

Which causal links are explicit?

What happened in the baseline?

What changed in the counterfactual?

Were the two histories equivalent before the fork?

What was the first observed divergence?

Which downstream changes have explicit causal ancestry?

How did the compared trajectory signatures differ?

What skill/opportunity difference resulted?

Can the same research result be reproduced after save/reload?

Did running the research query alter the simulation?

Does the current dataset support a valid Ouroboros recurrence claim?
```

The output may be terminal/structured.

Do not build a game UI for this demonstration.

---

# 25. Phase 9 Non-Goals

Do not allow Phase 9 to expand into:

```text
new civilization behavior
second discovery domain
generic institution framework
new political/economic simulation
new reproductive/development mechanics
new cultural transmission mechanics
continuous LLM cognition
LLM historical truth generation
semantic embeddings by default
vector database
deep clustering
deep representation learning
large causal-inference framework
Monte Carlo counterfactual search
MCTS
automated intervention optimization
massive batch experiment platform
cloud data warehouse
BI dashboard
full web research dashboard
generic benchmark framework
MLOps platform
distributed simulation
3D visualization
consciousness implementation
sentience claims
self-model/world-model cognition
metaphysical recurrence mechanics
```

Relevant destinations:

```text
large repeated-seed thesis experiments
→ after Phase 9 research surface is stable

visual research dashboard
→ separate visualization track if justified

MCTS / intervention search
→ later counterfactual-planning research if required

world models / self-models / consciousness indicators
→ Phase 10 under explicit human-reviewed research scope
```

---

# 26. Bridge to Phase 10

Phase 9 should leave the repository in this state:

```text
world generates deterministic history
↓
history can be grouped
↓
explicit causes can be traced
↓
lives can be compared
↓
counterfactuals can be measured
↓
recurrence can be evaluated when data qualifies
↓
research evidence can be extracted without changing the world
```

Only then should Phase 10 ask deeper questions about cognition.

Phase 10 may investigate mechanisms such as:

```text
perceived-world models
uncertainty
self/world distinction
metacognition
persistent intrinsic valuation
learned social models
hidden-cause inference
reality-anomaly experiments
```

Phase 9 must not implement them.

The reason is methodological:

> Before studying whether an artificial agent develops deeper internal models, the project needs a research engine capable of proving what happened to that agent, which histories differed, and whether an intervention actually changed the trajectory.

Without Phase 9, Phase 10 risks producing anecdotes.

With Phase 9, Phase 10 can produce controlled evidence.

---

# 27. Computer Engineering Problem Solved by Phase 9

The world-building vocabulary may sound historical or sociological.

The engineering result is precise.

Phase 9 solves a combination of:

```text
event-sourced history reconstruction
+
deterministic analytical projection
+
typed graph traversal
+
trajectory state representation
+
normalized multidimensional comparison
+
counterfactual alignment
+
provenance
+
read-only query design
+
persistence/restart reproducibility
+
analysis/simulation separation
+
resource-constrained execution
```

The key achievement is not:

> "The game can show history."

It is:

> **The system can transform a deterministic multi-agent event history into reproducible, source-traceable research evidence about historical episodes, explicit causal chains, trajectory similarity and controlled counterfactual divergence without perturbing the simulation being studied.**

That is directly defensible as Computer Engineering.

---

# 28. Research Problem Progression

At the end of Phase 8:

```text
Can agents discover and socially transmit a new affordance?
→ yes, under a controlled causal chain.
```

Phase 9 asks:

```text
Can the system reconstruct that chain as history?
Can it compare that history with a world where the chain never appears?
Can it measure how trajectories diverge?
Can it detect later structural recurrence without forcing it?
Can it expose the evidence reproducibly?
```

That progression is the thesis.

Not the number of simulated social phenomena.

---

# 29. Canonical Phase 9 Pattern

```text
REALITY
= authoritative simulation state + structured events

HISTORY
= deterministic projection over authoritative events

EPISODE
= bounded association of related events
  without inventing causality

CAUSAL TRACE
= traversal over explicit recorded causal references

TRAJECTORY
= structured summary of a life/world across a declared time window

SIMILARITY
= interpretable component comparison
  not metaphysical identity

OUROBOROS
= read-only recurrence candidate detection
  across qualifying historical distance

COUNTERFACTUAL
= same initial history
  + controlled fork
  → measurable divergence

RESEARCH
= query + provenance + reproducibility

OBSERVER RULE
= measuring the world must not change the world

LLM
= optional narration over research evidence

THESIS
= reproducible causal analysis of emergent artificial history
```

---

# 30. Immediate Authorized Build Order

Unless the human explicitly authorizes more, begin only with:

```text
9.0
→ freeze research boundary and Phase 8 reuse map

9A
→ deterministic historical episode extraction
→ focused proof
→ affected tests
→ subphase exit
→ commit
→ STOP
```

Do not automatically continue into 9B.

The human will review the 9A result and authorize the next milestone.

---

# 31. Codex Operating Rule for Phase 9

For every authorized milestone:

```text
1. inspect only the relevant current repository state
2. reuse existing Phase 8 research structures where possible
3. implement the smallest coherent mechanism satisfying this brief
4. preserve simulation authority and determinism
5. run focused causal/research proofs
6. run affected regression tests
7. run broader suite only at the appropriate exit gate
8. commit after the milestone passes
9. report concise evidence
10. stop
```

Do not:

```text
invent new product scope
redesign the project
add architecture for imagined future requirements
create new approval bureaucracy
continue to the next subphase without authorization
```

If a milestone exposes a genuine architectural conflict that makes this brief unsafe or impossible, report the conflict and the smallest viable alternatives.

Otherwise, implement.

---

# Final Phase 9 Principle

> **Phase 8 taught the civilization to change what becomes possible. Phase 9 teaches the research system to prove how that change entered history, how it propagated, how another history differed, and whether similar structures recur later.**

The world is now large enough.

The next engineering achievement is not making it simulate more things.

It is making the history it already produces **measurable, traceable, comparable and reproducible**.
