import sys
import os
from sqlalchemy import create_engine, text

# Add the parent directory to the Python path
# Add the parent directory (backend) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

LOG_FILE = "migration_status.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg)

log("---------- Starting migration script... ----------")
log(f"DEBUG: sys.path: {sys.path}")

try:
    from app.core.config import settings
    log("Imported settings successfully.")

    def add_columns():
        log(f"Connecting to DB: {settings.DATABASE_URL.split('@')[-1]}") # Log safe part of URL
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # Check if columns exist
            try:
                # 1. ended_by
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN ended_by VARCHAR"))
                    log("✅ Added 'ended_by' column to tasks table.")
                except Exception as e:
                    log(f"ℹ️ 'ended_by' column likely exists or error: {e}")

                # 2. end_reason
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN end_reason VARCHAR"))
                    log("✅ Added 'end_reason' column to tasks table.")
                except Exception as e:
                    log(f"ℹ️ 'end_reason' column likely exists or error: {e}")

            except Exception as e:
                log(f"❌ unexpected error connecting/executing: {e}")

    if __name__ == "__main__":
        add_columns()
        log("Migration script finished.")

except Exception as e:
    log(f"CRITICAL ERROR during import or setup: {e}")

