
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D


def build_network():
    """Create a network with latency and reliability data."""
    graph = nx.Graph()

    graph.add_nodes_from(["A", "B", "C", "D", "E", "F"])

    # (node_1, node_2, latency_ms, probability_up)
    links = [
        ("A", "B", 2.0, 0.98),
        ("A", "C", 1.4, 0.95),
        ("B", "C", 0.5, 0.97),
        ("B", "D", 1.2, 0.96),
        ("C", "D", 1.5, 0.98),
        ("C", "E", 3.5, 0.93),
        ("D", "E", 0.7, 0.97),
        ("D", "F", 2.2, 0.96),
        ("E", "F", 1.0, 0.98),
    ]

    for u, v, latency, probability_up in links:
        graph.add_edge(
            u,
            v,
            latency_ms=latency,
            probability_up=probability_up,
            is_up=True,
        )

    return graph


def get_operational_graph(graph):
    """Return a copy containing only operational links."""
    operational = graph.copy()

    failed_edges = [
        (u, v)
        for u, v, data in operational.edges(data=True)
        if not data["is_up"]
    ]

    operational.remove_edges_from(failed_edges)
    return operational


def find_shortest_route(graph, source, target):
    """Find the lowest-latency route using operational links."""
    operational = get_operational_graph(graph)

    if not nx.has_path(operational, source, target):
        return None, None

    path = nx.shortest_path(
        operational,
        source=source,
        target=target,
        weight="latency_ms",
    )

    total_latency = sum(
        operational.edges[u, v]["latency_ms"]
        for u, v in zip(path, path[1:])
    )

    return path, total_latency


def draw_network_panel(
    ax,
    graph,
    route,
    latency,
    title,
    positions,
    failed_edge=None,
):
    """Draw one network state and highlight its selected route."""
    # Draw all physical links in gray.
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        edge_color="#94a3b8",
        width=2,
    )

    # Highlight the selected route in green.
    if route is not None:
        route_edges = list(zip(route, route[1:]))

        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=route_edges,
            ax=ax,
            edge_color="#16a34a",
            width=4,
        )

    # Show a failed link in red with a dashed line.
    if failed_edge is not None:
        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=[failed_edge],
            ax=ax,
            edge_color="#dc2626",
            style="dashed",
            width=3,
        )

    # Display each link's latency.
    edge_labels = {
        (u, v): f"{data['latency_ms']:.1f} ms"
        for u, v, data in graph.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        ax=ax,
        font_size=8,
        rotate=False,
    )

    # Draw routers and their labels.
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_color="#dbeafe",
        edgecolors="#2563eb",
        node_size=1000,
        linewidths=1.5,
    )

    nx.draw_networkx_labels(
        graph,
        positions,
        ax=ax,
        font_size=11,
        font_weight="bold",
    )

    # Prepare the title.
    route_text = (
        " -> ".join(route)
        if route is not None
        else "No available route"
    )
    latency_text = (
        f"{latency:.1f} ms"
        if latency is not None
        else "N/A"
    )

    ax.set_title(
        f"{title}\n{route_text}\nTotal latency: {latency_text}",
        fontsize=11,
    )

    # Explain the colors.
    legend_items = [
        Line2D(
            [0], [0],
            color="#16a34a",
            linewidth=4,
            label="Selected route",
        )
    ]

    if failed_edge is not None:
        legend_items.append(
            Line2D(
                [0], [0],
                color="#dc2626",
                linestyle="dashed",
                linewidth=3,
                label="Failed link",
            )
        )

    ax.legend(
        handles=legend_items,
        loc="lower right",
        fontsize=8,
    )

    ax.axis("off")


def draw_comparison(
    graph_before,
    graph_after,
    route_before,
    latency_before,
    route_after,
    latency_after,
    failed_edge,
):
    """Visualize the network before and after a link failure."""
    # Keep the same layout in both panels for a fair visual comparison.
    positions = {
        "A": (0, 1),
        "B": (1, 2),
        "C": (1, 0),
        "D": (2, 1),
        "E": (3, 0),
        "F": (4, 1),
    }

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    draw_network_panel(
        axes[0],
        graph_before,
        route_before,
        latency_before,
        "Before link failure",
        positions,
    )

    draw_network_panel(
        axes[1],
        graph_after,
        route_after,
        latency_after,
        "After link failure",
        positions,
        failed_edge=failed_edge,
    )

    fig.suptitle(
        "Predictive Fault-Aware Routing - Baseline Simulation",
        fontsize=14,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.90])

    # Save the figure so it can be inspected or used in documentation.
    output_path = Path("outputs") / "routing_comparison.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    print(f"\nVisual saved to: {output_path.resolve()}")

    plt.show()


def main():
    source, target = "A", "F"
    failed_edge = ("C", "D")

    # Save the original state before simulating a failure.
    graph_before = build_network()
    graph_after = graph_before.copy()

    route_before, latency_before = find_shortest_route(
        graph_before, source, target
    )

    # Simulate a failure on link C-D.
    graph_after.edges[failed_edge]["is_up"] = False

    route_after, latency_after = find_shortest_route(
        graph_after, source, target
    )

    print("=== Before failure ===")
    if route_before is not None:
        print(
            f"Route: {' -> '.join(route_before)} "
            f"| latency = {latency_before:.1f} ms"
        )
    else:
        print("No available route.")

    print(f"\nSimulated link failure: {failed_edge[0]}-{failed_edge[1]}")
    print("=== After failure ===")

    if route_after is not None:
        print(
            f"Route: {' -> '.join(route_after)} "
            f"| latency = {latency_after:.1f} ms"
        )
    else:
        print("No available route.")

    draw_comparison(
        graph_before,
        graph_after,
        route_before,
        latency_before,
        route_after,
        latency_after,
        failed_edge,
    )


if __name__ == "__main__":
    main()
