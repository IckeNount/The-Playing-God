# Playing God Project Map

Use this map to find the owning subsystem before opening source. It describes the repository as it exists now; planned phases are listed separately and are not implemented claims.

## Dependency direction

```text
scripts
  -> persistence
       -> core world + agent + events + perception + RNG + social graph
  -> counterfactual comparison
       -> two isolated core worlds
  -> visualization
       -> social graph

core world
  -> agent + founder prehistory + family/reproduction + development + lifecycle + culture + decision + adaptive cognition + events + RNG + social graph + mobility + spatial map + intervention + faith + economy + institution + information + collective action
  -> perception / belief

exposure
  -> agent spatial state
  -> daily interaction opportunities in core world
```

Simulation code must not depend on `.agent/`, memory documents, or coding-agent tooling.

## `core-simulation` — agents, decisions, and world evolution

**Owns:** deterministic population creation, mutable agent state, goals, action selection and effects, daily progression, event recording, aging, and text reports.

**Entry points:**

- `src/playing_god/core/world.py` — `World`, including `run()`, `act()`, and `report()`.
- `src/playing_god/core/agent.py` — `Agent`, stable trait/sin keys, normalization.
- `src/playing_god/core/decision.py` — action scores, valid-candidate filtering, transient adjustments, the learned-preference boundary, and seeded weighted selection.
- `src/playing_god/core/events.py` — structured per-agent `Event`.
- `src/playing_god/core/prayer.py` — structured prayer records and deterministic prayer need/intensity derivation.
- `src/playing_god/core/rng.py` — RNG construction and persistence-safe state serialization.

**Focused tests:** `tests/test_decision.py`, `tests/test_reproducibility.py`, `tests/test_prayer.py`.

**Important boundary:** All causal randomness must use the world's seeded RNG. Avoid global randomness and changes to RNG call order unless the resulting determinism migration is intentional and tested. Decision modifiers, including learned preferences, are applied only after the base-valid candidate set is fixed; they may rank actions but cannot create eligibility or resolve consequences.

## `adaptive-cognition` — goal-context online action learning

**Owns:** compact goal context, before/after action-state capture, multidimensional consequence records, goal-relevant feedback, running mean action values, and bounded learned preference adjustments.

**Entry points:**

- `src/playing_god/core/adaptive.py` — learning context, consequence, update, and preference functions.
- `src/playing_god/core/agent.py` — per-agent in-memory `adaptive_values` table.
- `src/playing_god/core/world.py` — opt-in online capture/update around normal action execution.

**Focused tests:** `tests/test_adaptive.py`, `tests/test_decision.py`.

**Important boundary:** The current goal is the only learning context; base scores still handle immediate energy, stress, trait, and world-state detail. Consequences remain inspectable by dimension even though the current goal selects one bounded feedback projection. Learning consumes no RNG and is opt-in through `World(adaptive_cognition=True)`. Schema v12 persists the opt-in setting and exact running statistics; earlier worlds begin empty and disabled. Phase 7.0.3 defers Q-learning because current costly training already provides immediate skill-progress feedback.

## `founder-prehistory` — compact G0 causal initialization

**Owns:** three seeded structured prior-life records for each newly generated founder and reduction of their effects into important starting capability, livelihood, resources, and recent wellbeing.

**Entry points:**

- `src/playing_god/core/prehistory.py` — founder event generation, strict structure validation, and starting-state reduction.
- `src/playing_god/core/agent.py` — per-agent `founder_prehistory` history.
- `src/playing_god/core/world.py` — G0 generation from the compact records.

**Focused tests:** `tests/test_prehistory.py`, plus persistence and deterministic regression coverage.

**Important boundary:** Traits and sins remain initialized priors, not invented life events. New founders receive exactly three records without extra RNG draws or a full childhood simulation. No adaptive values are warm-started because the compact history does not yet contain action/outcome observations sufficient to derive them. Schema v13 persists the records; schema-v12 and older agents remain empty rather than receiving reconstructed histories.

## `family-reproduction` — constrained later-generation creation

**Owns:** opt-in adult-pair eligibility, seeded reproduction attempts, explicit genealogy and guardianship, birth environment context, bounded prior inheritance, and dependent-child creation.

**Entry points:**

- `src/playing_god/core/family.py` — eligibility thresholds/reasons, family and birth records, bounded prior inheritance, and family-link validation.
- `src/playing_god/core/agent.py` — per-agent `family` state.
- `src/playing_god/core/world.py` — opt-in daily attempts, child creation, family/social links, and dependency enforcement.

**Focused tests:** `tests/test_family.py`, plus persistence and split-run coverage.

**Important boundary:** Reproduction is abstract and enabled only with `World(reproduction_enabled=True)`. Eligibility requires two nondependent co-located adults with sufficient mutual affinity/trust/familiarity, resources, employment stability, acceptable stress, no close genealogical relationship, no recent child, and remaining population capacity. A successful 1% seeded daily attempt creates one dependent child with parent/guardian links and ±0.08 bounded variation around parent priors. It never copies memories, learned values, occupation, reputation, beliefs, or adult capability.

## `child-development` — annual causal development

**Owns:** exact birth-anniversary aging, age stages, inspectable upbringing and
school-exposure records, developed skill, adaptive training experience, and the
age-18 dependency boundary.

**Entry points:**

- `src/playing_god/core/development.py` — annual developmental inputs, outcomes,
  stages, and strict history validation.
- `src/playing_god/core/agent.py` — per-agent `development` history.
- `src/playing_god/core/world.py` — anniversary resolution, adaptive-policy
  integration, and adulthood activation.

**Focused tests:** `tests/test_development.py`, plus persistence and
reproducibility coverage.

**Important boundary:** Children do not run the adult daily action loop.
Development is one deterministic checkpoint per birth anniversary. Ages 6–17
can access the existing school only when current household resources,
employment, guardian stress, and guardian relationship support produce enough
opportunity. Skill requires aptitude plus access, practice, opportunity, and
feedback. Schema v15 persists exact history; older schemas remain empty rather
than receiving reconstructed childhood.

## `household-lifecycle` — support, turnover, and inheritance

**Owns:** annual dependent support, living-population inspection, retirement,
seeded age/stress mortality, inactive-but-retained deceased agents, estate
closure, and descendant inheritance receipts.

**Entry points:**

- `src/playing_god/core/lifecycle.py` — lifecycle records, household snapshots,
  mortality rule, parsing, and cross-agent validation.
- `src/playing_god/core/agent.py` — per-agent `lifecycle` state.
- `src/playing_god/core/world.py` — support deductions, anniversary transitions,
  retirement/death consequences, estate distribution, and active-agent filters.

**Focused tests:** `tests/test_lifecycle.py`, plus persistence, economy,
counterfactual, family, development, and reproducibility coverage.

**Important boundary:** Lifecycle defaults on for new reproduction-enabled
worlds but remains separately configurable; default and schema-v15 worlds stay
disabled. Support is one 48-unit annual summary, retirement occurs at 65, and
one world-RNG mortality check occurs per birthday from 70 with guaranteed exit
at 90. Positive estates go only to living direct children; debt does not
transfer. Deceased agents remain as immutable causal history but cannot act or
participate in current society. The 100-agent limit counts living agents and is
an engineering guardrail, not the primary demographic law.

## `cultural-transmission` — explicit social inheritance

**Owns:** one bounded cultural-norm representation, self-originated claims,
relationship-weighted accept/modify/reject responses, append-only exposure
records, school cultural exposure, and contact-bound norm relay.

**Entry points:**

- `src/playing_god/core/culture.py` — cultural values, information identity,
  deterministic response rule, persisted records, and causal-link validation.
- `src/playing_god/core/agent.py` — per-agent cultural transmission history.
- `src/playing_god/core/world.py` — explicit norm expression, annual guardian
  and school exposure, social-contact transmission, and belief updates.

**Focused tests:** `tests/test_culture.py`, plus information, development,
persistence, counterfactual, and split-run coverage.

**Important boundary:** Culture is not copied at birth and never copies adaptive
policy. A recipient must receive a guardian-anniversary, school-access, or
successful-interaction exposure. The raw claim remains an observation even when
the recipient rejects it; accepted or modified interpretations alone update the
existing belief state. The model has three abstract stances and one concrete
school norm, not a generic ideology engine. Transmission consumes no world RNG.

## `civilization-layer` — bounded runtime possibility records

**Owns:** engine-defined base primitives, first-hand primitive exposure,
bounded problem pressure and discovery eligibility, canonical candidate
composition, costly seeded attempts, validated-knowledge identity, per-agent
knowledge provenance and causal diffusion, knowledge-backed affordance
definitions, peer-training eligibility/execution, bounded effect validation,
Phase 8 snapshots and research metrics, and cross-record integrity.

**Entry points:**

- `src/playing_god/core/civilization.py` — immutable primitive definitions,
  structured civilization/discovery state, deterministic pressure and
  eligibility rules, the peer-training candidate/validator, seeded-score
  construction, deterministic knowledge responses and selection,
  canonical affordance activation, peer-training eligibility,
  lookup/signatures, JSON parsing, and integrity validation.
- `src/playing_god/core/agent.py` — per-agent knowledge, primitive exposure,
  and problem-pressure state.
- `src/playing_god/core/world.py` — training-outcome integration, explicit
  discovery-attempt resolution/costs, social, guardian, and adopted-school
  knowledge exposure, peer-training target selection and action-time
  execution, school-observed evidence, mutable civilization state, and
  read-only eligibility/primitive access.
- `src/playing_god/core/decision.py` — includes peer training only when the
  world supplies an eligible affordance utility; learned preferences may rank
  but cannot create availability.
- `src/playing_god/core/counterfactual.py` — immutable agent snapshots include
  local discovery/knowledge history; the Phase 8 snapshot also includes the
  world registry and durable school adoption state.
- `src/playing_god/core/civilization_metrics.py` — read-only recognition,
  attempt, validation, exposure, adoption, first-use, institution, current
  opportunity, and skill-delta metrics.

**Focused tests:** `tests/test_civilization.py`,
`tests/test_problem_pressure.py`, `tests/test_discovery.py`,
`tests/test_knowledge_diffusion.py`, `tests/test_peer_training.py`,
`tests/test_institutional_adoption.py`, `tests/test_phase8_exit.py`, plus
persistence, decision, adaptive-learning, institution, culture, exposure, and
counterfactual coverage.

**Important boundary:** Schema v18 persists mutable knowledge and affordance
state but rebuilds the three engine-owned peer-training primitives from code.
At Phase 8A the registry was not connected to action selection or execution.
Knowledge origins use existing persisted event indices, and that subphase
accepted only the direct-discovery agent route. Schema v19 adds bounded
per-agent primitive
exposure and training-access pressure linked to existing admission/denial event
indices. Recognition and read-only eligibility create no candidate, attempt,
knowledge, affordance, diffusion, action use, or institutional adoption.
Schema v20 adds resolved per-agent attempts. An explicit eligible call pays the
experiment cost before validation; only structurally valid candidates consume
the existing world RNG. Success creates validated world knowledge and a direct
discoverer record. Phase 8D reuses successful social interactions and annual
guardian development as the only current diffusion routes. The source must
have adopted the validated entry on an earlier day; relationship-weighted
accept/modify/reject responses consume no RNG, rejected exposure grants no
knowledge, and modified variants retain the original knowledge ID and bounded
registry effects. School diffusion was unavailable before institutional
adoption in 8F.
Phase 8E materializes exactly one canonical affordance when peer-training
knowledge validates. An adopter can offer it only to a co-located, mutually
familiar, lower-skill adult when both participants can pay the stored energy
costs. The ordinary chooser ranks the action; execution revalidates every
precondition, gives the learner a fixed `0.006` skill gain versus formal
training's minimum `0.009`, consumes no money or school capacity, and records
the teacher's exact knowledge-parent reference. Schema v21 upgrades prior
schema-v20 peer-training knowledge with this derivable canonical affordance.
Phase 8F adds one school-only institutionalization route. Three successful
peer-training uses observed at school on distinct days create one adoption
record linked to the evidence events and original discovery attempt. Schema
v22 persists that state; from the adoption day onward, existing annual school
access may expose later agents to the procedure. No generic institution or
policy framework is introduced.
Phase 8G adds no causal or persistent state. Its bounded seed-1 fixture forks
after two real training denials: a third denial enables day-5 validation,
day-6 social exposure creates a second adopter, and day-7 peer training adds
`0.006` learner skill; the same-prior formal-access branch has none of those
states or opportunities. Metrics scan authoritative records only on explicit
request and consume no RNG. No benchmark harness existed, so none was added.

## `artificial-history` — episodes and explicit causal traces

**Owns:** read-only flattening of authoritative per-agent events, stable source
references, bounded participant/causal association, deterministic episode
identity and ordering, transparent magnitude, and preservation of existing
causal references; query-time forward/reverse causal indexes; and bounded,
branch-preserving ancestor/descendant traces with visible gaps and corruption.

**Entry points:**

- `src/playing_god/core/history.py` — `HistoricalEpisode`, source and causal
  references, source resolution, and bounded episode extraction.
- `src/playing_god/core/causal_history.py` — authoritative event references,
  typed causal evidence derivation, `CausalTrace`, and deterministic ancestor
  and descendant traversal.

**Focused tests:** `tests/test_history.py`, `tests/test_causal_history.py`, plus
the Phase 8 discovery, knowledge, institutional and persistence proofs used by
explicit-reference and reload coverage.

**Important boundary:** Episodes are query-time projections, not events or
world state. The module is not imported by simulation execution, consumes no
RNG, stores no duplicate event payload, and does not infer causality from
participant overlap or chronology. `episode-v1` limits association to a
three-day adjacent gap, seven-day total duration and twelve events. Schema
remains v22. `causal-trace-v1` uses only explicit structured evidence, derives
its reverse index per query, defaults to depth 32 and 256 nodes, exposes every
limit boundary, and reports unresolved or cyclic records without inventing or
repairing history.

## `social` — relationships and contact

**Owns:** directed multidimensional relationships, social-event effects, co-location exposure detection, and probabilistic interaction resolution.

**Entry points:**

- `src/playing_god/core/social.py` — `SocialGraph` and social event effects.
- `src/playing_god/core/exposure.py` — `Exposure`, `Interaction`, detection, and resolution.
- `src/playing_god/visualization/social_graph.py` — optional NetworkX graph inspection.
- `scripts/show_social_graph.py` — manual visualization entry point; accepts a persisted-world database path and loads it through `load_world()`.

**Focused tests:** `tests/test_social.py`, `tests/test_exposure.py`.

**Important boundary:** `Agent.relationships` remains the legacy signed affinity used by current decisions. `SocialGraph` adds dimensions and is rebuilt from agents; changing one representation does not automatically make the other the source of truth.

## `shared-economy` — finite employment opportunity and macro inspection

**Owns:** deterministic initial job capacity, derived occupancy/vacancies, vacancy-constrained hiring, causal job-hunt traces, and read-only aggregate economic snapshots.

**Entry points:**

- `src/playing_god/core/economy.py` — `EconomyState`, `EconomySnapshot`, capacity derivation, and aggregate metrics.
- `src/playing_god/core/world.py` — job-hunt integration and `economic_snapshot()`.

**Focused tests:** `tests/test_economy.py`, plus persistence and split-run checks.

**Important boundary:** `job_capacity` is shared causal state; occupied jobs are derived from authoritative `Agent.employed` values and are never persisted separately. Metrics are read-only and consume no RNG.

## `school-institution` — capacity-limited training access

**Owns:** the fixed school location/rule, one daily training slot, seeded
first-attempt admission, daily reset, admission/denial traces, read-only rule
inspection, and one evidence-gated peer-training adoption.

**Entry points:**

- `src/playing_god/core/institution.py` — `SchoolState`, its read-only snapshot,
  bounded adoption evidence/state, serialization, and causal validation.
- `src/playing_god/core/world.py` — school-location eligibility, capacity
  checks, adoption transition, annual institutional exposure, and
  `school_snapshot()`.

**Focused tests:** `tests/test_institution.py`,
`tests/test_institutional_adoption.py`, plus split/restart coverage in
`tests/test_persistence.py`.

**Important boundary:** School capacity remains a fixed model rule; same-day
usage is transient and resets at the next simulated day. Schema v22 stores only
the school's durable peer-training evidence and adoption. Adoption changes no
past denial or development record and creates no generic institution framework.

## `information-diffusion` — contact-bound structured testimony

**Owns:** structured employment claims, deterministic relevance and trust limits, stable evidence/origin identity, bounded hop decay, loop protection, and read-only diffusion metrics.

**Entry points:**

- `src/playing_god/core/information.py` — `InformationItem`, `DiffusionSnapshot`, testimony selection, identity, decay, deduplication inputs, and aggregate metrics.
- `src/playing_god/core/world.py` — firsthand employment observations, testimony integration, transient evidence indexes, and `diffusion_snapshot()`.
- Information identity, origin day/agent, and hop count live on `Observation` in `src/playing_god/core/perception.py`.

**Focused tests:** `tests/test_information.py`, plus persistence and split-run coverage.

**Important boundary:** Information moves only through successful co-located interactions. World truth, source belief, transmitted claim, and recipient belief remain distinct. Relays consume no world RNG, confidence cannot increase through pure repetition, and transient indexes are rebuilt from persisted observations.

## `collective-action` — derived participation and local cascades

**Owns:** deterministic participation pressure, ordinary threshold-gated action selection, park movement, contact-bound participation evidence, trust-weighted social confirmation, collective metrics, and per-participant causal traces.

**Entry points:**

- `src/playing_god/core/collective.py` — pressure components, participation evidence identity/relevance, `CollectiveSnapshot`, `ParticipationTrace`, cascade-depth derivation, and causal inspection.
- `src/playing_god/core/decision.py` — eligible participation enters the ordinary seeded weighted action choice.
- `src/playing_god/core/world.py` — park participation effects, encounter-bound evidence creation, `collective_snapshot()`, and `participation_trace()`.

**Focused tests:** `tests/test_collective.py`, plus persistence and split-run coverage.

**Important boundary:** Participation is derived from current pressure, risk, social state, and received evidence; it is never a permanent activist trait or centrally scheduled outcome. Participation becomes known only through successful local interaction, each NPC still crosses its own threshold and selects its own action, and evidence relevance is bounded to seven days. Decision-time evidence and influencer IDs are frozen in the existing persisted participation event, so later trust changes cannot rewrite historical traces or cascade depth; all metrics remain read-only derivations.

## `spatial-mobility` — places, routes, and travel

**Owns:** location/road models, shortest-time routing, destination selection, travel state changes, and travel-event payloads.

**Entry points:**

- `src/playing_god/core/spatial.py` — `Location`, `Road`, and `WorldMap`.
- `src/playing_god/core/mobility.py` — destination choice, travel, and event data.
- `src/playing_god/visualization/spatial_map.py` — read-only fixed-map, NPC-position, and route renderer.
- `scripts/show_spatial_map.py` — persisted-world spatial visualization entry point.
- Agent location fields live in `src/playing_god/core/agent.py`.

**Focused tests:** `tests/test_spatial.py`, `tests/test_mobility.py`, `tests/test_exposure.py`, `tests/test_spatial_visualization.py`.

**Current state:** The full movement → exposure → interaction → relationship → visit movement loop participates in `World.run()`. Visits route to the actor's believed target location, so stale information can cause a failed rendezvous. The fixed map now also includes a shrine reached through ordinary routing. Successful encounters retain who/where context, physical/social energy are separate, and the optional renderer inspects locations, roads, NPC positions, and supplied routes without mutating the world.

## `shrine-prayer` — structured requests without guaranteed response

**Owns:** deterministic prayer utility, goal-derived desire classification, prayer intensity, shrine-only prayer completion, and append-only prayer history.

**Entry points:**

- `src/playing_god/core/prayer.py` — `Prayer`, goal blockage, habit, need, and record construction.
- `src/playing_god/core/decision.py` — prayer participates in the normal seeded action choice.
- `src/playing_god/core/world.py` — successful shrine prayer records a prayer and causal event.

**Focused tests:** `tests/test_prayer.py`, plus persistence and reproducibility checks.

**Important boundary:** Prayer expresses an NPC's structured desire. It does not prove a god exists, update faith, or guarantee intervention or outcomes.

## `indirect-intervention` — fallible external stimuli

**Owns:** structured time-bounded interventions, reachability, deterministic attention/interpretation, response history, and temporary action-score adjustments.

**Entry points:**

- `src/playing_god/core/intervention.py` — `Intervention`, `InterventionResponse`, attention, confidence, and response classification.
- `src/playing_god/core/world.py` — intervention creation, spatial/dream resolution, causal observation/event recording, and active score adjustments.
- `src/playing_god/core/decision.py` — applies supplied score adjustments inside the normal seeded weighted choice.

**Focused tests:** `tests/test_intervention.py`, plus persistence and reproducibility checks.

**Important boundary:** An intervention creates a stimulus, not a command. It may expire unseen, fail to produce perception or intention, or reinforce a different action through misinterpretation. It never directly changes success, relationships, faith, or causal truth.

## `faith-attribution` — uncertain interpretation of outcomes

**Owns:** the bounded faith/skepticism continuum, significant-outcome classification, recent prayer/response association, deterministic causal attribution, modest faith updates, and append-only attribution history.

**Entry points:**

- `src/playing_god/core/faith.py` — `Outcome`, `Attribution`, outcome classification, evidence matching, cause selection, and faith updates.
- `src/playing_god/core/world.py` — daily attribution resolution and causal attribution events.
- Per-agent faith and attribution history live in `src/playing_god/core/agent.py`.
- `src/playing_god/core/prayer.py` — current faith modestly affects future prayer utility.

**Focused tests:** `tests/test_faith.py`, plus persistence and reproducibility checks.

**Important boundary:** Attribution records what an NPC inferred; it does not establish world causation or prove a player exists. Explicit social and institutional causes remain available, and attribution consumes no random draws or LLM output.

## `perception-belief` — received evidence and agent knowledge

**Owns:** append-only observations, deterministic perception, and each agent's current revisable beliefs.

**Entry points:**

- `src/playing_god/core/perception.py` — `Observation`, `Perception`, `Belief`, and deterministic belief updating.
- Per-agent observation history and belief state live in `src/playing_god/core/agent.py`.
- Successful-interaction observations are produced in `src/playing_god/core/world.py`.

**Focused tests:** `tests/test_perception.py`, plus persistence and split-run checks.

**Important boundary:** World state remains causal truth. Observations contain only information that reached an NPC, perceptions interpret that evidence, and beliefs may remain stale after truth changes. Relationship-driven visits are the first decision path to consume belief state; missing or unusable location beliefs fall back to ordinary social travel.

## `persistence` — durable world state

**Owns:** SQLite schema/versioning, save/load, schema migration, validation, RNG continuation, agent state, founder prehistory, reproduction configuration/family state, development/lifecycle/cultural/knowledge history, adaptive-cognition setting/action values, shared job capacity, civilization state, relationship dimensions, immutable event/observation/prayer/intervention/attribution history, information origin/hop identity, and current beliefs.

**Entry points:**

- `src/playing_god/persistence/sqlite_store.py` — `save_world()`, `load_world()`, schema version 21, and persistence errors.
- `scripts/run_simulation.py` — create/load/run/save command line workflow.
- `scripts/inspect_agent.py` — manual persisted-agent inspection.

**Focused tests:** `tests/test_persistence.py`, plus split-run checks in `tests/test_reproducibility.py`.

**Important boundary:** A persisted restart must match an uninterrupted seeded run. Save/load transaction contexts explicitly close their SQLite connections. Schema changes require an explicit migration and round-trip/continuation coverage. Schema v12 stores adaptive state, v13 founder history, v14 family state, v15 development, v16 lifecycle, v17 checked cultural history, v18 compact civilization/agent-knowledge state, v19 bounded per-agent discovery pressure/exposure, v20 resolved discovery attempts, and v21 canonical peer-training affordance activation for existing validated knowledge. Older schemas load missing later-phase histories empty rather than reconstructing them, except for this engine-defined affordance derived from already validated state.

## `counterfactual-comparison` — paired same-seed experiments

**Owns:** scheduled intervention inputs, isolated baseline/intervention execution, immutable agent snapshots, changed-field summaries, and first-divergence evidence.

**Entry points:**

- `src/playing_god/core/counterfactual.py` — `ScheduledIntervention`, `CounterfactualComparison`, snapshotting, and paired execution.
- `scripts/compare_counterfactual.py` — one-intervention command-line comparison.

**Focused tests:** `tests/test_counterfactual.py`, plus the ordinary reproducibility suite.

**Important boundary:** Both branches share initial seed and configuration, but remain separate worlds. Results describe deterministic divergence inside this model, not supernatural proof or an estimate of real-world causation. After behavior diverges, the existing shared world-RNG call sequence may also diverge; the comparison does not claim per-event common random numbers.

## `tests-fixtures` — behavioral contracts

**Owns:** deterministic and persistence regression expectations.

**Entry points:**

- `tests/fixtures/phase1_seed_1947.json` — frozen Phase-1 structured snapshot.
- `tests/fixtures/report_1947.txt` — frozen report output.
- `tests/test_reproducibility.py` — seed and split-run contracts.

Fixtures are contracts, not generated output to refresh casually. Determine whether code or fixture intent is wrong before updating either.

## `research-docs` — thesis direction and phase intent

**Owns:** project vision, permanent research constraints, milestone definitions, and accepted future directions. These documents guide scope but do not override implemented source and tests.

**Entry points:**

- `docs/ROADMAP.md` — canonical phase sequence, outcomes, and exit conditions.
- `docs/STATUS.md` — current phase, completed step, and next implementation target.
- `docs/phases/phase-04-spatial-mobility.md` — Phase 4 spatial/mobility requirements.
- `docs/phases/phase-05-belief-intervention.md` — Phase 5 perception, prayer, intervention, faith, and counterfactual direction.
- `docs/phases/phase-06-society-information-institutions.md` — active Phase 6 economy, institution, information, and collective-action brief.
- `docs/research/phase-10-functional-consciousness.md` — human-review-gated functional cognition research; it is not an active implementation brief.
- `docs/archive/` — superseded versioned vision snapshots retained as research history, not active phase instructions.
- `docs/memory-implementation.md` — coding-agent memory principles and staged infrastructure.

## `coding-agent-memory` — navigation and rationale

**Owns:** stable agent rules, this subsystem map, concise current state, and significant engineering decisions/failures.

**Entry points:** `AGENTS.md`, `.agent/memory/CURRENT.md`, `.agent/memory/decisions.md`.

**Important boundary:** This layer is manually maintained, dependency-free supporting infrastructure. It is not simulation state, a runtime dependency, or an exhaustive activity log.

## Planned but not implemented

Phases 4–8 satisfy their roadmap exit conditions. Phase 8 provides persistent
civilization records, causal pressure, costly validated experiments, local
knowledge diffusion, one bounded knowledge-dependent action, one
evidence-gated school adoption route, and a reproducible counterfactual exit
proof with read-only metrics. Phase 7F recurrence detection remains deferred to
Phase 9 because no persisted multi-adult-generation dataset exists; no detector
or manufactured fixture is part of the current source. External code graphs,
semantic memory, CI/CD, MLOps, containers, and cloud infrastructure remain
deferred until an actual bottleneck or operational requirement exists.
