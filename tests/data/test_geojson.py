import pandas as pd
from pathlib import Path

from cmm.data.geojson import load_geojson

def test_load_geojson():
    path = Path(__file__).parent.parent.parent / "data" / "dev_geojson.geojson"

    df = load_geojson(path)

    assert isinstance(df, pd.DataFrame)
    assert "@id" in df.columns
    assert "geometry" in df.columns
    assert "maxspeed" in df.columns
    assert "bicycle" in df.columns