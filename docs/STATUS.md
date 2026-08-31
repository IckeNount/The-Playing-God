# Playing God — Current Status

**Updated:** 2026-08-31

**Current phase:** Phase 7 — Development, Adaptive Cognition, Reproduction & Generations

**Current position:** Phase 6 is accepted and closed. Phase 7.0.0 is complete: the existing decision chooser exposes a minimal learned-preference input that can change ranking only among actions already made valid by deterministic world state and constraints.

## Phase Progress

| Phase | Status | Description |
|---|---|---|
| 1 — Simulation foundation | Complete | Deterministic autonomous NPCs and life trajectories. |
| 2 — Persistent world | Complete | SQLite save/load and reproducible continuation. |
| 3 — Social causality | Complete | Directed relationships and cross-agent effects. |
| 4 — Spatial world, mobility, and encounters | Complete | Movement, exposure, interaction, familiarity, visits, and path inspection. |
| 5 — Belief, intervention, and counterfactual fate | Complete | Same-seed baseline and intervention timelines produce traceable, reproducible trajectory comparisons. |
| 6 — Society, information, and institutions | Complete | Shared scarcity, a capacity-limited institution, bounded information diffusion, and locally cascading collective action are implemented and inspectable. |
| 7 — Development, adaptive cognition, reproduction, and generations | In progress | 7.0.0 establishes the valid-action learning boundary; the first online learner is next. |
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

Implement Phase 7.0.1 only:

1. Define one compact, inspectable learning context over existing NPC/world information.
2. Derive bounded consequence feedback from existing state/event changes.
3. Prove in a controlled scenario that different experience changes later valid-action preference.
4. Do not add persistence yet; learned-state persistence belongs to 7.0.2.

## Phase 7 Progress

| Step | Status | What it means |
|---|---|---|
| 7.0.0 — Learning boundary | Complete | Learned preferences can influence only the ranking of already-valid actions; world rules still own eligibility and consequences. |
| 7.0.1 — Contextual adaptation | Next | Add the first deterministic, CPU-friendly online learner and prove experience-driven preference divergence. |
| 7.0.2–7F | Planned | Persistence, delayed-credit gate, founders, reproduction, development, lifecycle, culture, and optional recurrence detection remain gated by earlier milestones. |

## Documentation Guide

- [`ROADMAP.md`](ROADMAP.md) defines the canonical phase sequence and exit conditions.
- [`phases/`](phases/) contains detailed briefs for active, implemented phases.
- [`PROJECT_MAP.md`](PROJECT_MAP.md) maps implemented code ownership and tests.
- [`archive/`](archive/) contains superseded vision snapshots retained for research history.
- [`.agent/memory/CURRENT.md`](../.agent/memory/CURRENT.md) records concise engineering context for coding agents.
