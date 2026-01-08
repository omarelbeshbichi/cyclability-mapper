
def roads_in_bbox(south: float, west: float, north: float, east: float) -> str:
    """
    Build Overpass QL query fetching road geometries within a defined bounding box
    """

    return f"""
    [out:json][timeout:25];
    (
      way
        ["highway"]
        ({south},{west},{north},{east});
    );
    out geom;
    """

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