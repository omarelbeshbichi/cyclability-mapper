from fastapi.responses import FileResponse, RedirectResponse
from fastapi.responses import HTMLResponse
from frontend.figures.settings import settings
import boto3

s3_client = boto3.client("s3")

def get_scatter_response():

    # When working locally - return static HTML (faster than dynamic reconstruction)
    if settings.storage_backend == "local":
        path = f"{settings.local_static_dir}/metrics_scatter.html"
        return FileResponse(path)

    # For demo AWS deployment - uses S3 bucket for storing static HTML maps
    elif settings.storage_backend == "s3":
        s3_key = f"{settings.s3_prefix}/metrics_scatter.html"
        
        # Get map from S3 bucket (do this to retain FastAPI URL)
        obj = s3_client.get_object(Bucket=settings.s3_bucket, Key=s3_key)
        
        # Turn it into HTML
        html_content = obj["Body"].read().decode("utf-8")
        
        # Serve it
        return HTMLResponse(content=html_content, media_type="text/html")

    else:
        raise ValueError("Invalid storage backend")