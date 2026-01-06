import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def run_migration():
    with engine.connect() as conn:
        print("Starting schema check and migration for tasks table...")
        # Use autocommit for DDL operations
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        try:
            # Check data type of tasks.due_date
            # Note: Parameterized query for safety, though internal use
            result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='tasks' AND column_name='due_date'")).scalar()
            print(f"Current tasks.due_date type: {result}")

            # Only attempt to clean up empty strings if it is a string type
            if result in ('character varying', 'text', 'varchar', 'char'):
                print("Column is string type. Cleaning up empty strings...")
                conn.execute(text("UPDATE tasks SET due_date = NULL WHERE due_date = '';"))
            else:
                print(f"Column is {result}. Skipping empty string cleanup (not needed for Date/Timestamp types).")

            # Perform the ALTER if it's not already the correct type
            # We want 'timestamp with time zone' (TIMESTAMPTZ)
            if result != 'timestamp with time zone':
                print("Altering tasks table due_date to TIMESTAMPTZ...")
                # The USING clause ensures we cast existing data correctly
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN due_date TYPE TIMESTAMPTZ USING due_date::TIMESTAMPTZ;"))
                print("✅ tasks table migrated successfully.")
            else:
                print("✅ tasks.due_date is already TIMESTAMPTZ. No action needed.")

        except Exception as e:
            print(f"❌ Error migrating tasks table: {e}")
            
if __name__ == "__main__":
    run_migration()
