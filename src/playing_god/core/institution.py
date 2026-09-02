from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from playing_god.core.culture import SCHOOL_SOURCE_ID


SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD = 3


@dataclass(frozen=True)
class SchoolKnowledgeEvidence:
    day: int
    knowledge_id: str
    teacher_id: str
    learner_id: str
    teacher_event_index: int


@dataclass(frozen=True)
class SchoolKnowledgeAdoption:
    day: int
    knowledge_id: str
    action_id: str
    origin_agent_id: str
    origin_event_index: int
    evidence_count: int
    adoption_agent_id: str
    adoption_event_index: int


@dataclass(frozen=True)
class SchoolSnapshot:
    location: str
    day: int
    daily_training_capacity: int
    admissions_used: int
    remaining_capacity: int
    knowledge_evidence_count: int = 0
    adopted_knowledge_id: str | None = None
    knowledge_adoption_day: int | None = None


@dataclass
class SchoolState:
    """One concrete institution with a daily training limit."""

    location: ClassVar[str] = "school"
    daily_training_capacity: ClassVar[int] = 1
    current_day: int | None = field(default=None, init=False)
    admissions_used: int = field(default=0, init=False)
    knowledge_evidence: tuple[SchoolKnowledgeEvidence, ...] = ()
    knowledge_adoption: SchoolKnowledgeAdoption | None = None

    def start_day(self, day: int) -> None:
        if day != self.current_day:
            self.current_day = day
            self.admissions_used = 0

    def admit_training(self, day: int) -> int | None:
        """Return the admitted slot number, or None when full."""
        self.start_day(day)
        if self.admissions_used >= self.daily_training_capacity:
            return None

        self.admissions_used += 1
        return self.admissions_used

    def snapshot(self, day: int) -> SchoolSnapshot:
        admissions_used = (
            self.admissions_used
            if self.current_day == day
            else 0
        )
        return SchoolSnapshot(
            location=self.location,
            day=day,
            daily_training_capacity=self.daily_training_capacity,
            admissions_used=admissions_used,
            remaining_capacity=(
                self.daily_training_capacity - admissions_used
            ),
            knowledge_evidence_count=len(self.knowledge_evidence),
            adopted_knowledge_id=(
                self.knowledge_adoption.knowledge_id
                if self.knowledge_adoption is not None
                else None
            ),
            knowledge_adoption_day=(
                self.knowledge_adoption.day
                if self.knowledge_adoption is not None
                else None
            ),
        )

    def observe_peer_training(
        self,
        evidence: SchoolKnowledgeEvidence,
    ) -> bool:
        """Retain at most one successful-use observation per day."""
        if self.knowledge_adoption is not None:
            return False
        if any(
            item.day == evidence.day
            for item in self.knowledge_evidence
        ):
            return False
        self.knowledge_evidence += (evidence,)
        return (
            len(self.knowledge_evidence)
            >= SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD
        )


def school_state_to_data(state: SchoolState) -> dict[str, object]:
    return {
        "knowledge_evidence": [
            {
                "day": item.day,
                "knowledge_id": item.knowledge_id,
                "teacher_id": item.teacher_id,
                "learner_id": item.learner_id,
                "teacher_event_index": item.teacher_event_index,
            }
            for item in state.knowledge_evidence
        ],
        "knowledge_adoption": (
            None
            if state.knowledge_adoption is None
            else {
                "day": state.knowledge_adoption.day,
                "knowledge_id": state.knowledge_adoption.knowledge_id,
                "action_id": state.knowledge_adoption.action_id,
                "origin_agent_id": (
                    state.knowledge_adoption.origin_agent_id
                ),
                "origin_event_index": (
                    state.knowledge_adoption.origin_event_index
                ),
                "evidence_count": (
                    state.knowledge_adoption.evidence_count
                ),
                "adoption_agent_id": (
                    state.knowledge_adoption.adoption_agent_id
                ),
                "adoption_event_index": (
                    state.knowledge_adoption.adoption_event_index
                ),
            }
        ),
    }


def school_state_from_data(data: object) -> SchoolState:
    if not isinstance(data, dict) or set(data) != {
        "knowledge_evidence",
        "knowledge_adoption",
    }:
        raise ValueError("Invalid school state structure.")
    if not isinstance(data["knowledge_evidence"], list):
        raise ValueError("Invalid school evidence structure.")

    evidence_fields = set(SchoolKnowledgeEvidence.__dataclass_fields__)
    evidence = []
    for item in data["knowledge_evidence"]:
        if not isinstance(item, dict) or set(item) != evidence_fields:
            raise ValueError("Invalid school evidence record.")
        evidence.append(SchoolKnowledgeEvidence(**item))

    adoption_data = data["knowledge_adoption"]
    adoption = None
    if adoption_data is not None:
        adoption_fields = set(SchoolKnowledgeAdoption.__dataclass_fields__)
        if (
            not isinstance(adoption_data, dict)
            or set(adoption_data) != adoption_fields
        ):
            raise ValueError("Invalid school adoption record.")
        adoption = SchoolKnowledgeAdoption(**adoption_data)

    state = SchoolState(
        knowledge_evidence=tuple(evidence),
        knowledge_adoption=adoption,
    )
    validate_school_state(state)
    return state


def validate_school_state(state: SchoolState) -> None:
    if (
        not isinstance(state, SchoolState)
        or not isinstance(state.knowledge_evidence, tuple)
        or not all(
            isinstance(item, SchoolKnowledgeEvidence)
            for item in state.knowledge_evidence
        )
    ):
        raise ValueError("Invalid school state.")
    if state.knowledge_evidence != tuple(sorted(
        state.knowledge_evidence,
        key=lambda item: item.day,
    )):
        raise ValueError("School evidence is unordered.")
    if len({item.day for item in state.knowledge_evidence}) != len(
        state.knowledge_evidence
    ):
        raise ValueError("Duplicate school evidence day.")
    for item in state.knowledge_evidence:
        if (
            isinstance(item.day, bool)
            or not isinstance(item.day, int)
            or item.day < 0
            or not isinstance(item.knowledge_id, str)
            or not item.knowledge_id
            or not isinstance(item.teacher_id, str)
            or not item.teacher_id
            or not isinstance(item.learner_id, str)
            or not item.learner_id
            or item.teacher_id == item.learner_id
            or isinstance(item.teacher_event_index, bool)
            or not isinstance(item.teacher_event_index, int)
            or item.teacher_event_index < 0
        ):
            raise ValueError("Invalid school evidence values.")

    adoption = state.knowledge_adoption
    if adoption is None:
        if len(state.knowledge_evidence) >= (
            SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD
        ):
            raise ValueError("School omitted required adoption.")
        return
    if (
        isinstance(adoption.day, bool)
        or not isinstance(adoption.day, int)
        or adoption.day < 0
        or not isinstance(adoption.knowledge_id, str)
        or not adoption.knowledge_id
        or not isinstance(adoption.action_id, str)
        or not adoption.action_id
        or not isinstance(adoption.origin_agent_id, str)
        or not adoption.origin_agent_id
        or isinstance(adoption.origin_event_index, bool)
        or not isinstance(adoption.origin_event_index, int)
        or adoption.origin_event_index < 0
        or adoption.evidence_count
        != SCHOOL_KNOWLEDGE_EVIDENCE_THRESHOLD
        or not isinstance(adoption.adoption_agent_id, str)
        or not adoption.adoption_agent_id
        or isinstance(adoption.adoption_event_index, bool)
        or not isinstance(adoption.adoption_event_index, int)
        or adoption.adoption_event_index < 0
        or len(state.knowledge_evidence) != adoption.evidence_count
        or adoption.day != state.knowledge_evidence[-1].day
        or any(
            item.knowledge_id != adoption.knowledge_id
            for item in state.knowledge_evidence
        )
    ):
        raise ValueError("Invalid school adoption values.")


def validate_school_links(
    state: SchoolState,
    civilization,
    agents,
    *,
    current_day: int,
) -> None:
    from playing_god.core.civilization import (
        PEER_TRAIN_ACTION_ID,
        PEER_TRAIN_AFFORDANCE,
        affordance_definition,
        knowledge_entry,
    )

    validate_school_state(state)
    agents_by_id = {agent.id: agent for agent in agents}
    for item in state.knowledge_evidence:
        entry = knowledge_entry(civilization, item.knowledge_id)
        teacher = agents_by_id.get(item.teacher_id)
        learner = agents_by_id.get(item.learner_id)
        if (
            entry is None
            or entry.action_id != PEER_TRAIN_ACTION_ID
            or affordance_definition(
                civilization,
                PEER_TRAIN_ACTION_ID,
            ) != PEER_TRAIN_AFFORDANCE
            or teacher is None
            or learner is None
            or item.day < entry.creation_day
            or item.day > current_day
            or item.teacher_event_index >= len(teacher.events)
            or not any(
                record.knowledge_id == item.knowledge_id
                and record.response in {"accept", "modify"}
                and record.day <= item.day
                for record in teacher.knowledge.records
            )
        ):
            raise ValueError("Invalid school evidence link.")
        event = teacher.events[item.teacher_event_index]
        if (
            event.day != item.day
            or event.kind != "peer_training"
            or event.target_id != learner.id
            or event.location != state.location
            or item.knowledge_id not in event.description
        ):
            raise ValueError("Invalid school evidence event.")

    adoption = state.knowledge_adoption
    if adoption is None:
        return
    entry = knowledge_entry(civilization, adoption.knowledge_id)
    adopter = agents_by_id.get(adoption.adoption_agent_id)
    if (
        entry is None
        or adoption.action_id != entry.action_id
        or adoption.origin_agent_id != entry.origin_agent_id
        or adoption.origin_event_index != entry.origin_event_index
        or adoption.day > current_day
        or adopter is None
        or adoption.adoption_event_index >= len(adopter.events)
        or adopter.id != state.knowledge_evidence[-1].teacher_id
    ):
        raise ValueError("Invalid school adoption link.")
    event = adopter.events[adoption.adoption_event_index]
    origin = f"{entry.origin_agent_id}:{entry.origin_event_index}"
    if (
        event.day != adoption.day
        or event.kind != "institution_adoption"
        or event.target_id != SCHOOL_SOURCE_ID
        or event.location != state.location
        or adoption.knowledge_id not in event.description
        or origin not in event.description
    ):
        raise ValueError("Invalid school adoption event.")
