from shapely import LineString, Point
from cmm.validation.geometry import validate_gdf_linestrings
import geopandas as gpd

from cmm.utils.geometry import get_bounds, get_length, midpoint, distance, is_valid, fix_invalid, buffer_zone, coords

# Create simple Shapely object to perform test with
line = LineString([(0, 0), (1, 0), (1, 1)])
point1 = Point(0, 0)
point2 = Point(1, 1)

def test_geometry_functions():
    assert get_bounds(line) == (0.0, 0.0, 1.0, 1.0)
    assert get_length(line) == 2.0
    assert midpoint(line) == Point(1.0, 0.0)
    assert distance(point1, point2) == 2**0.5
    assert is_valid(line) == True
    assert buffer_zone(line, 1).geom_type == "Polygon"
    assert coords(point1) == [(0.0, 0.0)]

def test_validate_gdf_linestrings_filters_invalid():
    
    # Test GeoDataFrame
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0,0),(1,1)]), Point((0,0))]
    })
    
    validated = validate_gdf_linestrings(gdf)
    
    assert all(validated.geometry.type == "LineString")
    assert all(validated.geometry.length > 0)