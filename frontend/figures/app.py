from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .figures import create_city_metrics_scatter_plot
import io
import base64
import matplotlib.pyplot as plt
app = FastAPI()

@app.get("/metrics_scatter", response_class = HTMLResponse)
def serve_map():

    plt = create_city_metrics_scatter_plot()

    # Save figure to PNG in memory
    buf = io.BytesIO()
    plt.savefig(buf, format = "png")
    plt.close()
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