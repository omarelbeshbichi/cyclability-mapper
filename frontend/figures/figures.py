from fastapi import FastAPI
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import os
import logging
import pandas as pd
import numpy as np
import plotly.express as px

logging.basicConfig(level = logging.INFO)

app = FastAPI()

def create_city_metrics_scatter_plot():
    """
    Creates an interactive Plotly scatter plot of city metrics vs uncertainty.
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

        df = pd.read_sql(query, engine)

        if df.empty:
            logging.info("No city metrics found in database.")
            return None

        # Clean up display names
        df["city_name"] = df["city_name"].str.title()

        fig = px.scatter(
            df,
            x="total_city_score_uncertainty",
            y="total_city_score",
            color="total_city_score",
            color_continuous_scale="Viridis",
            hover_name="city_name",
            hover_data={
                "total_city_score": ":.3f",
                "total_city_score_uncertainty": ":.3f",
                "city_name": False
            },
            labels={
                "total_city_score_uncertainty": "Total City Score Uncertainty",
                "total_city_score": "Total City Score",
            },
            title="City Metrics Scatter Plot",
        )

        fig.update_traces(
            marker=dict(size=12, line=dict(width=1, color="black")),
            selector=dict(mode="markers")
        )

        fig.update_layout(
            xaxis=dict(range=[0, 0.5]),
            yaxis=dict(range=[0, 1]),
            coloraxis_colorbar=dict(title="Total City Score"),
            template="plotly_white"
        )

        return fig

    except Exception as e:
        logging.error(f"Error creating city metrics plot: {e}")
        return None

    finally:
        engine.dispose()

def create_group_sensitivity_plot(city_name: str) -> plt.Figure:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    try:
        query = text("""
            SELECT
                target_group,
                delta_group_weight,
                sweep_city_score_result
            FROM group_sensitivity
            WHERE city_name = :city_name
            ORDER BY city_name, target_group;
        """)

        params = {"city_name": city_name}

        with engine.connect() as conn:
            result = conn.execute(query, params).fetchall()

        if not result:
            logging.info("No group sensitivity data found.")
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
            ax.axis("off")
            return fig

        fig, ax = plt.subplots(figsize=(12, 8))

        for row in result:
            target_group, delta_group_weight, sweep_city_score_result = row

            x = [float(v) for v in delta_group_weight]
            y = [float(v) for v in sweep_city_score_result]

            ax.plot(
                x,
                y,
                marker="o",
                linestyle="-",
                alpha=0.8,
                label=f"{target_group}"
            )

        ax.set_xlabel("Delta Group Weight")
        ax.set_ylabel("Total City Score")
        ax.set_ylim(0, 1)
        ax.set_title(f"Sensitivity Sweep - {city_name} (diagnostics)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=9, loc="best")
        fig.tight_layout()

        return fig

    except Exception as e:
        logging.error(f"Error creating group sensitivity plot: {e}")
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, f"Error: {e}", ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    finally:
        engine.dispose()

def create_group_sensitivity_heatmap(metric_name: str = "cyclability") -> plt.Figure:
    """
    Create a city for group heatmap of local sensitivity slopes.
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
                target_group,
                sensitivity
            FROM group_sensitivity
            WHERE metric_name = :metric_name
            ORDER BY city_name, target_group;
        """)

        params = {
            "metric_name": metric_name
        }

        with engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        if not rows:
            logging.info("No sensitivity data found.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
            ax.axis("off")
            return fig

        df = pd.DataFrame(
            rows,
            columns=["city_name", "target_group", "sensitivity"]
        )
        df["sensitivity"] = pd.to_numeric(df["sensitivity"], errors="coerce")

        heatmap_df = df.pivot(
            index="city_name",
            columns="target_group",
            values="sensitivity"
        )

        values = heatmap_df.values
        cities = heatmap_df.index.str.title().tolist()
        groups = heatmap_df.columns.tolist()

        fig, ax = plt.subplots(figsize=(12, 8))

        # Symmetric color scale around zero
        vmax = np.nanmax(np.abs(values))
        im = ax.imshow(
            values,
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
            aspect="auto"
        )

        # Ticks and labels
        ax.set_xticks(np.arange(len(groups)))
        ax.set_yticks(np.arange(len(cities)))
        ax.set_xticklabels(groups, rotation=45, ha="right")
        ax.set_yticklabels(cities)

        # Annotate cells
        for i in range(len(cities)):
            for j in range(len(groups)):
                val = values[i, j]
                if not np.isnan(val):
                    ax.text(
                        j, i,
                        f"{val:.3f}",
                        ha="center",
                        va="center",
                        fontsize=9
                    )

        ax.set_title("Weight Sensitivity (diagnostics)")

        # Colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.85)
        cbar.set_label("[∂Score / ∂Weight]")

        fig.tight_layout()
        return fig

    except Exception as e:
        logging.error(f"Error creating sensitivity heatmap: {e}")
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, f"Error: {e}", ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    finally:
        engine.dispose()