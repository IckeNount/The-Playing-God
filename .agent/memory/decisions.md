# Engineering Decisions and Failures

Record only durable rationale or failures future agents would otherwise rediscover. Source and tests remain current truth.

## 2026-08-21 — Keep coding-agent memory repository-native

**Area:** coding-agent-memory

**Decision:** Use four small Markdown entry points—`AGENTS.md`, `docs/PROJECT_MAP.md`, `CURRENT.md`, and this file—for the initial M1/M2/M4 memory foundation.

**Reason:** The repository is small enough for targeted text retrieval. Manual, dependency-free memory solves session rediscovery without creating a second application to maintain.

**Rejected for now:** Custom schemas, record classes, validation frameworks, ID machinery, a large CLI, semantic/vector storage, Graphify/Serena integration, and separate infrastructure databases. Reconsider only after a measurable retrieval or consistency problem appears.

**Affected:** `AGENTS.md`, `docs/PROJECT_MAP.md`, `.agent/memory/`

## Existing invariant — deterministic simulation truth

**Area:** core-simulation, persistence

**Decision:** Causal randomness comes from the world's seeded RNG, and a saved/reloaded continuation must equal an uninterrupted run.

**Reason:** Reproducibility and causal traceability are thesis requirements. Coding-agent memory may explain this invariant but must never participate in runtime behavior.

**Avoid:** Global randomness, hidden LLM decisions, or memory-derived simulation state.

**Affected:** `src/playing_god/core/rng.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_reproducibility.py`, `tests/test_persistence.py`

## 2026-08-21 — Persist only current agent spatial state first

**Area:** spatial-mobility, persistence

**Decision:** SQLite schema version 3 adds `current_location` and nullable `destination` to the existing `agents` table. Version 1/2 databases load with `home` and `None` defaults and migrate on their next save.

**Reason:** Agent position must survive restarts before movement can join the daily world loop. These are the only Phase 4 spatial fields currently represented by `Agent`.

**Rejected for now:** Separate location, road, position, travel-event, or encounter tables before those concepts have an integrated runtime owner.

**Affected:** `src/playing_god/persistence/sqlite_store.py`, `tests/test_persistence.py`

## Existing invariant — preserve legacy affinity during social expansion

**Area:** social

**Decision:** `Agent.relationships` remains the signed affinity consumed by existing Phase-2 behavior; `SocialGraph` adds explicit relationship dimensions and is rebuilt from agent state.

**Reason:** This allows richer social modeling without silently changing established decision behavior.

**Avoid:** Treating the NetworkX graph as a drop-in replacement before all consumers and persistence paths have an intentional migration.

**Affected:** `src/playing_god/core/agent.py`, `src/playing_god/core/social.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`

## 2026-08-21 — Integrate one event-driven movement per daily action

**Area:** spatial-mobility, core-simulation

**Decision:** Each NPC selects its existing daily action, chooses a destination from normalized needs plus that action/goal, and travels by Dijkstra route before applying the action. New and loaded worlds rebuild the same six-location fixed map.

**Reason:** This adds causal movement without frame loops or new RNG draws and provides the physical state required for later exposure detection.

**Rejected for now:** Procedural maps, frame-based movement, A*, and calibrated default money/energy travel costs. The travel engine accounts for edge costs, but the V1 shared map keeps them neutral until research assumptions justify values.

**Compatibility:** Travel events are excluded from the legacy 30-event crisis window, and the frozen Phase-1 fixture compares a non-spatial projection. This prevents logging frequency from changing prior causal behavior.

**Affected:** `src/playing_god/core/spatial.py`, `src/playing_god/core/mobility.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_spatial.py`, `tests/test_mobility.py`, `tests/test_reproducibility.py`

## 2026-08-21 — Exposure creates familiarity before relationships

**Area:** spatial-mobility, social

**Decision:** After all daily movement, node co-location creates exposures. A deterministic RNG derived from world seed and day resolves those opportunities, and each successful interaction adds `0.04` familiarity in both directions.

**Reason:** A separate day-derived stream keeps encounters reproducible across restarts without perturbing the established core RNG sequence. Familiarity records repeated contact while deferring stronger relationship semantics.

**Rejected for now:** Interaction without co-location, instant friendship, new encounter tables, and per-interaction long-term event logging. `last_exposures` and `last_interactions` support current-day inspection; cumulative familiarity persists in the existing relationship schema.

**Compatibility:** `Agent.relationships` remains authoritative affinity and is mirrored into `SocialGraph` before encounter updates, eliminating pre-save/load graph drift.

**Affected:** `src/playing_god/core/exposure.py`, `src/playing_god/core/world.py`, `tests/test_exposure.py`, `tests/test_persistence.py`, `tests/test_reproducibility.py`

## 2026-08-22 — Gate autonomous relationship actions by familiar exposure

**Area:** social, spatial-mobility

**Decision:** `socialize`, `help`, and `compete` select targets only from current co-location exposures, and both directed familiarity values must be at least `0.22` before stronger effects occur. A social outing may still consume the actor's ordinary outing resources when no familiar target is available, but it cannot alter another NPC.

**Reason:** Three successful `0.04` familiarity gains from the `0.10` baseline are required before ordinary interaction can become a stronger relationship event. This implements stranger → recognized stranger → acquaintance without instant friendship.

**Compatibility:** Causal targeting intentionally supersedes modern Phase-1 trajectory compatibility. The frozen fixture now tests `archive/phrase1_main.py`; the current engine retains independent deterministic, split-run, and save/load contracts.

**Affected:** `src/playing_god/core/world.py`, `tests/test_social.py`, `tests/test_reproducibility.py`

## 2026-08-22 — Let strong ties create visit movement

**Area:** spatial-mobility, social

**Decision:** A `socialize` or `help` trip may redirect from the normal cafe destination to the current location of the strongest mutually familiar positive tie. Both familiarity values must be at least `0.34` and both affinities at least `0.18`.

**Reason:** This closes the Phase 4 bidirectional loop: movement creates encounters, repeated encounters create relationships, and relationships change later movement. Deterministic strongest-tie selection avoids extra RNG draws.

**Constraints:** Low energy or high stress still selects home/park before a visit is considered. Visits use the same fixed graph, Dijkstra route, spatial state, and travel event path as ordinary movement; the target may still move later, so a visit opportunity does not guarantee interaction.

**Affected:** `src/playing_god/core/world.py`, `tests/test_mobility.py`

## 2026-08-22 — Store successful encounters in ordinary events

**Area:** social, persistence

**Decision:** Each successful interaction appends a reciprocal `interaction` event with nullable `target_id` and `location`. SQLite schema version 4 adds those fields to the existing append-only events table; schema version 3 records load with null context and migrate on save.

**Reason:** This preserves inspectable who/where history across restarts with two nullable fields and no new runtime subsystem. Only realized interactions are durable; exposures remain current-day opportunities.

**Compatibility:** Interaction events are excluded from the legacy crisis lookback so added logging frequency cannot change crisis timing. Existing event constructors and older databases default the new fields to `None`.

**Affected:** `src/playing_god/core/events.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_exposure.py`, `tests/test_persistence.py`

## 2026-08-22 — Separate physical and social energy without new randomness

**Area:** core-simulation, spatial-mobility, social, persistence

**Decision:** Keep legacy `Agent.energy` as physical energy with an explicit `physical_energy` alias, and add a separately bounded `social_energy`. Social energy affects social-action scores, social-trip cancellation, encounter probability, conversation cost, and rest/daily recovery; physical travel and work continue using physical energy.

**Reason:** This implements the Phase 4 separation law while preserving the existing energy API and RNG sequence. New agents initialize both energies from the same existing draw, then causal activity makes them diverge.

**Compatibility:** SQLite schema version 5 persists social energy. Version 1–4 worlds default it to their stored physical energy and migrate on save. Split-run, save/load, and seeded determinism remain tested.

**Affected:** `src/playing_god/core/agent.py`, `src/playing_god/core/decision.py`, `src/playing_god/core/exposure.py`, `src/playing_god/core/mobility.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`

## 2026-08-22 — Keep the spatial debug map read-only

**Area:** visualization, spatial-mobility

**Decision:** Render fixed location coordinates, roads, deterministic NPC offsets, optional route highlighting, and day labels from existing world state. The renderer accepts data and returns a Matplotlib axis; only the CLI calls `show()`.

**Reason:** This satisfies Phase 4 path-debugging requirements without placing frame state, interpolation, plotting dependencies, or mutation inside the simulation loop.

**Rejected:** Browser UI, 3D/game rendering, continuous animation, procedural layout, and renderer-owned position state.

**Affected:** `src/playing_god/visualization/spatial_map.py`, `scripts/show_spatial_map.py`, `tests/test_spatial_visualization.py`

## 2026-08-22 — Separate received evidence from current belief

**Area:** perception-belief, social, persistence

**Decision:** A successful interaction gives each participant an append-only `agent_location` observation about the other participant. A deterministic perception step converts observation reliability and attention into confidence, then replaces the current belief value while retaining an evidence count. World truth never refreshes beliefs directly.

**Reason:** A location belief provides the smallest concrete proof of the Phase 5 boundary: an NPC can directly learn where someone was, that person can move, and the NPC's belief remains stale until new evidence arrives. The generic observation/perception/belief records support later information types without requiring an LLM or changing RNG order.

**Deferred:** Random perceptual error, misinformation, social testimony, decision consumption, prayer, intervention, and faith attribution. Direct successful interaction currently has reliability and attention `1.0`; imperfection first appears as incomplete and stale information rather than fabricated error.

**Compatibility:** SQLite schema version 6 stores append-only observations and replaceable current beliefs. Version 1–5 worlds load with empty perception state and migrate on save. Seeded, split-run, save/load, and archived Phase-1 contracts remain intact.

**Affected:** `src/playing_god/core/perception.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_perception.py`, `tests/test_persistence.py`

## 2026-08-22 — Route visits by believed location

**Area:** perception-belief, spatial-mobility, social

**Decision:** Relationship-driven visits select only strong ties for whom the actor has a positive-confidence `agent_location` belief pointing to a valid map location. Travel uses that belief value, never the target NPC's live `current_location`.

**Reason:** This makes the perception boundary causally meaningful with the smallest existing decision path. A current belief can produce a meeting, a stale belief can produce a failed rendezvous, and absent knowledge cannot grant omniscient tracking.

**Fallback:** Missing, zero-confidence, or invalid location beliefs leave the ordinary cafe destination unchanged. Relationship thresholds, Dijkstra routing, travel logging, and RNG order remain unchanged.

**Affected:** `src/playing_god/core/world.py`, `tests/test_mobility.py`

## 2026-08-22 — Use phase-based names for active research documents

**Area:** research-docs, coding-agent-memory

**Decision:** `docs/ROADMAP.md` is the canonical phase sequence, `docs/STATUS.md` states current progress, and active detailed briefs use `docs/phases/phase-XX-*.md`. Superseded versioned vision documents live under `docs/archive/`.

**Reason:** Historical document versions such as 0.2.3 and 0.2.4 had phase numbers that no longer matched the canonical roadmap. Stable role- and phase-based names let humans and agents identify current authority without translating version history.

**Compatibility:** Historical content remains available in the archive. Phase 5's detailed brief now defines 5A–5E directly; no runtime code or simulation behavior depends on these documentation paths.

**Affected:** `AGENTS.md`, `README.md`, `docs/ROADMAP.md`, `docs/STATUS.md`, `docs/PROJECT_MAP.md`, `docs/phases/`, `docs/archive/`, `.agent/memory/CURRENT.md`

## 2026-08-22 — Preserve consciousness work as gated Phase 10 research

**Area:** research-docs, coding-agent-memory

**Decision:** Keep the functional-consciousness architecture, candidate experiments, ablations, ethical limits, and scientific non-claims in `docs/research/phase-10-functional-consciousness.md`. Its status is `RESEARCH — HUMAN REVIEW REQUIRED`; it is not an active phase brief and does not authorize implementation.

**Reason:** The research gives future Phase 10 a concrete computer-engineering direction, but implementing it during Phase 5 would skip required social, developmental, discovery, and experimental foundations. Separating research from `docs/phases/` lets coding agents preserve the vision without mistaking it for the next task.

**Boundary:** The current milestone remains Phase 5B. Do not introduce ML/RL frameworks, world-model infrastructure, emotion labels, or consciousness mechanisms from the Phase 10 research unless a human-approved experiment passes the roadmap gate and `docs/STATUS.md` advances the project.

**Affected:** `AGENTS.md`, `docs/ROADMAP.md`, `docs/PROJECT_MAP.md`, `docs/research/phase-10-functional-consciousness.md`

## 2026-08-23 — Make prayer an ordinary seeded action with no guaranteed response

**Area:** core-simulation, spatial-mobility, shrine-prayer, persistence

**Decision:** Add a connected shrine to the fixed map and let `pray` participate in the existing seeded weighted action choice. Prayer utility and intensity use only current stress, goal blockage, physical energy, and prior prayer count. A structured prayer and matching causal event are created only after the NPC reaches the shrine.

**Reason:** This implements the smallest inspectable need → travel → prayer chain without inventing faith, emotion flags, supernatural causation, or a second decision engine. Prayer itself consumes no random draws and guarantees no intervention or outcome.

**Compatibility:** SQLite schema version 7 stores append-only prayer history. Version 1–6 worlds load with empty prayer state and migrate on save. Current seeded, split-run, save/load, and archived Phase-1 contracts remain intact.

**Affected:** `src/playing_god/core/prayer.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/decision.py`, `src/playing_god/core/mobility.py`, `src/playing_god/core/spatial.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_prayer.py`, `tests/test_persistence.py`, `tests/test_mobility.py`, `tests/test_spatial.py`

## 2026-08-23 — Model intervention as a fallible world stimulus

**Area:** indirect-intervention, perception-belief, core-simulation, persistence

**Decision:** Represent dreams, signs, and opportunities as immutable target-specific conditions with strength, theme, suggested action, creation/expiry days, and optional location. Dreams are eligible without location; signs and opportunities require the target to reach their location. Existing traits and stress deterministically classify the response as missed, ignored, aligned, or misinterpreted.

**Reason:** The player changes an information condition, not agent state or a decision. Noticed stimuli pass through ordinary observation/perception with no divine source. An interpreted stimulus only supplies a bounded temporary score adjustment to the existing seeded chooser, so the selected action and its outcome remain autonomous and uncertain.

**Compatibility:** Intervention resolution consumes no world RNG. SQLite schema version 8 stores append-only interventions and responses; version 1–7 worlds load with empty intervention state. Active-intervention continuation matches uninterrupted execution.

**Deferred:** Faith attribution, claims of supernatural causation, intervention resources, multi-target propagation, and formal baseline/counterfactual comparison.

**Affected:** `src/playing_god/core/intervention.py`, `src/playing_god/core/world.py`, `src/playing_god/core/decision.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_intervention.py`, `tests/test_persistence.py`, `tests/test_reproducibility.py`

## 2026-08-23 — Treat faith as revisable attribution, not causal truth

**Area:** faith-attribution, shrine-prayer, indirect-intervention, persistence

**Decision:** Store one bounded faith value per NPC and derive skepticism as `1 - faith`. After each day, classify only significant supported outcome events and append an attribution to miracle, coincidence, personal effort, social help, institutional cause, manipulation, or unknown. Cause selection uses prior faith, existing traits, a recent matching prayer, a remembered interpreted intervention response, explicit cause evidence, and event significance.

**Reason:** This supplies an inspectable prayer → stimulus → outcome → interpretation → belief-update chain while preserving the distinction between NPC inference and simulation truth. Explicit social or institutional causes cannot be silently relabeled as miracles. Attribution and faith updates consume no RNG draws or LLM output.

**Memory boundary:** A perceived response can support attribution for 30 simulated days even after its stimulus expires; expiry governs future exposure and action influence, not erasure of received evidence. Faith only feeds back modestly into normal prayer utility at this stage.

**Compatibility:** SQLite schema version 9 stores current faith and append-only exact-event attribution history. Version 1–8 worlds load with neutral faith and empty attribution state. Seeded, split-run, repeated-save, and save/load behavior remain reproducible.

**Deferred:** Social testimony and propagation, doctrine or religious institutions, intervention resources, and formal baseline/counterfactual comparison.

**Affected:** `src/playing_god/core/faith.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/prayer.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_faith.py`, `tests/test_persistence.py`, `tests/test_reproducibility.py`

## 2026-08-23 — Compare interventions as isolated same-seed worlds

**Area:** counterfactual-comparison, reproducibility, thesis-methodology

**Decision:** Build baseline and intervention branches as separate fresh `World` instances with identical seed, population, and duration. Apply an immutable intervention schedule only to the intervention branch, advance both one day at a time, and compare immutable final agent snapshots plus the first day and event where trajectories differ.

**Reason:** This satisfies the Phase 5 research bridge without coupling experiments to SQLite, copying mutable world internals, or reducing comparison to event counts. The returned worlds preserve complete histories for inspection, while structured differences expose resources, career, state, geography, relationships, beliefs, prayer, faith attribution, actions, and causal events.

**Scientific boundary:** The paired worlds hold random initialization constant and are exactly reproducible. They use the existing single world RNG stream, so once an intervention changes behavior, branch-specific code paths may consume later draws differently. Results are total deterministic model divergence, not a per-event common-random-number treatment estimate and never proof of supernatural causation.

**Rejected:** Database cloning as experiment state, a generic recursive dictionary diff, event-count-only comparison, and an RNG-kernel migration inside Phase 5.

**Affected:** `src/playing_god/core/counterfactual.py`, `scripts/compare_counterfactual.py`, `tests/test_counterfactual.py`, `docs/phases/phase-05-belief-intervention.md`

## 2026-08-31 — Keep adaptive learning subordinate to valid action selection

**Area:** core-simulation, adaptive-cognition, reproducibility

**Decision:** `decision.choose()` accepts action-keyed learned preferences only after deriving the candidate set from existing deterministic scores and eligibility sentinels. Transient intervention adjustments use the same valid-only boundary. Both may change relative weighted preference, but neither may make an unavailable action selectable.

**Reason:** Phase 7 learning should adapt choice among possibilities the world already permits, not become a second source of physical, economic, social, or institutional truth. A narrow additive seam preserves the existing seeded chooser and lets 7.0.1 add one learner without redesigning the decision engine.

**Deferred:** Context representation, consequence feedback, online updates, learned state on `Agent`, and persistence all remain in milestones 7.0.1–7.0.2.

**Affected:** `src/playing_god/core/decision.py`, `tests/test_decision.py`, `docs/phases/phase-07-development-generations.md`

## 2026-09-01 — Learn action values within the NPC's current goal

**Area:** adaptive-cognition, core-simulation, reproducibility

**Decision:** Use the existing five-value current goal as the contextual learner's state. For each `(goal, action)`, retain observation count, running mean goal-relevant feedback, and running means of the separate money, skill, energy, social-energy, stress, reputation, relationship, employment, and job-level consequences. Convert mean feedback into an additive decision adjustment capped at `0.75`.

**Reason:** The goal already summarizes the NPC's most pressing employment, resource, skill, or social condition. It provides contextual adaptation without a large bucket taxonomy. Keeping raw consequence dimensions inspectable avoids treating all life outcomes as one happiness score, while a goal-specific projection supplies the scalar preference required by the existing seeded chooser.

**Compatibility:** Learning consumes no RNG and is explicitly enabled with `World(adaptive_cognition=True)`. Default worlds remain non-adaptive, preserving Phase 1–6 behavior. Schema-v12 persistence is recorded in the later adaptive-persistence decision.

**Affected:** `src/playing_god/core/adaptive.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/world.py`, `tests/test_adaptive.py`

## 2026-09-01 — Persist adaptive values as agent-owned JSON

**Area:** adaptive-cognition, persistence, reproducibility

**Decision:** SQLite schema v12 adds one checked `adaptive_cognition` flag to `world_state` and one `adaptive_values_json` field to each agent. The JSON contains only the nested `(goal, action)` observation count, mean feedback, and mean multidimensional consequence already owned by the agent.

**Reason:** The table is small, variable, agent-owned state similar to existing action/trait JSON. A separate relational policy subsystem would add joins, tables, and synchronization without a current query requirement. Strict load validation preserves inspectability and rejects unknown contexts/actions, invalid counts, non-finite components, and out-of-range feedback.

**Compatibility:** Schema-v11 and older worlds load with adaptation disabled and empty learned values, preserving RNG state and never fabricating experience. Saving migrates them to v12. Adaptive save/reload continuation exactly matches an uninterrupted run.

**Affected:** `src/playing_god/persistence/sqlite_store.py`, `tests/test_persistence.py`, `docs/phases/phase-07-development-generations.md`

## 2026-09-01 — Defer delayed-credit learning at the Phase 7.0 gate

**Area:** adaptive-cognition, development, anti-overengineering

**Decision:** Do not add Q-learning in Phase 7.0. Successful training already produces immediate positive skill progress in the `improve_skill` context, even though it also reduces money and energy and increases stress. The contextual learner can therefore reinforce training from a real one-step developmental consequence.

**Reason:** Later employability and income are downstream benefits, but they are not the only signal. The current model directly changes capability during training, and institutional denial correctly produces no capability feedback. No approved Phase 7 behavior currently lacks a meaningful immediate progress signal, so a multi-step value learner would add state/action-transition machinery without solving a demonstrated failure.

**Revisit gate:** Add delayed-credit learning only when a controlled approved behavior has a necessary benefit that appears only in a future context and the contextual action-value learner demonstrably cannot represent it.

**Affected:** `src/playing_god/core/adaptive.py`, `src/playing_god/core/world.py`, `tests/test_adaptive.py`, `docs/phases/phase-07-development-generations.md`

## 2026-09-01 — Derive G0 starting state from three founder records

**Area:** founder-prehistory, core-simulation, persistence, reproducibility

**Decision:** Generate exactly three structured records per new G0 adult: capability exposure, livelihood entry, and recent material conditions. Reduce their effects into starting skill, employment/job level/salary, money, energy/social energy, stress, and reputation. Keep traits and sins as priors and age as a demographic. Do not warm-start adaptive values without prior action/outcome evidence.

**Reason:** This is the smallest causal history that explains important state already used by the current model without simulating childhoods, inventing prose biography, or adding RNG draws. Retaining the prior draw order preserves verified trajectories while making their initialization inspectable.

**Compatibility:** SQLite schema v13 persists founder history as agent-owned checked JSON. Schema-v12 and older worlds load empty and migrate on save without reconstructing a history or consuming RNG.

**Affected:** `src/playing_god/core/prehistory.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_prehistory.py`, `tests/test_persistence.py`, `docs/phases/phase-07-development-generations.md`

## 2026-09-02 — Keep first reproduction abstract, constrained, and opt-in

**Area:** family-reproduction, core-simulation, persistence, reproducibility

**Decision:** Add opt-in daily reproduction for unordered pairs of nondependent co-located adults. Eligibility is a structured result derived from age, mutual affinity/trust/familiarity, combined resources, employment, stress, close-family exclusion, a one-year parent cooldown, and a fixed population ceiling. Only eligible pairs consume the 1% seeded attempt roll. A success creates a dependent child with explicit parents/guardians, birth context, reciprocal genealogy, and parent-mean traits/sins with ±0.08 variation.

**Reason:** This is the smallest mechanism that creates G1 from current world history rather than arbitrary adult initialization. Opt-in execution preserves Phase 1–7A default RNG allocation, while dependency prevents Phase 7B from inventing child cognition or adult behavior before Phase 7C.

**Inheritance boundary:** Do not copy parent memories, observations, beliefs, learned values, occupation, reputation, grudges, adult skill, or founder prehistory. The birth context records the environment; it does not precompute the child's life outcome.

**Compatibility:** SQLite schema v14 stores the reproduction flag and checked agent-owned family JSON. Schema-v13 and older worlds load disabled with empty founder family state, preserve RNG state, and migrate without fabricated genealogy. Reciprocal parent/child links are validated on save and load.

**Affected:** `src/playing_god/core/family.py`, `src/playing_god/core/agent.py`, `src/playing_god/core/world.py`, `src/playing_god/persistence/sqlite_store.py`, `tests/test_family.py`, `tests/test_persistence.py`, `docs/phases/phase-07-development-generations.md`
