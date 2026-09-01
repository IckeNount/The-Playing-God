from __future__ import annotations

from itertools import islice

from playing_god.core.adaptive import (
    capture_state,
    consequence_between,
    context_for,
    learn,
    learned_preferences,
)
from playing_god.core.agent import Agent, NAMES, SINS, TRAITS
from playing_god.core.decision import (
    belonging_need,
    choose,
    money_pressure,
    scores as decision_scores,
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
from playing_god.core.economy import EconomySnapshot, EconomyState
from playing_god.core.events import Event
from playing_god.core.exposure import (
    Interaction,
    detect_exposures,
    resolve_interactions,
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
from playing_god.core.institution import SchoolSnapshot, SchoolState
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
    belief_key,
    receive_observation,
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
    ):
        self.seed = seed
        self.rng = create_rng(seed)
        self.day = 0
        self.adaptive_cognition = adaptive_cognition
        self.interventions: list[Intervention] = []
        self.intervention_responses: list[
            InterventionResponse
        ] = []
        self.information_items: list[InformationItem] = []

        self.agents = self._create_agents(population)
        self.economy = EconomyState.from_agents(self.agents)
        self.school = SchoolState()
        self._create_relationships()
        self.rebuild_social_graph()
        self.rebuild_spatial_map()
        self.rebuild_information_index()

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
        return self.economy.snapshot(self.agents)

    def school_snapshot(self) -> SchoolSnapshot:
        return self.school.snapshot(self.day)

    def diffusion_snapshot(
        self,
        information_id: str,
    ) -> DiffusionSnapshot:
        return diffusion_snapshot(
            self.agents,
            information_id,
        )

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
        return build_collective_snapshot(self.agents)

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
    ) -> None:
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

    def update_goal(self, a: Agent) -> None:
        if not a.employed:
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
        self.last_exposures = detect_exposures(self.agents)

        agents_by_id = {
            agent.id: agent
            for agent in self.agents
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

        for exposure in detect_exposures(self.agents):
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
                if b.id != a.id
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
            if other.id == a.id:
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
        participation = None
        if action == "participate":
            participation = self.participation_pressure(a)
            if (
                not participation.eligible
                or a.current_location != "park"
            ):
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
                self.record(
                    a,
                    "institution",
                    (
                        "School denied training: agent is "
                        f"not at school; current location: "
                        f"{a.current_location}"
                    ),
                    0.25,
                    location=a.current_location,
                )
                a.normalize()
                return

            admission_slot = self.school.admit_training(self.day)
            if admission_slot is None:
                self.record(
                    a,
                    "institution",
                    (
                        "School denied training: daily capacity "
                        f"{self.school.daily_training_capacity} "
                        "exhausted"
                    ),
                    0.35,
                    location=self.school.location,
                )
                a.normalize()
                return

            self.record(
                a,
                "institution",
                (
                    f"School admitted training slot {admission_slot} "
                    f"of {self.school.daily_training_capacity}"
                ),
                0.30,
                location=self.school.location,
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

            order = self.agents[:]
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
            self.resolve_daily_attributions()

        # Preserve Phase-1 aging for uninterrupted runs,
        # while also making split runs equivalent.
        birthdays_crossed = (
            target_day // 365
            - start_day // 365
        )

        if birthdays_crossed:
            for a in self.agents:
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
                    f"{'L' + str(a.job_level) if a.employed else 'unemployed'}"
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
