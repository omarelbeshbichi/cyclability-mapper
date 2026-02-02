from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .figures import create_city_metrics_scatter_plot, create_group_sensitivity_plot, create_group_sensitivity_heatmap
import io
import base64
import matplotlib.pyplot as plt
app = FastAPI()

@app.get("/metrics_scatter", response_class = HTMLResponse)
def serve_map():

    plt_module = create_city_metrics_scatter_plot()

    # Save figure to PNG in memory
    buf = io.BytesIO()
    plt_module.savefig(buf, format = "png")
    plt_module.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # Get HTML <img>
    html_content = f"""
    <html>
    <head>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }}
        img {{ max-width: 95vw; max-height: 95vh; }}
    </style>
    </head>
    <body>
        <img src="data:image/png;base64,{img_base64}" alt="City Metrics Plot">
    </body>
    </html>
    """

    return HTMLResponse(html_content)

@app.get("/group_sensitivity/heatmap", response_class=HTMLResponse)
def serve_group_sensitivity_heatmap(metric_name: str = "cyclability"):
    """
    Serve a heatmap of local sensitivity slopes (∂Score / ∂Weight)
    across all cities and groups.
    """

    fig_module = create_group_sensitivity_heatmap(
        metric_name = metric_name
    )

    buf = io.BytesIO()
    fig_module.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig_module)
    buf.seek(0)

    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    return HTMLResponse(f"""
    <html>
    <head>
        <title>Group Sensitivity Heatmap</title>
        <style>
            body {{
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #ffffff;
            }}
            img {{
                max-width: 95vw;
                max-height: 95vh;
            }}
        </style>
    </head>
    <body>
        <img
            src="data:image/png;base64,{img_base64}"
            alt="Group Sensitivity Heatmap"
        >
    </body>
    </html>
    """)

@app.get("/group_sensitivity/{city_name}", response_class=HTMLResponse)
def serve_group_sensitivity_plot(city_name):

    fig_module = create_group_sensitivity_plot(city_name)

    buf = io.BytesIO()
    fig_module.savefig(buf, format="png")
    plt.close(fig_module)
    buf.seek(0)

    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    return HTMLResponse(f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            img {{
                max-width: 95vw;
                max-height: 95vh;
            }}
        </style>
    </head>
    <body>
        <img src="data:image/png;base64,{img_base64}"
             alt="Group Sensitivity Plot">
    </body>
    </html>
    """)


