# Current Engineering State

**Updated:** 2026-08-30

## Current milestone

Phases 4 and 5 are complete. Phase 6A shared economy, Phase 6B school institution, Phase 6C information diffusion, and Phase 6D collective action are implemented and verified. Phase 6 awaits final human review.

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
- Employment now consumes a finite shared job capacity initialized with deterministic 70% half-up rounding while preserving all initially employed agents. Occupancy and vacancies are derived from `Agent.employed`; each job-hunt draw is preserved and its vacancy/chance/roll outcome is traceable.
- SQLite schema version 10 persists only `job_capacity`. Schema 1–9 worlds derive valid capacity from loaded agents without RNG draws, and invalid capacity below occupancy is rejected.
- `World.economic_snapshot()` reports population, employment, capacity, vacancies, total/median money, and negative balances without mutation or RNG consumption.
- Exact social-affinity synchronization now avoids additive floating-point drift that could otherwise break persistence equality on Phase 6 trajectories.
- The existing school is now a concrete institution with one fixed training slot per day. Seeded world order determines admission; denied or off-site attempts receive no training effects, and structured events explain the outcome.
- School capacity resets by simulated day and has no changing long-term field, so schema 10 remains unchanged. `World.school_snapshot()` inspects the current rule and usage without mutation, and day-boundary restart matches uninterrupted execution.
- Successful contact creates structured employment evidence and may transmit one relevant third-party claim through the existing observation/perception/belief path. Stale claims are not refreshed from world truth, and testimony adds no world-RNG draws.
- Stable evidence IDs preserve origin agent/day and hop count across relays. Each hop is capped at 85% of source confidence plus existing trust/familiarity limits; agents ignore evidence identities already seen, preventing circular amplification.
- Direct employment observations are recorded only when new or more authoritative than the current belief. Transient seen/latest indexes keep weak-hardware cost bounded and rebuild exactly from persisted observations.
- SQLite schema version 11 persists information identity, origin, and hop count on observations. Schema 10 worlds load with neutral missing identity and migrate on save; restart continuation remains exact.
- `World.diffusion_snapshot()` derives historical reach, current matching-belief count, maximum hop depth, and average/median belief confidence without mutation or RNG consumption.
- Participation willingness is dynamically derived from economic pressure, employment, stress, risk tolerance, social state, and received evidence. Crossing the fixed model threshold only makes `participate` available to the ordinary seeded action selector; normal mobility routes successful participation to the park.
- Successful encounters with a recent participant create structured direct participation evidence with stable participant/day identity. Trust-weighted confirmation remains relevant for seven days, introduces no world-RNG draw, and cannot spread without local interaction.
- `World.collective_snapshot()` derives unique participants, participation rate, first day, daily peak, and evidence-generation depth. `World.participation_trace()` reconstructs the recorded score components, pre-decision evidence IDs, selected action, movement event, and participation event.
- The deliberate Phase 6 integration scenario links occupied finite job capacity, contact-acquired unemployment evidence, trusted participation evidence, a selective A-to-B cascade, a lower-pressure nonparticipant, macro metrics, SQLite reload, and exact one-day continuation without schema 12 or new dependencies.

## Active architectural concern

The current world uses one seeded RNG stream. Same-seed branches have identical initialization and remain exactly reproducible, but an intervention-induced behavior change can alter later RNG draw allocation. Phase 5 comparisons therefore measure total model trajectory divergence, not an isolated treatment effect with per-event common random numbers. Keyed/substream RNG would require an intentional kernel migration before stronger causal claims.

## Known failures and blockers

- Full suite after Phase 6D.3: 141 tests pass with warnings suppressed; focused Phase 6, persistence, and reproducibility suites also pass.
- Persistence tests emit unclosed-SQLite `ResourceWarning` messages. They do not currently fail the suite but should be diagnosed separately.

## Next logical task

Review the complete Phase 6 exit condition. Do not begin Phase 7 until its implementation brief is human-approved.
