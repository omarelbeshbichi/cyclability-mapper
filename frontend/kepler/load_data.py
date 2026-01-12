import geopandas as gpd
from sqlalchemy import create_engine
import logging 
import json
import pandas as pd

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
            
            # After flattening the JSON columns
            gdf['all_scores'] = (
                "bike_inf:" + gdf['metric_features_scores'].str['bike_infrastructure'].round(2).astype(str) + " | " +
                "maxspeed:" + gdf['metric_features_scores'].str["maxspeed"].round(2).astype(str) + " | " +
                "surface:" + gdf['metric_features_scores'].str["surface"].round(2).astype(str) + " | " +
                "lighting:" + gdf['metric_features_scores'].str["lighting"].round(2).astype(str) + " | " +
                "oneway:" + gdf['metric_features_scores'].str["oneway"].round(2).astype(str)
            )




            # Extract JSON fields into separate columns
            #json_df = gdf['metric_features_scores'].apply(pd.Series)
            
            # Prefix column names to avoid conflicts
            #json_df.columns = [f"score_{col}" for col in json_df.columns]
            
            # Replace original metric_features_scores with new columns
            #gdf = gdf.drop('metric_features_scores', axis=1)
            #gdf = gdf.join(json_df)

        logging.info(f"Data successfully queried from PostGIS database for frontend use.")

    except Exception as e:
        logging.error(f"Error loading data from PostGIS for frontend use: {e}")
        raise 

    finally:
        engine.dispose()

    return gdf