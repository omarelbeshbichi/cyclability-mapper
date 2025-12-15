"""
Module for loading raw OSM GeoJSON data into a Postgres dataframe.
"""

from .geojson import load_json_from_path
import psycopg2
import json

def raw_to_postgres(path: str):
    """
    Loads raw GeoJSON data to Postgres database.

    Parameters
    ----------
    path: str
        Path to the GeoJSON file to load    
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
        cur.execute("TRUNCATE TABLE test_geoms RESTART IDENTITY;")

        # Insert data in table
        for feature in features:
            properties = feature.get('properties')
            geometry = feature.get('geometry')
            geometries_str = json.dumps(geometry)
            names = properties.get('name')

            query = """
            INSERT INTO test_geoms (street_name, geom) 
            VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            """
            cur.execute(query, (names, geometries_str))
        conn.commit()

        # Check table
        cur.execute("SELECT id, street_name, ST_AsGeoJSON(geom) FROM test_geoms")
        rows = cur.fetchall()

    except psycopg2.OperationalError as e:
            print(f"Database connection error: {e}")
            
            # Rollback if error
            conn.rollback()

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

    return rows