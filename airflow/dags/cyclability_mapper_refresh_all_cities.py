from airflow import DAG
from airflow.decorators import task # type: ignore
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import os

def get_all_cities():
    """
    Helper function to get all cities in PostGIS database
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    result = engine.execute(
        "SELECT DISTINCT city_name FROM network_segments"
    )

    cities = [row[0] for row in result]
    
    engine.dispose()

    return cities

# Here use TaskFlow API (@task) to define tasks as Python functions.
# Perform dynamic mapping of 'recompute_city' task for each city in database.
# To perform dynamic mapping use .expand()

@task
def fetch_cities():
    return get_all_cities()

@task(execution_timeout=timedelta(hours=2)) # if longer than 2 hours - fail task
def recompute_city(city_name: str):
    """
    Simply run refresh_osm_data CLI job for a given city
    """

    import subprocess

    subprocess.run(
        [
            "docker",
            "exec",
            "-w",
            "/app",
            "app",
            "python",
            "-m",
            "city_metrics.jobs.refresh_osm_data",
            "--chunk", "5000", 
            "--tout", "50",
            "--no-tiling",
            "--retries", "50",
            "--delay", "5.0",
            "--city",
            city_name,
        ],
        check=True,
    )

default_args = {
    "owner": "cyclability-mapper",
    "retries": 2, # two retries allowed
    "retry_delay": timedelta(minutes=5) # wait 5 minutes between retries
}

with DAG(
    dag_id="cyclability-mapper-refresh_all_cities",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",  # recompute every week
    catchup=False,
    default_args=default_args,
    max_active_tasks = 1, #only process one city per time 
    tags=["cyclability-mapper", "metrics"],
) as dag:

    cities = fetch_cities()
    recompute_city.expand(city_name = cities)