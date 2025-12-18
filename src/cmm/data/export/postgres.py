"""
Module for exporting processed data.
"""

import psycopg2
import geopandas as gpd
import logging 

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
        database = "cmm_db"
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