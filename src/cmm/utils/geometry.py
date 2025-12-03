"""
Utility functions for common Shapely geometrical operations.
"""

from shapely.geometry import Point

# Geometry info
def get_bounds(geom):
    """Return (minx, miny, maxx, maxy) bounding the geometry."""
    return geom.bounds

def get_length(geom):
    """Return length of the geometry."""
    return geom.length

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