import os
import logging
import click
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)

@click.command()
def main():
    """
    List available cities in the database.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    try:
        query = text("""
            SELECT DISTINCT city_name
            FROM v_cyclability_segment_detail
            ORDER BY city_name;
        """)

        with engine.connect() as conn:
            result = conn.execute(query).fetchall()

        if not result:
            logging.info("No cities found in database.")
            return

        logging.info("Available cities in database:")
        for (city_name,) in result:
            logging.info(f" - {city_name}")

    except Exception as e:
        logging.error(f"Error retrieving cities: {e}")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
