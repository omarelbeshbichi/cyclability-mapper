from shapely import LineString
from shapely import Point

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