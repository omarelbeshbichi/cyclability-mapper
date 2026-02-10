from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    storage_backend: str = "local"   # local | s3 (local use vs demo AWS deploy)
    local_static_dir: str = "/app/static_maps"
    s3_bucket: str = "city-maps"
    s3_prefix: str = "static_maps"

settings = Settings()