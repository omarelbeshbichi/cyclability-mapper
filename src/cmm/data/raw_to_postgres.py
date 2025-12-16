"""
Module for loading raw OSM GeoJSON data into a Postgres dataframe.
"""

from .geojson import load_json_from_path
import psycopg2
import json
import logging
from ..validation.geometry import find_invalid_geometries
from ..validation.geometry import clean_linestrings

def raw_to_postgres(path: str, 
                    table_name: str):
    """
    Loads raw GeoJSON data to Postgres database.

    Parameters
    ----------
    path: str
        Path to the GeoJSON file to load    
    table_name: str
        Name of PostGIS table to be used as database
    """

    # Load data from JSON
    data = load_json_from_path(path)
    features = data.get('features')
    
    # Initiate Postgres session
    conn = psycopg2.connect(
        host = "localhost",
        user = "user",
        password = "pass",
        database = "cmm_db"
    )

    try:
        cur = conn.cursor()

        # Truncate table (dev)
        cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")

        # Insert data in table
        for feature in features:
            properties = feature.get('properties')
            names = properties.get('name')
            ids = properties.get('@id')
            geometry = feature.get('geometry')

            if geometry is None:
                continue
            if geometry.get('type') != "LineString":
                logging.debug(f"Skipping geometry type {geometry.get('type')} for feature {ids}")
                continue

            geometries_str = json.dumps(geometry)
            
            query = f"""
            INSERT INTO {table_name} (street_name, geom) 
            VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            """
            cur.execute(query, (names, geometries_str))

        # Check table
        cur.execute(f"SELECT id, street_name, ST_AsGeoJSON(geom) FROM {table_name}")
        rows = cur.fetchall()

        # Evaluate geometry validity
        is_invalid, invalid_id_reason = find_invalid_geometries(cur, table_name)

        # Delete degenerate LineString segments
        if is_invalid is True:
            
            text_geometry = "geometry" if len(invalid_id_reason) == 1 else "geometries"

            logging.warning(f'Found {len(invalid_id_reason)} degenerate {text_geometry}.')
            logging.info(f'Degenerate {text_geometry}: {invalid_id_reason}')
            
            n_deleted = clean_linestrings(cur, table_name)

            logging.info(f'Deleted {n_deleted} degenerate {text_geometry}.')
            logging.info(f'Geometry cleaning completed.')
        else:
            logging.info(f'All geometries imported are valid.')

        conn.commit()

    except psycopg2.OperationalError as e:
            print(f"Database connection error: {e}")
            
            # Rollback if error
            conn.rollback()

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()