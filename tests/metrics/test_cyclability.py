from cmm.metrics.cyclability import compute_cyclability_metrics
import geopandas as gpd
from shapely.geometry import LineString

def test_compute_cyclability_metrics():
    
    # Test GeoDataFrame
    gdf = gpd.GeoDataFrame({
        'highway': ['primary', 'footway'],
        'bicycle': ['yes', None],
        'geometry': [LineString([(0,0),(1,1)]), LineString([(0,0),(1,0)])]
    })
    
    metrics = compute_cyclability_metrics(gdf)
    
    # check expected type / range
    assert isinstance(metrics, float)
    assert 0 <= metrics <= 1