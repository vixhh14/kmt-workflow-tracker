import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable, default to SQLite for local dev
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workflow.db")

# Handle Render's postgres:// URL format (SQLAlchemy requires postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper for direct connection (legacy support if needed, but prefer ORM)
def get_db_connection():
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        import sqlite3
        conn = sqlite3.connect("workflow.db")
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # For PostgreSQL, we should rely on SQLAlchemy session
        raise NotImplementedError("Direct connection not supported for PostgreSQL. Use get_db() session instead.")
