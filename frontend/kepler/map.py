from keplergl import KeplerGl
from .load_data import load_segments


def create_map(user="user", host="localhost", password="pass", database="db"):

    gdf = load_segments(user, host, password, database)
    gdf = gdf.rename_geometry("geometry")

    m = KeplerGl(height=800)
    m.add_data(gdf, "segments")

    # THIS is the correct attribute
    m.config = {
        "version": "v1",
        "config": {
            "visState": {
                "layers": [
                    {
                        "id": "cyclability",
                        "type": "geojson",
                        "config": {
                            "dataId": "segments",
                            "label": "Cyclability",
                            "columns": {
                                "geojson": "geometry"
                            },
                            "isVisible": True,
                            "visConfig": {
                                "thickness": 1,
                                "strokeColorRange": {
                                    "type": "sequential",
                                    "category": "Custom",
                                    "colors": [
                                        "#d7191c",
                                        "#fdae61",
                                        "#ffffbf",
                                        "#a6d96a",
                                        "#1a9641"
                                    ]
                                }
                            }
                        },
                        "visualChannels": {
                            "strokeColorField": {
                                "name": "total_score",
                                "type": "real"
                            },
                            "strokeColorScale": "linear"
                        }
                    }
                ]
            }
        }
    }

    return m