"""
Utility functions for common Shapely geometrical operations.
"""

from shapely.geometry import Point, box, Polygon
from shapely.geometry.base import BaseGeometry
from pyproj import Geod

# Geometry info
def geom_from_bbox(south: float,
                    west: float,
                    north: float,
                    east: float) -> Polygon:
    """
    Define geometry (Polygon) from bounding box.
    """

    geom = box(west, south, east, north)
    return geom

def bbox_from_geom(geom: BaseGeometry) -> tuple[float, float, float, float]:
    """
    Returns bounding box of given Shapely geometry.
    """

    minx, miny, maxx, maxy = geom.bounds
    return miny, minx, maxy, maxx

def get_length(geom):
    """Return length of the geometry."""
    return geom.length

def geodesic_length(geom):
    """
    Calculate WGS84 geodesic length of segment (more accurate - it computes length on ellipsoid surface instead of using projections). 
    """
    
    geod = Geod(ellps = "WGS84") # WGS84: World Geodetic System 1984

    return geod.geometry_length(geom)

# Geometrical operations
def midpoint(geom):
    """Return the midpoint along a linear geometry."""
    return geom.interpolate(0.5, normalized = True)

def distance(a, b):
    """Return the minimum distance between two geometries."""
    return a.distance(b)

# Validity
def is_valid(geom):
    """
    Return True if a feature satisfies the OGC Simple Features validity rules.
    
    Check self-intersection, degeneracies, and correct type constraints.
    """
    return geom.is_valid

def fix_invalid(geom):
    """Return an attempted repair of an invalid geometry by using zero-width buffer."""
    return geom.buffer(0.0)

# Buffer
def buffer_zone(geom, meters):
    """Return a polygon of all points within given distance from the geometry."""
    return geom.buffer(meters)

# Coordinates
def coords(geom):
    """Return coordinates of a Point geometry."""
    if not isinstance(geom, Point):
        raise TypeError("coords() is only defined for Point objects.")
    return list(geom.coords)