import requests
from typing import Tuple
from shapely.geometry import shape, Polygon

def city_to_bbox(city_name: str) -> Tuple[float, float, float, float]:
    """
    Obtain bounding box starting from city name using Nominatim.

    Nominatim returns a JSON file containing several ways to locate the requested city.
    
    Something like this:
    [
        {
            "place_id": "12345",
            "osm_type": "relation",
            "osm_id": "7444",
            "boundingbox": ["59.85", "60.05", "10.60", "10.85"],
            "lat": "59.9139",
            "lon": "10.7522",
            "display_name": "Oslo, Norway",
            "type": "city",
            "importance": 0.8
        }
    ]

    Returns
    -------
    (south, west, north, east)
    """

    url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": city_name,
        "format": "json", # JSON output
        "limit": 1
    }
    
    headers = {"User-Agent": "cmm-pipeline"}

    r = requests.get(url, 
                     params = params, 
                     headers = headers, 
                     timeout = 10)
    r.raise_for_status()
    
    
    data = r.json()

    if not data:
        raise ValueError(f"City not found: {city_name}")

    south, north, west, east = map(float, data[0]["boundingbox"])

    return south, west, north, east

def city_to_polygon(city_name: str) -> Polygon:
    """
    Obtain the city boundary as a polygon starting from the city name using Nominatim.

    Nominatim returns a JSON containing a GeoJSON polygon of the city when `polygon_geojson=1` is used.

    Returns
    -------
    shapely.geometry.Polygon or MultiPolygon
        The polygon representing the city boundary.
    """

    url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": city_name,
        "format": "json",        # JSON output
        "limit": 1,
        "polygon_geojson": 1     # Get the city boundary polygon
    }
    
    headers = {"User-Agent": "cmm-pipeline"}

    r = requests.get(url, 
                     params = params, 
                     headers = headers, 
                     timeout = 10)
    r.raise_for_status()
    
    data = r.json()

    if not data:
        raise ValueError(f"City not found: {city_name}")

    geom = data[0].get("geojson")

    if not geom:
        raise ValueError(f"No polygon found for city: {city_name}")

    city_polygon = shape(geom)

    if not isinstance(city_polygon, Polygon):
        raise ValueError(f"Returned geometry is not a Polygon for city: {city_name}")

    return city_polygon