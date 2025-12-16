from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL
import sys

def add_soft_delete_columns():
    print("Connecting to database...")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            # Task
            print("Processing tasks table...")
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"))
                print("  - 'is_deleted' column ensured on tasks")
            except Exception as e:
                print(f"  Ref: {e}")

            # Project
            print("Processing projects table...")
            try:
                conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"))
                print("  - 'is_deleted' column ensured on projects")
            except Exception as e:
                print(f"  Ref: {e}")

            # Machine
            print("Processing machines table...")
            try:
                conn.execute(text("ALTER TABLE machines ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"))
                print("  - 'is_deleted' column ensured on machines")
            except Exception as e:
                print(f"  Ref: {e}")

            conn.commit()
            print("Database schema update completed successfully.")
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_soft_delete_columns()
