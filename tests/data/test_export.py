from unittest.mock import MagicMock, patch
from cmm.data.export.postgres import gdf_to_postgres  
from pathlib import Path
from cmm.data.ingest.geojson_loader import geojson_to_gdf_from_path

path = Path(__file__).parent.parent.parent / "tests" / "_fixtures" / "dev_geojson.geojson"

@patch('cmm.data.export.postgres.psycopg2.connect')
def test_gdf_to_postgres(mock_connect, dev_geojson_path):

    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    gdf = geojson_to_gdf_from_path(dev_geojson_path)
    gdf_to_postgres(gdf, table_name='test_table')

    # Checks
    assert mock_cursor.execute.call_count == len(gdf) + 1  # insert + truncate
    mock_conn.commit.assert_called_once() # check commit works
    mock_cursor.close.assert_called_once() # check cursor is closed at end
    mock_conn.close.assert_called_once() # check connection is closed at end