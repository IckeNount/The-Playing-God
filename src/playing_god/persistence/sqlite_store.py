from __future__ import annotations

import json
import sqlite3

from collections import Counter
from pathlib import Path

from playing_god.core.agent import Agent
from playing_god.core.events import Event
from playing_god.core.perception import (
    Belief,
    Observation,
    belief_key,
)
from playing_god.core.rng import (
    create_rng,
    restore_state,
    serialize_state,
)
from playing_god.core.world import World


SCHEMA_VERSION = 6


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
                reputation,
                goal,
                actions_json,
                current_location,
                destination
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
                    location
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
                    location
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        with _connect(path) as conn:
            conn.executescript(SCHEMA)

            _migrate_agents_to_v3(conn)
            _migrate_events_to_v4(conn)
            _migrate_agents_to_v5(conn)

            _save_world_state(
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
) -> None:
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

        agents_by_id[agent_id].observations.append(
            Observation(
                day=row["day"],
                kind=row["kind"],
                subject_id=row["subject_id"],
                value=row["value"],
                source_id=row["source_id"],
                reliability=row["reliability"],
                location=row["location"],
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
        with _connect(path) as conn:
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

            if has_perception_state:
                _validate_perception_tables(conn)

            agents = _load_agents(conn)

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
                )
                _load_beliefs(
                    conn,
                    agents_by_id,
                )

            # Do NOT call World(seed).
            #
            # That would generate a temporary population
            # and consume RNG draws before restoration.
            world = World.__new__(World)

            world.seed = state["seed"]
            world.day = state["day"]
            world.agents = agents

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
