import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load .env or .env.production depending on environment
load_dotenv()

# Fetch DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception(" DATABASE_URL is missing — backend cannot start.")

# Fix Render-style postgres:// URL → postgresql:// and ensure sslmode=require
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Check for sslmode and add if missing (Required for external Render DB connections)
if "sslmode=" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

# Create SQLAlchemy engine for PostgreSQL with robust connection arguments
engine = create_engine(
    DATABASE_URL,
    # connect_args are passed to the DB-API (psycopg2)
    connect_args={
        "sslmode": "require",
        "gssencmode": "disable", # Fixes certain SSL issues on Windows
        "connect_timeout": 15,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
    # Pooling settings for production-grade stability
    pool_size=5,
    max_overflow=10,
    pool_timeout=45,
    pool_recycle=1200, # Recycle faster to avoid stale connections
    pool_pre_ping=True, # Verify connection health before use
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db():
    """Yields a database session for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
