import requests
from typing import Tuple, Optional
from shapely.geometry import shape, Polygon, MultiPolygon

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

def city_to_polygon(city_name: str, 
                    country_code: str = "it",
                    tolerance: Optional[float] = 0.0005):
    """
    Get city boundary polygon from OpenStreetMap (Nominatim).
    Returns a shapely geometry.
    """

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": f"{city_name}, {country_code}",
        "format": "json",
        "polygon_geojson": 1,
        "limit": 1
    }

    headers = {
        "User-Agent": "city-boundary-script"
    }

    r = requests.get(url, params = params, headers = headers)
    r.raise_for_status()
    data = r.json()

    if not data:
        # retry without country code
        params["q"] = city_name
        r = requests.get(url, params = params, headers = headers)
        r.raise_for_status()
        data = r.json()

    if not data or "geojson" not in data[0]:
        raise ValueError(f"No boundary polygon found for {city_name}")

    geom = shape(data[0]["geojson"])

    if isinstance(geom, MultiPolygon):
        # take the largest polygon by area
        geom = max(geom.geoms, key=lambda p: p.area)

    if not isinstance(geom, Polygon):
        raise TypeError(f"Expected Polygon, got {type(geom)}")

    geom = geom.simplify(tolerance=tolerance, preserve_topology=True)

    return geom
