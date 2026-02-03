import networkx as nx
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def city_cyclability(G: nx.Graph, sources: list):
    """
    Approximate average weighted shortest path length.
    Uses node sampling for speed.
    """

    total = 0.0
    count = 0

    # for each node
    for u in sources:
        # compute weighted length (weight is cyclability cost)
        lengths = nx.single_source_dijkstra_path_length(G, u, weight="weight")
        for v, d in lengths.items():
            if u != v:
                total += d # accumulate length
                count += 1

    # Get approximate metrics (cyclability)
    metrics = total / count

    return metrics


def compute_edge_value(edge_data, betweenness):
    """
    Simple, intuitive value of upgrading an edge:
    - central edges matter more
    - bad edges matter more
    """
    # Get edge score
    score = edge_data["score"]

    # Get edge length in km
    length_km = edge_data["length"] / 1000

    if length_km <= 0:
        return 0.0

    # Return the value of the edge in these terms:
    # - betweenness: how important edge is in the network
    # - score: worse edges get higher priority
    return betweenness * (1.0 / score)

def best_edges_under_budget(G: nx.Graph, budget_km: float):

    logging.info("Starting edges betwenness computation")
    # Compute edge betweenness centrality for the network
    # Indication of how often each edge appears in shortest paths between given A - B nodes
    # Weighted by cycling cost ("weight")
    # Getting normalized values (normalized = True)
    # Using 100 random nodes instead of all - for speed (k)
    edge_bw = nx.edge_betweenness_centrality(G, weight = "weight", normalized=True, k = 100)
    
    # Total number of edges (for logging)
    total = G.number_of_edges()

    # Enumerate all edges with:
    # u = start node
    # v = end node
    # d = dict of edge features
    candidates = []
    for idx, (u, v, d) in enumerate(G.edges(data = True), start = 1):
        
        # Remove irrelevant OSM highway types
        if d.get("highway") in {"footway", "crossing", "service"}:
            continue

        # Logging - progress every 100 rows or last row
        if idx % 100 == 0 or idx == total:
           logger.info(f"Processed {idx}/{total} segments.")

        # Define edge length, skip if too long for budget
        # Skip very short edges - assume at least 40 m long
        length_km = d["length"] / 1000
        if length_km > budget_km or length_km < 0.04:
            continue

        # Extract edge betweenness
        # take into account both start->end and end->start directionality
        edge_betweennes = edge_bw.get((u, v), edge_bw.get((v, u), 0.0))
        
        # Compute how valuable is edge, skip if not meaningful edge_value
        edge_value = compute_edge_value(d, edge_betweennes)
        if edge_value <= 0:
            continue
        
        # Add effective limit of 50 m to length_km - 
        # Avoid ratio to blow for short segments
        effective_length = max(length_km, 0.05)

        # Store results in dict
        candidates.append({
            "segment": d.get("osm_id"),
            "length_km": length_km,
            "edge_value": edge_value,
            "ratio": edge_value / effective_length
        })

    # Sort findal candidates by edge_value density
    candidates.sort(key=lambda x: x["ratio"], reverse=True)

    # Only return candidates within budgeted km
    selected = []
    spent = 0.0

    for c in candidates:
        if spent + c["length_km"] <= budget_km:
            selected.append(c)
            spent += c["length_km"]

    return selected