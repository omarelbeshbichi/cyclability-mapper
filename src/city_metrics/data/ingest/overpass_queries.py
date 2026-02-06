from shapely.geometry import Polygon
from typing import Optional


def roads_in_bbox(south: float, west: float, north: float, east: float, timeout: Optional[int] = 50) -> str:
    """
    Build Overpass QL query fetching road geometries within a defined bounding box
    """

    return f"""
    [out:json][timeout:{timeout}];
    (
      way
        ["highway"]
        ({south},{west},{north},{east});
    );
    out geom;
    """

def roads_in_polygon(city_polygon: Polygon,
                     timeout: Optional[int] = 50) -> str:
    """
    Build Overpass QL query fetching road geometries within a defined Polygon
    """

    # Extract coordinates of polygon shape
    coords = city_polygon.exterior.coords
    # Reconstruct polygon query string in Overpass QL format
    # " ".join([a, b]) -> add space between all elements of list 
    poly_query = " ".join(f"{lat} {lon}" for lon, lat in coords)  # Overpass wants lat lon

    # Build the Overpass QL query
    query = f"""
    [out:json][timeout:{timeout}];
    (
      way
        ["highway"]
        (poly:"{poly_query}"); 
    );
    out geom;
    """

    return query

def roads_in_municipality(admin_unit: str, admin_level: int = 8) -> str:
    """
    Build Overpass QL query fetching road geometries within a given administrative boundary

    Parameters
    ----------
    admin_unit : str
        Name of the administrative unit (e.g. "Oslo")
    admin_level : int
        OSM administrative level (default: 8 = municipality)
    """

    return f"""
    [out:json][timeout:50];
    // Find the administrative boundary of the city
    area["name"="{admin_unit}"]["admin_level"={admin_level}]->.searchArea;
    
    // Gather all ways tagged "highway" inside that area
    (
      way["highway"](area.searchArea);
    );
    
    // Output geometries
    out geom;
    """