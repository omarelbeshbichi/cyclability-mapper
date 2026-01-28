import geopandas as gpd
from shapely.geometry import LineString
from city_metrics.metrics.compute_metrics import define_augmented_geodataframe, compute_metrics_score_from_segment, compute_total_city_metrics
from city_metrics.utils.config_helpers import read_config
from city_metrics.domain.segment import CyclabilitySegment
from city_metrics.utils.geometry import geodesic_length


def test_define_augmented_geodataframe():
    
    # Test GeoDataFrame
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0,0),(1,1)]), LineString([(0,0),(2,2)])],
        "highway": ["primary", "footway"],
        "bicycle": ["yes", None],
        "surface": ["asphalt", "gravel"],
        "lit": ["yes", None],
        "maxspeed": [50, None]
    })
    
    # Paths to YAML configs
    weights_path = "src/city_metrics/metrics/config/weights.yaml"
    cyclability_path = "src/city_metrics/metrics/config/cyclability.yaml"

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", cyclability_path)
    metrics_config.pop("version")

    # Init bike_infra values for which score is 1.0 (track, etc.)
    # Dict used in prepare_cyclability_segment for maxspeed missing info definition
    # Defined here to avoid definition at each gdf row and at each chunk 
    bike_infra_mapping = metrics_config["bike_infrastructure"]["mapping"]
    excellent_bike_infra = {k for k, v in bike_infra_mapping.items() if v == 1.0}


    result, result_components = define_augmented_geodataframe(gdf, 
                                                              weights_config, 
                                                              metrics_config,
                                                              cyclability_path,
                                                              excellent_bike_infra)

    assert "cyclability_metrics" in result.columns # metrics added
    assert len(result) == len(gdf) # same rows

def test_compute_metrics_score_from_segment():
    
    # Test segment
    segment = CyclabilitySegment(
        osm_id="way/123",
        name = "street",
        geometry= LineString([(0,0),(1,1)]),
        segment_length= geodesic_length(LineString([(0,0),(1,1)])),
        bike_infrastructure= "lane",
        oneway= "no",
        maxspeed= 50,
        surface= "asphalt",
        lighting= "yes",
        highway= "primary"
    )
    
    # Paths to YAML configs
    weights_path = "src/city_metrics/metrics/config/weights.yaml"
    cyclability_path = "src/city_metrics/metrics/config/cyclability.yaml"

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", cyclability_path)
    metrics_config.pop("version")

    metrics, components = compute_metrics_score_from_segment(segment, 
                                                             weights_config, 
                                                             metrics_config,
                                                             cyclability_path, 
                                                             "cyclability")

    # Check if all components are within range
    to_test = all(0 <= x <= 1 for x in components.values())
 
    # check expected type and range
    assert isinstance(metrics, float)
    assert 0 <= metrics <= 1
    
    assert to_test == True

def test_compute_total_city_metrics():

    # Test GeoDataFrame
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0,0),(1,1)]), LineString([(0,0),(2,2)])],
        "highway": ["primary", "footway"],
        "bicycle": ["yes", None],
        "surface": ["asphalt", "gravel"],
        "lit": ["yes", None],
        "maxspeed": [50, None],
        "segment_length": [1, 2],
        "total_score": [0.7, 0.8],
        "missing_info": [{"maxspeed": False, "surface": True, "lighting": True}]*2
    })

    metrics_name = "cyclability"

    weights_path = "src/city_metrics/metrics/config/weights.yaml"

    city_score, feature_uncertainty, city_score_uncertainty = compute_total_city_metrics(gdf, metrics_name, weights_path)

     # Check if all uncertainty components are within range
    assert all(0 <= x <= 1 for x in feature_uncertainty)

    # check expected type and range
    assert isinstance(city_score, float)
    assert 0 <= city_score <= 1

    assert isinstance(city_score_uncertainty, float)
    assert 0 <= city_score_uncertainty <= 1
