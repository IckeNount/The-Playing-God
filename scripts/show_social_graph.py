import sys

from playing_god.persistence.sqlite_store import load_world
from playing_god.visualization.social_graph import show_social_graph


def main(db_path: str = "world_1947.db") -> None:
    world = load_world(db_path)

    show_social_graph(world.social)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "world_1947.db")

