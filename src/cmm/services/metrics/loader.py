import geopandas as gpd
from sqlalchemy import create_engine, text
import logging 
import os

def load_segments_for_metrics_recompute(city_name: str) -> gpd.GeoDataFrame:
    """
    Load cyclability segments of given city from PostGIS for metrics recomputation.
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
            street_name,
            geom,
            maxspeed,
            is_lit,
            bike_infra,
            is_oneway,
            surface,
            highway,
            missing_features
        FROM v_cyclability_segment_detail
        WHERE city_name = :city_name
        """)

        # Read data and store in GeoDataFrame
        gdf = gpd.read_postgis(query, 
                               engine, 
                               geom_col = "geom",
                               params = {"city_name": city_name}, 
                               crs = "EPSG:4326")

        # Rename for pipeline compatibility
        gdf = gdf.rename(columns={"street_name": "name"})
        gdf = gdf.rename(columns={"geom": "geometry"})
        gdf = gdf.rename(columns={"is_lit": "lit"})
        gdf = gdf.rename(columns={"missing_features": "missing_info"})
        
        gdf = gdf.set_geometry("geometry")

        # Resolve bool to comply with pipeline
        gdf["lit"] = gdf["lit"].map({True: "yes", False: "no"})
        gdf["is_oneway"] = gdf["is_oneway"].map({True: "one", False: "both"})


        logging.info(f"{city_name} data successfully retrieved from PostGIS database for metrics recomputation.")

        return gdf
    
    except Exception as e:
        logging.error(f"Error loading {city_name} data from PostGIS for metrics recomputation: {e}")
        raise 

    finally:
        engine.dispose()


def load_data_for_city_metrics_compute(city_name: str) -> gpd.GeoDataFrame:
    """
    Load data of given city from PostGIS for total city metrics computation.
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
            geom,
            segment_length,
            total_score,
            missing_features
        FROM v_cyclability_segment_detail
        WHERE city_name = :city_name
        """)

        # Read data and store in GeoDataFrame
        gdf = gpd.read_postgis(query, 
                               engine, 
                               geom_col = "geom",
                               params = {"city_name": city_name}, 
                               crs = "EPSG:4326")

        # Rename for pipeline compatibility
        gdf = gdf.rename(columns={"geom": "geometry"})
        gdf = gdf.rename(columns={"missing_features": "missing_info"})
        
        gdf = gdf.set_geometry("geometry")

        logging.info(f"{city_name} data successfully retrieved from PostGIS database for total city metrics computation.")

        return gdf
    
    except Exception as e:
        logging.error(f"Error loading {city_name} data from PostGIS for metrics recomputation: {e}")
        raise 

    finally:
        engine.dispose()