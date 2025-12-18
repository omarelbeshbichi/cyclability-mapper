
import geopandas as gpd
from shapely.geometry import LineString
from cmm.metrics.compute_metrics import compute_metrics

def test_compute_metrics_adds_column():
    
    gdf = gpd.GeoDataFrame({
        'geometry':[LineString([(0,0),(1,1)]), LineString([(0,0),(2,2)])]
    })
    
    result = compute_metrics(gdf)

    assert 'cyclability_metrics' in result.columns # metrics added
    assert len(result) == len(gdf) # same rows