"""
Module for exporting processed data.
"""

import psycopg2
import geopandas as gpd
import pandas as pd
import logging 
from sqlalchemy import create_engine
from ...metrics.config.versioning import get_config_version
import json


def gdf_to_postgres(gdf: gpd.GeoDataFrame, 
                    table_name: str):
    """
    Load GeoDataFrame data to Postgres database.

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoPandas GeoDataframe to load.   
    table_name: str
        Name of PostGIS table to be used as database
    """
    
    # Initiate Postgres session
    conn = psycopg2.connect(
        host = "localhost",
        user = "user",
        password = "pass",
        database = "db"
    )

    try:
        cur = conn.cursor()

        # Truncate table (dev)
        cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")

        query = f"""
            INSERT INTO {table_name} (street_name, geom) 
            VALUES (%s, ST_SetSRID(ST_GeomFromText(%s), 4326))
            """
        
        # Insert data in table
        for _, row in gdf.iterrows():
            cur.execute(query, (row.get("name"), row.geometry.wkt))

        conn.commit()
        logging.info("Data successfully loaded in PostGIS.")

    except psycopg2.OperationalError as e:
            print(f"Database connection error: {e}")
            
            # Rollback if error
            conn.rollback()

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def gdf_to_postgres_alchemy(gdf: gpd.GeoDataFrame, 
                            table_name: str,
                            user: str = "user",
                           password: str = "pass",
                           host: str = "localhost",
                           database: str = "db",
                            if_exists: str = "replace"):
    """
    Load GeoDataFrame data to PostGIS database using GeoPandas to_postgis.

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoPandas GeoDataFrame to load.   
    table_name: str
        Name of PostGIS table to be used as database.
    user, password, host, database: str
        Database connection parameters.
    if_exists: str
        What to do if table exists: 'fail', 'replace', or 'append'. Default is 'replace'.
    """

    try:
        # Create SQLAlchemy engine
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{database}")

        # Write GeoDataFrame to PostGIS
        gdf.to_postgis(table_name, engine, if_exists=if_exists, index=False)
        
        logging.info(f"Data successfully loaded into table '{table_name}'.")

    except Exception as e:
        logging.error(f"Error loading data to PostGIS: {e}")

###
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
            'id': 'osm_id',
            'name': 'street_name',
            'geometry': 'geom',
            'bike_infrastructure': 'bike_infra',
            'oneway': 'is_oneway',
            'lighting': 'is_lit'
        })
    
    # Convert booleans
    gdf['is_oneway'] = gdf['is_oneway'].map({'yes': True, 'no': False, True: True, False: False}).fillna(False)
    gdf['is_lit'] = gdf['is_lit'].map({'yes': True, 'no': False, 'unknown': False, True: True, False: False}).fillna(False)
    

    # Convert numeric columns
    gdf['maxspeed'] = pd.to_numeric(gdf['maxspeed'], errors='coerce')
    
    # Select final columns
    gdf = gdf[['osm_id', 'street_name', 'geom', 'bike_infra', 'maxspeed', 'is_oneway', 'is_lit', 'surface', 'highway']]
    
    return gdf

def prepare_metrics_gdf_for_postgis(augmented_gdf: gpd.GeoDataFrame,
                                    metric_name: str,
                                    yaml_path: str) -> pd.DataFrame:
    """
    Prepare GeoDataFrame with metrics for insertion into PostGIS database (segment_metrics SQL table)

    Parameters
    ----------
    augmented_gdf: GeoDataFrame
        Processed GeoDataFrame - augmented with metrics scores (output from define_augmented_geodataframe function)
    metric_name: str
        Name of current metrics (eg, cyclability)
    yaml_path: str
        Path to the YAML configuration file

    Returns
    -------
    pd.DataFrame
        Metric DataFrame ready for PostGIS insertion
    """

    gdf = augmented_gdf.copy()
    
    # Define original metrics column name
    metric_col = metric_name + "_metrics"

    # Define versioning
    metric_version = get_config_version(yaml_path)

    # Convert metrics into a dataframe
    metrics_df = pd.DataFrame({
        "osm_id": gdf["id"],
        "metric_name": metric_name,
        "metric_version": metric_version,
        "total_score": gdf[metric_col],
        "components": [json.dumps({}) for _ in range(len(gdf))],  # empty JSON for now
        "metadata": [json.dumps({}) for _ in range(len(gdf))]     # empty JSON
    })

    return metrics_df