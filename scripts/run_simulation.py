from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Allow running directly with:
# python3 scripts/run_simulation.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from playing_god.core.world import World
from playing_god.persistence.sqlite_store import (
    PersistenceError,
    WorldLoadError,
    load_world,
    save_world,
)


DEFAULT_WORLD_DIR = PROJECT_ROOT / "data" / "worlds"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create, continue, and persist "
            "The Playing God simulation."
        )
    )

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--seed",
        type=int,
        help=(
            "Create a new universe using this "
            "deterministic seed."
        ),
    )

    mode.add_argument(
        "--load",
        type=Path,
        help=(
            "Load an existing SQLite universe."
        ),
    )

    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help=(
            "Number of simulated days to advance. "
            "Default: 1"
        ),
    )

    parser.add_argument(
        "--db",
        type=Path,
        help=(
            "Database path for a new universe. "
            "Defaults to "
            "data/worlds/world_<seed>.db"
        ),
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help=(
            "Print the world report after running."
        ),
    )

    return parser


def resolve_new_world_path(
    seed: int,
    explicit_path: Path | None,
) -> Path:
    if explicit_path is not None:
        return explicit_path

    return (
        DEFAULT_WORLD_DIR
        / f"world_{seed}.db"
    )


def create_new_world(
    seed: int,
    db_path: Path,
) -> World:
    if db_path.exists():
        raise PersistenceError(
            "Refusing to create a new universe "
            f"because the database already exists: "
            f"{db_path}\n"
            "Use --load to continue it, or choose "
            "another --db path."
        )

    return World(seed=seed)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.days < 0:
        parser.error(
            "--days must be zero or greater"
        )

    try:
        if args.seed is not None:
            db_path = resolve_new_world_path(
                args.seed,
                args.db,
            )

            world = create_new_world(
                args.seed,
                db_path,
            )

            mode = "created"

        else:
            db_path = args.load

            world = load_world(
                db_path
            )

            mode = "loaded"

        starting_day = world.day

        if args.days:
            world.run(
                args.days
            )

        save_world(
            world,
            db_path,
        )

        print(
            f"Universe {world.seed} {mode}"
        )

        print(
            f"Day {starting_day} "
            f"-> Day {world.day}"
        )

        print(
            f"Agents: {len(world.agents)}"
        )

        print(
            f"Saved: {db_path}"
        )

        if args.report:
            print()
            print(world.report())

        return 0

    except (
        PersistenceError,
        WorldLoadError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())