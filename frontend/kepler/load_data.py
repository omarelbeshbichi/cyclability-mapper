import geopandas as gpd
from sqlalchemy import create_engine
import logging 
import json
import pandas as pd
import os


def load_segments() -> gpd.GeoDataFrame:
    """
    Text
    """

    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)

        # Select data from PostGIS virtual (view) table v_cyclability_score
        query = """
        SELECT
            osm_id,
            total_score,
            metric_features_scores,
            geom
        FROM v_cyclability_score
        """

        # Read data and store in GeoDataFrame
        gdf = gpd.read_postgis(query, engine, geom_col="geom", crs="EPSG:4326")

        # Load metric_features_scores
        if 'metric_features_scores' in gdf.columns:
            # Parse JSON if it is a string
            if isinstance(gdf['metric_features_scores'].iloc[0], str):
                gdf['metric_features_scores'] = gdf['metric_features_scores'].apply(json.loads)
            
            # Use a dictionary to map short labels to JSON keys
            labels = {
                "bike_inf": "bike_infrastructure",
                "maxspeed": "maxspeed",
                "surface": "surface",
                "lighting": "lighting",
                "oneway": "oneway"
            }
            
            # Build the parts dynamically
            parts = [
                f"{label}: " + gdf['metric_features_scores'].str[key].round(2).astype(str)
                for label, key in labels.items()
            ]

            # Join with newline for vertical display
            gdf['all_scores'] = parts[0].str.cat(parts[1:], sep=" | ")


        logging.info(f"Data successfully queried from PostGIS database for frontend use.")

    except Exception as e:
        logging.error(f"Error loading data from PostGIS for frontend use: {e}")
        raise 

    finally:
        engine.dispose()

    return gdf