
def overpass_elements_to_geojson(elements: list) -> dict:
    """
    Convert Overpass API JSON elements to GeoJSON FeatureCollection

    Parameters
    ----------
    elements : list
        List of elements returned by the Overpass API

    Returns
    -------
    dict
        GeoJSON FeatureCollection containing LineString features
    """

    features = []

    for element in elements:
        # Skip if element is not a way or if geometry is not available
        if element["type"] != "way":
            continue
        if "geometry" not in element:
            continue

        # Collect linestrings coordinates
        coordinates = [
            [point["lon"], point["lat"]] for point in element["geometry"]
        ]

        # Discard degenerate geometries
        if len(coordinates) < 2:
            continue
        
        # Define feature dictionary in GeoJSON format
        feature = {
            "type": "Feature",
            "properties": {
                "osm_id": f"way/{element['id']}",
                **element.get("tags", {}) # Return empty dictionary if no tags
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "id": f"way/{element['id']}"
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }