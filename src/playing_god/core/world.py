from __future__ import annotations

from dataclasses import replace
from itertools import combinations, islice
import math

from playing_god.core.adaptive import (
    capture_state,
    consequence_between,
    context_for,
    learn,
    learned_preferences,
)
from playing_god.core.agent import Agent, NAMES, SINS, TRAITS
from playing_god.core.civilization import (
    BASE_PRIMITIVES,
    EXPERIMENT_ENERGY_COST,
    EXPERIMENT_MONEY_COST,
    EXPERIMENT_STRESS_COST,
    PEER_TRAIN_ACTION_ID,
    PEER_TRAIN_AFFORDANCE,
    PEER_TRAIN_KNOWLEDGE_ID,
    TRAINING_ACCESS_PROBLEM_ID,
    AgentKnowledgeRecord,
    AgentKnowledgeState,
    BasePrimitive,
    CivilizationState,
    DiscoveryAttempt,
    DiscoveryCandidate,
    DiscoveryEligibility,
    KnowledgeEntry,
    PeerTrainingEligibility,
    PROBLEM_RECOGNITION_THRESHOLD,
    activate_peer_training_affordance,
    affordance_definition,
    compose_peer_training_candidate,
    discovery_attempt_score,
    discovery_eligibility,
    knowledge_entry,
    knowledge_response,
    knowledge_signature,
    peer_training_eligibility as evaluate_peer_training_eligibility,
    record_primitive_exposure,
    record_training_access_denial,
    select_knowledge_for_exposure,
    validate_discovery_candidate,
)
from playing_god.core.decision import (
    belonging_need,
    choose,
    money_pressure,
    scores as decision_scores,
)
from playing_god.core.development import (
    ADULT_AGE,
    advance_development,
)
from playing_god.core.collective import (
    CollectiveSnapshot,
    PARTICIPATED,
    PARTICIPATION_STATUS,
    ParticipationTrace,
    ParticipationPressure,
    build_collective_snapshot,
    build_participation_trace,
    participation_provenance,
    participation_information_id,
    participation_pressure,
    recent_participation_day,
)
from playing_god.core.culture import (
    CULTURAL_NORM,
    CULTURAL_VALUES,
    SCHOOL_NORM_SUBJECT,
    SCHOOL_NORM_VALUE,
    SCHOOL_SOURCE_ID,
    CulturalState,
    cultural_information_id,
    make_transmission,
    select_cultural_claim,
)
from playing_god.core.economy import EconomySnapshot, EconomyState
from playing_god.core.events import Event
from playing_god.core.exposure import (
    Interaction,
    detect_exposures,
    resolve_interactions,
)
from playing_god.core.family import (
    BirthContext,
    FamilyState,
    MAX_POPULATION,
    REPRODUCTION_COST,
    REPRODUCTION_DAILY_CHANCE,
    ReproductionEligibility,
    inherited_priors,
    reproduction_eligibility,
)
from playing_god.core.faith import (
    Attribution,
    classify_outcome,
    create_attribution,
    recent_matching_prayer,
)
from playing_god.core.mobility import choose_destination, travel
from playing_god.core.intervention import (
    INTERVENTION_KINDS,
    Intervention,
    InterventionResponse,
    classify_interpretation,
    intervention_attention,
    intervention_confidence,
)
from playing_god.core.institution import (
    SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD,
    SchoolKnowledgeAdoption,
    SchoolKnowledgeEvidence,
    SchoolSnapshot,
    SchoolState,
)
from playing_god.core.lifecycle import (
    ANNUAL_DEPENDENT_SUPPORT,
    MIN_MORTALITY_AGE,
    RETIREMENT_AGE,
    DeathRecord,
    HouseholdSnapshot,
    HouseholdSupportRecord,
    InheritanceTransfer,
    MortalityCheck,
    SupportContribution,
    household_snapshot,
    mortality_probability,
)
from playing_god.core.information import (
    DiffusionSnapshot,
    EMPLOYMENT_STATUS,
    InformationItem,
    diffusion_snapshot,
    employment_information_id,
    employment_status,
    observation_information_id,
    select_testimony,
)
from playing_god.core.perception import (
    Observation,
    Perception,
    belief_key,
    receive_observation,
    update_belief,
)
from playing_god.core.prayer import create_prayer
from playing_god.core.prehistory import (
    founder_starting_state,
    generate_founder_prehistory,
)
from playing_god.core.rng import create_rng
from playing_god.core.spatial import create_default_world_map
from .social import SocialGraph


MIN_RELATIONSHIP_FAMILIARITY = 0.22
MIN_VISIT_FAMILIARITY = 0.34
MIN_VISIT_AFFINITY = 0.18


class World:
    def __init__(
        self,
        seed: int = 1947,
        population: int = 10,
        *,
        adaptive_cognition: bool = False,
        reproduction_enabled: bool = False,
        lifecycle_enabled: bool | None = None,
    ):
        self.seed = seed
        self.rng = create_rng(seed)
        self.day = 0
        self.adaptive_cognition = adaptive_cognition
        self.reproduction_enabled = reproduction_enabled
        self.lifecycle_enabled = (
            reproduction_enabled
            if lifecycle_enabled is None
            else lifecycle_enabled
        )
        self.interventions: list[Intervention] = []
        self.intervention_responses: list[
            InterventionResponse
        ] = []
        self.information_items: list[InformationItem] = []
        self.civilization = CivilizationState()

        self.agents = self._create_agents(population)
        self.economy = EconomyState.from_agents(self.agents)
        self.school = SchoolState()
        self._create_relationships()
        self.rebuild_social_graph()
        self.rebuild_spatial_map()
        self.rebuild_information_index()

    @property
    def base_primitives(self) -> tuple[BasePrimitive, ...]:
        """Return engine-owned possibilities in canonical order."""
        return BASE_PRIMITIVES

    def rebuild_social_graph(self) -> None:
        self.social = SocialGraph.from_agents(self.agents)

    def rebuild_spatial_map(self) -> None:
        self.world_map = create_default_world_map()
        self.last_exposures = []
        self.last_interactions = []

    def rebuild_information_index(self) -> None:
        self._information_seen = {
            agent.id: {
                evidence_id
                for observation in agent.observations
                if (
                    evidence_id := observation_information_id(
                        observation
                    )
                ) is not None
            }
            for agent in self.agents
        }
        self._information_item_ids = {
            item.id
            for item in self.information_items
        }
        self._latest_information = {
            agent.id: {
                observation.subject_id: observation
                for observation in agent.observations
                if observation.kind == EMPLOYMENT_STATUS
            }
            for agent in self.agents
        }
        self._information_observation_counts = {
            agent.id: len(agent.observations)
            for agent in self.agents
        }

    def _ensure_information_index(self, agent: Agent) -> None:
        if (
            self._information_observation_counts[agent.id]
            == len(agent.observations)
        ):
            return

        self._information_seen[agent.id] = {
            evidence_id
            for observation in agent.observations
            if (
                evidence_id := observation_information_id(observation)
            ) is not None
        }
        self._latest_information[agent.id] = {
            observation.subject_id: observation
            for observation in agent.observations
            if observation.kind == EMPLOYMENT_STATUS
        }
        self._information_observation_counts[agent.id] = len(
            agent.observations
        )

    def economic_snapshot(self) -> EconomySnapshot:
        return self.economy.snapshot(self.living_agents())

    def living_agents(self) -> list[Agent]:
        return [
            agent
            for agent in self.agents
            if agent.lifecycle.alive
        ]

    def school_snapshot(self) -> SchoolSnapshot:
        return self.school.snapshot(self.day)

    def diffusion_snapshot(
        self,
        information_id: str,
    ) -> DiffusionSnapshot:
        return diffusion_snapshot(
            self.living_agents(),
            information_id,
        )

    def express_cultural_norm(
        self,
        agent_id: str,
        subject_id: str,
        value: str,
        *,
        confidence: float = 1.0,
    ) -> Observation:
        """Give one living agent an explicit, self-originated norm."""
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("Cultural agent ID must not be empty.")
        agents_by_id = {agent.id: agent for agent in self.agents}
        if agent_id not in agents_by_id:
            raise ValueError(f"Unknown agent: {agent_id}")
        agent = agents_by_id[agent_id]
        if not agent.lifecycle.alive:
            raise ValueError("A deceased agent cannot express culture.")
        if not isinstance(subject_id, str) or not subject_id:
            raise ValueError("Cultural subject must not be empty.")
        if not isinstance(value, str) or value not in CULTURAL_VALUES:
            raise ValueError(f"Unknown cultural value: {value}")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0.0 <= confidence <= 1.0
        ):
            raise ValueError("Cultural confidence must be within [0, 1].")
        confidence = float(confidence)

        information_id = cultural_information_id(
            subject_id,
            agent.id,
            self.day,
            value,
        )
        observation = Observation(
            day=self.day,
            kind=CULTURAL_NORM,
            subject_id=subject_id,
            value=value,
            source_id=agent.id,
            reliability=confidence,
            location=agent.current_location,
            information_id=information_id,
            origin_agent_id=agent.id,
            origin_day=self.day,
            hop_count=0,
        )
        receive_observation(agent, observation)
        self._ensure_information_index(agent)
        self._information_seen[agent.id].add(information_id)
        self._information_observation_counts[agent.id] = len(
            agent.observations
        )
        self.record(
            agent,
            "cultural_expression",
            f"Expressed {subject_id} as {value}",
            confidence,
            location=agent.current_location,
        )
        return observation

    def participation_pressure(
        self,
        agent: Agent,
        *,
        observed_participation: float = 0.0,
    ) -> ParticipationPressure:
        return participation_pressure(
            agent,
            self.social,
            observed_participation=observed_participation,
            day=self.day,
        )

    def collective_snapshot(self) -> CollectiveSnapshot:
        return build_collective_snapshot(self.living_agents())

    def discovery_eligibility(
        self,
        agent_id: str,
    ) -> DiscoveryEligibility:
        agent = next(
            (
                item
                for item in self.agents
                if item.id == agent_id
            ),
            None,
        )
        if agent is None:
            raise ValueError("Unknown discovery agent")
        return discovery_eligibility(
            agent,
            current_day=self.day,
        )

    def attempt_discovery(
        self,
        agent_id: str,
        *,
        candidate: DiscoveryCandidate | None = None,
    ) -> DiscoveryAttempt | None:
        agent = next(
            (
                item
                for item in self.agents
                if item.id == agent_id
            ),
            None,
        )
        if agent is None:
            raise ValueError("Unknown discovery agent")
        existing = next(
            (
                attempt
                for attempt in agent.discovery.attempts
                if attempt.day == self.day
            ),
            None,
        )
        if existing is not None:
            return existing
        if not self.discovery_eligibility(agent_id).eligible:
            return None

        candidate = candidate or compose_peer_training_candidate(agent)
        agent.money -= EXPERIMENT_MONEY_COST
        agent.energy -= EXPERIMENT_ENERGY_COST
        agent.stress += EXPERIMENT_STRESS_COST
        agent.normalize()
        attempt_event_index = self.record(
            agent,
            "discovery_attempted",
            (
                f"Attempted {candidate.action_id} discovery; "
                f"signature: {candidate.signature}; cost: "
                f"money {EXPERIMENT_MONEY_COST:.2f}, "
                f"energy {EXPERIMENT_ENERGY_COST:.2f}, "
                f"stress {EXPERIMENT_STRESS_COST:.2f}"
            ),
            0.65,
            location=agent.current_location,
        )
        validation_errors = validate_discovery_candidate(
            candidate,
            agent,
            self.civilization,
            current_day=self.day,
        )
        score = None
        roll = None
        knowledge_id = None
        if validation_errors:
            outcome = "structural_rejection"
            resolution_event_index = self.record(
                agent,
                "discovery_rejected",
                (
                    "Discovery candidate failed structural validation: "
                    + ", ".join(validation_errors)
                ),
                0.55,
                location=agent.current_location,
            )
        else:
            pressure = next(
                item
                for item in agent.discovery.pressures
                if item.id == candidate.problem_id
            )
            score = discovery_attempt_score(agent, pressure)
            roll = self.rng.random()
            if roll >= score:
                outcome = "failed"
                resolution_event_index = self.record(
                    agent,
                    "discovery_rejected",
                    (
                        "Discovery experiment was insufficient; "
                        f"score: {score:.4f}; roll: {roll:.4f}"
                    ),
                    0.58,
                    location=agent.current_location,
                )
            else:
                outcome = "validated"
                knowledge_id = PEER_TRAIN_KNOWLEDGE_ID
                resolution_event_index = self.record(
                    agent,
                    "discovery_validated",
                    (
                        "Validated peer-training knowledge; "
                        f"score: {score:.4f}; roll: {roll:.4f}"
                    ),
                    0.85,
                    location=agent.current_location,
                )
                entry = KnowledgeEntry(
                    id=knowledge_id,
                    signature=knowledge_signature(
                        candidate.primitive_ids,
                        candidate.action_id,
                    ),
                    origin_agent_id=agent.id,
                    origin_event_index=attempt_event_index,
                    discoverer_ids=(agent.id,),
                    primitive_ids=candidate.primitive_ids,
                    action_id=candidate.action_id,
                    creation_day=self.day,
                )
                self.civilization = activate_peer_training_affordance(
                    replace(
                        self.civilization,
                        knowledge=tuple(sorted(
                            self.civilization.knowledge + (entry,),
                            key=lambda item: item.id,
                        )),
                    )
                )
                agent.knowledge = AgentKnowledgeState(
                    records=agent.knowledge.records + (
                        AgentKnowledgeRecord(
                            day=self.day,
                            knowledge_id=knowledge_id,
                            source_id=agent.id,
                            route="discovery",
                            response="accept",
                            variant_id=None,
                            causal_parent_agent_id=agent.id,
                            causal_parent_event_index=(
                                resolution_event_index
                            ),
                        ),
                    ),
                )

        attempt = DiscoveryAttempt(
            id=f"attempt:{agent.id}:{self.day}",
            day=self.day,
            candidate=candidate,
            pressure_recognition_event_index=next(
                item.recognition_event_index
                for item in agent.discovery.pressures
                if item.id == TRAINING_ACCESS_PROBLEM_ID
            ),
            attempt_event_index=attempt_event_index,
            resolution_event_index=resolution_event_index,
            outcome=outcome,
            score=score,
            roll=roll,
            validation_errors=validation_errors,
            money_cost=EXPERIMENT_MONEY_COST,
            energy_cost=EXPERIMENT_ENERGY_COST,
            stress_cost=EXPERIMENT_STRESS_COST,
            knowledge_id=knowledge_id,
        )
        agent.discovery = replace(
            agent.discovery,
            attempts=agent.discovery.attempts + (attempt,),
        )
        return attempt

    def peer_training_eligibility(
        self,
        teacher_id: str,
        learner_id: str,
    ) -> PeerTrainingEligibility:
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        if teacher_id not in agents_by_id or learner_id not in agents_by_id:
            raise ValueError("Unknown peer-training participant")
        teacher = agents_by_id[teacher_id]
        learner = agents_by_id[learner_id]
        outward = self.social.get_relationship(
            teacher.id,
            learner.id,
        ) or {}
        inward = self.social.get_relationship(
            learner.id,
            teacher.id,
        ) or {}
        return evaluate_peer_training_eligibility(
            teacher,
            learner,
            self.civilization,
            outward_familiarity=outward.get("familiarity", 0.0),
            inward_familiarity=inward.get("familiarity", 0.0),
            minimum_familiarity=MIN_RELATIONSHIP_FAMILIARITY,
        )

    def peer_training_target(self, teacher: Agent) -> Agent | None:
        if affordance_definition(
            self.civilization,
            PEER_TRAIN_ACTION_ID,
        ) is None or not any(
            record.knowledge_id == PEER_TRAIN_KNOWLEDGE_ID
            and record.response in {"accept", "modify"}
            for record in teacher.knowledge.records
        ):
            return None
        candidates = []
        for learner in sorted(self.agents, key=lambda agent: agent.id):
            if learner.id == teacher.id:
                continue
            eligibility = self.peer_training_eligibility(
                teacher.id,
                learner.id,
            )
            if not eligibility.eligible:
                continue
            outward = self.social.get_relationship(
                teacher.id,
                learner.id,
            ) or {}
            inward = self.social.get_relationship(
                learner.id,
                teacher.id,
            ) or {}
            familiarity = min(
                outward.get("familiarity", 0.0),
                inward.get("familiarity", 0.0),
            )
            candidates.append((
                -familiarity,
                learner.skill,
                learner.id,
                learner,
            ))
        return min(candidates)[-1] if candidates else None

    def peer_training_utility(self, teacher: Agent) -> float | None:
        learner = self.peer_training_target(teacher)
        if learner is None:
            return None
        outward = self.social.get_relationship(
            teacher.id,
            learner.id,
        ) or {}
        inward = self.social.get_relationship(
            learner.id,
            teacher.id,
        ) or {}
        familiarity = min(
            outward.get("familiarity", 0.0),
            inward.get("familiarity", 0.0),
        )
        current = decision_scores(teacher)
        return round(
            0.55 * current["help"]
            + 0.45 * current["train"]
            - 0.20
            + 0.10 * familiarity,
            6,
        )

    def reproduction_eligibility(
        self,
        first_id: str,
        second_id: str,
    ) -> ReproductionEligibility:
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        if first_id not in agents_by_id or second_id not in agents_by_id:
            raise ValueError("Unknown reproduction parent")
        eligibility = reproduction_eligibility(
            agents_by_id[first_id],
            agents_by_id[second_id],
            self.social,
            agents_by_id,
            self.day,
        )
        if len(self.living_agents()) >= MAX_POPULATION:
            return replace(
                eligibility,
                eligible=False,
                reasons=(
                    eligibility.reasons
                    + ("population_capacity",)
                ),
            )
        return eligibility

    def _next_child_identity(self, generation: int) -> tuple[str, str]:
        used_ids = {agent.id for agent in self.agents}
        number = len(self.agents) + 1
        while f"npc_{number:03d}" in used_ids:
            number += 1
        generation_index = 1 + sum(
            agent.family.generation == generation
            for agent in self.agents
        )
        return (
            f"npc_{number:03d}",
            f"G{generation}-{generation_index:03d}",
        )

    def _create_child(
        self,
        first: Agent,
        second: Agent,
        eligibility: ReproductionEligibility,
        roll: float,
    ) -> Agent:
        parent_ids = (first.id, second.id)
        generation = max(
            first.family.generation,
            second.family.generation,
        ) + 1
        child_id, child_name = self._next_child_identity(generation)
        traits, sins = inherited_priors(first, second, self.rng)
        household_money = first.money + second.money
        guardian_stress = (first.stress + second.stress) / 2
        birth_context = BirthContext(
            day=self.day,
            parent_ids=parent_ids,
            guardian_ids=parent_ids,
            location=first.current_location,
            household_money=household_money,
            employed_guardians=sum((first.employed, second.employed)),
            guardian_stress=guardian_stress,
            mutual_affinity=eligibility.mutual_affinity,
            mutual_trust=eligibility.mutual_trust,
            mutual_familiarity=eligibility.mutual_familiarity,
            reproduction_roll=roll,
        )
        starting_stress = max(
            0.0,
            min(
                1.0,
                0.10
                + 0.10 * guardian_stress
                + 0.10 * (1 - min(household_money / 600.0, 1.0)),
            ),
        )
        child = Agent(
            id=child_id,
            name=child_name,
            age=0,
            traits=traits,
            sins=sins,
            money=0.0,
            employed=False,
            salary=0.0,
            job_level=0,
            skill=0.0,
            energy=1.0,
            social_energy=1.0,
            stress=starting_stress,
            reputation=0.0,
            current_location=first.current_location,
            family=FamilyState(
                generation=generation,
                birth_day=self.day,
                dependent=True,
                parent_ids=parent_ids,
                guardian_ids=parent_ids,
                birth_context=birth_context,
            ),
        )

        existing_agents = self.agents[:]
        for agent in existing_agents:
            family_affinity = 0.45 if agent.id in parent_ids else 0.0
            agent.relationships[child.id] = family_affinity
            child.relationships[agent.id] = family_affinity

        self.agents.append(child)
        self.social.add_agent(child.id)
        for agent in existing_agents:
            if agent.id in parent_ids:
                dimensions = {
                    "trust": 0.70,
                    "familiarity": 1.0,
                    "respect": 0.30,
                }
            else:
                dimensions = {}
            self.social.add_relationship(
                agent.id,
                child.id,
                affinity=agent.relationships[child.id],
                **dimensions,
            )
            self.social.add_relationship(
                child.id,
                agent.id,
                affinity=child.relationships[agent.id],
                **dimensions,
            )

        for parent in (first, second):
            parent.family = replace(
                parent.family,
                child_ids=parent.family.child_ids + (child.id,),
            )
            parent.money -= REPRODUCTION_COST / 2
            parent.stress += 0.05
            parent.social_energy -= 0.05
            parent.normalize()
            self.record(
                parent,
                "birth",
                f"Became a parent of {child.name}",
                0.95,
                target_id=child.id,
                location=child.current_location,
            )

        self.record(
            child,
            "birth",
            f"Born to {first.name} and {second.name}",
            1.0,
            target_id=first.id,
            location=child.current_location,
        )
        self._information_seen[child.id] = set()
        self._latest_information[child.id] = {}
        self._information_observation_counts[child.id] = 0
        return child

    def attempt_reproduction(
        self,
        first_id: str,
        second_id: str,
    ) -> Agent | None:
        if not self.reproduction_enabled:
            return None

        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        eligibility = self.reproduction_eligibility(
            first_id,
            second_id,
        )
        if not eligibility.eligible:
            return None

        roll = self.rng.random()
        if roll >= REPRODUCTION_DAILY_CHANCE:
            return None
        return self._create_child(
            agents_by_id[first_id],
            agents_by_id[second_id],
            eligibility,
            roll,
        )

    def resolve_reproduction(self) -> list[Agent]:
        if not self.reproduction_enabled:
            return []

        births = []
        adults = sorted(
            (
                agent
                for agent in self.agents
                if (
                    agent.lifecycle.alive
                    and not agent.family.dependent
                )
            ),
            key=lambda agent: agent.id,
        )
        used_parents = set()
        for first, second in combinations(adults, 2):
            if first.id in used_parents or second.id in used_parents:
                continue
            child = self.attempt_reproduction(first.id, second.id)
            if child is None:
                continue
            births.append(child)
            used_parents.update((first.id, second.id))
            if len(self.living_agents()) >= MAX_POPULATION:
                break

        return births

    def resolve_development(self) -> list[Agent]:
        """Resolve exact birth anniversaries without daily child actions."""
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        progressed = []
        for child in sorted(self.agents, key=lambda agent: agent.id):
            birth_day = child.family.birth_day
            if birth_day is None:
                continue
            days_since_birth = self.day - birth_day
            if days_since_birth <= 0 or days_since_birth % 365:
                continue

            age = days_since_birth // 365
            child.age = age
            if age > ADULT_AGE or not child.family.dependent:
                continue
            if (
                child.development.records
                and child.development.records[-1].age >= age
            ):
                continue

            if self.lifecycle_enabled and age < ADULT_AGE:
                self.resolve_household_support(child, age)

            guardians = [
                agents_by_id[guardian_id]
                for guardian_id in child.family.guardian_ids
            ]
            outcome = advance_development(
                child,
                guardians,
                self.social,
                day=self.day,
                age=age,
                school_available=(
                    self.school.location in self.world_map.locations
                ),
            )
            child.development = outcome.state
            child.skill = outcome.skill
            if (
                self.adaptive_cognition
                and outcome.state.records[-1].school_access
            ):
                learn(
                    child,
                    "improve_skill",
                    "train",
                    consequence_between(
                        replace(
                            capture_state(child),
                            skill=outcome.state.records[-1].skill_before,
                        ),
                        capture_state(child),
                    ),
                )
            if outcome.became_adult:
                child.family = replace(
                    child.family,
                    dependent=False,
                )

            record = outcome.state.records[-1]
            for guardian in sorted(
                guardians,
                key=lambda agent: agent.id,
            ):
                if guardian.lifecycle.alive:
                    self._transmit_cultural_claim(
                        guardian,
                        child,
                        route="guardian",
                        location=child.current_location,
                        allow_repeat=True,
                    )
                    self._transmit_knowledge(
                        guardian,
                        child,
                        route="guardian",
                        location=child.current_location,
                        allow_repeat=True,
                    )
            self._transmit_school_culture(child)
            self._transmit_school_knowledge(child)

            description = (
                f"Reached age {age}: {record.stage}; "
                f"school_access={str(record.school_access).lower()}; "
                f"skill_gain={record.skill_gain:.6f}"
            )
            self.record(
                child,
                "development",
                description,
                0.75 if outcome.became_adult else 0.30,
                location=(
                    self.school.location
                    if record.school_access
                    else child.current_location
                ),
            )
            progressed.append(child)
        return progressed

    def household_snapshot(self, dependent_id: str) -> HouseholdSnapshot:
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        if dependent_id not in agents_by_id:
            raise ValueError(f"Unknown dependent: {dependent_id}")
        return household_snapshot(
            agents_by_id[dependent_id],
            agents_by_id,
        )

    def resolve_household_support(
        self,
        child: Agent,
        age: int,
    ) -> HouseholdSupportRecord:
        if not child.family.dependent or not child.lifecycle.alive:
            raise ValueError("Household support requires a living dependent.")
        if (
            child.lifecycle.support_received
            and child.lifecycle.support_received[-1].day == self.day
        ):
            return child.lifecycle.support_received[-1]

        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        guardians = [
            agents_by_id[guardian_id]
            for guardian_id in child.family.guardian_ids
        ]
        living = [
            guardian
            for guardian in guardians
            if guardian.lifecycle.alive
        ]
        target_share = (
            ANNUAL_DEPENDENT_SUPPORT / len(living)
            if living
            else 0.0
        )
        contributions = []
        for guardian in guardians:
            amount = (
                min(target_share, max(0.0, guardian.money))
                if guardian.lifecycle.alive
                else 0.0
            )
            guardian.money -= amount
            contributions.append(SupportContribution(
                guardian_id=guardian.id,
                amount=amount,
            ))

        total_support = sum(item.amount for item in contributions)
        stress_before = child.stress
        child.stress -= min(0.08, total_support / 600.0)
        child.normalize()
        record = HouseholdSupportRecord(
            day=self.day,
            age=age,
            dependent_id=child.id,
            guardian_ids=child.family.guardian_ids,
            contributions=tuple(contributions),
            total_support=total_support,
            stress_before=stress_before,
            stress_after=child.stress,
        )
        child.lifecycle = replace(
            child.lifecycle,
            support_received=(
                child.lifecycle.support_received + (record,)
            ),
        )
        return record

    def _retire(self, agent: Agent) -> None:
        agent.lifecycle = replace(
            agent.lifecycle,
            retired=True,
            retirement_day=self.day,
        )
        agent.employed = False
        agent.salary = 0.0
        agent.job_level = 0
        self.record(
            agent,
            "lifecycle",
            f"Retired at age {agent.age}",
            0.80,
            location=agent.current_location,
        )

    def _die(self, agent: Agent) -> None:
        agents_by_id = {
            item.id: item
            for item in self.agents
        }
        heirs = sorted(
            (
                agents_by_id[child_id]
                for child_id in agent.family.child_ids
                if agents_by_id[child_id].lifecycle.alive
            ),
            key=lambda item: item.id,
        )
        estate = max(0.0, agent.money)
        transfers = []
        remaining = estate
        distribution_heirs = heirs if estate > 0.0 else []
        for index, heir in enumerate(distribution_heirs):
            amount = (
                remaining
                if index == len(distribution_heirs) - 1
                else estate / len(distribution_heirs)
            )
            remaining -= amount
            transfer = InheritanceTransfer(
                day=self.day,
                deceased_id=agent.id,
                heir_id=heir.id,
                amount=amount,
            )
            transfers.append(transfer)
            heir.money += amount
            heir.lifecycle = replace(
                heir.lifecycle,
                inheritance_received=(
                    heir.lifecycle.inheritance_received + (transfer,)
                ),
            )
            self.record(
                heir,
                "inheritance",
                f"Inherited {amount:.2f} from {agent.name}",
                0.82,
                target_id=agent.id,
                location=heir.current_location,
            )

        death = DeathRecord(
            day=self.day,
            age=agent.age,
            estate=estate,
            transfers=tuple(transfers),
            unallocated=estate if not distribution_heirs else 0.0,
        )
        agent.lifecycle = replace(
            agent.lifecycle,
            alive=False,
            death=death,
        )
        agent.money = 0.0
        agent.employed = False
        agent.salary = 0.0
        agent.job_level = 0
        agent.destination = None
        self.record(
            agent,
            "lifecycle",
            f"Died at age {agent.age}",
            1.0,
            location=agent.current_location,
        )

    def resolve_lifecycle(self) -> list[Agent]:
        if not self.lifecycle_enabled:
            return []

        transitioned = []
        for agent in sorted(self.agents, key=lambda item: item.id):
            if not agent.lifecycle.alive:
                continue
            birth_day = agent.family.birth_day
            is_anniversary = False
            if birth_day is None:
                is_anniversary = self.day > 0 and self.day % 365 == 0
                if (
                    is_anniversary
                    and agent.lifecycle.last_age_day != self.day
                ):
                    agent.age += 1
                else:
                    is_anniversary = False
            else:
                days_since_birth = self.day - birth_day
                is_anniversary = (
                    days_since_birth > 0
                    and days_since_birth % 365 == 0
                    and agent.lifecycle.last_age_day != self.day
                )
                if is_anniversary:
                    agent.age = days_since_birth // 365

            if not is_anniversary:
                continue
            agent.lifecycle = replace(
                agent.lifecycle,
                last_age_day=self.day,
            )

            if agent.age >= RETIREMENT_AGE and not agent.lifecycle.retired:
                self._retire(agent)
                transitioned.append(agent)

            if agent.age < MIN_MORTALITY_AGE:
                continue
            probability = mortality_probability(agent.age, agent.stress)
            roll = self.rng.random()
            check = MortalityCheck(
                day=self.day,
                age=agent.age,
                probability=probability,
                roll=roll,
                died=roll < probability,
            )
            agent.lifecycle = replace(
                agent.lifecycle,
                mortality_checks=(
                    agent.lifecycle.mortality_checks + (check,)
                ),
            )
            if check.died:
                self._die(agent)
                if all(item.id != agent.id for item in transitioned):
                    transitioned.append(agent)

        return transitioned

    def participation_trace(
        self,
        agent_id: str,
    ) -> ParticipationTrace:
        agent = next(
            (
                item
                for item in self.agents
                if item.id == agent_id
            ),
            None,
        )
        if agent is None:
            raise ValueError(f"Unknown agent: {agent_id}")
        return build_participation_trace(agent)

    def apply_social_event(
        self,
        actor_id: str,
        target_id: str,
        event_type: str,
    ) -> None:
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        if (
            actor_id in agents_by_id
            and not agents_by_id[actor_id].lifecycle.alive
        ) or (
            target_id in agents_by_id
            and not agents_by_id[target_id].lifecycle.alive
        ):
            raise ValueError("Social events require living agents")
        self.social.apply_social_event(
            actor_id,
            target_id,
            event_type,
        )

    def create_intervention(
        self,
        *,
        kind: str,
        target_id: str,
        theme: str,
        suggested_action: str,
        strength: float = 0.70,
        location: str | None = None,
        duration: int = 7,
    ) -> Intervention:
        """Create a condition that may influence, never force, an NPC."""
        if kind not in INTERVENTION_KINDS:
            raise ValueError(f"Unknown intervention kind: {kind}")

        targets = {
            agent.id: agent
            for agent in self.agents
        }
        if target_id not in targets:
            raise ValueError(
                f"Unknown intervention target: {target_id}"
            )
        if targets[target_id].family.dependent:
            raise ValueError(
                "Dependent interventions require child development"
            )
        if not targets[target_id].lifecycle.alive:
            raise ValueError("Interventions require a living target")

        if not theme.strip():
            raise ValueError("Intervention theme cannot be empty")

        if suggested_action not in decision_scores(
            targets[target_id]
        ):
            raise ValueError(
                "Unknown suggested action: "
                f"{suggested_action}"
            )

        if not 0.0 <= strength <= 1.0:
            raise ValueError(
                "Intervention strength must be within [0, 1]"
            )

        if duration < 1:
            raise ValueError(
                "Intervention duration must be at least one day"
            )

        if kind == "dream":
            if location is not None:
                raise ValueError(
                    "Dream interventions cannot have a location"
                )
        elif location not in self.world_map.locations:
            raise ValueError(
                "Sign and opportunity interventions require "
                "a valid location"
            )

        intervention = Intervention(
            id=(
                "intervention_"
                f"{len(self.interventions) + 1:06d}"
            ),
            kind=kind,
            target_id=target_id,
            theme=theme.strip(),
            suggested_action=suggested_action,
            strength=strength,
            created_day=self.day,
            expires_day=self.day + duration,
            location=location,
        )
        self.interventions.append(intervention)
        return intervention

    def intervention_action_adjustments(
        self,
        agent: Agent,
    ) -> dict[str, float]:
        interventions = {
            intervention.id: intervention
            for intervention in self.interventions
        }
        adjustments: dict[str, float] = {}

        for response in self.intervention_responses:
            if response.agent_id != agent.id:
                continue

            if response.interpreted_action is None:
                continue

            intervention = interventions.get(
                response.intervention_id
            )
            if intervention is None:
                continue

            if not response.day <= self.day <= intervention.expires_day:
                continue

            adjustments[response.interpreted_action] = (
                adjustments.get(response.interpreted_action, 0.0)
                + 0.90
                * intervention.strength
                * response.confidence
            )

        return adjustments

    def _alternative_interpretation(
        self,
        agent: Agent,
        suggested_action: str,
    ) -> str | None:
        alternatives = [
            (score, action)
            for action, score in decision_scores(agent).items()
            if action != suggested_action and score > -50
        ]
        if not alternatives:
            return None

        return max(alternatives)[1]

    def resolve_interventions(
        self,
    ) -> list[InterventionResponse]:
        """Resolve newly reachable stimuli without using world RNG."""
        responded = {
            response.intervention_id
            for response in self.intervention_responses
        }
        agents_by_id = {
            agent.id: agent
            for agent in self.agents
        }
        new_responses = []

        for intervention in self.interventions:
            if intervention.id in responded:
                continue

            if not (
                intervention.created_day
                < self.day
                <= intervention.expires_day
            ):
                continue

            agent = agents_by_id[intervention.target_id]
            if not agent.lifecycle.alive:
                continue
            if (
                intervention.kind != "dream"
                and agent.current_location != intervention.location
            ):
                continue

            confidence = intervention_confidence(
                agent,
                intervention,
            )
            interpretation = classify_interpretation(confidence)
            interpreted_action = None

            if interpretation == "aligned":
                interpreted_action = intervention.suggested_action
            elif interpretation == "misinterpreted":
                interpreted_action = self._alternative_interpretation(
                    agent,
                    intervention.suggested_action,
                )

            noticed = interpretation != "missed"
            response = InterventionResponse(
                intervention_id=intervention.id,
                agent_id=agent.id,
                day=self.day,
                noticed=noticed,
                interpretation=interpretation,
                interpreted_action=interpreted_action,
                confidence=confidence,
            )
            self.intervention_responses.append(response)
            new_responses.append(response)

            if not noticed:
                continue

            receive_observation(
                agent,
                Observation(
                    day=self.day,
                    kind=intervention.kind,
                    subject_id=intervention.id,
                    value=intervention.theme,
                    source_id=None,
                    reliability=intervention.strength,
                    location=intervention.location,
                ),
                attention=intervention_attention(agent),
            )

            if interpreted_action is None:
                description = (
                    f"Noticed a {intervention.kind} about "
                    f"{intervention.theme} but formed no intention"
                )
            else:
                description = (
                    f"Interpreted a {intervention.kind} about "
                    f"{intervention.theme} as a reason to "
                    f"{interpreted_action}"
                )

            self.record(
                agent,
                intervention.kind,
                description,
                confidence,
                location=intervention.location,
            )

        return new_responses

    def _recent_intervention_response(
        self,
        agent: Agent,
        action: str | None,
        *,
        window: int = 30,
    ) -> InterventionResponse | None:
        if action is None:
            return None

        candidates = []

        for response in self.intervention_responses:
            if response.agent_id != agent.id:
                continue
            if response.interpreted_action != action:
                continue
            if not 0 <= self.day - response.day <= window:
                continue

            candidates.append(response)

        return max(
            candidates,
            key=lambda response: response.day,
            default=None,
        )

    def resolve_daily_attributions(
        self,
    ) -> list[Attribution]:
        """Attribute today's significant outcomes without causal proof."""
        new_attributions = []

        for agent in self.agents:
            processed = set()
            for attribution in reversed(agent.attributions):
                if attribution.day < self.day:
                    break
                if attribution.day == self.day:
                    processed.add(attribution.outcome_event_index)

            current_events = []
            for event_index in range(len(agent.events) - 1, -1, -1):
                event = agent.events[event_index]
                if event.day < self.day:
                    break
                if event.day == self.day:
                    current_events.append((event_index, event))

            for event_index, event in reversed(current_events):
                if event_index in processed:
                    continue

                outcome = classify_outcome(event)
                if outcome is None:
                    continue

                prayer = recent_matching_prayer(
                    agent,
                    outcome.desire_type,
                    self.day,
                )
                response = self._recent_intervention_response(
                    agent,
                    outcome.action,
                )
                attribution = create_attribution(
                    agent,
                    event,
                    event_index,
                    outcome,
                    prayer=prayer,
                    response=response,
                )
                agent.attributions.append(attribution)
                agent.faith = attribution.faith_after
                new_attributions.append(attribution)

                self.record(
                    agent,
                    "attribution",
                    (
                        f"Attributed {event.kind} outcome to "
                        f"{attribution.cause}; faith "
                        f"{attribution.faith_before:.2f} -> "
                        f"{attribution.faith_after:.2f}"
                    ),
                    attribution.confidence,
                    target_id=event.target_id,
                    location=event.location,
                )

        return new_attributions

    def _create_agents(
        self,
        population: int,
    ) -> list[Agent]:
        people = []

        for i in range(population):
            traits = {
                k: round(self.rng.uniform(0.15, 0.85), 3)
                for k in TRAITS
            }

            sins = {
                k: round(self.rng.uniform(0.10, 0.90), 3)
                for k in SINS
            }

            age, founder_prehistory = (
                generate_founder_prehistory(self.rng)
            )
            starting_state = founder_starting_state(
                founder_prehistory
            )

            people.append(
                Agent(
                    id=f"npc_{i + 1:03d}",
                    name=NAMES[i],
                    age=age,
                    traits=traits,
                    sins=sins,
                    money=float(starting_state["money"]),
                    employed=bool(starting_state["employed"]),
                    salary=float(starting_state["salary"]),
                    job_level=int(starting_state["job_level"]),
                    skill=float(starting_state["skill"]),
                    energy=float(starting_state["energy"]),
                    social_energy=float(
                        starting_state["social_energy"]
                    ),
                    stress=float(starting_state["stress"]),
                    reputation=float(
                        starting_state["reputation"]
                    ),
                    founder_prehistory=founder_prehistory,
                )
            )

        return people

    def _create_relationships(self) -> None:
        for a in self.agents:
            for b in self.agents:
                if a.id != b.id:
                    a.relationships[b.id] = self.rng.uniform(
                        -0.08,
                        0.08,
                    )

    def record(
        self,
        a: Agent,
        kind: str,
        description: str,
        significance: float,
        *,
        target_id: str | None = None,
        location: str | None = None,
    ) -> int:
        event_index = len(a.events)
        a.events.append(
            Event(
                day=self.day,
                kind=kind,
                description=description,
                significance=significance,
                target_id=target_id,
                location=location,
            )
        )
        return event_index

    def _record_training_denial(
        self,
        a: Agent,
        description: str,
        significance: float,
        *,
        reason: str,
        location: str,
    ) -> None:
        event_index = self.record(
            a,
            "institution",
            description,
            significance,
            location=location,
        )
        a.discovery, newly_recognized = (
            record_training_access_denial(
                a.discovery,
                agent_id=a.id,
                day=self.day,
                event_index=event_index,
                reason=reason,
                recognition_event_index=len(a.events),
            )
        )
        if newly_recognized:
            self.record(
                a,
                "problem_pressure_recognized",
                (
                    "Recognized repeated training-access pressure "
                    f"after {PROBLEM_RECOGNITION_THRESHOLD} denials"
                ),
                0.60,
                location=location,
            )

    def update_goal(self, a: Agent) -> None:
        if a.lifecycle.retired:
            new_goal = (
                "build_relationships"
                if belonging_need(a) > 0.46
                else "improve_skill"
            )
        elif not a.employed:
            new_goal = "find_job"

        elif a.money < 180:
            new_goal = "build_savings"

        elif a.skill < 0.58:
            new_goal = "improve_skill"

        elif belonging_need(a) > 0.46:
            new_goal = "build_relationships"

        else:
            new_goal = "advance_career"

        if new_goal != a.goal:
            old = a.goal or "none"
            a.goal = new_goal

            self.record(
                a,
                "goal",
                f"Goal changed: {old} -> {new_goal}",
                0.62,
            )

    def move_for_action(
        self,
        a: Agent,
        action: str,
    ) -> None:
        if a.family.dependent or not a.lifecycle.alive:
            return
        if action == "peer_train":
            return

        destination = choose_destination(a, action)
        visit_target = None

        if destination == "cafe":
            visit_target = self.visit_target(a, action)

            if visit_target is not None:
                destination = self.believed_location(
                    a,
                    visit_target,
                )

        if destination == a.current_location:
            return

        result = travel(
            a,
            self.world_map,
            destination,
        )

        route = " -> ".join(result.route)
        purpose = f"for {action}"

        if visit_target is not None:
            purpose = f"to visit {visit_target.name}"

        self.record(
            a,
            "travel",
            f"Travelled {route} {purpose}",
            0.10,
        )

    def resolve_daily_interactions(self) -> list[Interaction]:
        """Resolve only interaction opportunities created by co-location."""
        active_agents = [
            agent
            for agent in self.agents
            if agent.lifecycle.alive and not agent.family.dependent
        ]
        self.last_exposures = detect_exposures(active_agents)

        agents_by_id = {
            agent.id: agent
            for agent in active_agents
        }
        encounter_seed = (
            self.seed * 1_000_003
            + self.day * 97_409
        )
        encounter_rng = create_rng(encounter_seed)

        self.last_interactions = resolve_interactions(
            self.last_exposures,
            agents_by_id,
            encounter_rng,
        )

        for interaction in self.last_interactions:
            self.social.update_relationship(
                interaction.agent_a,
                interaction.agent_b,
                familiarity=0.04,
            )
            self.social.update_relationship(
                interaction.agent_b,
                interaction.agent_a,
                familiarity=0.04,
            )

            first = agents_by_id[interaction.agent_a]
            second = agents_by_id[interaction.agent_b]
            self._ensure_information_index(first)
            self._ensure_information_index(second)

            for participant in (first, second):
                participant.social_energy -= (
                    0.02
                    + 0.02
                    * (1 - participant.traits["sociability"])
                )
                participant.normalize()

            self.record(
                first,
                "interaction",
                f"Interacted with {second.name} at "
                f"{interaction.location}",
                0.20,
                target_id=second.id,
                location=interaction.location,
            )
            self.record(
                second,
                "interaction",
                f"Interacted with {first.name} at "
                f"{interaction.location}",
                0.20,
                target_id=first.id,
                location=interaction.location,
            )

            receive_observation(
                first,
                Observation(
                    day=self.day,
                    kind="agent_location",
                    subject_id=second.id,
                    value=interaction.location,
                    source_id=second.id,
                    reliability=1.0,
                    location=interaction.location,
                ),
            )
            receive_observation(
                second,
                Observation(
                    day=self.day,
                    kind="agent_location",
                    subject_id=first.id,
                    value=interaction.location,
                    source_id=first.id,
                    reliability=1.0,
                    location=interaction.location,
                ),
            )
            self._information_observation_counts[first.id] = len(
                first.observations
            )
            self._information_observation_counts[second.id] = len(
                second.observations
            )

            self._observe_participation(
                first,
                second,
                interaction.location,
            )
            self._observe_participation(
                second,
                first,
                interaction.location,
            )

            self._transmit_testimony(
                first,
                second,
                interaction.location,
            )
            self._transmit_testimony(
                second,
                first,
                interaction.location,
            )

            self._transmit_cultural_claim(
                first,
                second,
                route="social",
                location=interaction.location,
            )
            self._transmit_cultural_claim(
                second,
                first,
                route="social",
                location=interaction.location,
            )

            self._transmit_knowledge(
                first,
                second,
                route="social",
                location=interaction.location,
            )
            self._transmit_knowledge(
                second,
                first,
                route="social",
                location=interaction.location,
            )

            self._observe_employment(
                first,
                second,
                interaction.location,
            )
            self._observe_employment(
                second,
                first,
                interaction.location,
            )

        return self.last_interactions

    def _transmit_knowledge(
        self,
        source: Agent,
        recipient: Agent,
        *,
        route: str,
        location: str,
        allow_repeat: bool = False,
    ) -> KnowledgeEntry | None:
        entry = select_knowledge_for_exposure(
            source,
            recipient,
            self.civilization,
            current_day=self.day,
            allow_repeat=allow_repeat,
        )
        if entry is None:
            return None

        relationship = self.social.get_relationship(
            recipient.id,
            source.id,
        ) or {}
        influence, response, variant_id = knowledge_response(
            recipient,
            knowledge_id=entry.id,
            route=route,
            trust=relationship.get("trust", 0.0),
            familiarity=relationship.get("familiarity", 0.0),
        )
        already_adopted = entry.id in {
            record.knowledge_id
            for record in recipient.knowledge.records
            if record.response in {"accept", "modify"}
        }
        response_label = {
            "accept": "Accepted",
            "modify": "Modified",
            "reject": "Rejected",
        }[response]
        exposure_event_index = self.record(
            recipient,
            "knowledge_exposed",
            (
                f"{response_label} {entry.id} from "
                f"{source.name} via {route}; influence: "
                f"{influence:.6f}"
            ),
            influence,
            target_id=source.id,
            location=location,
        )
        record = AgentKnowledgeRecord(
            day=self.day,
            knowledge_id=entry.id,
            source_id=source.id,
            route=route,
            response=response,
            variant_id=variant_id,
            causal_parent_agent_id=recipient.id,
            causal_parent_event_index=exposure_event_index,
        )
        recipient.knowledge = AgentKnowledgeState(records=tuple(sorted(
            recipient.knowledge.records + (record,),
            key=lambda item: (
                item.day,
                item.knowledge_id,
                item.source_id,
                item.route,
            ),
        )))
        if response in {"accept", "modify"} and not already_adopted:
            self.record(
                recipient,
                "knowledge_adopted",
                (
                    f"Adopted {entry.id} via {route}"
                    + (
                        f" as {variant_id}"
                        if variant_id is not None
                        else ""
                    )
                ),
                influence,
                target_id=source.id,
                location=location,
            )
        return entry

    def _transmit_cultural_claim(
        self,
        source: Agent,
        recipient: Agent,
        *,
        route: str,
        location: str,
        allow_repeat: bool = False,
    ) -> InformationItem | None:
        seen = {
            (record.source_id, record.information_id)
            for record in recipient.culture.records
            if record.information_id is not None
        }
        seen.update(
            (source.id, observation.information_id)
            for observation in recipient.observations
            if observation.information_id is not None
        )
        item = select_cultural_claim(
            source,
            seen=seen,
            allow_repeat=allow_repeat,
        )
        if item is None:
            return None

        relationship = self.social.get_relationship(
            recipient.id,
            source.id,
        ) or {}
        record = make_transmission(
            recipient,
            day=self.day,
            subject_id=item.subject_id,
            source_id=source.id,
            route=route,
            source_value=item.value,
            source_confidence=item.reliability,
            trust=relationship.get("trust", 0.0),
            familiarity=relationship.get("familiarity", 0.0),
            information_id=item.id,
            origin_agent_id=item.origin_agent_id,
            origin_day=item.origin_day,
            hop_count=item.hop_count,
        )
        recipient.culture = CulturalState(
            records=recipient.culture.records + (record,),
        )

        if item.id not in self._information_item_ids:
            self.information_items.append(item)
            self._information_item_ids.add(item.id)

        observation = Observation(
            day=self.day,
            kind=item.kind,
            subject_id=item.subject_id,
            value=item.value,
            source_id=source.id,
            reliability=item.reliability,
            location=location,
            information_id=item.id,
            origin_agent_id=item.origin_agent_id,
            origin_day=item.origin_day,
            hop_count=item.hop_count,
        )
        recipient.observations.append(observation)
        if record.resulting_value is not None:
            update_belief(
                recipient,
                Perception(
                    day=self.day,
                    kind=CULTURAL_NORM,
                    subject_id=item.subject_id,
                    value=record.resulting_value,
                    confidence=record.resulting_confidence,
                ),
            )
        self._ensure_information_index(recipient)
        self._information_seen[recipient.id].add(item.id)
        self._information_observation_counts[recipient.id] = len(
            recipient.observations
        )

        response_label = {
            "accept": "Accepted",
            "modify": "Modified",
            "reject": "Rejected",
        }[record.response]
        description = (
            f"{response_label} {item.subject_id} "
            f"from {source.name} via {route}"
        )
        self.record(
            recipient,
            "cultural_transmission",
            description,
            record.influence,
            target_id=source.id,
            location=location,
        )
        self.record(
            source,
            "cultural_transmission",
            f"Shared {item.subject_id} with {recipient.name} via {route}",
            item.reliability,
            target_id=recipient.id,
            location=location,
        )
        return item

    def _transmit_school_culture(
        self,
        child: Agent,
    ) -> None:
        record = child.development.records[-1]
        if not record.school_access:
            return

        school_years = sum(
            item.school_access
            for item in child.development.records
        )
        transmission = make_transmission(
            child,
            day=self.day,
            subject_id=SCHOOL_NORM_SUBJECT,
            source_id=SCHOOL_SOURCE_ID,
            route="school",
            source_value=SCHOOL_NORM_VALUE,
            source_confidence=round(record.feedback, 6),
            trust=record.relationship_support,
            familiarity=min(1.0, school_years / 4),
            information_id=None,
            origin_agent_id=None,
            origin_day=None,
            hop_count=None,
        )
        child.culture = CulturalState(
            records=child.culture.records + (transmission,),
        )
        observation = Observation(
            day=self.day,
            kind=CULTURAL_NORM,
            subject_id=SCHOOL_NORM_SUBJECT,
            value=SCHOOL_NORM_VALUE,
            source_id=SCHOOL_SOURCE_ID,
            reliability=round(record.feedback, 6),
            location=self.school.location,
        )
        child.observations.append(observation)
        if transmission.resulting_value is not None:
            update_belief(
                child,
                Perception(
                    day=self.day,
                    kind=CULTURAL_NORM,
                    subject_id=SCHOOL_NORM_SUBJECT,
                    value=transmission.resulting_value,
                    confidence=transmission.resulting_confidence,
                ),
            )
        self._ensure_information_index(child)
        self._information_observation_counts[child.id] = len(
            child.observations
        )
        self.record(
            child,
            "cultural_transmission",
            {
                "accept": "Accepted learning via school",
                "modify": "Modified learning via school",
                "reject": "Rejected learning via school",
            }[transmission.response],
            transmission.influence,
            location=self.school.location,
        )

    def _transmit_school_knowledge(
        self,
        child: Agent,
    ) -> KnowledgeEntry | None:
        development = child.development.records[-1]
        adoption = self.school.knowledge_adoption
        if (
            not development.school_access
            or adoption is None
            or self.day < adoption.day
        ):
            return None
        entry = knowledge_entry(
            self.civilization,
            adoption.knowledge_id,
        )
        if entry is None:
            return None

        school_years = sum(
            item.school_access
            for item in child.development.records
        )
        influence, response, variant_id = knowledge_response(
            child,
            knowledge_id=entry.id,
            route="school",
            trust=development.relationship_support,
            familiarity=min(1.0, school_years / 4),
        )
        already_adopted = entry.id in {
            record.knowledge_id
            for record in child.knowledge.records
            if record.response in {"accept", "modify"}
        }
        response_label = {
            "accept": "Accepted",
            "modify": "Modified",
            "reject": "Rejected",
        }[response]
        exposure_event_index = self.record(
            child,
            "knowledge_exposed",
            (
                f"{response_label} {entry.id} from school; "
                f"institutional adoption day: {adoption.day}; "
                f"influence: {influence:.6f}"
            ),
            influence,
            target_id=SCHOOL_SOURCE_ID,
            location=self.school.location,
        )
        record = AgentKnowledgeRecord(
            day=self.day,
            knowledge_id=entry.id,
            source_id=SCHOOL_SOURCE_ID,
            route="school",
            response=response,
            variant_id=variant_id,
            causal_parent_agent_id=child.id,
            causal_parent_event_index=exposure_event_index,
        )
        child.knowledge = AgentKnowledgeState(records=tuple(sorted(
            child.knowledge.records + (record,),
            key=lambda item: (
                item.day,
                item.knowledge_id,
                item.source_id,
                item.route,
            ),
        )))
        if response in {"accept", "modify"} and not already_adopted:
            self.record(
                child,
                "knowledge_adopted",
                (
                    f"Adopted {entry.id} via school"
                    + (
                        f" as {variant_id}"
                        if variant_id is not None
                        else ""
                    )
                ),
                influence,
                target_id=SCHOOL_SOURCE_ID,
                location=self.school.location,
            )
        return entry

    def _observe_school_peer_training(
        self,
        teacher: Agent,
        learner: Agent,
        *,
        knowledge_id: str,
        teacher_event_index: int,
    ) -> None:
        if teacher.current_location != self.school.location:
            return
        entry = knowledge_entry(self.civilization, knowledge_id)
        if (
            entry is None
            or entry.action_id != PEER_TRAIN_ACTION_ID
            or affordance_definition(
                self.civilization,
                PEER_TRAIN_ACTION_ID,
            ) != PEER_TRAIN_AFFORDANCE
        ):
            return
        ready = self.school.observe_peer_training(
            SchoolKnowledgeEvidence(
                day=self.day,
                knowledge_id=knowledge_id,
                teacher_id=teacher.id,
                learner_id=learner.id,
                teacher_event_index=teacher_event_index,
            )
        )
        if not ready:
            return

        origin = f"{entry.origin_agent_id}:{entry.origin_event_index}"
        adoption_event_index = self.record(
            teacher,
            "institution_adoption",
            (
                f"School adopted {knowledge_id} after "
                f"{SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD} "
                f"successful-use observations; origin: {origin}"
            ),
            0.85,
            target_id=SCHOOL_SOURCE_ID,
            location=self.school.location,
        )
        self.school.knowledge_adoption = SchoolKnowledgeAdoption(
            day=self.day,
            knowledge_id=knowledge_id,
            action_id=entry.action_id,
            origin_agent_id=entry.origin_agent_id,
            origin_event_index=entry.origin_event_index,
            evidence_count=len(self.school.knowledge_evidence),
            adoption_agent_id=teacher.id,
            adoption_event_index=adoption_event_index,
        )

    def _observe_participation(
        self,
        observer: Agent,
        subject: Agent,
        location: str,
    ) -> Observation | None:
        participation_day = recent_participation_day(
            subject,
            self.day,
        )
        if participation_day is None:
            return None

        information_id = participation_information_id(
            subject.id,
            participation_day,
        )
        if information_id in self._information_seen[observer.id]:
            return None

        observation = Observation(
            day=self.day,
            kind=PARTICIPATION_STATUS,
            subject_id=subject.id,
            value=PARTICIPATED,
            source_id=subject.id,
            reliability=1.0,
            location=location,
            information_id=information_id,
            origin_agent_id=subject.id,
            origin_day=participation_day,
            hop_count=0,
        )
        receive_observation(observer, observation)
        self._information_seen[observer.id].add(information_id)
        self._information_observation_counts[observer.id] = len(
            observer.observations
        )
        return observation

    def _observe_employment(
        self,
        observer: Agent,
        subject: Agent,
        location: str,
    ) -> Observation | None:
        value = employment_status(subject.employed)
        current = observer.beliefs.get(
            belief_key(EMPLOYMENT_STATUS, subject.id)
        )
        if (
            current is not None
            and current.value == value
            and current.confidence >= 1.0
        ):
            return None

        information_id = employment_information_id(
            subject.id,
            self.day,
            value,
        )
        observation = Observation(
            day=self.day,
            kind=EMPLOYMENT_STATUS,
            subject_id=subject.id,
            value=value,
            source_id=subject.id,
            reliability=1.0,
            location=location,
            information_id=information_id,
            origin_agent_id=subject.id,
            origin_day=self.day,
            hop_count=0,
        )
        receive_observation(observer, observation)
        self._information_seen[observer.id].add(information_id)
        self._latest_information[observer.id][subject.id] = observation
        self._information_observation_counts[observer.id] = len(
            observer.observations
        )
        return observation

    def _transmit_testimony(
        self,
        source: Agent,
        recipient: Agent,
        location: str,
    ) -> InformationItem | None:
        self._ensure_information_index(source)
        self._ensure_information_index(recipient)
        item = select_testimony(
            source,
            recipient,
            day=self.day,
            relationship=self.social.get_relationship(
                recipient.id,
                source.id,
            ),
            recipient_evidence=self._information_seen[recipient.id],
            source_information=(
                self._latest_information[source.id].values()
            ),
        )
        if item is None:
            return None

        if item.id not in self._information_item_ids:
            self.information_items.append(item)
            self._information_item_ids.add(item.id)

        receive_observation(
            recipient,
            Observation(
                day=self.day,
                kind=item.kind,
                subject_id=item.subject_id,
                value=item.value,
                source_id=source.id,
                reliability=item.reliability,
                location=location,
                information_id=item.id,
                origin_agent_id=item.origin_agent_id,
                origin_day=item.origin_day,
                hop_count=item.hop_count,
            ),
        )
        self._information_seen[recipient.id].add(item.id)
        self._latest_information[recipient.id][item.subject_id] = (
            recipient.observations[-1]
        )
        self._information_observation_counts[recipient.id] = len(
            recipient.observations
        )

        description = (
            f"Shared {item.id} with {recipient.name}: "
            f"{item.subject_id} is {item.value}"
        )
        self.record(
            source,
            "testimony",
            description,
            item.reliability,
            target_id=recipient.id,
            location=location,
        )
        self.record(
            recipient,
            "testimony",
            (
                f"Received {item.id} from {source.name}: "
                f"{item.subject_id} is {item.value}"
            ),
            item.reliability,
            target_id=source.id,
            location=location,
        )
        return item

    def sync_social_affinities(self) -> None:
        """Mirror authoritative Agent affinity into the social graph."""
        for agent in self.agents:
            for target_id, affinity in agent.relationships.items():
                relationship = self.social.get_relationship(
                    agent.id,
                    target_id,
                )
                current = relationship["affinity"]

                if current != affinity:
                    self.social.set_affinity(
                        agent.id,
                        target_id,
                        affinity,
                    )

    def exposed_people(self, a: Agent) -> list[Agent]:
        target_ids = set()
        active_agents = [
            agent
            for agent in self.agents
            if agent.lifecycle.alive and not agent.family.dependent
        ]

        for exposure in detect_exposures(active_agents):
            if exposure.agent_a == a.id:
                target_ids.add(exposure.agent_b)
            elif exposure.agent_b == a.id:
                target_ids.add(exposure.agent_a)

        return [
            agent
            for agent in self.agents
            if agent.id in target_ids
        ]

    def other_person(
        self,
        a: Agent,
        candidates: list[Agent] | None = None,
    ) -> Agent | None:
        others = candidates

        if others is None:
            others = [
                b
                for b in self.agents
                if (
                    b.id != a.id
                    and b.lifecycle.alive
                    and not b.family.dependent
                )
            ]
        else:
            others = [
                other
                for other in others
                if other.lifecycle.alive and not other.family.dependent
            ]

        if not others:
            return None

        weights = [
            0.25 + abs(a.relationships[b.id])
            for b in others
        ]

        return self.rng.choices(
            others,
            weights=weights,
            k=1,
        )[0]

    def relationship_target(self, a: Agent) -> Agent | None:
        familiar = []

        for other in self.exposed_people(a):
            outward = self.social.get_relationship(
                a.id,
                other.id,
            )["familiarity"]
            inward = self.social.get_relationship(
                other.id,
                a.id,
            )["familiarity"]

            if min(outward, inward) >= MIN_RELATIONSHIP_FAMILIARITY:
                familiar.append(other)

        return self.other_person(a, familiar)

    def visit_target(
        self,
        a: Agent,
        action: str,
    ) -> Agent | None:
        if action not in {"socialize", "help"}:
            return None

        candidates = []

        for other in self.agents:
            if (
                other.id == a.id
                or not other.lifecycle.alive
                or other.family.dependent
            ):
                continue

            if self.believed_location(a, other) is None:
                continue

            outward = self.social.get_relationship(a.id, other.id)
            inward = self.social.get_relationship(other.id, a.id)

            if (
                min(
                    outward["familiarity"],
                    inward["familiarity"],
                ) < MIN_VISIT_FAMILIARITY
            ):
                continue

            if (
                min(
                    outward["affinity"],
                    inward["affinity"],
                ) < MIN_VISIT_AFFINITY
            ):
                continue

            score = (
                outward["familiarity"]
                + inward["familiarity"]
                + outward["affinity"]
                + inward["affinity"]
            )
            candidates.append((score, other))

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda candidate: candidate[0],
        )[1]

    def believed_location(
        self,
        observer: Agent,
        subject: Agent,
    ) -> str | None:
        belief = observer.beliefs.get(
            belief_key(
                "agent_location",
                subject.id,
            )
        )

        if belief is None or belief.confidence <= 0.0:
            return None

        if belief.value not in self.world_map.locations:
            return None

        return belief.value

    def act(
        self,
        a: Agent,
        action: str,
    ) -> None:
        if a.family.dependent or not a.lifecycle.alive:
            return
        if a.lifecycle.retired and action in {"work", "job_hunt"}:
            return

        participation = None
        if action == "participate":
            participation = self.participation_pressure(a)
            if (
                not participation.eligible
                or a.current_location != "park"
            ):
                a.normalize()
                return

        peer_learner = None
        peer_training = None
        if action == "peer_train":
            peer_learner = self.peer_training_target(a)
            if peer_learner is None:
                a.normalize()
                return
            peer_training = self.peer_training_eligibility(
                a.id,
                peer_learner.id,
            )
            if not peer_training.eligible:
                a.normalize()
                return

        a.actions[action] += 1

        if action == "work":
            a.money += a.salary * 0.25
            a.energy -= 0.11

            a.stress += (
                0.025
                + 0.035 * a.sins["wrath"]
            )

            a.skill += (
                0.0025
                * (
                    0.5
                    + a.traits["discipline"]
                )
            )

            a.reputation += (
                0.002
                * (
                    a.traits["discipline"]
                    - a.sins["sloth"]
                )
            )

            promotion = (
                0.0012
                + 0.003 * a.skill
                + 0.002 * a.traits["ambition"]
                + 0.0015 * max(0, a.reputation)
            )

            fired = (
                0.0005
                + 0.0018 * a.stress
                + 0.0015 * a.sins["wrath"]
                - 0.001 * a.traits["discipline"]
            )

            if (
                self.rng.random()
                < max(0, promotion)
                and a.job_level < 5
            ):
                a.job_level += 1
                a.salary *= 1.18
                a.reputation += 0.10

                self.record(
                    a,
                    "career",
                    f"Promoted to job level {a.job_level}",
                    0.92,
                )

            elif self.rng.random() < max(0, fired):
                a.employed = False
                a.job_level = 0
                a.salary = 0
                a.stress += 0.22

                self.record(
                    a,
                    "career",
                    "Lost their job",
                    0.96,
                )

        elif action == "job_hunt":
            a.money -= 4
            a.energy -= 0.07
            a.stress += 0.025

            chance = (
                0.04
                + 0.14 * a.skill
                + 0.05 * max(0, a.reputation)
                + 0.04 * a.traits["sociability"]
            )

            vacancies_before = self.economy.vacancies(
                self.agents
            )
            roll = self.rng.random()

            if vacancies_before > 0 and roll < chance:
                a.employed = True
                a.job_level = 1

                a.salary = (
                    24
                    + 9 * a.skill
                    + 4 * a.reputation
                )

                a.stress -= 0.15

                self.record(
                    a,
                    "career",
                    (
                        f"Found a job paying {a.salary:.0f}/day; "
                        f"vacancies before: {vacancies_before}; "
                        f"chance: {chance:.4f}; roll: {roll:.4f}"
                    ),
                    0.94,
                )
            else:
                reason = (
                    "no vacancy"
                    if vacancies_before <= 0
                    else "selection roll"
                )
                self.record(
                    a,
                    "career",
                    (
                        f"Job hunt failed: {reason}; "
                        f"vacancies before: {vacancies_before}; "
                        f"chance: {chance:.4f}; roll: {roll:.4f}"
                    ),
                    0.35,
                )

        elif action == "train":
            if a.current_location != self.school.location:
                self._record_training_denial(
                    a,
                    (
                        "School denied training: agent is "
                        f"not at school; current location: "
                        f"{a.current_location}"
                    ),
                    0.25,
                    reason="not_at_school",
                    location=a.current_location,
                )
                a.normalize()
                return

            admission_slot = self.school.admit_training(self.day)
            if admission_slot is None:
                self._record_training_denial(
                    a,
                    (
                        "School denied training: daily capacity "
                        f"{self.school.daily_training_capacity} "
                        "exhausted"
                    ),
                    0.35,
                    reason="capacity_exhausted",
                    location=self.school.location,
                )
                a.normalize()
                return

            admission_event_index = self.record(
                a,
                "institution",
                (
                    f"School admitted training slot {admission_slot} "
                    f"of {self.school.daily_training_capacity}"
                ),
                0.30,
                location=self.school.location,
            )
            a.discovery = record_primitive_exposure(
                a.discovery,
                agent_id=a.id,
                day=self.day,
                event_index=admission_event_index,
            )
            before = a.skill

            a.money -= 7
            a.energy -= 0.08
            a.stress += 0.015

            a.skill += (
                0.009
                + 0.006
                * a.traits["discipline"]
            )

            if before < 0.60 <= a.skill:
                self.record(
                    a,
                    "growth",
                    "Reached skilled-worker level",
                    0.80,
                )

            if before < 0.75 <= a.skill:
                self.record(
                    a,
                    "growth",
                    "Reached expert-skill level",
                    0.86,
                )

        elif action == "peer_train":
            affordance = affordance_definition(
                self.civilization,
                action,
            )
            if (
                peer_learner is None
                or peer_training is None
                or affordance is None
            ):
                raise RuntimeError("Peer-training eligibility drifted.")
            learner_before = capture_state(peer_learner)
            participants = {
                "teacher": a,
                "learner": peer_learner,
            }
            for effect in affordance.costs:
                target = participants[effect.target]
                if effect.operation == "consume_energy":
                    target.energy -= effect.amount
                elif effect.operation == "spend_money":
                    target.money -= effect.amount
                elif effect.operation == "increase_stress":
                    target.stress += effect.amount
                else:
                    raise RuntimeError("Unsupported peer-training cost.")
            for effect in affordance.effects:
                target = participants[effect.target]
                if effect.operation == "increase_skill":
                    target.skill += effect.amount
                else:
                    raise RuntimeError("Unsupported peer-training effect.")
            a.normalize()
            peer_learner.normalize()
            parent = (
                f"{peer_training.knowledge_parent_agent_id}:"
                f"{peer_training.knowledge_parent_event_index}"
            )
            variant = peer_training.variant_id or "original"
            teacher_event_index = self.record(
                a,
                "peer_training",
                (
                    f"Peer-trained {peer_learner.name}; knowledge: "
                    f"{peer_training.knowledge_id}; adoption parent: "
                    f"{parent}; variant: {variant}"
                ),
                0.60,
                target_id=peer_learner.id,
                location=a.current_location,
            )
            self.record(
                peer_learner,
                "peer_training",
                (
                    f"Learned from {a.name}; knowledge: "
                    f"{peer_training.knowledge_id}; teacher adoption "
                    f"parent: {parent}; variant: {variant}"
                ),
                0.60,
                target_id=a.id,
                location=peer_learner.current_location,
            )
            self._observe_school_peer_training(
                a,
                peer_learner,
                knowledge_id=peer_training.knowledge_id,
                teacher_event_index=teacher_event_index,
            )
            if self.adaptive_cognition:
                learn(
                    peer_learner,
                    "improve_skill",
                    "train",
                    consequence_between(
                        learner_before,
                        capture_state(peer_learner),
                    ),
                )

        elif action == "socialize":
            b = self.relationship_target(a)

            a.money -= 5
            a.social_energy -= 0.06
            a.stress -= 0.035

            if b is None:
                a.normalize()
                return

            before = a.relationships[b.id]

            change = (
                0.06 * a.traits["sociability"]
                + 0.05 * a.traits["empathy"]
                - 0.05 * a.sins["wrath"]
                - 0.03 * a.sins["envy"]
                + self.rng.uniform(-0.055, 0.055)
            )

            a.relationships[b.id] += change

            b.relationships[a.id] += (
                change
                * self.rng.uniform(0.65, 1.05)
            )

            after = a.relationships[b.id]

            if before < 0.42 <= after:
                self.record(
                    a,
                    "relationship",
                    f"Became close with {b.name}",
                    0.84,
                )

            elif before > -0.42 >= after:
                self.record(
                    a,
                    "relationship",
                    (
                        f"Relationship with "
                        f"{b.name} turned hostile"
                    ),
                    0.86,
                )

        elif action == "help":
            b = self.relationship_target(a)

            if b is None:
                a.normalize()
                return

            cost = min(
                10,
                max(
                    2,
                    a.money * 0.025,
                ),
            )

            before = a.relationships[b.id]

            gain = (
                0.035
                + 0.045
                * a.traits["empathy"]
            )

            a.money -= cost
            b.money += cost * 0.65

            a.relationships[b.id] += gain
            b.relationships[a.id] += gain * 1.1
            self.social.apply_social_event(
                a.id,
                b.id,
                "help",
            )

            a.reputation += 0.012
            a.social_energy -= 0.045

            self.record(
                b,
                "support",
                f"Received material help from {a.name}",
                0.55,
                target_id=a.id,
                location=a.current_location,
            )

            if before < 0.42 <= a.relationships[b.id]:
                self.record(
                    a,
                    "relationship",
                    (
                        f"Helping {b.name} "
                        f"created a close alliance"
                    ),
                    0.84,
                )

        elif action == "compete":
            b = self.relationship_target(a)

            if b is None:
                a.normalize()
                return

            edge = (
                a.skill
                + 0.4 * a.traits["ambition"]
                + self.rng.uniform(-0.35, 0.35)
                - (
                    b.skill
                    + 0.2 * b.traits["ambition"]
                )
            )

            a.relationships[b.id] -= (
                0.025
                + 0.035 * a.sins["envy"]
            )

            b.relationships[a.id] -= (
                0.020
                + 0.025 * b.sins["pride"]
            )

            a.energy -= 0.07
            a.social_energy -= 0.04
            a.stress += 0.05

            if edge > 0:
                a.reputation += 0.025
                a.money += 12

                if edge > 0.48:
                    self.record(
                        a,
                        "status",
                        (
                            f"Outperformed "
                            f"{b.name} in competition"
                        ),
                        0.72,
                    )

            else:
                a.reputation -= 0.018
                a.stress += 0.035

                if edge < -0.48:
                    self.record(
                        a,
                        "status",
                        (
                            f"Lost badly to "
                            f"{b.name} in competition"
                        ),
                        0.72,
                    )

        elif action == "risky_move":
            a.energy -= 0.05

            chance = (
                0.28
                + 0.24
                * a.traits["risk_tolerance"]
                + 0.18 * a.skill
                - 0.10 * a.stress
            )

            if self.rng.random() < chance:
                gain = (
                    self.rng.uniform(25, 90)
                    * (
                        0.7
                        + a.sins["greed"]
                    )
                )

                a.money += gain
                a.stress -= 0.025
                a.reputation += 0.01

                if gain > 110:
                    self.record(
                        a,
                        "fortune",
                        (
                            f"A risky move "
                            f"paid off: +{gain:.0f}"
                        ),
                        0.80,
                    )

            else:
                loss = self.rng.uniform(18, 65)

                a.money -= loss
                a.stress += 0.08

                if loss > 60:
                    self.record(
                        a,
                        "misfortune",
                        (
                            f"A risky move "
                            f"failed: -{loss:.0f}"
                        ),
                        0.78,
                    )

        elif action == "pray":
            if a.current_location == "shrine":
                prayer = create_prayer(a, self.day)
                a.prayers.append(prayer)
                a.energy -= 0.02
                a.stress -= 0.04

                self.record(
                    a,
                    "prayer",
                    (
                        f"Prayed for {prayer.desire_type} "
                        f"with intensity {prayer.intensity:.2f}"
                    ),
                    prayer.intensity,
                    location="shrine",
                )

        elif action == "participate":
            a.energy -= 0.05
            a.social_energy -= 0.04
            a.stress -= 0.02
            (
                social_evidence_ids,
                trusted_evidence_ids,
                influencer_ids,
            ) = participation_provenance(
                a,
                self.social,
                self.day,
            )

            # ponytail: the event is already durable; add a table only if
            # provenance later needs independent queries.
            def recorded(values: tuple[str, ...]) -> str:
                return ",".join(values) or "-"

            self.record(
                a,
                "participation",
                (
                    "Joined the public gathering; "
                    f"score: {participation.score:.3f}; "
                    f"threshold: {participation.threshold:.3f}; "
                    "personal: "
                    f"{participation.personal_pressure:.3f}; "
                    "confirmation: "
                    f"{participation.social_confirmation:.3f}; "
                    "trusted information: "
                    f"{participation.trusted_information:.3f}; "
                    "social motivation: "
                    f"{participation.social_motivation:.3f}; "
                    f"cost: {participation.perceived_cost:.3f}; "
                    f"risk aversion: {participation.risk_aversion:.3f}; "
                    f"influencers: {recorded(influencer_ids)}; "
                    "social evidence ids: "
                    f"{recorded(social_evidence_ids)}; "
                    "trusted information evidence ids: "
                    f"{recorded(trusted_evidence_ids)}"
                ),
                0.68,
                location="park",
            )

        elif action == "rest":
            a.money -= 3
            a.energy += 0.22
            a.social_energy += 0.22
            a.stress -= 0.11

        a.normalize()

    def end_day(self, a: Agent) -> None:
        if a.family.dependent or not a.lifecycle.alive:
            return

        # Employment is a background condition.
        # The selected action is the person's main
        # discretionary focus for this simulated day.
        if a.employed:
            a.money += a.salary * 0.85

        a.money -= 24

        if not a.employed:
            a.stress += (
                0.018
                + 0.025
                * money_pressure(a)
            )

        if a.money < 0:
            a.stress += 0.055
            a.reputation -= 0.006

        if (
            a.money < -250
            and not any(
                e.kind == "crisis"
                for e in islice(
                    (
                        event
                        for event in reversed(a.events)
                        if event.kind not in {
                            "travel",
                            "interaction",
                        }
                    ),
                    30,
                )
            )
        ):
            self.record(
                a,
                "crisis",
                "Entered severe debt",
                0.90,
            )

        # Small external shock.
        if (
            a.employed
            and self.rng.random() < 0.0008
        ):
            a.employed = False
            a.job_level = 0
            a.salary = 0
            a.stress += 0.20

            self.record(
                a,
                "career",
                "Lost job in workplace downsizing",
                0.95,
            )

        a.energy += 0.035
        a.social_energy += 0.035
        a.stress -= 0.012

        a.normalize()
        self.update_goal(a)

    def run(self, days: int = 365) -> None:
        """
        Advance the existing world by `days`.

        Fresh-world behavior remains identical to Phase 1.

        Unlike Phase 1, repeated calls continue from the
        current simulated day instead of restarting at Day 1.
        """
        start_day = self.day
        target_day = start_day + days

        for day in range(
            start_day + 1,
            target_day + 1,
        ):
            self.day = day
            self.resolve_interventions()

            order = [
                agent
                for agent in self.agents
                if agent.lifecycle.alive and not agent.family.dependent
            ]
            self.rng.shuffle(order)

            for a in order:
                self.update_goal(a)

                participation = self.participation_pressure(a)
                learning_context = (
                    context_for(a)
                    if self.adaptive_cognition
                    else None
                )
                before_action = (
                    capture_state(a)
                    if learning_context is not None
                    else None
                )

                action = choose(
                    a,
                    self.rng,
                    score_adjustments=(
                        self.intervention_action_adjustments(a)
                    ),
                    participation_utility=(
                        participation.score
                        if participation.eligible
                        else None
                    ),
                    peer_training_utility=(
                        self.peer_training_utility(a)
                    ),
                    learned_preferences=(
                        learned_preferences(a, learning_context)
                        if learning_context is not None
                        else None
                    ),
                )

                self.move_for_action(
                    a,
                    action,
                )

                self.act(
                    a,
                    action,
                )

                if (
                    learning_context is not None
                    and before_action is not None
                ):
                    learn(
                        a,
                        learning_context,
                        action,
                        consequence_between(
                            before_action,
                            capture_state(a),
                        ),
                    )

                self.end_day(a)

            self.sync_social_affinities()
            self.resolve_daily_interactions()
            self.resolve_reproduction()
            self.resolve_development()
            self.resolve_lifecycle()
            self.resolve_daily_attributions()

        # Preserve Phase-1 aging for uninterrupted runs,
        # while also making split runs equivalent.
        birthdays_crossed = (
            target_day // 365
            - start_day // 365
        )

        if birthdays_crossed and not self.lifecycle_enabled:
            for a in self.agents:
                if a.family.birth_day is None:
                    a.age += birthdays_crossed

    def report(self) -> str:
        names = {
            a.id: a.name
            for a in self.agents
        }

        lines = [
            (
                f"THE PLAYING GOD | "
                f"seed={self.seed} | "
                f"day={self.day}"
            ),
            "=" * 74,
        ]

        for a in self.agents:
            if not a.lifecycle.alive:
                livelihood = "deceased"
            elif a.lifecycle.retired:
                livelihood = "retired"
            elif a.employed:
                livelihood = "L" + str(a.job_level)
            else:
                livelihood = "unemployed"
            best = max(
                a.relationships.items(),
                key=lambda x: x[1],
            )

            worst = min(
                a.relationships.items(),
                key=lambda x: x[1],
            )

            major = [
                e
                for e in a.events
                if e.significance >= 0.78
            ]

            major = sorted(
                major,
                key=lambda e: (
                    e.significance,
                    e.day,
                ),
                reverse=True,
            )[:8]

            major = sorted(
                major,
                key=lambda e: e.day,
            )

            behavior = ", ".join(
                f"{k}:{v}"
                for k, v
                in a.actions.most_common(3)
            )

            lines += [
                "",
                (
                    f"{a.id} | "
                    f"{a.name} | "
                    f"age {a.age}"
                ),
                (
                    f"  job="
                    f"{livelihood}"
                    f"  money={a.money:.0f}"
                    f"  skill={a.skill:.2f}"
                    f"  stress={a.stress:.2f}"
                ),
                (
                    f"  reputation="
                    f"{a.reputation:+.2f}"
                    f"  goal={a.goal}"
                ),
                (
                    f"  dominant behavior: "
                    f"{behavior}"
                ),
                (
                    f"  strongest tie: "
                    f"{names[best[0]]} "
                    f"{best[1]:+.2f}"
                    f" | weakest: "
                    f"{names[worst[0]]} "
                    f"{worst[1]:+.2f}"
                ),
                "  major life events:",
            ]

            if major:
                lines += [
                    (
                        f"    day {e.day:03d} "
                        f"[{e.kind}] "
                        f"{e.description}"
                    )
                    for e in major
                ]

            else:
                lines.append(
                    "    none above threshold"
                )

        return "\n".join(lines)
