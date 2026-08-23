# Current Engineering State

**Updated:** 2026-08-23

## Current milestone

Phases 4 and 5 are complete. Phase 5A–5E now cover perception/belief, shrine/prayer, indirect intervention, faith attribution, and paired counterfactual comparison at foundation scope. Phase 6 — Society, Information & Institutions requires scope refinement next.

## Recent completed work

- Added stable coding-agent rules and a retrieval-first session protocol.
- Mapped current subsystem ownership, entry points, focused tests, and dependency boundaries.
- Added concise episodic decision/failure memory without introducing a runtime dependency or external service.
- Focused location, routing, mobility, exposure, and interaction tests pass; exposure/interaction remain standalone.
- SQLite schema version 3 persists `current_location` and `destination`; version 1/2 worlds load with backward-compatible `home`/`None` defaults.
- `World.run()` now moves each NPC once for its selected daily activity without adding RNG draws. The fixed map is rebuilt identically for new and loaded worlds.
- The Phase-1 fixture now verifies a legacy projection, so spatial fields/travel events can evolve while prior non-spatial behavior remains protected.
- After daily movement, co-located pairs become exposures; a world-seed/day-derived RNG resolves interactions, and successful pairs gain familiarity in both graph directions.
- Persistence/reproducibility snapshots now include full social-graph state. Authoritative `Agent.relationships` affinity is synchronized into `SocialGraph` before encounter updates.
- Autonomous `socialize`, `help`, and `compete` actions can target only co-located NPCs whose mutual familiarity is at least `0.22`; familiar help also updates trust/respect through the social graph.
- The frozen Phase-1 fixture now validates the archived Phase-1 engine. Current Phase-4 behavior has separate seeded, split-run, and persistence reproducibility contracts.
- Socialize/help travel can visit the current location of the strongest mutually familiar positive tie (`familiarity >= 0.34`, affinity `>= 0.18` in both directions). Needs still override visits, and the visit uses normal Dijkstra travel.
- Successful interactions now append reciprocal events containing the other agent ID and location. SQLite schema version 4 persists this context; version 3 events load with `None` context and migrate on save.
- `Agent.energy` remains the backward-compatible physical-energy state and `physical_energy` alias; bounded `social_energy` separately affects social decisions, trips, encounter probability, social actions, and recovery. SQLite schema version 5 persists it and defaults older worlds from physical energy without new RNG draws.
- Added a read-only Matplotlib spatial debug map for fixed locations, roads, current NPC positions, optional highlighted routes, and simulation day. `scripts/show_spatial_map.py` loads persisted worlds; renderer tests verify it does not mutate simulation state.
- Successful interactions now give each participant an append-only direct observation of the other's location. Deterministic perception updates a separate belief, which remains stale if truth later changes without new evidence.
- SQLite schema version 6 persists observation histories and current beliefs. Version 1–5 worlds load with empty perception state and migrate on save without consuming RNG draws.
- Strong-tie visits require a positive-confidence location belief. Current beliefs route normally, stale beliefs can cause failed rendezvous, and missing/invalid beliefs fall back to ordinary cafe travel without new RNG draws.
- Documentation now uses stable phase-based names: `docs/ROADMAP.md`, `docs/STATUS.md`, and `docs/phases/phase-XX-*.md`. Superseded versioned vision briefs live under `docs/archive/` and no longer drive phase numbering.
- The fixed map includes a shrine connected by ordinary roads. `pray` participates in normal seeded action choice using existing stress, goal blockage, energy, and prayer habit; only an NPC at the shrine creates a structured prayer and matching causal event.
- SQLite schema version 7 persists append-only prayer histories with desire type, intensity, related goal, and simulated-day timestamp. Version 1–6 worlds load with empty prayer state and migrate on save.
- Target-specific `dream`, `sign`, and `opportunity` interventions are time-bounded world conditions. Dreams can reach a target anywhere; signs/opportunities require co-location and can expire unseen.
- Existing state deterministically produces missed, ignored, aligned, or misinterpreted responses without consuming world RNG. Noticed stimuli create ordinary observations and events with no divine source; interpreted stimuli only add temporary normal-action score adjustments.
- SQLite schema version 8 persists append-only interventions and responses. Version 1–7 worlds load with empty intervention state and migrate on save.
- Each NPC has a bounded `faith` value initialized neutrally at `0.5`; `skepticism` is its computed complement rather than separately mutable state. Faith modestly affects later prayer utility.
- Significant outcomes are deterministically classified and linked to an append-only attribution: miracle, coincidence, personal effort, social help, institutional cause, manipulation, or unknown. Explicit identifiable causes outrank supernatural inference.
- Recent matching prayer, remembered interpreted intervention response, prior faith, traits, and event significance shape causal attribution without RNG or LLM input. The response memory window is 30 days and is independent of stimulus expiry.
- Attribution records link the exact outcome event index to evidence and preserve faith before/after. Matching causal events remain explicit that the record is an NPC inference, not proof of world causation.
- SQLite schema version 9 persists current faith and append-only attribution history. Version 1–8 worlds load with neutral faith and empty attribution state, then migrate on save.
- A scheduled counterfactual comparison runs isolated same-seed baseline and intervention worlds day by day. The baseline exactly matches an ordinary run, empty schedules remain identical, and repeated comparisons are exact.
- Immutable agent snapshots cover dynamic resources, career, state, location, relationships/social graph, beliefs, histories, actions, prayers, and attribution. Results identify changed fields, affected agents, first differing events, and the first divergence day.
- `scripts/compare_counterfactual.py` runs a one-intervention comparison and labels its output as deterministic model divergence rather than supernatural proof.

## Active architectural concern

The current world uses one seeded RNG stream. Same-seed branches have identical initialization and remain exactly reproducible, but an intervention-induced behavior change can alter later RNG draw allocation. Phase 5 comparisons therefore measure total model trajectory divergence, not an isolated treatment effect with per-event common random numbers. Keyed/substream RNG would require an intentional kernel migration before stronger causal claims.

## Known failures and blockers

- Full suite after Phase 5 counterfactual comparison: 103 tests pass.
- Persistence tests emit unclosed-SQLite `ResourceWarning` messages. They do not currently fail the suite but should be diagnosed separately.

## Next logical task

Refine and approve the first Phase 6 scope, likely beginning with a minimal 6A economy mechanism grounded in existing employment, money, help, and resource flows.
