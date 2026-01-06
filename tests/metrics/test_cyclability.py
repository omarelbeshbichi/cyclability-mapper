from cmm.metrics.cyclability import compute_metrics_from_segment
import geopandas as gpd
from shapely.geometry import LineString

def test_compute_metrics_from_segment():
    
    # Test segment
    segment = {
        'highway': 'primary',
        'bicycle': 'yes',
        'geometry': LineString([(0,0),(1,1)]),
        'surface': 'asphalt',
        'lighting': 'yes',
        'maxspeed': 50,
        'bike_infrastructure': 'lane',
        'oneway': 'no'
    }
    
    # Paths to your YAML configs
    weights_path = "src/cmm/metrics/config/weights.yaml"
    cyclability_path = "src/cmm/metrics/config/cyclability.yaml"

    metrics = compute_metrics_from_segment(segment, weights_path, cyclability_path)
    
    # check expected type / range
    assert isinstance(metrics, float)
    assert 0 <= metrics <= 1