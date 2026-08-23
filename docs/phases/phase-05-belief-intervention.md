# Phase 5 — Belief, Intervention & Counterfactual Fate

**Status:** Complete — 5A–5E implemented at foundation scope

**Roadmap:** [`Phase 5`](../ROADMAP.md#phase-5--belief-intervention--counterfactual-fate)

**Prerequisite:** [`Phase 4 — Spatial World, Mobility & Encounters`](phase-04-spatial-mobility.md)

**Historical source:** Pre-normalization belief/intervention vision, reorganized as Phase 5 on 2026-08-22. Historical document versions must not be used as phase numbers.

**Purpose:** Add imperfect perception, belief formation, prayer, sparse intervention, faith, and counterfactual divergence without giving the player direct control over NPCs.

---

# 1. Core Principle

NPCs act on perceived reality, not omniscient world truth.

```text
WORLD TRUTH
→ observation / exposure
→ imperfect perception
→ belief
→ appraisal
→ emotion / desire
→ intention
→ action
→ consequence
→ memory / belief update
```

```text
world truth ≠ NPC perception ≠ NPC belief
```

Misunderstanding, uncertainty, misinformation, attribution, faith, and skepticism therefore become causal mechanisms.

---

# 2. Phase 5 Build Order

| Step | Status | Outcome |
|---|---|---|
| 5A — Perception and belief | Complete | World truth, received observations, perceptions, and beliefs are distinct; beliefs persist and affect visit movement. |
| 5B — Shrine and prayer | Complete | An ordinary shrine and structured, deterministic prayer behavior are implemented and persistent. |
| 5C — Indirect intervention | Complete | Persistent dreams, signs, and opportunities create fallible stimuli and temporary action utility rather than commands. |
| 5D — Faith and causal attribution | Complete | NPCs interpret outcomes through prior faith and available evidence, then update faith or skepticism. |
| 5E — Counterfactual comparison | Complete | Compare reproducible baseline and intervention timelines. |

Phase 4 remains responsible for:

```text
locations
roads
movement
routes
co-location
exposure
encounters
```

Phase 5 builds on that physical layer rather than replacing it.

## Current implementation position

The 5A foundation is complete at its intended initial scope:

- successful interaction creates reciprocal location observations;
- deterministic perception produces confidence without new RNG draws;
- current beliefs remain distinct from changing world truth;
- SQLite schema version 6 persists observations and beliefs;
- strong-tie visits use believed locations, so stale knowledge can cause failed rendezvous.

The 5B foundation is complete at its intended initial scope:

- the fixed world map includes an ordinary, connected shrine;
- prayer is a seeded action whose utility uses existing stress, goal blockage, physical energy, and prior prayer habit;
- an NPC records a structured prayer only after reaching the shrine;
- prayer records contain agent, desire type, intensity, related goal, and simulated-day timestamp;
- prayer also appears in causal event history, but it guarantees no response;
- SQLite schema version 7 persists append-only prayer history, while version 1–6 worlds load with empty prayer state.

The 5C foundation is complete at its intended initial scope:

- `dream`, `sign`, and `opportunity` are structured, target-specific, time-bounded world conditions;
- dreams can reach a target anywhere, while signs and opportunities require ordinary spatial co-location and may expire unseen;
- existing traits, stress, and intervention strength deterministically produce missed, ignored, aligned, or misinterpreted responses without consuming world RNG;
- noticed stimuli pass through observation and perception without identifying a divine source;
- aligned or misinterpreted stimuli temporarily adjust one ordinary action score, but never force selection or success;
- intervention creation, responses, causal NPC events, and schema-version-8 persistence remain inspectable and restart-equivalent.

The 5D foundation is complete at its intended initial scope:

- each NPC has one bounded faith continuum, with skepticism defined as its complement;
- significant outcomes receive an append-only attribution to miracle, coincidence, personal effort, social help, institutional cause, manipulation, or unknown cause;
- prior faith, recent matching prayer, remembered intervention response, explicit social/institutional evidence, traits, and outcome significance deterministically shape attribution;
- attribution changes faith modestly and feeds it back only into future prayer utility, without changing causal truth or guaranteeing action;
- perceived intervention responses remain attribution evidence for a bounded 30-day window even after the original stimulus expires;
- schema version 9 persists faith and exact event-linked attribution history, while version 1–8 worlds load with neutral faith and empty attribution state.

The 5E foundation is complete at its intended initial scope:

- a scheduled intervention record defines deterministic intervention timing and parameters;
- paired fresh worlds hold seed, population, and duration constant while only one branch receives the schedule;
- immutable agent snapshots compare resources, career, state, location, relationships, social graph, beliefs, prayers, attribution, actions, and causal events;
- each affected agent reports changed fields and its first differing event, while the result records the first day any agent trajectory diverged;
- an empty schedule produces identical worlds and RNG states, a baseline branch matches an ordinary same-seed run, and repeated comparisons are exact;
- `scripts/compare_counterfactual.py` exposes one intervention comparison without persistence, network access, or an LLM.

The Phase 5 exit condition is satisfied. Phase 6 scope must be refined before further implementation.

---

# 3. Perception & Belief

An NPC should not automatically know the complete world state.

Conceptual separation:

```text
REALITY
what happened

OBSERVATION
what information reached the NPC

PERCEPTION
what the NPC noticed / understood

BELIEF
what the NPC currently thinks is true
```

Perception may depend on:

```text
location
exposure
attention
memory
capabilities
trust
emotion
information source
prior belief
uncertainty
```

Beliefs may be:

```text
accurate
incomplete
incorrect
uncertain
contradictory
socially inherited
```

The decision engine consumes the NPC's perceived state rather than direct omniscient truth whenever appropriate.

---

# 4. Shrine & Prayer

Shrines are ordinary world locations with special behavioral meaning.

Possible triggers:

```text
stress
fear
grief
desire
gratitude
uncertainty
habit
existing faith
```

These are human-readable interpretations, not required emotion fields. The initial implementation should derive prayer utility from measurable existing state such as stress, goal blockage, loss events, uncertainty, habit, and faith; it must not add `fear`, `grief`, or similar flags merely to manufacture the example.

Pattern:

```text
need / emotion
→ shrine utility increases
→ NPC travels to shrine
→ prayer event
```

Minimum structured prayer:

```text
Prayer
├── agent_id
├── desire_type
├── intensity
├── related_goal
└── timestamp
```

Prayer does not guarantee intervention.

---

# 5. God Intervention

The player changes conditions, not NPC decisions.

Initial intervention types:

```text
dream
sign
opportunity
```

Later possibilities may include:

```text
warning
encounter
luck modifier
protection
misfortune
```

Pattern:

```text
PLAYER INTENTION
→ intervention event
→ world condition changes
→ NPC may or may not perceive it
→ NPC interprets it
→ normal decision engine responds
→ downstream consequences
```

Intervention must never directly force:

```text
belief
decision
success
failure
relationship
```

Every causal link may fail, be ignored, misunderstood, or create unintended effects.

---

# 6. Dreams & Signs

Dreams and signs are noisy communication channels.

```text
player intention
→ symbolic stimulus
→ perception
→ memory + prior belief + emotion
→ interpretation
→ possible action
```

The same stimulus may produce different interpretations across NPCs.

The LLM may later generate language or symbolism, but the simulation remains responsible for causal meaning and effects.

---

# 7. Faith & Causal Attribution

NPCs never receive proof that the player exists.

Faith changes through perceived causality:

```text
prayer / desire
→ later event
→ temporal association
→ interpretation
→ attribution
→ faith / skepticism update
```

Possible interpretations:

```text
miracle
coincidence
personal achievement
help from another NPC
institutional cause
manipulation
unknown cause
```

Faith is therefore a belief state influenced by experience, prior belief, evidence, social influence, and uncertainty.

---

# 8. Social Propagation

Belief may spread through the existing social world.

```text
experience
→ testimony / rumour
→ trusted relationship
→ social confirmation
→ belief update
```

Possible influences:

```text
source trust
repetition
status
emotional resonance
group alignment
contradictory evidence
skepticism
```

Phase 5 only needs the mechanism. Large-scale religion, ideology, propaganda, and institutions remain later extensions.

---

# 9. Counterfactual Intervention

The intervention system must preserve reproducibility.

```text
Seed X
+ no intervention
→ baseline timeline

Seed X
+ intervention at time T
→ counterfactual timeline
```

Compare downstream divergence in:

```text
goals
resources
relationships
stress
belief
location
career
life events
```

This is the main research bridge between the fictional god mechanic and the thesis experiment framework.

---

# 10. Minimal Data Direction

Add only what Phase 5 requires.

Conceptual entities:

```text
observations
beliefs
prayers
interventions
```

Existing systems remain responsible for:

```text
agents
relationships
events
locations
roads
movement
```

Belief changes, prayers, and interventions should also appear in causal event history when significant.

---

# 11. Phase 5 Completion Test

A valid Phase 5 run should support a causal chain such as:

```text
NPC loses job
→ stress increases
→ shrine becomes attractive
→ NPC travels to shrine
→ prayer is recorded
→ player creates opportunity
→ NPC encounters opportunity
→ NPC interprets event
→ decision engine chooses response
→ trajectory changes
→ faith / skepticism updates
```

And:

```text
same seed
baseline vs intervention
→ measurable divergence
```

No LLM should be required for this test.

---

# 12. Out of Scope for Phase 5

```text
reproduction
child development
deep generations
Ouroboros
technology discovery
civilization mutation
large institutions
macroeconomics
politics
semantic embeddings
ML / RL expansion
social media
full religion systems
3D visualization
```

These remain later systems from the archived vision documents.

---

# 13. Phase 5 Design Laws

1. NPCs act on perceived reality, not guaranteed world truth.
2. Reality, observation, perception, and belief remain distinct.
3. Geography and exposure determine what information can physically reach an NPC.
4. Prayer is a structured desire event, not a command to the player.
5. Intervention changes conditions, never guaranteed outcomes.
6. Dreams and signs are noisy communication channels.
7. NPC interpretation depends on prior state, memory, belief, and context.
8. Faith emerges from causal attribution under uncertainty.
9. Identical interventions may produce different interpretations and trajectories.
10. Beliefs may propagate through trusted social relationships.
11. All important intervention effects must remain traceable in causal history.
12. Baseline and intervention runs must remain reproducible from the same seed.
13. The simulation must function without an LLM or API key.
14. Phase 5 should remain lightweight, explainable, offline, and weak-hardware compatible.
15. Human emotion words in this brief describe possible interpretations; they do not authorize hard-coded emotion labels or Phase 10 cognitive mechanisms.

---

# Canonical Phase 5 Pattern

```text
REALITY
= world state + events

PERCEPTION
= reachable information × attention × capability × uncertainty

BELIEF
= perception + memory + prior belief + social information

PRAYER
= desire + emotion + belief → structured request event

GOD
= sparse indirect perturbation of world conditions

INTERPRETATION
= intervention perception + prior belief + context

FAITH
= causal attribution under uncertainty

ACTION
= perceived state + belief + goals + needs + social context + stochastic choice

COUNTERFACTUAL
= same seed + different intervention history → trajectory divergence
```

---

## Updated Vision

**The Playing God now distinguishes reality from what its inhabitants believe reality to be.**

NPCs occupy a causal physical world, encounter only a fraction of its information, build imperfect beliefs, seek meaning, pray, receive ambiguous interventions, interpret outcomes differently, and update their future behavior accordingly.

The player does not control lives directly.

The player perturbs reality and observes what autonomous agents make of it.

```text
WORLD
→ EXPOSURE
→ PERCEPTION
→ BELIEF
→ PRAYER
→ INTERVENTION
→ INTERPRETATION
→ DECISION
→ CONSEQUENCE
→ FAITH
→ NEW BELIEF
```

**Computer Engineering thesis identity:** a reproducible multi-agent causal simulation studying how imperfect information and sparse external perturbations propagate through autonomous agents and produce measurable trajectory divergence.
