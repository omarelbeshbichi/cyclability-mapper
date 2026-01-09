import geopandas as gpd
from sqlalchemy import create_engine
import logging 

def load_segments(user: str = "user",
                host: str = "localhost",
                password: str = "pass",
                database: str = "db") -> gpd.GeoDataFrame:
    """
    Text
    """

    try:
        # Create SQLAlchemy engine
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{database}")

        # Select data from PostGIS virtual (view) table v_cyclability_score
        query = """
        SELECT
            id,
            total_score,
            geom
        FROM v_cyclability_score
        """

        # Read data and store in GeoDataFrame
        gdf = gpd.read_postgis(query, engine, geom_col="geom", crs="EPSG:4326")

        logging.info(f"Data successfully queried from PostGIS database for frontend use.")

    except Exception as e:
        logging.error(f"Error loading data from PostGIS for frontend use: {e}")
        raise 

    finally:
        engine.dispose()

    return gdf