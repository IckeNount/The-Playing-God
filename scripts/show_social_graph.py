# from playing_god.core.world import World
# from playing_god.visualization.social_graph import show_social_graph


# def main():
#     world = World(seed=42)

#     show_social_graph(world.social)


# if __name__ == "__main__":
#     main()

from playing_god.persistence.sqlite_store import SQLiteStore
from playing_god.visualization.social_graph import show_social_graph

 
def main():
    store = SQLiteStore("world_1947.db")

    world = store.load_world()

    show_social_graph(world.social)


if __name__ == "__main__":
    main()


