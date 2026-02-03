import click
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

@click.command()
@click.option("--city", "--city-name", "city_name", type=str, required=True)
@click.option("--budget", "budget_km", type=float, required=True)
def main(city_name, budget_km):
    from city_metrics.analysis.graph.build import build_graph
    from city_metrics.analysis.graph.metrics import best_edges_under_budget, city_cyclability
    from city_metrics.services.metrics.loader import load_segments_for_metrics_recompute, load_data_for_city_metrics_compute
    import networkx as nx

    logging.info("LOAD SEGMENTS FOR GRAPH - EXPERIMENTAL JOB")
    gdf = load_segments_for_metrics_recompute(city_name)

    logging.info("LOAD METRICS DATA")
    gdf_metrics = load_data_for_city_metrics_compute(city_name)

    # Attach metric used for graph weighting
    gdf["total_score"] = gdf_metrics["total_score"]

    logging.info("BUILD GRAPH")
    G = build_graph(gdf)

    logging.info("GRAPH STATS | nodes=%s edges=%s components=%s",
        G.number_of_nodes(),
        G.number_of_edges(),
        nx.number_connected_components(G),
    )

    logging.info("RUN BUDGET OPTIMIZATION (budget = %.2f km)", budget_km)
    selected = best_edges_under_budget(G, budget_km=budget_km)

    # Sort results by highest ratio (segment_value / effective_length)
    selected.sort(key=lambda x: x["ratio"], reverse=True)

    # Return values in CLI (experimental - for now keep only this as output)
    logging.info("SELECTED %s EDGES", len(selected))
    for s in selected:
        click.echo(
            f"Edge {s['segment']} | "
            f"length = {s['length_km']:.3f} km | "
            f"edge_value = {s['edge_value']:.2e} | "
            f"ratio = {s['ratio']:.2e}"
        )


    sources = list(G.nodes())

    # Compute approximate original cyclability metrics
    logging.info("COMPUTE BASELINE CYCLABILITY")
    old_metric = city_cyclability(G, sources)

    # Assume all segments considered are improved to 1.0 - recompute metrics
    logging.info("COMPUTE POST-UPGRADE CYCLABILITY")
    G_new = G.copy()

    selected_ids = {s["segment"] for s in selected}

    for _, _, d in G_new.edges(data=True):
        if d.get("osm_id") in selected_ids:           
            d["score"] = 1.0 # assign max score to given segment
            d["weight"] = d["length"] / d["score"]

    new_metric = city_cyclability(G_new, sources)

    improvement = (old_metric - new_metric) / old_metric * 100
    
    # Log data
    logging.info(
        "CITY CYCLABILITY | before=%.3f after=%.3f improvement=%.2f%% (varies at each run due to sampling)",
        old_metric,
        new_metric,
        improvement,
    )

    
    logging.info("DONE")

if __name__ == "__main__":
    main()