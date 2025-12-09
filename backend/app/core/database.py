import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Calculate absolute path to workflow.db in the backend directory
# This ensures the same database file is used regardless of current working directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "workflow.db")

# Get database URL from environment variable
database_url_env = os.getenv("DATABASE_URL")

# Check if running on Render
IS_RENDER = os.getenv("RENDER") == "true"

if database_url_env:
    SQLALCHEMY_DATABASE_URL = database_url_env
    print(f"[DB] Using DATABASE_URL from environment")
elif IS_RENDER:
    # Use Render Disk path for persistence
    # NOTE: You must attach a disk to /var/data in Render dashboard
    RENDER_DB_PATH = "/var/data/workflow.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{RENDER_DB_PATH}"
    print(f"[DB] Running on Render. Using persistent disk at: {RENDER_DB_PATH}")
    # Update DEFAULT_DB_PATH for get_db_connection legacy support
    DEFAULT_DB_PATH = RENDER_DB_PATH
else:
    # Use absolute path to ensure consistent database location locally
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"
    print(f"[DB] Using local SQLite database at: {DEFAULT_DB_PATH}")

# Handle Render's postgres:// URL format (SQLAlchemy requires postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )
else:
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

def get_db_connection():
    """
    Legacy helper for direct SQLite connection.
    Uses the same absolute path as SQLAlchemy engine.
    Prefer using get_db() with SQLAlchemy ORM instead.
    """
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        import sqlite3
        print(f"[DB] Direct SQLite connection to: {DEFAULT_DB_PATH}")
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        raise NotImplementedError(
            "Direct connection not supported for PostgreSQL. Use get_db() session instead."
        )

# Export the database path for other modules that need it
DB_PATH = DEFAULT_DB_PATH
