# Playing God — Current Status

**Updated:** 2026-09-02

**Current phase:** Phase 7 — Development, Adaptive Cognition, Reproduction & Generations

**Current position:** Phase 7D Household, Inheritance & Lifecycle is complete. Material guardian support now shapes development, retirement and mortality create turnover, and positive estates transfer traceably to living children.

## Phase Progress

| Phase | Status | Description |
|---|---|---|
| 1 — Simulation foundation | Complete | Deterministic autonomous NPCs and life trajectories. |
| 2 — Persistent world | Complete | SQLite save/load and reproducible continuation. |
| 3 — Social causality | Complete | Directed relationships and cross-agent effects. |
| 4 — Spatial world, mobility, and encounters | Complete | Movement, exposure, interaction, familiarity, visits, and path inspection. |
| 5 — Belief, intervention, and counterfactual fate | Complete | Same-seed baseline and intervention timelines produce traceable, reproducible trajectory comparisons. |
| 6 — Society, information, and institutions | Complete | Shared scarcity, a capacity-limited institution, bounded information diffusion, and locally cascading collective action are implemented and inspectable. |
| 7 — Development, adaptive cognition, reproduction, and generations | In progress | Adaptive cognition, founder prehistory, reproduction, development, and lifecycle turnover are complete; cultural transmission is next. |
| 8–11 — Discovery through recursive reality | Planned | Later roadmap phases; not part of the current implementation. |

## Phase 5 Progress

| Step | Status | What it means |
|---|---|---|
| 5A — Perception and belief | Complete | NPCs receive limited observations, form persistent beliefs, and use believed locations for visits. |
| 5B — Shrine and prayer | Complete | An ordinary shrine, deterministic prayer utility, structured prayer history, and schema-v7 persistence are implemented. |
| 5C — Indirect intervention | Complete | Persistent dreams, signs, and opportunities can expire unseen, be missed, ignored, aligned, or misinterpreted, and only adjust normal action utility. |
| 5D — Faith and causal attribution | Complete | Outcomes receive inspectable causal interpretations that update a bounded faith/skepticism continuum. |
| 5E — Counterfactual comparison | Complete | Immutable snapshots, first-divergence evidence, and a CLI compare same-seed branches. |

## Phase 6 Progress

| Step | Status | What it means |
|---|---|---|
| 6A — Minimal shared economy | Complete | Finite job capacity creates shared scarcity, persists through schema v10+, and has read-only macro metrics. |
| 6B — First rule-bearing institution | Complete | The school has one deterministic daily training slot with traceable admission and denial. |
| 6C — Information and belief diffusion | Complete | Employment claims move only through contact, preserve origin and hop identity, decay across relays, resist loops, persist through schema v11, and expose read-only diffusion metrics. |
| 6D — Collective action | Complete | Derived pressure enters ordinary action selection, participation evidence moves through local encounters, individual thresholds create selective cascades, and read-only metrics expose participants, rate, onset, peak, and depth with per-agent causal traces. |

## What We Are Doing Next

Implement Phase 7E only:

1. Reuse parent/guardian, social, school, and information channels for cultural exposure.
2. Let descendants accept, reject, or modify transmitted beliefs/norms without copying parent policy.
3. Keep culture separate from inherited priors and prevent society-wide teleportation.

## Phase 7 Progress

| Step | Status | What it means |
|---|---|---|
| 7.0.0 — Learning boundary | Complete | Learned preferences can influence only the ranking of already-valid actions; world rules still own eligibility and consequences. |
| 7.0.1 — Contextual adaptation | Complete | Goal-context action values learn online from multidimensional consequences; controlled outcomes produce inspectable preference and later-choice divergence. |
| 7.0.2 — Learned-state persistence | Complete | Schema v12 preserves adaptive configuration and minimal learned values; legacy worlds remain empty/disabled and adaptive split runs remain exact. |
| 7.0.3 — Delayed-consequence gate | Complete | Costly training has immediate goal-relevant capability feedback, so contextual adaptation is sufficient and Q-learning is deferred. |
| 7A — Founder prehistory | Complete | Three seeded structured records causally define each new founder's capability, livelihood, resources, and recent wellbeing; schema v13 persists them without fabricating legacy history. |
| 7B — Family / reproduction foundation | Complete | Opt-in seeded reproduction checks explicit relationship, age, co-location, resource, stress, kinship, cooldown, and population constraints; G1 children retain parents, guardians, birth context, and bounded inherited priors through schema v14. |
| 7C — Child development | Complete | Exact birth-anniversary checkpoints turn inherited aptitude plus family resources, relationships, school access, practice, and feedback into persisted skill and learned training value; adult actions remain blocked through age 17. |
| 7D — Household, inheritance, and lifecycle | Complete | Annual guardian support consumes real resources; retirement, seeded mortality, living-descendant inheritance, and inactive historical death create traceable turnover through schema v16. |
| 7E — Cultural transmission | Next | Move beliefs, norms, or knowledge through explicit family, social, institutional, and information exposure rather than genetic or society-wide copying. |
| 7F — Optional recurrence detection | Planned | Structural recurrence remains gated by completion of causal cultural transmission. |

## Documentation Guide

- [`ROADMAP.md`](ROADMAP.md) defines the canonical phase sequence and exit conditions.
- [`phases/`](phases/) contains detailed briefs for active, implemented phases.
- [`PROJECT_MAP.md`](PROJECT_MAP.md) maps implemented code ownership and tests.
- [`archive/`](archive/) contains superseded vision snapshots retained for research history.
- [`.agent/memory/CURRENT.md`](../.agent/memory/CURRENT.md) records concise engineering context for coding agents.
