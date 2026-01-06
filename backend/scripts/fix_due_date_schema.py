import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def run_migration():
    with engine.connect() as conn:
        print("Starting schema migration for due_date columns...")
        # Use autocommit for DDL operations
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        # 1. Tasks Table (General Tasks)
        # Previously String, sometimes containing empty strings or 'YYYY-MM-DD'
        try:
            print("Migrating tasks table...")
            # Clean up empty strings first to avoid casting errors
            conn.execute(text("UPDATE tasks SET due_date = NULL WHERE due_date = '';"))
            
            # Alter column to TIMESTAMPTZ using cast
            # Note: If existing data is just 'YYYY-MM-DD', casting to TIMESTAMPTZ defaults to midnight.
            # This is acceptable for old data. New data will include time.
            conn.execute(text("ALTER TABLE tasks ALTER COLUMN due_date TYPE TIMESTAMPTZ USING due_date::TIMESTAMPTZ;"))
            print("✅ tasks table migrated successfully.")
        except Exception as e:
            print(f"⚠️  Note on tasks table: {e}")

        # 2. Filing Tasks (Operational)
        # Previously Date
        try:
            print("Migrating filing_tasks table...")
            conn.execute(text("ALTER TABLE filing_tasks ALTER COLUMN due_date TYPE TIMESTAMPTZ USING due_date::TIMESTAMPTZ;"))
            print("✅ filing_tasks table migrated successfully.")
        except Exception as e:
            print(f"⚠️  Note on filing_tasks table: {e}")

        # 3. Fabrication Tasks (Operational)
        # Previously Date
        try:
            print("Migrating fabrication_tasks table...")
            conn.execute(text("ALTER TABLE fabrication_tasks ALTER COLUMN due_date TYPE TIMESTAMPTZ USING due_date::TIMESTAMPTZ;"))
            print("✅ fabrication_tasks table migrated successfully.")
        except Exception as e:
            print(f"⚠️  Note on fabrication_tasks table: {e}")
        
        print("Migration process finished.")

if __name__ == "__main__":
    run_migration()
