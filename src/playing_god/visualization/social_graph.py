from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx


def show_social_graph(social) -> None:
    graph = social.graph

    # Reproducible positioning.
    pos = nx.spring_layout(
        graph,
        seed=42,
        k=1.2,
    )

    plt.figure(figsize=(10, 8))

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=1200,
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=8,
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=True,
        alpha=0.25,
        arrowsize=12,
    )

    plt.title("The Playing God — Social Network")
    plt.axis("off")
    plt.tight_layout()
    plt.show()