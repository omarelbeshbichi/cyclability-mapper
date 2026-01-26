
import geopandas as gpd
from shapely.geometry import LineString
from cmm.metrics.compute_metrics import define_augmented_geodataframe
from cmm.utils.config_reader import read_config
def test_compute_metrics_adds_column():
    
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0,0),(1,1)]), LineString([(0,0),(2,2)])],
        "highway": ["primary", "footway"],
        "bicycle": ["yes", None],
        "surface": ["asphalt", "gravel"],
        "lit": ["yes", None],
        "maxspeed": [50, None]
    })
    
    # Paths to your YAML configs
    weights_path = "src/cmm/metrics/config/weights.yaml"
    cyclability_path = "src/cmm/metrics/config/cyclability.yaml"

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", cyclability_path)
    metrics_config.pop("version")

    result, result_components = define_augmented_geodataframe(gdf, weights_config, metrics_config)

    assert "cyclability_metrics" in result.columns # metrics added
    assert len(result) == len(gdf) # same rows