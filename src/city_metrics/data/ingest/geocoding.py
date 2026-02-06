import requests
from typing import Tuple, Optional, List
from shapely.geometry import shape, Polygon, MultiPolygon, Point, box
import logging
from math import cos, radians

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
    
    headers = {"User-Agent": "city_metrics-pipeline"}

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

    if not data:
        raise ValueError(f"No results found for city {city_name}")
    
    # Convert geojson to shapely geometry
    # if not geojson, fallback to Point with given coordinates
    geom = shape(data[0].get("geojson", {"type": "Point", "coordinates": [float(data[0]['lon']), float(data[0]['lat'])]}))


    if isinstance(geom, MultiPolygon):
        # take the largest polygon by area
        geom = max(geom.geoms, key=lambda p: p.area)

    # If Point, convert to small box buffer (Polygon)
    if isinstance(geom, Point):
        lon, lat = geom.x, geom.y # [deg]
        box_half_km = 5  # 10 km box size 
        
        # Get delta degrees of latitude for 5 km distance
        # (kilometer shift per degree latitude is: 110.574 [km/deg] - everywhere)
        delta_lat = box_half_km / 110.574 # [deg]
        
        # Get longitude shift as function of latitude
        # At equator maximum change, 111.32 [km/deg] - at poles no change (longitude lines converge to poles)
        # It can be shown that circumference arc (d) due to given longitude shift (alpha) is -- d = alpha R cos(phi) [km]
        #   - alpha: longitude shift [rad]
        #   - R: earth radius [km]
        #   - phi: latitude [rad]
        
        # For single longitude degree, the distance in km is: d = 2(pi)/360 * R * cos(phi) = 111.32 * cos (phi) [km/deg]
        # It can be used to determine delta degrees of longitude for 5 km distance (box_half_km)
        delta_lon = box_half_km / (111.320 * cos(radians(lat))) # [deg]

        geom = Polygon([
            (lon - delta_lon, lat - delta_lat),
            (lon - delta_lon, lat + delta_lat),
            (lon + delta_lon, lat + delta_lat),
            (lon + delta_lon, lat - delta_lat),
            (lon - delta_lon, lat - delta_lat)
        ])
        logging.warning(f"Using buffer bounding box (10 km) around city center - no GeoJSON available from Nominatism for {city_name}")

    if not isinstance(geom, Polygon):
        raise TypeError(f"Expected Polygon, got {type(geom)}")

    # Simplify Polygon for easier API fetch
    geom = geom.simplify(tolerance=tolerance, preserve_topology=True)

    return geom


def split_polygon_into_bboxes(polygon, step_deg: float = 0.005) -> List[tuple]:
    """
    Split a polygon bounding box into smaller bbox tiles.

    Returns list of boxes (south, west, north, east)
    """
    minx, miny, maxx, maxy = polygon.bounds  # lon/lat

    tiles = []

    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            south = y
            west = x
            north = min(y + step_deg, maxy)
            east = min(x + step_deg, maxx)

            tile = box(west, south, east, north)

            # only keep tiles that intersect the city polygon
            if polygon.intersects(tile):
                tiles.append((south, west, north, east))

            x += step_deg
        y += step_deg

    return tiles