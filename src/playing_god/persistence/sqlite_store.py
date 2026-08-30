from __future__ import annotations

import json
import sqlite3

from collections import Counter
from contextlib import closing
from pathlib import Path

from playing_god.core.agent import Agent
from playing_god.core.economy import EconomyState
from playing_god.core.events import Event
from playing_god.core.faith import ATTRIBUTION_CAUSES, Attribution
from playing_god.core.intervention import (
    INTERPRETATIONS,
    INTERVENTION_KINDS,
    Intervention,
    InterventionResponse,
)
from playing_god.core.institution import SchoolState
from playing_god.core.perception import (
    Belief,
    Observation,
    belief_key,
)
from playing_god.core.prayer import Prayer
from playing_god.core.rng import (
    create_rng,
    restore_state,
    serialize_state,
)
from playing_god.core.world import World


SCHEMA_VERSION = 11


class PersistenceError(RuntimeError):
    pass


class WorldLoadError(PersistenceError):
    pass


SCHEMA = """
CREATE TABLE IF NOT EXISTS world_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    schema_version INTEGER NOT NULL,
    seed INTEGER NOT NULL,
    day INTEGER NOT NULL,
    rng_state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS economy_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    job_capacity INTEGER NOT NULL CHECK (job_capacity >= 0)
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,

    traits_json TEXT NOT NULL,
    sins_json TEXT NOT NULL,

    money REAL NOT NULL,
    employed INTEGER NOT NULL,
    salary REAL NOT NULL,
    job_level INTEGER NOT NULL,

    skill REAL NOT NULL,
    energy REAL NOT NULL,
    social_energy REAL NOT NULL,
    stress REAL NOT NULL,
    faith REAL NOT NULL,
    reputation REAL NOT NULL,

    goal TEXT NOT NULL,
    actions_json TEXT NOT NULL,

    current_location TEXT NOT NULL DEFAULT 'home',
    destination TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    value REAL NOT NULL,

    trust REAL NOT NULL DEFAULT 0.25,
    familiarity REAL NOT NULL DEFAULT 0.10,
    attraction REAL NOT NULL DEFAULT 0.0,
    hostility REAL NOT NULL DEFAULT 0.0,
    respect REAL NOT NULL DEFAULT 0.25,

    PRIMARY KEY (source_id, target_id),

    FOREIGN KEY (source_id)
        REFERENCES agents(id)
        ON DELETE CASCADE,

    FOREIGN KEY (target_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    agent_id TEXT NOT NULL,
    event_index INTEGER NOT NULL,

    day INTEGER NOT NULL,
    kind TEXT NOT NULL,
    description TEXT NOT NULL,
    significance REAL NOT NULL,
    target_id TEXT,
    location TEXT,

    PRIMARY KEY (agent_id, event_index),

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS observations (
    agent_id TEXT NOT NULL,
    observation_index INTEGER NOT NULL,

    day INTEGER NOT NULL,
    kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    value TEXT NOT NULL,
    source_id TEXT,
    reliability REAL NOT NULL,
    location TEXT,
    information_id TEXT,
    origin_agent_id TEXT,
    origin_day INTEGER,
    hop_count INTEGER CHECK (
        hop_count IS NULL OR hop_count >= 0
    ),

    PRIMARY KEY (agent_id, observation_index),

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS beliefs (
    agent_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,

    value TEXT NOT NULL,
    confidence REAL NOT NULL,
    updated_day INTEGER NOT NULL,
    evidence_count INTEGER NOT NULL,

    PRIMARY KEY (agent_id, kind, subject_id),

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prayers (
    agent_id TEXT NOT NULL,
    prayer_index INTEGER NOT NULL,

    desire_type TEXT NOT NULL,
    intensity REAL NOT NULL,
    related_goal TEXT NOT NULL,
    timestamp INTEGER NOT NULL,

    PRIMARY KEY (agent_id, prayer_index),

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interventions (
    id TEXT PRIMARY KEY,
    intervention_index INTEGER NOT NULL UNIQUE,

    kind TEXT NOT NULL,
    target_id TEXT NOT NULL,
    theme TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    strength REAL NOT NULL,
    created_day INTEGER NOT NULL,
    expires_day INTEGER NOT NULL,
    location TEXT,

    FOREIGN KEY (target_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS intervention_responses (
    intervention_id TEXT PRIMARY KEY,
    response_index INTEGER NOT NULL UNIQUE,

    agent_id TEXT NOT NULL,
    day INTEGER NOT NULL,
    noticed INTEGER NOT NULL,
    interpretation TEXT NOT NULL,
    interpreted_action TEXT,
    confidence REAL NOT NULL,

    FOREIGN KEY (intervention_id)
        REFERENCES interventions(id)
        ON DELETE CASCADE,

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attributions (
    agent_id TEXT NOT NULL,
    attribution_index INTEGER NOT NULL,

    day INTEGER NOT NULL,
    outcome_event_index INTEGER NOT NULL,
    outcome_kind TEXT NOT NULL,
    outcome_valence TEXT NOT NULL,
    cause TEXT NOT NULL,
    confidence REAL NOT NULL,
    faith_before REAL NOT NULL,
    faith_after REAL NOT NULL,
    prayer_timestamp INTEGER,
    intervention_id TEXT,

    PRIMARY KEY (agent_id, attribution_index),
    UNIQUE (agent_id, outcome_event_index),

    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE,

    FOREIGN KEY (agent_id, outcome_event_index)
        REFERENCES events(agent_id, event_index)
        ON DELETE CASCADE,

    FOREIGN KEY (intervention_id)
        REFERENCES interventions(id)
        ON DELETE SET NULL
);
"""


REQUIRED_TABLES = {
    "world_state",
    "agents",
    "relationships",
    "events",
}

PERCEPTION_TABLES = {
    "observations",
    "beliefs",
}

PRAYER_TABLES = {
    "prayers",
}

INTERVENTION_TABLES = {
    "interventions",
    "intervention_responses",
}

ATTRIBUTION_TABLES = {
    "attributions",
}

ECONOMY_TABLES = {
    "economy_state",
}


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _migrate_relationships_to_v2(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        "PRAGMA table_info(relationships)"
    ).fetchall()

    columns = {
        row["name"]
        for row in rows
    }

    additions = {
        "trust": "REAL NOT NULL DEFAULT 0.25",
        "familiarity": "REAL NOT NULL DEFAULT 0.10",
        "attraction": "REAL NOT NULL DEFAULT 0.0",
        "hostility": "REAL NOT NULL DEFAULT 0.0",
        "respect": "REAL NOT NULL DEFAULT 0.25",
    }

    for name, definition in additions.items():
        if name not in columns:
            conn.execute(
                f"ALTER TABLE relationships "
                f"ADD COLUMN {name} {definition}"
            )


def _migrate_agents_to_v3(
    conn: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(agents)"
        ).fetchall()
    }

    if "current_location" not in columns:
        conn.execute(
            "ALTER TABLE agents ADD COLUMN "
            "current_location TEXT NOT NULL "
            "DEFAULT 'home'"
        )

    if "destination" not in columns:
        conn.execute(
            "ALTER TABLE agents ADD COLUMN "
            "destination TEXT"
        )


def _migrate_events_to_v4(
    conn: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(events)"
        ).fetchall()
    }

    if "target_id" not in columns:
        conn.execute(
            "ALTER TABLE events ADD COLUMN target_id TEXT"
        )

    if "location" not in columns:
        conn.execute(
            "ALTER TABLE events ADD COLUMN location TEXT"
        )


def _migrate_agents_to_v5(
    conn: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(agents)"
        ).fetchall()
    }

    if "social_energy" not in columns:
        conn.execute(
            "ALTER TABLE agents ADD COLUMN social_energy REAL"
        )
        conn.execute(
            "UPDATE agents SET social_energy = energy"
        )


def _migrate_agents_to_v9(
    conn: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(agents)"
        ).fetchall()
    }

    if "faith" not in columns:
        conn.execute(
            "ALTER TABLE agents ADD COLUMN "
            "faith REAL NOT NULL DEFAULT 0.5"
        )


def _migrate_observations_to_v11(
    conn: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(observations)"
        ).fetchall()
    }
    additions = {
        "information_id": "TEXT",
        "origin_agent_id": "TEXT",
        "origin_day": "INTEGER",
        "hop_count": "INTEGER",
    }

    for name, definition in additions.items():
        if name not in columns:
            conn.execute(
                f"ALTER TABLE observations "
                f"ADD COLUMN {name} {definition}"
            )

def _validate_tables(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    found = {
        row["name"]
        for row in rows
    }

    missing = REQUIRED_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))

        raise WorldLoadError(
            f"Invalid world database. "
            f"Missing tables: {names}"
        )


def _validate_perception_tables(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    found = {
        row["name"]
        for row in rows
    }
    missing = PERCEPTION_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))
        raise WorldLoadError(
            "Invalid perception state. "
            f"Missing tables: {names}"
        )


def _validate_prayer_tables(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    found = {
        row["name"]
        for row in rows
    }
    missing = PRAYER_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))
        raise WorldLoadError(
            "Invalid prayer state. "
            f"Missing tables: {names}"
        )


def _validate_intervention_tables(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    found = {
        row["name"]
        for row in rows
    }
    missing = INTERVENTION_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))
        raise WorldLoadError(
            "Invalid intervention state. "
            f"Missing tables: {names}"
        )


def _validate_attribution_tables(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    found = {
        row["name"]
        for row in rows
    }
    missing = ATTRIBUTION_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))
        raise WorldLoadError(
            "Invalid attribution state. "
            f"Missing tables: {names}"
        )


def _validate_economy_tables(
    conn: sqlite3.Connection,
) -> None:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    found = {
        row["name"]
        for row in rows
    }
    missing = ECONOMY_TABLES - found

    if missing:
        names = ", ".join(sorted(missing))
        raise WorldLoadError(
            "Invalid economy state. "
            f"Missing tables: {names}"
        )


def _save_world_state(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    existing = conn.execute(
        """
        SELECT seed
        FROM world_state
        WHERE id = 1
        """
    ).fetchone()

    if (
        existing is not None
        and existing["seed"] != world.seed
    ):
        raise PersistenceError(
            "Refusing to overwrite a database "
            f"for seed {existing['seed']} "
            f"with seed {world.seed}."
        )

    conn.execute(
        """
        INSERT INTO world_state (
            id,
            schema_version,
            seed,
            day,
            rng_state
        )
        VALUES (1, ?, ?, ?, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            schema_version = excluded.schema_version,
            seed = excluded.seed,
            day = excluded.day,
            rng_state = excluded.rng_state
        """,
        (
            SCHEMA_VERSION,
            world.seed,
            world.day,
            serialize_state(world.rng),
        ),
    )
    _migrate_relationships_to_v2(conn)


def _save_economy_state(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    occupied_jobs = world.economy.occupied_jobs(world.agents)

    if occupied_jobs > world.economy.job_capacity:
        raise PersistenceError(
            "Cannot save economy with more occupied jobs "
            "than job capacity."
        )

    conn.execute(
        """
        INSERT INTO economy_state (
            id,
            job_capacity
        )
        VALUES (1, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            job_capacity = excluded.job_capacity
        """,
        (world.economy.job_capacity,),
    )


def _save_agents(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    for agent in world.agents:
        conn.execute(
            """
            INSERT INTO agents (
                id,
                name,
                age,
                traits_json,
                sins_json,
                money,
                employed,
                salary,
                job_level,
                skill,
                energy,
                social_energy,
                stress,
                faith,
                reputation,
                goal,
                actions_json,
                current_location,
                destination
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )

            ON CONFLICT(id)
            DO UPDATE SET
                name = excluded.name,
                age = excluded.age,
                traits_json = excluded.traits_json,
                sins_json = excluded.sins_json,
                money = excluded.money,
                employed = excluded.employed,
                salary = excluded.salary,
                job_level = excluded.job_level,
                skill = excluded.skill,
                energy = excluded.energy,
                social_energy = excluded.social_energy,
                stress = excluded.stress,
                faith = excluded.faith,
                reputation = excluded.reputation,
                goal = excluded.goal,
                actions_json = excluded.actions_json,
                current_location = excluded.current_location,
                destination = excluded.destination
            """,
            (
                agent.id,
                agent.name,
                agent.age,
                json.dumps(agent.traits),
                json.dumps(agent.sins),
                agent.money,
                int(agent.employed),
                agent.salary,
                agent.job_level,
                agent.skill,
                agent.energy,
                agent.social_energy,
                agent.stress,
                agent.faith,
                agent.reputation,
                agent.goal,
                json.dumps(dict(agent.actions)),
                agent.current_location,
                agent.destination,
            ),
        )


def _save_relationships(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    for agent in world.agents:
        for target_id, value in agent.relationships.items():

            social = world.social.get_relationship(
                agent.id,
                target_id,
            )

            if social is None:
                trust = 0.25
                familiarity = 0.10
                attraction = 0.0
                hostility = 0.0
                respect = 0.25
            else:
                trust = social["trust"]
                familiarity = social["familiarity"]
                attraction = social["attraction"]
                hostility = social["hostility"]
                respect = social["respect"]

            conn.execute(
                """
                INSERT INTO relationships (
                    source_id,
                    target_id,
                    value,
                    trust,
                    familiarity,
                    attraction,
                    hostility,
                    respect
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(source_id, target_id)
                DO UPDATE SET
                    value = excluded.value,
                    trust = excluded.trust,
                    familiarity = excluded.familiarity,
                    attraction = excluded.attraction,
                    hostility = excluded.hostility,
                    respect = excluded.respect
                """,
                (
                    agent.id,
                    target_id,
                    value,
                    trust,
                    familiarity,
                    attraction,
                    hostility,
                    respect,
                ),
            )


def _save_events(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    for agent in world.agents:
        for index, event in enumerate(agent.events):
            existing = conn.execute(
                """
                SELECT
                    day,
                    kind,
                    description,
                    significance,
                    target_id,
                    location
                FROM events
                WHERE agent_id = ?
                  AND event_index = ?
                """,
                (
                    agent.id,
                    index,
                ),
            ).fetchone()

            if existing is not None:
                same_event = (
                    existing["day"] == event.day
                    and existing["kind"] == event.kind
                    and existing["description"]
                    == event.description
                    and existing["significance"]
                    == event.significance
                    and existing["target_id"]
                    == event.target_id
                    and existing["location"]
                    == event.location
                )

                if not same_event:
                    raise PersistenceError(
                        "Existing event history was "
                        "modified unexpectedly: "
                        f"{agent.id} event {index}"
                    )

                continue

            conn.execute(
                """
                INSERT INTO events (
                    agent_id,
                    event_index,
                    day,
                    kind,
                    description,
                    significance,
                    target_id,
                    location
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.id,
                    index,
                    event.day,
                    event.kind,
                    event.description,
                    event.significance,
                    event.target_id,
                    event.location,
                ),
            )


def _save_observations(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    for agent in world.agents:
        for index, observation in enumerate(agent.observations):
            existing = conn.execute(
                """
                SELECT
                    day,
                    kind,
                    subject_id,
                    value,
                    source_id,
                    reliability,
                    location,
                    information_id,
                    origin_agent_id,
                    origin_day,
                    hop_count
                FROM observations
                WHERE agent_id = ?
                  AND observation_index = ?
                """,
                (
                    agent.id,
                    index,
                ),
            ).fetchone()

            values = (
                observation.day,
                observation.kind,
                observation.subject_id,
                observation.value,
                observation.source_id,
                observation.reliability,
                observation.location,
                observation.information_id,
                observation.origin_agent_id,
                observation.origin_day,
                observation.hop_count,
            )

            if existing is not None:
                if tuple(existing) != values:
                    raise PersistenceError(
                        "Existing observation history was "
                        "modified unexpectedly: "
                        f"{agent.id} observation {index}"
                    )

                continue

            conn.execute(
                """
                INSERT INTO observations (
                    agent_id,
                    observation_index,
                    day,
                    kind,
                    subject_id,
                    value,
                    source_id,
                    reliability,
                    location,
                    information_id,
                    origin_agent_id,
                    origin_day,
                    hop_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.id,
                    index,
                    *values,
                ),
            )


def _save_beliefs(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    conn.execute("DELETE FROM beliefs")

    for agent in world.agents:
        for belief in agent.beliefs.values():
            conn.execute(
                """
                INSERT INTO beliefs (
                    agent_id,
                    kind,
                    subject_id,
                    value,
                    confidence,
                    updated_day,
                    evidence_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.id,
                    belief.kind,
                    belief.subject_id,
                    belief.value,
                    belief.confidence,
                    belief.updated_day,
                    belief.evidence_count,
                ),
            )


def _save_prayers(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    for agent in world.agents:
        for index, prayer in enumerate(agent.prayers):
            if prayer.agent_id != agent.id:
                raise PersistenceError(
                    "Prayer owner does not match "
                    f"its agent: {prayer.agent_id} != {agent.id}"
                )

            if not 0.0 <= prayer.intensity <= 1.0:
                raise PersistenceError(
                    "Prayer intensity is outside "
                    f"[0, 1] for {agent.id}."
                )

            existing = conn.execute(
                """
                SELECT
                    desire_type,
                    intensity,
                    related_goal,
                    timestamp
                FROM prayers
                WHERE agent_id = ?
                  AND prayer_index = ?
                """,
                (
                    agent.id,
                    index,
                ),
            ).fetchone()

            values = (
                prayer.desire_type,
                prayer.intensity,
                prayer.related_goal,
                prayer.timestamp,
            )

            if existing is not None:
                if tuple(existing) != values:
                    raise PersistenceError(
                        "Existing prayer history was "
                        "modified unexpectedly: "
                        f"{agent.id} prayer {index}"
                    )

                continue

            conn.execute(
                """
                INSERT INTO prayers (
                    agent_id,
                    prayer_index,
                    desire_type,
                    intensity,
                    related_goal,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.id,
                    index,
                    *values,
                ),
            )


def _save_interventions(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    agent_ids = {
        agent.id
        for agent in world.agents
    }

    for index, intervention in enumerate(world.interventions):
        expected_id = f"intervention_{index + 1:06d}"
        if intervention.id != expected_id:
            raise PersistenceError(
                "Intervention history has an invalid ID. "
                f"Expected {expected_id}, found {intervention.id}."
            )

        if intervention.kind not in INTERVENTION_KINDS:
            raise PersistenceError(
                "Unknown intervention kind: "
                f"{intervention.kind}"
            )

        if intervention.target_id not in agent_ids:
            raise PersistenceError(
                "Intervention references missing agent: "
                f"{intervention.target_id}"
            )

        if not 0.0 <= intervention.strength <= 1.0:
            raise PersistenceError(
                "Intervention strength is outside "
                f"[0, 1] for {intervention.id}."
            )

        values = (
            index,
            intervention.kind,
            intervention.target_id,
            intervention.theme,
            intervention.suggested_action,
            intervention.strength,
            intervention.created_day,
            intervention.expires_day,
            intervention.location,
        )
        existing = conn.execute(
            """
            SELECT
                intervention_index,
                kind,
                target_id,
                theme,
                suggested_action,
                strength,
                created_day,
                expires_day,
                location
            FROM interventions
            WHERE id = ?
            """,
            (intervention.id,),
        ).fetchone()

        if existing is not None:
            if tuple(existing) != values:
                raise PersistenceError(
                    "Existing intervention history was "
                    "modified unexpectedly: "
                    f"{intervention.id}"
                )
            continue

        conn.execute(
            """
            INSERT INTO interventions (
                id,
                intervention_index,
                kind,
                target_id,
                theme,
                suggested_action,
                strength,
                created_day,
                expires_day,
                location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                intervention.id,
                *values,
            ),
        )


def _save_intervention_responses(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    intervention_targets = {
        intervention.id: intervention.target_id
        for intervention in world.interventions
    }

    for index, response in enumerate(
        world.intervention_responses
    ):
        if response.intervention_id not in intervention_targets:
            raise PersistenceError(
                "Response references missing intervention: "
                f"{response.intervention_id}"
            )

        if (
            response.agent_id
            != intervention_targets[response.intervention_id]
        ):
            raise PersistenceError(
                "Intervention response owner does not match "
                f"its target: {response.agent_id} != "
                f"{intervention_targets[response.intervention_id]}"
            )

        if response.interpretation not in INTERPRETATIONS:
            raise PersistenceError(
                "Unknown intervention interpretation: "
                f"{response.interpretation}"
            )

        if not 0.0 <= response.confidence <= 1.0:
            raise PersistenceError(
                "Intervention confidence is outside "
                f"[0, 1] for {response.intervention_id}."
            )

        values = (
            index,
            response.agent_id,
            response.day,
            int(response.noticed),
            response.interpretation,
            response.interpreted_action,
            response.confidence,
        )
        existing = conn.execute(
            """
            SELECT
                response_index,
                agent_id,
                day,
                noticed,
                interpretation,
                interpreted_action,
                confidence
            FROM intervention_responses
            WHERE intervention_id = ?
            """,
            (response.intervention_id,),
        ).fetchone()

        if existing is not None:
            if tuple(existing) != values:
                raise PersistenceError(
                    "Existing intervention response was "
                    "modified unexpectedly: "
                    f"{response.intervention_id}"
                )
            continue

        conn.execute(
            """
            INSERT INTO intervention_responses (
                intervention_id,
                response_index,
                agent_id,
                day,
                noticed,
                interpretation,
                interpreted_action,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                response.intervention_id,
                *values,
            ),
        )


def _save_attributions(
    conn: sqlite3.Connection,
    world: World,
) -> None:
    response_agents = {
        response.intervention_id: response.agent_id
        for response in world.intervention_responses
    }

    for agent in world.agents:
        previous_faith_after = None

        for index, attribution in enumerate(agent.attributions):
            if attribution.agent_id != agent.id:
                raise PersistenceError(
                    "Attribution owner does not match "
                    f"its agent: {attribution.agent_id} != {agent.id}"
                )

            if attribution.cause not in ATTRIBUTION_CAUSES:
                raise PersistenceError(
                    "Unknown attribution cause: "
                    f"{attribution.cause}"
                )

            if attribution.outcome_valence not in {
                "positive",
                "negative",
            }:
                raise PersistenceError(
                    "Unknown attribution valence: "
                    f"{attribution.outcome_valence}"
                )

            if not 0.0 <= attribution.confidence <= 1.0:
                raise PersistenceError(
                    "Attribution confidence is outside "
                    f"[0, 1] for {agent.id}."
                )

            if not (
                0.0 <= attribution.faith_before <= 1.0
                and 0.0 <= attribution.faith_after <= 1.0
            ):
                raise PersistenceError(
                    "Attribution faith state is outside "
                    f"[0, 1] for {agent.id}."
                )

            if (
                previous_faith_after is not None
                and attribution.faith_before
                != previous_faith_after
            ):
                raise PersistenceError(
                    "Attribution faith history is discontinuous "
                    f"for {agent.id}."
                )

            if not 0 <= attribution.outcome_event_index < len(agent.events):
                raise PersistenceError(
                    "Attribution references missing event: "
                    f"{agent.id} event "
                    f"{attribution.outcome_event_index}"
                )

            event = agent.events[attribution.outcome_event_index]
            if (
                event.day != attribution.day
                or event.kind != attribution.outcome_kind
            ):
                raise PersistenceError(
                    "Attribution outcome does not match its event: "
                    f"{agent.id} attribution {index}"
                )

            if (
                attribution.prayer_timestamp is not None
                and not any(
                    prayer.timestamp == attribution.prayer_timestamp
                    for prayer in agent.prayers
                )
            ):
                raise PersistenceError(
                    "Attribution references missing prayer: "
                    f"{agent.id} day {attribution.prayer_timestamp}"
                )

            if (
                attribution.intervention_id is not None
                and response_agents.get(attribution.intervention_id)
                != agent.id
            ):
                raise PersistenceError(
                    "Attribution references missing intervention response: "
                    f"{attribution.intervention_id}"
                )

            values = (
                attribution.day,
                attribution.outcome_event_index,
                attribution.outcome_kind,
                attribution.outcome_valence,
                attribution.cause,
                attribution.confidence,
                attribution.faith_before,
                attribution.faith_after,
                attribution.prayer_timestamp,
                attribution.intervention_id,
            )
            existing = conn.execute(
                """
                SELECT
                    day,
                    outcome_event_index,
                    outcome_kind,
                    outcome_valence,
                    cause,
                    confidence,
                    faith_before,
                    faith_after,
                    prayer_timestamp,
                    intervention_id
                FROM attributions
                WHERE agent_id = ?
                  AND attribution_index = ?
                """,
                (
                    agent.id,
                    index,
                ),
            ).fetchone()

            if existing is not None:
                if tuple(existing) != values:
                    raise PersistenceError(
                        "Existing attribution history was "
                        "modified unexpectedly: "
                        f"{agent.id} attribution {index}"
                    )
            else:
                conn.execute(
                    """
                    INSERT INTO attributions (
                        agent_id,
                        attribution_index,
                        day,
                        outcome_event_index,
                        outcome_kind,
                        outcome_valence,
                        cause,
                        confidence,
                        faith_before,
                        faith_after,
                        prayer_timestamp,
                        intervention_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent.id,
                        index,
                        *values,
                    ),
                )

            previous_faith_after = attribution.faith_after

        if (
            previous_faith_after is not None
            and previous_faith_after != agent.faith
        ):
            raise PersistenceError(
                "Current faith does not match attribution history "
                f"for {agent.id}."
            )


def save_world(
    world: World,
    db_path: str | Path,
) -> None:
    path = Path(db_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with closing(_connect(path)) as conn, conn:
            conn.executescript(SCHEMA)

            _migrate_agents_to_v3(conn)
            _migrate_events_to_v4(conn)
            _migrate_agents_to_v5(conn)
            _migrate_agents_to_v9(conn)
            _migrate_observations_to_v11(conn)

            _save_world_state(
                conn,
                world,
            )

            _save_economy_state(
                conn,
                world,
            )

            _save_agents(
                conn,
                world,
            )

            _save_relationships(
                conn,
                world,
            )

            _save_events(
                conn,
                world,
            )

            _save_observations(
                conn,
                world,
            )

            _save_beliefs(
                conn,
                world,
            )

            _save_prayers(
                conn,
                world,
            )

            _save_interventions(
                conn,
                world,
            )

            _save_intervention_responses(
                conn,
                world,
            )

            _save_attributions(
                conn,
                world,
            )

    except sqlite3.DatabaseError as exc:
        raise PersistenceError(
            f"Could not save world database: {path}"
        ) from exc


def _load_agents(
    conn: sqlite3.Connection,
) -> list[Agent]:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(agents)"
        ).fetchall()
    }
    has_spatial_state = {
        "current_location",
        "destination",
    }.issubset(columns)
    has_social_energy = "social_energy" in columns
    has_faith = "faith" in columns

    rows = conn.execute(
        """
        SELECT *
        FROM agents
        ORDER BY id
        """
    ).fetchall()

    if not rows:
        raise WorldLoadError(
            "World database contains no agents."
        )

    agents = []

    for row in rows:
        try:
            traits = json.loads(
                row["traits_json"]
            )

            sins = json.loads(
                row["sins_json"]
            )

            actions = Counter(
                json.loads(
                    row["actions_json"]
                )
            )

        except (json.JSONDecodeError, TypeError) as exc:
            raise WorldLoadError(
                f"Invalid JSON state for agent "
                f"{row['id']}."
            ) from exc

        agent = Agent(
            id=row["id"],
            name=row["name"],
            age=row["age"],
            traits=traits,
            sins=sins,
            money=row["money"],
            employed=bool(row["employed"]),
            salary=row["salary"],
            job_level=row["job_level"],
            skill=row["skill"],
            energy=row["energy"],
            social_energy=(
                row["social_energy"]
                if has_social_energy
                else row["energy"]
            ),
            stress=row["stress"],
            faith=(
                row["faith"]
                if has_faith
                else 0.5
            ),
            reputation=row["reputation"],
            goal=row["goal"],
            relationships={},
            events=[],
            actions=actions,
            current_location=(
                row["current_location"]
                if has_spatial_state
                else "home"
            ),
            destination=(
                row["destination"]
                if has_spatial_state
                else None
            ),
        )

        agents.append(agent)

    return agents


def _load_economy_state(
    conn: sqlite3.Connection,
    agents: list[Agent],
) -> EconomyState:
    row = conn.execute(
        """
        SELECT job_capacity
        FROM economy_state
        WHERE id = 1
        """
    ).fetchone()

    if row is None:
        raise WorldLoadError(
            "World database has no economy state."
        )

    job_capacity = row["job_capacity"]
    if not isinstance(job_capacity, int) or job_capacity < 0:
        raise WorldLoadError(
            "Economy job capacity must be a non-negative integer."
        )

    economy = EconomyState(job_capacity=job_capacity)
    occupied_jobs = economy.occupied_jobs(agents)
    if occupied_jobs > job_capacity:
        raise WorldLoadError(
            "Economy has more occupied jobs than job capacity."
        )

    return economy


def _load_relationships(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
) -> dict[tuple[str, str], dict[str, float]]:

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(relationships)"
        ).fetchall()
    }

    has_phase3 = "trust" in columns

    rows = conn.execute(
        """
        SELECT *
        FROM relationships
        ORDER BY source_id, target_id
        """
    ).fetchall()

    social_state = {}

    for row in rows:
        source_id = row["source_id"]
        target_id = row["target_id"]

        if source_id not in agents_by_id:
            raise WorldLoadError(
                f"Relationship references missing agent: {source_id}"
            )

        if target_id not in agents_by_id:
            raise WorldLoadError(
                f"Relationship references missing agent: {target_id}"
            )

        agents_by_id[
            source_id
        ].relationships[target_id] = row["value"]

        if has_phase3:
            social_state[(source_id, target_id)] = {
                "trust": row["trust"],
                "familiarity": row["familiarity"],
                "attraction": row["attraction"],
                "hostility": row["hostility"],
                "respect": row["respect"],
            }
        else:
            # Old Phase-2 world.
            social_state[(source_id, target_id)] = {
                "trust": 0.25,
                "familiarity": 0.10,
                "attraction": 0.0,
                "hostility": 0.0,
                "respect": 0.25,
            }

    return social_state


def _load_events(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(events)"
        ).fetchall()
    }
    has_encounter_context = {
        "target_id",
        "location",
    }.issubset(columns)

    rows = conn.execute(
        """
        SELECT *
        FROM events
        ORDER BY agent_id, event_index
        """
    ).fetchall()

    expected_index = {
        agent_id: 0
        for agent_id in agents_by_id
    }

    last_day = {
        agent_id: -1
        for agent_id in agents_by_id
    }

    for row in rows:
        agent_id = row["agent_id"]

        if agent_id not in agents_by_id:
            raise WorldLoadError(
                "Event references missing agent: "
                f"{agent_id}"
            )

        expected = expected_index[agent_id]

        if row["event_index"] != expected:
            raise WorldLoadError(
                "Event history contains a missing "
                "or duplicated index for "
                f"{agent_id}. "
                f"Expected {expected}, "
                f"found {row['event_index']}."
            )

        if row["day"] < last_day[agent_id]:
            raise WorldLoadError(
                "Event history is not chronological "
                f"for {agent_id}."
            )

        event = Event(
            day=row["day"],
            kind=row["kind"],
            description=row["description"],
            significance=row["significance"],
            target_id=(
                row["target_id"]
                if has_encounter_context
                else None
            ),
            location=(
                row["location"]
                if has_encounter_context
                else None
            ),
        )

        agents_by_id[
            agent_id
        ].events.append(event)

        expected_index[agent_id] += 1
        last_day[agent_id] = row["day"]


def _load_observations(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
    *,
    require_information_state: bool,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(observations)"
        ).fetchall()
    }
    information_columns = {
        "information_id",
        "origin_agent_id",
        "origin_day",
        "hop_count",
    }
    has_information_state = information_columns.issubset(columns)
    if require_information_state and not has_information_state:
        raise WorldLoadError(
            "Invalid information state. Missing observation "
            "identity columns."
        )

    rows = conn.execute(
        """
        SELECT *
        FROM observations
        ORDER BY agent_id, observation_index
        """
    ).fetchall()
    expected_index = {
        agent_id: 0
        for agent_id in agents_by_id
    }
    last_day = {
        agent_id: -1
        for agent_id in agents_by_id
    }

    for row in rows:
        agent_id = row["agent_id"]

        if agent_id not in agents_by_id:
            raise WorldLoadError(
                "Observation references missing agent: "
                f"{agent_id}"
            )

        expected = expected_index[agent_id]

        if row["observation_index"] != expected:
            raise WorldLoadError(
                "Observation history contains a missing "
                "or duplicated index for "
                f"{agent_id}. Expected {expected}, "
                f"found {row['observation_index']}."
            )

        if row["day"] < last_day[agent_id]:
            raise WorldLoadError(
                "Observation history is not chronological "
                f"for {agent_id}."
            )

        if not 0.0 <= row["reliability"] <= 1.0:
            raise WorldLoadError(
                "Observation reliability is outside "
                f"[0, 1] for {agent_id}."
            )

        information_id = (
            row["information_id"]
            if has_information_state
            else None
        )
        origin_agent_id = (
            row["origin_agent_id"]
            if has_information_state
            else None
        )
        origin_day = (
            row["origin_day"]
            if has_information_state
            else None
        )
        hop_count = (
            row["hop_count"]
            if has_information_state
            else None
        )
        identity_values = (
            information_id,
            origin_agent_id,
            origin_day,
            hop_count,
        )
        if any(value is not None for value in identity_values):
            if any(value is None for value in identity_values):
                raise WorldLoadError(
                    "Observation has incomplete information "
                    f"identity for {agent_id}."
                )
            if origin_agent_id not in agents_by_id:
                raise WorldLoadError(
                    "Observation information origin references "
                    f"missing agent: {origin_agent_id}"
                )
            if origin_day > row["day"] or hop_count < 0:
                raise WorldLoadError(
                    "Observation has invalid information origin "
                    f"or hop count for {agent_id}."
                )

        agents_by_id[agent_id].observations.append(
            Observation(
                day=row["day"],
                kind=row["kind"],
                subject_id=row["subject_id"],
                value=row["value"],
                source_id=row["source_id"],
                reliability=row["reliability"],
                location=row["location"],
                information_id=information_id,
                origin_agent_id=origin_agent_id,
                origin_day=origin_day,
                hop_count=hop_count,
            )
        )
        expected_index[agent_id] += 1
        last_day[agent_id] = row["day"]


def _load_beliefs(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
) -> None:
    rows = conn.execute(
        """
        SELECT *
        FROM beliefs
        ORDER BY agent_id, kind, subject_id
        """
    ).fetchall()

    for row in rows:
        agent_id = row["agent_id"]

        if agent_id not in agents_by_id:
            raise WorldLoadError(
                "Belief references missing agent: "
                f"{agent_id}"
            )

        if not 0.0 <= row["confidence"] <= 1.0:
            raise WorldLoadError(
                "Belief confidence is outside "
                f"[0, 1] for {agent_id}."
            )

        if row["evidence_count"] < 1:
            raise WorldLoadError(
                "Belief evidence count must be positive "
                f"for {agent_id}."
            )

        belief = Belief(
            kind=row["kind"],
            subject_id=row["subject_id"],
            value=row["value"],
            confidence=row["confidence"],
            updated_day=row["updated_day"],
            evidence_count=row["evidence_count"],
        )
        agents_by_id[agent_id].beliefs[
            belief_key(
                belief.kind,
                belief.subject_id,
            )
        ] = belief


def _load_prayers(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
) -> None:
    rows = conn.execute(
        """
        SELECT *
        FROM prayers
        ORDER BY agent_id, prayer_index
        """
    ).fetchall()
    expected_index = {
        agent_id: 0
        for agent_id in agents_by_id
    }
    last_timestamp = {
        agent_id: -1
        for agent_id in agents_by_id
    }

    for row in rows:
        agent_id = row["agent_id"]

        if agent_id not in agents_by_id:
            raise WorldLoadError(
                "Prayer references missing agent: "
                f"{agent_id}"
            )

        expected = expected_index[agent_id]
        if row["prayer_index"] != expected:
            raise WorldLoadError(
                "Prayer history contains a missing "
                "or duplicated index for "
                f"{agent_id}. Expected {expected}, "
                f"found {row['prayer_index']}."
            )

        if row["timestamp"] < last_timestamp[agent_id]:
            raise WorldLoadError(
                "Prayer history is not chronological "
                f"for {agent_id}."
            )

        if not 0.0 <= row["intensity"] <= 1.0:
            raise WorldLoadError(
                "Prayer intensity is outside "
                f"[0, 1] for {agent_id}."
            )

        agents_by_id[agent_id].prayers.append(
            Prayer(
                agent_id=agent_id,
                desire_type=row["desire_type"],
                intensity=row["intensity"],
                related_goal=row["related_goal"],
                timestamp=row["timestamp"],
            )
        )
        expected_index[agent_id] += 1
        last_timestamp[agent_id] = row["timestamp"]


def _load_interventions(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
) -> list[Intervention]:
    rows = conn.execute(
        """
        SELECT *
        FROM interventions
        ORDER BY intervention_index
        """
    ).fetchall()
    interventions = []

    for expected_index, row in enumerate(rows):
        if row["intervention_index"] != expected_index:
            raise WorldLoadError(
                "Intervention history contains a missing "
                "or duplicated index. "
                f"Expected {expected_index}, "
                f"found {row['intervention_index']}."
            )

        expected_id = f"intervention_{expected_index + 1:06d}"
        if row["id"] != expected_id:
            raise WorldLoadError(
                "Intervention history has an invalid ID. "
                f"Expected {expected_id}, found {row['id']}."
            )

        if row["target_id"] not in agents_by_id:
            raise WorldLoadError(
                "Intervention references missing agent: "
                f"{row['target_id']}"
            )

        if row["kind"] not in INTERVENTION_KINDS:
            raise WorldLoadError(
                "Unknown intervention kind: "
                f"{row['kind']}"
            )

        if not 0.0 <= row["strength"] <= 1.0:
            raise WorldLoadError(
                "Intervention strength is outside "
                f"[0, 1] for {row['id']}."
            )

        if row["expires_day"] < row["created_day"]:
            raise WorldLoadError(
                "Intervention expires before creation: "
                f"{row['id']}"
            )

        interventions.append(
            Intervention(
                id=row["id"],
                kind=row["kind"],
                target_id=row["target_id"],
                theme=row["theme"],
                suggested_action=row["suggested_action"],
                strength=row["strength"],
                created_day=row["created_day"],
                expires_day=row["expires_day"],
                location=row["location"],
            )
        )

    return interventions


def _load_intervention_responses(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
    intervention_targets: dict[str, str],
) -> list[InterventionResponse]:
    rows = conn.execute(
        """
        SELECT *
        FROM intervention_responses
        ORDER BY response_index
        """
    ).fetchall()
    responses = []
    last_day = -1

    for expected_index, row in enumerate(rows):
        if row["response_index"] != expected_index:
            raise WorldLoadError(
                "Intervention response history contains a "
                "missing or duplicated index. "
                f"Expected {expected_index}, "
                f"found {row['response_index']}."
            )

        if row["intervention_id"] not in intervention_targets:
            raise WorldLoadError(
                "Response references missing intervention: "
                f"{row['intervention_id']}"
            )

        if (
            row["agent_id"]
            != intervention_targets[row["intervention_id"]]
        ):
            raise WorldLoadError(
                "Intervention response owner does not match "
                f"its target: {row['intervention_id']}"
            )

        if row["agent_id"] not in agents_by_id:
            raise WorldLoadError(
                "Intervention response references missing agent: "
                f"{row['agent_id']}"
            )

        if row["day"] < last_day:
            raise WorldLoadError(
                "Intervention response history is not chronological."
            )

        if row["noticed"] not in (0, 1):
            raise WorldLoadError(
                "Intervention response noticed state is invalid: "
                f"{row['intervention_id']}"
            )

        if row["interpretation"] not in INTERPRETATIONS:
            raise WorldLoadError(
                "Unknown intervention interpretation: "
                f"{row['interpretation']}"
            )

        if not 0.0 <= row["confidence"] <= 1.0:
            raise WorldLoadError(
                "Intervention confidence is outside "
                f"[0, 1] for {row['intervention_id']}."
            )

        noticed = bool(row["noticed"])
        interpreted_action = row["interpreted_action"]
        interpretation = row["interpretation"]
        if (
            (interpretation == "missed" and noticed)
            or (interpretation != "missed" and not noticed)
            or (
                interpretation in {"missed", "ignored"}
                and interpreted_action is not None
            )
            or (
                interpretation in {"aligned", "misinterpreted"}
                and interpreted_action is None
            )
        ):
            raise WorldLoadError(
                "Inconsistent intervention response: "
                f"{row['intervention_id']}"
            )

        responses.append(
            InterventionResponse(
                intervention_id=row["intervention_id"],
                agent_id=row["agent_id"],
                day=row["day"],
                noticed=noticed,
                interpretation=interpretation,
                interpreted_action=interpreted_action,
                confidence=row["confidence"],
            )
        )
        last_day = row["day"]

    return responses


def _load_attributions(
    conn: sqlite3.Connection,
    agents_by_id: dict[str, Agent],
    response_ids: set[str],
) -> None:
    rows = conn.execute(
        """
        SELECT *
        FROM attributions
        ORDER BY agent_id, attribution_index
        """
    ).fetchall()
    expected_index = {
        agent_id: 0
        for agent_id in agents_by_id
    }
    previous_faith_after: dict[str, float] = {}
    last_day = {
        agent_id: -1
        for agent_id in agents_by_id
    }

    for row in rows:
        agent_id = row["agent_id"]
        if agent_id not in agents_by_id:
            raise WorldLoadError(
                "Attribution references missing agent: "
                f"{agent_id}"
            )

        expected = expected_index[agent_id]
        if row["attribution_index"] != expected:
            raise WorldLoadError(
                "Attribution history contains a missing "
                "or duplicated index for "
                f"{agent_id}. Expected {expected}, "
                f"found {row['attribution_index']}."
            )

        if row["day"] < last_day[agent_id]:
            raise WorldLoadError(
                "Attribution history is not chronological "
                f"for {agent_id}."
            )

        if row["cause"] not in ATTRIBUTION_CAUSES:
            raise WorldLoadError(
                "Unknown attribution cause: "
                f"{row['cause']}"
            )

        if row["outcome_valence"] not in {"positive", "negative"}:
            raise WorldLoadError(
                "Unknown attribution valence: "
                f"{row['outcome_valence']}"
            )

        if not 0.0 <= row["confidence"] <= 1.0:
            raise WorldLoadError(
                "Attribution confidence is outside "
                f"[0, 1] for {agent_id}."
            )

        if not (
            0.0 <= row["faith_before"] <= 1.0
            and 0.0 <= row["faith_after"] <= 1.0
        ):
            raise WorldLoadError(
                "Attribution faith state is outside "
                f"[0, 1] for {agent_id}."
            )

        if (
            agent_id in previous_faith_after
            and row["faith_before"]
            != previous_faith_after[agent_id]
        ):
            raise WorldLoadError(
                "Attribution faith history is discontinuous "
                f"for {agent_id}."
            )

        agent = agents_by_id[agent_id]
        event_index = row["outcome_event_index"]
        if not 0 <= event_index < len(agent.events):
            raise WorldLoadError(
                "Attribution references missing event: "
                f"{agent_id} event {event_index}"
            )

        event = agent.events[event_index]
        if (
            event.day != row["day"]
            or event.kind != row["outcome_kind"]
        ):
            raise WorldLoadError(
                "Attribution outcome does not match its event: "
                f"{agent_id} attribution {expected}"
            )

        prayer_timestamp = row["prayer_timestamp"]
        if (
            prayer_timestamp is not None
            and not any(
                prayer.timestamp == prayer_timestamp
                for prayer in agent.prayers
            )
        ):
            raise WorldLoadError(
                "Attribution references missing prayer: "
                f"{agent_id} day {prayer_timestamp}"
            )

        intervention_id = row["intervention_id"]
        if (
            intervention_id is not None
            and intervention_id not in response_ids
        ):
            raise WorldLoadError(
                "Attribution references missing intervention response: "
                f"{intervention_id}"
            )

        agent.attributions.append(
            Attribution(
                agent_id=agent_id,
                day=row["day"],
                outcome_event_index=event_index,
                outcome_kind=row["outcome_kind"],
                outcome_valence=row["outcome_valence"],
                cause=row["cause"],
                confidence=row["confidence"],
                faith_before=row["faith_before"],
                faith_after=row["faith_after"],
                prayer_timestamp=prayer_timestamp,
                intervention_id=intervention_id,
            )
        )
        expected_index[agent_id] += 1
        last_day[agent_id] = row["day"]
        previous_faith_after[agent_id] = row["faith_after"]

    for agent_id, faith_after in previous_faith_after.items():
        if agents_by_id[agent_id].faith != faith_after:
            raise WorldLoadError(
                "Current faith does not match attribution history "
                f"for {agent_id}."
            )


def load_world(
    db_path: str | Path,
) -> World:
    path = Path(db_path)

    # Important:
    # sqlite3.connect() creates a missing file.
    # Loading must NEVER do that.
    if not path.exists():
        raise WorldLoadError(
            f"World database does not exist: {path}"
        )

    if not path.is_file():
        raise WorldLoadError(
            f"World database is not a file: {path}"
        )

    try:
        with closing(_connect(path)) as conn, conn:
            _validate_tables(conn)

            state = conn.execute(
                """
                SELECT
                    schema_version,
                    seed,
                    day,
                    rng_state
                FROM world_state
                WHERE id = 1
                """
            ).fetchone()

            if state is None:
                raise WorldLoadError(
                    "World database has no world_state."
                )

            if state["schema_version"] not in (
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                SCHEMA_VERSION,
            ):
                raise WorldLoadError(
                    "Unsupported database schema "
                    f"version: "
                    f"{state['schema_version']}"
                )

            has_perception_state = (
                state["schema_version"] >= 6
            )
            has_prayer_state = (
                state["schema_version"] >= 7
            )
            has_intervention_state = (
                state["schema_version"] >= 8
            )
            has_attribution_state = (
                state["schema_version"] >= 9
            )
            has_economy_state = (
                state["schema_version"] >= 10
            )
            has_information_state = (
                state["schema_version"] >= 11
            )

            if has_perception_state:
                _validate_perception_tables(conn)

            if has_prayer_state:
                _validate_prayer_tables(conn)

            if has_intervention_state:
                _validate_intervention_tables(conn)

            if has_attribution_state:
                _validate_attribution_tables(conn)

            if has_economy_state:
                _validate_economy_tables(conn)

            agents = _load_agents(conn)
            economy = (
                _load_economy_state(conn, agents)
                if has_economy_state
                else EconomyState.from_agents(agents)
            )

            agents_by_id = {
                agent.id: agent
                for agent in agents
            }

            social_state = _load_relationships(
                conn,
                agents_by_id,
            )

            _load_events(
                conn,
                agents_by_id,
            )

            if has_perception_state:
                _load_observations(
                    conn,
                    agents_by_id,
                    require_information_state=(
                        has_information_state
                    ),
                )
                _load_beliefs(
                    conn,
                    agents_by_id,
                )

            if has_prayer_state:
                _load_prayers(
                    conn,
                    agents_by_id,
                )

            interventions = []
            intervention_responses = []
            if has_intervention_state:
                interventions = _load_interventions(
                    conn,
                    agents_by_id,
                )
                intervention_responses = (
                    _load_intervention_responses(
                        conn,
                        agents_by_id,
                        {
                            intervention.id: intervention.target_id
                            for intervention in interventions
                        },
                    )
                )

            if has_attribution_state:
                _load_attributions(
                    conn,
                    agents_by_id,
                    {
                        response.intervention_id
                        for response in intervention_responses
                    },
                )

            # Do NOT call World(seed).
            #
            # That would generate a temporary population
            # and consume RNG draws before restoration.
            world = World.__new__(World)

            world.seed = state["seed"]
            world.day = state["day"]
            world.agents = agents
            world.economy = economy
            world.school = SchoolState()
            world.interventions = interventions
            world.intervention_responses = intervention_responses
            world.information_items = []

            world.rng = create_rng(
                world.seed
            )

            try:
                restore_state(
                    world.rng,
                    state["rng_state"],
                )

            except (
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ) as exc:
                raise WorldLoadError(
                    "Stored RNG state is corrupted."
                ) from exc
            world.rebuild_social_graph()
            world.rebuild_spatial_map()
            world.rebuild_information_index()

            for intervention in world.interventions:
                if (
                    intervention.kind == "dream"
                    and intervention.location is not None
                ):
                    raise WorldLoadError(
                        "Dream intervention has a location: "
                        f"{intervention.id}"
                    )

                if (
                    intervention.kind != "dream"
                    and intervention.location
                    not in world.world_map.locations
                ):
                    raise WorldLoadError(
                        "Intervention has an invalid location: "
                        f"{intervention.id}"
                    )

            for (
                source_id,
                target_id,
            ), relationship in social_state.items():

                world.social.add_relationship(
                    source_id,
                    target_id,
                    affinity=agents_by_id[
                        source_id
                    ].relationships[target_id],
                    **relationship,
                )

            return world

    except WorldLoadError:
        raise

    except sqlite3.DatabaseError as exc:
        raise WorldLoadError(
            f"Invalid or corrupted world database: "
            f"{path}"
        ) from exc
