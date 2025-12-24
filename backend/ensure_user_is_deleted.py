import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load Environment
load_dotenv(os.path.join("backend", ".env.production"))
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("DATABASE_URL not found")
    sys.exit(1)

def ensure_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking for is_deleted in users table...")
        try:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='is_deleted';"))
            row = result.fetchone()
            if not row:
                print("Adding is_deleted column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("UPDATE users SET is_deleted = FALSE WHERE is_deleted IS NULL;"))
                print("Column added successfully.")
            else:
                print("Column is_deleted already exists.")
            
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    ensure_columns()
