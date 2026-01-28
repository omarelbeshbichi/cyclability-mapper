import geopandas as gpd
from sqlalchemy import create_engine, text
import logging 
import json
import os

def load_segments_for_viz(city_name: str) -> gpd.GeoDataFrame:
    """
    Load cyclability segments from PostGIS for visualization use.
    """

    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    # Create SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

    try:

        # Select data from PostGIS virtual (view) table v_cyclability_segment_detail
        query = text("""
        SELECT
            osm_id,
            total_score,
            metric_features_scores,
            geom,
            segment_length
        FROM v_cyclability_segment_detail
        WHERE city_name = :city_name
        """)

        # Read data and store in GeoDataFrame
        gdf = gpd.read_postgis(query, 
                               engine, 
                               geom_col = "geom", 
                               params = {"city_name": city_name},
                               crs="EPSG:4326")

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

        return gdf
    
    except Exception as e:
        logging.error(f"Error loading data from PostGIS for frontend use: {e}")
        raise 

    finally:
        engine.dispose()

def load_segment_from_id(city_name: str,
                         osm_id: str) -> gpd.GeoDataFrame:
    """
    Load network segment from PostGIS associated to specific OSM ID.
    """

    # Normalize ID in compliace with PostGIS
    osm_id = f"way/{osm_id}"
    
    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    # Create SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

    try:

        # Select data from PostGIS virtual (view) table v_cyclability_segment_detail
        query = text("""
        SELECT
            osm_id,
            street_name,
            bike_infra,
            maxspeed,
            is_oneway,
            is_lit,
            surface,
            highway,
            total_score,
            missing_features,
            metric_features_scores,
            metric_version
        FROM v_cyclability_segment_detail
        WHERE city_name = :city_name
        AND osm_id = :osm_id;
        """)

        with engine.connect() as conn:
            result = conn.execute(query, 
                                  {"city_name": city_name, "osm_id": osm_id}).mappings().first()

        logging.info(f"Data successfully queried from PostGIS database for API use.")

        return dict(result) if result else None
    
    except Exception as e:
        logging.error(f"Error loading data from PostGIS for API use: {e}")
        raise 

    finally:
        engine.dispose()