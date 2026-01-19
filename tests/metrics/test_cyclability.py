from cmm.metrics.compute_metrics import compute_metrics_score_from_segment
import geopandas as gpd
from shapely.geometry import LineString
from cmm.domain.segment import CyclabilitySegment

def test_compute_metrics_from_segment_with_components():
    
    # Test segment
    segment = CyclabilitySegment(
        osm_id="way/123",
        name = "street",
        geometry= LineString([(0,0),(1,1)]),
        bike_infrastructure= "lane",
        oneway= "no",
        maxspeed= 50,
        surface= "asphalt",
        lighting= "yes",
        highway= "primary"
    )
    
    # Paths to your YAML configs
    weights_path = "src/cmm/metrics/config/weights.yaml"
    cyclability_path = "src/cmm/metrics/config/cyclability.yaml"

    metrics, components = compute_metrics_score_from_segment(segment, weights_path, cyclability_path, "cyclability")
    
    # check expected type / range
    assert isinstance(metrics, float)
    assert 0 <= metrics <= 1