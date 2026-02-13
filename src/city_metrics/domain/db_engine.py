
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user:pass@localhost:5432/db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # 5 persistent connections
    max_overflow=2,     # allow 2 extra temporary ones
    pool_pre_ping=True  # avoids stale connections
)