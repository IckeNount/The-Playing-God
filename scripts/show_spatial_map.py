from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from playing_god.persistence.sqlite_store import load_world
from playing_god.visualization.spatial_map import show_spatial_map


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show a persisted world's spatial debug map."
    )
    parser.add_argument(
        "database",
        type=Path,
        help="Path to a saved SQLite universe.",
    )
    args = parser.parse_args()

    show_spatial_map(load_world(args.database))


if __name__ == "__main__":
    main()
