import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
from city_metrics.utils.geometry import geodesic_length


def build_graph(gdf: gpd.GeoDataFrame,
                weight: str = "cycling_cost") -> nx.Graph:
    """
    Build NetworkX graph based on GeoDataFrame information, segment lengths, and metric score

    Define cycling cost per segment as segment length / segment score
    """

    G = nx.Graph()

    for _, row in gdf.iterrows():

        # geometry
        geom: LineString = row.geometry
        start = geom.coords[0]
        end = geom.coords[1]
        length = geodesic_length(geom) # length in meters

        # segment score
        score = max(row["total_score"], 1e-3) 
        
        # segment cycling cost
        cycling_cost = length / score # very long segment + low cyclability -> high cost
        
        # build graph
        G.add_edge(
            start,
            end,
            weight = cycling_cost,
            length = length,
            osm_id = row.get("osm_id"),
            score = row.get("total_score")
        )

    return G