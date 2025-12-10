import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable
database_url_env = os.getenv("DATABASE_URL")

# Check if running on Render
IS_RENDER = os.getenv("RENDER") == "true"

if database_url_env:
    SQLALCHEMY_DATABASE_URL = database_url_env
    print(f"[DB] Using DATABASE_URL from environment")
else:
    # Fail loud if DATABASE_URL is missing to ensure we never accidentally use a default
    raise ValueError("DATABASE_URL not found in environment. Please set it in .env file.")

# Handle Render's postgres:// URL format (SQLAlchemy requires postgresql://)
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# PostgreSQL configuration with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,         # Basic pool size
    max_overflow=10      # Allow some overflow
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

