


from .cyclability import compute_cyclability_score
import geopandas as gpd


def compute_metrics(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Text

    Parameters
    ----------

    Returns
    -------
    """

    for _, row in gdf.iterrows():
        cyclability_score = compute_cyclability_score(row)

    return gdf_augmented