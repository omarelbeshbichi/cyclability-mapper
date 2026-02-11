from fastapi.responses import FileResponse, RedirectResponse
from .settings import settings

def get_map_response(city_name: str):

    # When working locally - return static HTML (faster than dynamic reconstruction)
    if settings.storage_backend == "local":
        path = f"{settings.local_static_dir}/{city_name}.html"
        return FileResponse(path)

    # For demo AWS deployment - uses S3 bucket for storing static HTML maps
    elif settings.storage_backend == "s3":
        url = f"https://{settings.s3_bucket}.s3.amazonaws.com/{settings.s3_prefix}/{city_name}.html"
        return RedirectResponse(url)

    else:
        raise ValueError("Invalid storage backend")