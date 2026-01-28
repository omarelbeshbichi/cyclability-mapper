import os
import logging
import click
from sqlalchemy import create_engine, text
from tabulate import tabulate 

logging.basicConfig(level=logging.INFO)

@click.command()
def main():
    """
    List aggregated city metrics stored in the database.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    try:
        query = text("""
            SELECT
                city_name,
                metric_name,
                metric_version,
                total_city_score,
                total_city_score_uncertainty,
                feature_uncertainty_contributions,
                created_at
            FROM city_metrics
            ORDER BY total_city_score DESC;
        """)

        with engine.connect() as conn:
            result = conn.execute(query).fetchall()

        if not result:
            logging.info("No city metrics found in database.")
            return

        # Prepare data for tabulate
        headers = [
            "City", "Metric", "Version", "Score",
            "Uncertainty", "Feature Uncertainty", "Created"
        ]

        # Define rows of table as list comprehension
        rows = [
            # Collect rows here
            [
                row.city_name,
                row.metric_name,
                row.metric_version,
                row.total_city_score,
                row.total_city_score_uncertainty,
                row.feature_uncertainty_contributions,
                row.created_at
            ]
            for row in result
        ]

        # Print table
        print(tabulate(rows, headers = headers, tablefmt = "fancy_grid"))


    except Exception as e:
        logging.error(f"Error retrieving city metrics: {e}")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
