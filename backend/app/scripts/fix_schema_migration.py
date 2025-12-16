from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL
import time

def run_migration():
    print("Connecting to database...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        with conn.begin():
            print("--- MIGRATING MACHINES ---")
            
            # 1. Rename column 'name' -> 'machine_name' if exists
            # We check if 'machine_name' already exists to avoid error
            check = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='machines' AND column_name='machine_name'"))
            if not check.first():
                print("Renaming 'name' to 'machine_name'...")
                try:
                    conn.execute(text("ALTER TABLE machines RENAME COLUMN name TO machine_name"))
                except Exception as e:
                    print(f"Rename failed (maybe column missing?): {e}")
            else:
                print("'machine_name' column already exists.")

            # 2. Fix is_deleted (handle NULLs)
            print("Normalizing is_deleted...")
            conn.execute(text("UPDATE machines SET is_deleted = FALSE WHERE is_deleted IS NULL"))
            conn.execute(text("ALTER TABLE machines ALTER COLUMN is_deleted SET DEFAULT FALSE"))
            
            # 3. Fix Timestamps
            print("Converting timestamps to TIMESTAMPTZ...")
            try:
                conn.execute(text("ALTER TABLE machines ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"))
                conn.execute(text("ALTER TABLE machines ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'"))
            except Exception as e:
                print(f"Timestamp conversion warning: {e}")

            print("\n--- MIGRATING TASKS ---")
            
            # 4. Fix is_deleted for tasks
            print("Normalizing is_deleted...")
            conn.execute(text("UPDATE tasks SET is_deleted = FALSE WHERE is_deleted IS NULL"))
            conn.execute(text("ALTER TABLE tasks ALTER COLUMN is_deleted SET DEFAULT FALSE"))

            # 5. Fix Timestamps for tasks
            print("Converting timestamps to TIMESTAMPTZ...")
            try:
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"))
                # Columns might be started_at, completed_at, etc.
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE USING started_at AT TIME ZONE 'UTC'"))
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE USING completed_at AT TIME ZONE 'UTC'"))
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN actual_start_time TYPE TIMESTAMP WITH TIME ZONE USING actual_start_time AT TIME ZONE 'UTC'"))
                conn.execute(text("ALTER TABLE tasks ALTER COLUMN actual_end_time TYPE TIMESTAMP WITH TIME ZONE USING actual_end_time AT TIME ZONE 'UTC'"))
            except Exception as e:
                print(f"Timestamp conversion warning: {e}")

            print("\nMigration completed successfully.")

if __name__ == "__main__":
    run_migration()
