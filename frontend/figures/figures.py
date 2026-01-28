from fastapi import FastAPI
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import os
import logging

logging.basicConfig(level = logging.INFO)

app = FastAPI()

def create_city_metrics_scatter_plot() -> plt:
    """
    Creates a 2D scatter plot of city metrics as function of uncertainty and returns it as plt
    (similar to ktmp/Kepler approach).
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
                total_city_score,
                total_city_score_uncertainty
            FROM city_metrics
            ORDER BY total_city_score DESC;
        """)

        with engine.connect() as conn:
            result = conn.execute(query).fetchall()

        if not result:
            logging.info("No city metrics found in database.")
            return "<p>No city metrics found</p>"

        cities = [row.city_name.title() for row in result]
        scores = [float(row.total_city_score) for row in result]
        uncertainties = [float(row.total_city_score_uncertainty) for row in result]

        # Create figure
        plt.figure(figsize = (12, 8))
        plt.scatter(
            uncertainties,
            scores,
            s = 100,
            c = scores,
            cmap = "viridis",
            alpha = 0.8,
            edgecolors = "k"
        )
        for x, y, name in zip(uncertainties, scores, cities):
            plt.text(x + 0.01, y, name, fontsize = 9, alpha = 0.8)

        plt.xlabel("Total City Score Uncertainty")
        plt.ylabel("Total City Score")
        plt.xlim(0, 0.5)
        plt.ylim(0, 1)
        plt.title("City Metrics Scatter Plot")
        plt.colorbar(label = "Total City Score")

        plt.grid(True, linestyle = "--", alpha = 0.5)
        plt.tight_layout()

        return plt

    except Exception as e:
        logging.error(f"Error creating city metrics plot: {e}")
        return f"<p>Error: {e}</p>"

    finally:
        engine.dispose()