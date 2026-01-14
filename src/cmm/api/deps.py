from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user:pass@localhost:5432/db"
) 

# Create engine architecture
engine = create_engine(
    DATABASE_URL,
)

# Create session architecture
SessionLocal = sessionmaker(
    bind = engine
)

def get_db() -> Session:
    # At function call, actually open a session
    db = SessionLocal()
    try:
        yield db # yield -> generator, ie function returns generator object
                 # representing a session
    finally:
        db.close() # Close session