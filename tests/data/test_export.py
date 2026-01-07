from unittest.mock import patch, ANY
from pathlib import Path

from cmm.data.export.postgres import dataframe_to_postgres
from cmm.data.ingest.geojson_loader import geojson_to_gdf_from_path
from cmm.validation.geometry import validate_gdf_linestrings
from cmm.utils.misc import get_project_root
from cmm.data.normalize.cleaning import restrict_gdf
from cmm.metrics.compute_metrics import define_augmented_geodataframe
from cmm.data.export.postgres import prepare_network_segments_gdf_for_postgis

# Fixture paths
dev_geojson_path = Path(__file__).parent.parent.parent / "tests" / "_fixtures" / "dev_geojson.geojson"
root_path = get_project_root()
weights_config_path = root_path / 'src' / 'cmm' / 'metrics' / 'config' / "weights.yaml"
cyclability_config_path = root_path / 'src' / 'cmm' / 'metrics' / 'config' / "cyclability.yaml"


def test_dataframe_to_postgres():

    # Load and process GeoDataFrame
    gdf = geojson_to_gdf_from_path(dev_geojson_path)
    gdf_proc = validate_gdf_linestrings(gdf)
    gdf_proc = restrict_gdf(gdf_proc)
    gdf_proc, components = define_augmented_geodataframe(gdf_proc, weights_config_path, cyclability_config_path)
    gdf_proc_prepared = prepare_network_segments_gdf_for_postgis(gdf_proc)

    # Define geometry column
    gdf_proc_prepared.set_geometry("geom", inplace=True)

    # Patch GeoDataFrame.to_postgis to avoid actual call
    with patch.object(gdf_proc_prepared, "to_postgis") as mock_to_postgis:
        dataframe_to_postgres(
            gdf=gdf_proc_prepared,
            table_name='network_segments',
            df_type='gdf',
            user='user',
            password='pass',
            host='localhost',
            database='db',
            if_exists='append'
        )

        # Assert to_postgis was called once
        mock_to_postgis.assert_called_once_with(
            'network_segments', # table name
            ANY,        # SQLAlchemy engine object - any type tested
            if_exists='append',
            index=False
        )
