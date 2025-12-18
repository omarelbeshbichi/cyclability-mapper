import pytest
from pathlib import Path

@pytest.fixture
def dev_geojson_path():
    return Path(__file__).parent / "_fixtures" / "dev_geojson.geojson"
