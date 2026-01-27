from unittest.mock import patch, ANY
from pathlib import Path
from cmm.data.export.postgres import dataframe_to_postgres
from cmm.data.ingest.geojson_loader import geojson_to_gdf_from_path
from cmm.validation.geometry import validate_gdf_linestrings
from cmm.utils.misc import get_project_root
from cmm.data.normalize.cleaning import restrict_gdf
from cmm.metrics.compute_metrics import define_augmented_geodataframe
from cmm.data.export.postgres import prepare_network_segments_gdf_for_postgis
from cmm.utils.config_helpers import read_config

# Fixture paths
dev_geojson_path = Path(__file__).parent.parent.parent / "tests" / "_fixtures" / "dev_geojson.geojson"
root_path = get_project_root()
weights_config_path = root_path / "src" / "cmm" / "metrics" / "config" / "weights.yaml"
cyclability_config_path = root_path / "src" / "cmm" / "metrics" / "config" / "cyclability.yaml"

# Get config info
#(remove version info from resulting dict)
weights_config = read_config("weights", "yaml", weights_config_path)
weights_config.pop("version")

metrics_config = read_config("cyclability", "yaml", cyclability_config_path)
metrics_config.pop("version")

# Init bike_infra values for which score is 1.0 (track, etc.)
# Dict used in prepare_cyclability_segment for maxspeed missing info definition
# Defined here to avoid definition at each gdf row and at each chunk 
bike_infra_mapping = metrics_config["bike_infrastructure"]["mapping"]
excellent_bike_infra = {k for k, v in bike_infra_mapping.items() if v == 1.0}

city_name = "city"

def test_dataframe_to_postgres():

    # Load and process GeoDataFrame
    gdf = geojson_to_gdf_from_path(dev_geojson_path)
    gdf_proc = validate_gdf_linestrings(gdf)
    gdf_proc = restrict_gdf(gdf_proc)
    gdf_proc, components = define_augmented_geodataframe(gdf_proc, 
                                                         weights_config, 
                                                         metrics_config,
                                                         cyclability_config_path,
                                                         excellent_bike_infra)
    gdf_proc_prepared = prepare_network_segments_gdf_for_postgis(city_name, gdf_proc)

    # Define geometry column
    gdf_proc_prepared.set_geometry("geom", inplace=True)

    # Patch GeoDataFrame.to_postgis to avoid actual call
    with patch.object(gdf_proc_prepared, "to_postgis") as mock_to_postgis:
        dataframe_to_postgres(
            gdf = gdf_proc_prepared,
            table_name = "network_segments",
            df_type = "gdf",
            if_exists = "append"
        )

        # Assert to_postgis was called once
        mock_to_postgis.assert_called_once_with(
            "network_segments", # table name
            ANY,        # SQLAlchemy engine object - any type tested
            if_exists = "append",
            index = False
        )
