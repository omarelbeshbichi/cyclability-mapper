from .cyclability import compute_cyclability_metrics
import geopandas as gpd

def compute_metrics(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Text

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoDataFrame storing input data

    Returns
    -------
    gdf: gpd.GeoDataFrame
        GeoDataframe augmented of metrics
    """

    for index, row in gdf.iterrows():

        # Compute cyclability metrics
        cyclability_metrics = compute_cyclability_metrics(row)
        gdf.loc[index, 'cyclability_metrics'] = cyclability_metrics

    return gdf