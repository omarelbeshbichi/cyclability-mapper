"""
Module for exporting processed data.
"""

import geopandas as gpd
import pandas as pd
import logging 
from sqlalchemy import create_engine
from sqlalchemy import text
from ...metrics.config.versioning import get_config_version
import json
import os


def dataframe_to_postgres(gdf: gpd.GeoDataFrame,
                        table_name: str,
                        df_type: str = "gdf", 
                        user: str = "user",
                        password: str = "pass",
                        host: str = "localhost",
                        database: str = "db",
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
    user, password, host, database: str
        Database connection parameters.
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

        # Reset network_segment table - clear rows, restart ids, delete dependencies
        # NB: CASCADE -> delete also rows in segment_metrics associated with network_metrics
        with engine.begin() as conn:
            conn.execute(text(f"""
                TRUNCATE TABLE {table_name}
                RESTART IDENTITY
                CASCADE;
            """))

        # Load gdf to network_segments table
        if df_type == "gdf":
            gdf.to_postgis(table_name, engine, if_exists=if_exists, index=False)
        if df_type == "df":
            gdf.to_sql(table_name, engine, if_exists=if_exists, index=False)


        logging.info(f"Data successfully loaded into PostGIS table '{table_name}'.")

    except Exception as e:
        logging.error(f"Error loading data to PostGIS: {e}")

    finally:
        engine.dispose()

def prepare_network_segments_gdf_for_postgis(augmented_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Prepare a GeoDataFrame for PostGIS of network segments (network_segments SQL table).

    Parameters
    ----------
    augmented_gdf: GeoDataFrame
        Processed GeoDataFrame - augmented with metrics scores (output from define_augmented_geodataframe function)

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with segments ready for PostGIS insertion     
    """

    gdf = augmented_gdf.copy()
    
    # Rename columns
    gdf = gdf.rename(columns={
            "id": "osm_id",
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
    gdf = gdf[["osm_id", "street_name", "geom", "bike_infra", "maxspeed", "is_oneway", "is_lit", "surface", "highway"]]
    
    return gdf

def prepare_metrics_df_for_postgis(augmented_gdf: gpd.GeoDataFrame,
                                   metrics_features_scores_cyclability: list,
                                    metric_name: str,
                                    yaml_path: str,
                                    user: str = "user",
                                    password: str = "pass",
                                    host: str = "localhost",
                                    database: str = "db") -> pd.DataFrame:
    """
    Prepare DataFrame with metrics for insertion into PostGIS database (segment_metrics SQL table)

    Parameters
    ----------
    augmented_gdf: GeoDataFrame
        Processed GeoDataFrame - augmented with metrics scores (output from define_augmented_geodataframe function)
    metrics_features_scores_cyclability: list
        List of dictionaries storing metrics scores of all features for all segments
    metric_name: str
        Name of current metrics (eg, cyclability)
    yaml_path: str
        Path to the YAML configuration file
    user, password, host, database: str
        Database connection parameters.
        
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
        segments_df = pd.read_sql("SELECT id, osm_id FROM network_segments", engine)


        logging.info(f"Segments IDs successfully collected from table network_segments.")

    except Exception as e:
        logging.error(f"Error collecting IDs from table network_segments: {e}")

    finally:
        engine.dispose()

    # Keep only matching elements - used for robustness
    gdf_aligned = gdf.merge(segments_df, left_on="id", right_on="osm_id", how="inner") 

    # Define components
    features_scores_json = [json.dumps(f) for f in metrics_features_scores_cyclability]

    # Convert metrics into a dataframe
    metrics_df_final = pd.DataFrame({
        "segment_id": gdf_aligned["id_y"],
        "metric_name": metric_name,
        "metric_version": metric_version,
        "total_score": gdf_aligned[metric_col],
        "metric_features_scores": features_scores_json,
        "metadata": [json.dumps({}) for _ in range(len(gdf))]     # empty JSON for now
    })

    return metrics_df_final