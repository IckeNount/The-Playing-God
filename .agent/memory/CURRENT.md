# Current Engineering State

**Updated:** 2026-09-02

## Current milestone

Phases 4–7 are complete. Phase 7F recurrence detection was evaluated and deferred to Phase 9 because the repository has no persisted multi-adult-generation dataset. Phase 8 is planned but not approved or started.

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
- Participation events now freeze the decision-time influencer and evidence IDs used by traces and cascade depth. Later trust mutation cannot rewrite that history, and existing schema-v11 event persistence carries the data without a migration.
- The Phase 6 integration scenario now includes an actual job-hunt attempt against zero vacancies and verifies the resulting unemployment evidence before diffusion and selective participation.
- `save_world()` and `load_world()` explicitly close SQLite connections; repeated round trips produce no connection `ResourceWarning`. `scripts/show_social_graph.py` again loads a supplied persisted-world path through the existing `load_world()` API.
- `decision.choose()` accepts a separate learned-preference mapping only after it fixes the base-valid candidate set. Learned and intervention adjustments can rank valid actions but cannot resurrect an ineligible action.
- Opt-in adaptive worlds use the existing current goal as a five-value learning context. Each `(context, action)` retains a running mean of multidimensional consequences and goal-relevant feedback, producing a bounded `0.75` preference adjustment without consuming RNG.
- A controlled equal-prior training scenario proves that institutional admission versus denial creates different learned preference and later choice. Same-seed adaptive runs remain exact, and adaptation stays explicitly opt-in so legacy default behavior is unchanged.
- SQLite schema version 12 persists the world adaptive-cognition flag and each agent's exact contextual action-value table. Schema-v11 and older worlds load disabled/empty without RNG draws or fabricated history, malformed adaptive JSON is rejected, and adaptive split-run continuation matches uninterrupted execution.
- The 7.0.3 delayed-consequence gate defers Q-learning: successful training has immediate money/energy/stress costs but also immediate skill progress, which supplies positive `improve_skill` feedback; denied training supplies none. No current Phase 7 behavior requires backward assignment of later income.
- Each new G0 founder now has exactly three structured prior-life records covering capability exposure, livelihood entry, and recent conditions. Their effects authoritatively define starting skill, employment/job level/salary, resources, energy, stress, and reputation without changing the existing RNG draw order or initialized values.
- Traits and sins remain priors, age remains a founder demographic, and adaptive values remain empty until real action/outcome experience occurs. Founder prehistory adds no full-childhood simulation, prose biography, new dependency, or extra random draw.
- SQLite schema version 13 persists compact founder history as checked agent-owned JSON. Schema-v12 and older worlds load empty without fabricated events or RNG consumption and migrate honestly on save.
- Opt-in `World(reproduction_enabled=True)` evaluates unordered adult pairs through explicit age, co-location, mutual relationship, resource, employment, stress, close-family, cooldown, and population constraints. Only eligible pairs consume a 1% seeded reproduction draw.
- A successful birth creates a deterministic G1 identity, reciprocal parent/child links, parent guardianship, birth day/location, a structured household/relationship/roll context, and bounded ±0.08 parent-derived trait/sin priors. It never copies memories, beliefs, learned values, occupation, reputation, adult skill, or founder history.
- Later-generation children remain dependent and cannot move, act, receive interventions, become social-action targets, or enter encounters before Phase 7C. Parents receive a modest resource/stress cost and all three agents receive structured birth events.
- SQLite schema version 14 persists the reproduction flag and checked agent family JSON. Schema-v13 and older worlds load disabled with empty founder family state, preserve RNG, and migrate without fabricated genealogy; reciprocal family links and restart continuation are validated.
- Later-generation agents now age on exact birth anniversaries through one compact annual developmental checkpoint; founders preserve legacy global-year aging. Each record freezes guardian IDs, household resources, employment/stress, relationship support, learning potential, school availability/opportunity, practice, feedback, and skill change.
- Ages 6–17 can acquire skill only when the existing school is available and current family/resource opportunity crosses the explicit threshold. Supported school years also update the existing adaptive `improve_skill` / `train` value when adaptive cognition is enabled; development itself consumes no RNG.
- Children remain outside adult movement, action, intervention, encounter, and social-target paths through age 17. The age-18 checkpoint ends dependency and admits the developed agent to ordinary adult behavior.
- A controlled same-prior comparison reaches 0.295559 skill with 12 learned training observations under supported access versus zero skill/no training value under constrained upbringing. SQLite schema v15 persists checked developmental histories; schema-v14 and older histories remain honestly empty, and restart continuation is exact.
- A direct 6,570-day anniversary scan took about 0.012 seconds for one child and retained only 18 developmental records; no benchmark framework was added.
- Lifecycle defaults on for new reproduction-enabled worlds but remains separately configurable; default and schema-v15 worlds remain disabled. Ages 1–17 receive one structured annual support record whose 48-unit target is divided among living guardians and deducted from their actual money.
- Lifecycle-enabled founders age at global 365-day boundaries while descendants retain exact birth anniversaries. Retirement at 65 ends employment and blocks work/job-hunt; annual world-RNG mortality checks begin at 70, use explicit age/stress probability, and guarantee exit at 90.
- Death retains the agent, genealogy, and event history while excluding the deceased from actions, encounters, interventions, reproduction, and living economy/diffusion/collective metrics. Positive estates transfer deterministically to living direct children with mirrored receipts; debt does not transfer and childless estates remain explicitly unallocated.
- The 100-agent limit now counts living population as a weak-hardware guardrail, so a traceable death reopens birth capacity without deleting history. The supported 7C comparison now reaches 0.237020 skill after 816 total guardian support cost versus zero under constrained upbringing.
- SQLite schema v16 persists the lifecycle setting and checked support, retirement, mortality, death, and inheritance records. Schema-v15 and older worlds load disabled/empty; death/inheritance and split lifecycle continuation survive restart exactly. A direct 91-year scan took about 0.056 seconds and retained 11 mortality checks.
- One bounded `cultural_norm` claim uses abstract support/oppose/uncertain stances. Explicit agent expression can move through annual guardian exposure, actual school access, or successful social contact; culture never copies at birth and never copies adaptive policy.
- Each exposure freezes route, source, relationship inputs, influence, accept/modify/reject response, resulting stance, and information provenance. Rejected and modified claims remain raw observations, while only accepted or modified interpretations revise beliefs. Transmission consumes no world RNG.
- Cultural link validation requires a matching developmental guardian checkpoint, school-access record, or interaction event plus the raw received observation. Schema v17 persists this history; schema-v16 and older worlds load empty cultural records, and split continuation remains exact.
- Counterfactual snapshots and compact trajectory signatures include cultural history, so a changed response remains visible even when later belief state converges.
- The 7F gate found both repository databases are founder-only schema-v1/v2 worlds. A bounded ordinary seed-1947 probe reached 10 G0 plus 13 G1 after seven years/53.81 seconds, but had no adult descendant or G2 and only two descendants with culture; implementing recurrence now would manufacture the evidence.
- The controlled same-prior development scenario now runs both descendants through age 18 and directly proves Phase 7's exit: supported adulthood retains 0.237020 skill, 12 school exposures, and learned training value, while constrained adulthood retains zero for all three.

## Active architectural concern

The current world uses one seeded RNG stream. Same-seed branches have identical initialization and remain exactly reproducible, but an intervention-induced behavior change can alter later RNG draw allocation. Phase 5 comparisons therefore measure total model trajectory divergence, not an isolated treatment effect with per-event common random numbers. Keyed/substream RNG would require an intentional kernel migration before stronger causal claims.

## Known failures and blockers

- No known Phase 7 failure. The full suite passes 197 tests.

## Next logical task

Await an approved Phase 8 implementation brief. Keep recurrence analysis deferred to Phase 9 until real persisted histories contain multiple adult generations.
