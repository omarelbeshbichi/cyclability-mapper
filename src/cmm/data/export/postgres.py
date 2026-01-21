"""
Module for exporting processed data.
"""

import geopandas as gpd
import pandas as pd
import logging 
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.sql import quoted_name
from ...metrics.config.versioning import get_config_version
import json
import os
from shapely import wkb
from shapely.geometry import Polygon, base

def reference_area_to_postgres(city_name: str, 
                                geom: Polygon):
    """
    Insert or update reference area geometry to PostGIS (table refresh_areas).

    Parameters
    ----------
    city_name : str
        Name of given city (e.g. "oslo")
    geom: Polygon
        Reference polygon used to define database data
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    try:
    
        engine = create_engine(DATABASE_URL)

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO refresh_areas (city_name, geom, created_at)
                    VALUES (
                        :city_name,
                        ST_SetSRID(ST_GeomFromWKB(:geom), 4326),
                        NOW()
                    )
                    ON CONFLICT (city_name)
                    DO UPDATE SET
                        geom = EXCLUDED.geom,
                        created_at = NOW();
                """),
                {
                    "city_name": city_name,
                    "geom": wkb.dumps(geom)
                }
            )

        logging.info(f"Reference area '{city_name}' added successfully to refresh_areas table.")

    finally:
        engine.dispose()

def load_reference_area(city_name: str):
    """
    Load reference geometry stored in refresh_areas table to define refresh polygon.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    try:

        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT ST_AsBinary(geom) AS geom_wkb
                    FROM refresh_areas
                    WHERE city_name = :city_name
                """),
                {"city_name": city_name}
            ).fetchone()

            if result is None:
                raise ValueError(f"'{city_name}' not found in PostGIS (refresh_areas table).")

            geom_wkb = result[0]

            # Handle memoryview type (used in psycopg2 and other drivers)
            if isinstance(geom_wkb, memoryview):
                geom_wkb = geom_wkb.tobytes()

            return wkb.loads(geom_wkb)

    finally:
        engine.dispose()

def delete_city_rows(table_name: str, city_name: str):
    """
    Remove all rows associated with a given city from PostGIS table.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    try:
        quoted_table = quoted_name(table_name, quote = True)

        with engine.begin() as conn:
            
            # Delete data in segment_metrics -> use network_segments to get city_name info
            if table_name == "segment_metrics":
                conn.execute(
                    text(f"""
                        DELETE FROM {quoted_table} sm
                        USING network_segments ns
                        WHERE sm.segment_id = ns.id
                          AND ns.city_name = :city_name
                    """),
                    {"city_name": city_name}
                )
            else:
                # Retrieve city_name directly (network_segments and refresh areas have it)
                conn.execute(
                    text(f"""
                        DELETE FROM {quoted_table}
                        WHERE city_name = :city_name;
                    """),
                    {"city_name": city_name}
                )

        logging.info(
            f"Rows for city '{city_name}' successfully removed from '{table_name}'."
        )

    except Exception as e:
        logging.error(f"Error deleting rows from '{table_name}': {e}")
        raise

    finally:
        engine.dispose()

def truncate_table(table_name: str):
    """
    Remove all rows from a PostGIS table, reset IDs, and cascade deletes.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    try:
        engine = create_engine(DATABASE_URL)

        quoted_table = quoted_name(table_name, quote=True)

        with engine.begin() as conn:
            conn.execute(text(f"""
                TRUNCATE TABLE {quoted_table}
                RESTART IDENTITY
                CASCADE;
            """))

        logging.info(f"Table '{table_name}' successfully cleared.")

    except Exception as e:
        logging.error(f"Error clearing table '{table_name}': {e}")

    finally:
        engine.dispose()

def delete_segments_in_polygon(city_name: str,
                                polygon: base.BaseGeometry):
    """
    Remove from PostGIS table all segments intersecting given polygon.
    """

    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    ) 

    # Convert geometry to WKT
    wkt = polygon.wkt

    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)

        # Use SQL query to delete only data associated with segments within the provided reference polygon.
        with engine.begin() as conn:
                result = conn.execute(text(f"""
                DELETE FROM network_segments
                WHERE city_name = :city_name
                AND ST_Intersects(
                        geom,
                        ST_SetSRID(ST_GeomFromText(:polygon_wkt), 4326)
                );
            """), {
                "city_name": city_name,
                "polygon_wkt": wkt
            })
            
        deleted_rows = result.rowcount

        logging.info(f"{deleted_rows} rows for {city_name} deleted from PostGIS (network_segments) within polygon.")

    except Exception as e:
        logging.error(f"Error deleting bbox data for {city_name} from PostGIS: {e}")

    finally:
        engine.dispose()

def delete_segment_metrics_in_polygon(city_name: str,
                                      polygon: base.BaseGeometry):
    """
    Remove from PostGIS metrics table all data associated to a given reference polygon.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    # Convert polygon to WKT for PostGIS
    wkt = polygon.wkt

    try:
        engine = create_engine(DATABASE_URL)

        # Use SQL query to delete only metrics associated with segments within the provided reference polygon.
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM segment_metrics sm
                    USING network_segments ns
                    WHERE sm.segment_id = ns.id
                    AND ns.city_name = :city_name
                    AND ST_Intersects(
                        geom,
                        ST_SetSRID(ST_GeomFromText(:polygon_wkt), 4326)
                    );
                """),
                {
                    "city_name": city_name,
                    "polygon_wkt": wkt
                }
            )

            deleted_rows = result.rowcount

        logging.info(f"{deleted_rows} rows for {city_name} deleted from PostGIS (segment_metrics) within polygon.")

    except Exception as e:
        logging.error(f"Error deleting segment_metrics in bbox: {e}")
        raise

    finally:
        engine.dispose()

def dataframe_to_postgres(gdf: gpd.GeoDataFrame,
                        table_name: str,
                        df_type: str = "gdf",
                        if_exists: str = "append"):
    """
    Load Dataframe data to PostGIS database using GeoPandas to_postgis.

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoPandas GeoDataFrame to load.   
    table_name: str
        Name of PostGIS table to be used as database.
    df_type: str
        Type of dataframe: df or gdf.
    if_exists: str
        What to do if table exists: "fail", "replace", or "append". Default is "append".
    """
    
    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    ) 

    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)

        # Write GeoDataFrame to PostGIS

        # Load gdf to network_segments table
        if df_type == "gdf":
            gdf.to_postgis(table_name, engine, if_exists = if_exists, index = False)
        if df_type == "df":
            gdf.to_sql(table_name, engine, if_exists = if_exists, index=  False)

        rows_inserted = len(gdf)

        logging.info(f"Data successfully loaded into PostGIS table '{table_name}': {rows_inserted} rows.")

    except Exception as e:
        logging.error(f"Error loading data to PostGIS: {e}")

    finally:
        engine.dispose()

def prepare_network_segments_gdf_for_postgis(city_name: str, 
                                             augmented_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Prepare a GeoDataFrame for PostGIS of network segments (network_segments SQL table).

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo").
    augmented_gdf: GeoDataFrame
        Processed GeoDataFrame - augmented with metrics scores (output from define_augmented_geodataframe function)

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with segments ready for PostGIS insertion     
    """

    gdf = augmented_gdf.copy()
    
    # Assign city name
    gdf["city_name"] = city_name

    # Rename columns
    gdf = gdf.rename(columns={
            "name": "street_name",
            "geometry": "geom",
            "bike_infrastructure": "bike_infra",
            "oneway": "is_oneway",
            "lighting": "is_lit"
        })
    gdf = gdf.set_geometry("geom")

    # Convert booleans
    gdf["is_oneway"] = gdf["is_oneway"].map({"yes": True, "no": False, True: True, False: False}).fillna(False)
    gdf["is_lit"] = gdf["is_lit"].map({"yes": True, "no": False, "unknown": False, True: True, False: False}).fillna(False)
    

    # Convert numeric columns
    gdf["maxspeed"] = (
        pd.to_numeric(gdf["maxspeed"], errors="coerce")
        .round()
        .astype("Int64")   # Enforce Int
    )
    
    # Select final columns
    gdf = gdf[["osm_id", 
               "street_name", 
               "city_name", 
               "geom", 
               "segment_length", 
               "bike_infra", 
               "maxspeed", 
               "is_oneway", 
               "is_lit", 
               "surface", 
               "highway"]]
    
    return gdf

def prepare_metrics_df_for_postgis(city_name: str,
                                    augmented_gdf: gpd.GeoDataFrame,
                                    metrics_features_scores_cyclability: list,
                                    metric_name: str,
                                    yaml_path: str) -> pd.DataFrame:
    """
    Prepare DataFrame with metrics for insertion into PostGIS database (segment_metrics SQL table)

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo).
    augmented_gdf: GeoDataFrame
        Processed GeoDataFrame - augmented with metrics scores (output from define_augmented_geodataframe function)
    metrics_features_scores_cyclability: list
        List of dictionaries storing metrics scores of all features for all segments
    metric_name: str
        Name of current metrics (eg, cyclability)
    yaml_path: str
        Path to the YAML configuration file
        
    Returns
    -------
    pd.DataFrame
        Metric DataFrame ready for PostGIS insertion
    """

    # Use DATABASE_URL if running inside Docker, else fallback to localhost
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    gdf = augmented_gdf.copy()
    
    # Define original metrics column name
    metric_col = metric_name + "_metrics"

    # Define versioning
    metric_version = get_config_version(yaml_path)

    # Retrieve segments IDs from network_segments table in PostGIS
    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)
        
        # Collect ids and osm_ids from network_segments table in PostGIS
        segments_df = pd.read_sql(
            """
            SELECT id, osm_id
            FROM network_segments
            WHERE city_name = %(city_name)s
            """, 
            engine,
            params = {"city_name": city_name}
        )

        logging.info(f"{city_name} segments IDs successfully collected from table network_segments.")

    except Exception as e:
        logging.error(f"Error collecting {city_name} segments IDs from table network_segments: {e}")

    finally:
        engine.dispose()

    # Keep only matching elements - used for robustness
    gdf_aligned = gdf.merge(segments_df, on = "osm_id", how = "inner") 

    # Define components
    features_scores_json = [json.dumps(f) for f in metrics_features_scores_cyclability]

    # Convert metrics into a dataframe
    metrics_df_final = pd.DataFrame({
        "segment_id": gdf_aligned["id"],
        "metric_name": metric_name,
        "metric_version": metric_version,
        "total_score": gdf_aligned[metric_col],
        "metric_features_scores": features_scores_json,
        "metadata": [json.dumps({}) for _ in range(len(gdf))]     # empty JSON for now
    })

    return metrics_df_final