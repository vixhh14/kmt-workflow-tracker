from sqlalchemy import text
from app.core.database import engine
import sys

def migrate():
    print("Starting Project ID Column Type Migration (INTEGER -> VARCHAR)...", flush=True)
    try:
        with engine.connect() as conn:
            # 1. Update Referencing Tables
            print("Updating tasks table...", flush=True)
            conn.execute(text("ALTER TABLE tasks ALTER COLUMN project_id TYPE VARCHAR USING project_id::VARCHAR"))
            
            print("Updating filing_tasks table...", flush=True)
            conn.execute(text("ALTER TABLE filing_tasks ALTER COLUMN project_id TYPE VARCHAR USING project_id::VARCHAR"))
            
            print("Updating fabrication_tasks table...", flush=True)
            conn.execute(text("ALTER TABLE fabrication_tasks ALTER COLUMN project_id TYPE VARCHAR USING project_id::VARCHAR"))
            
            # 2. Update Primary Table
            print("Updating projects table...", flush=True)
            conn.execute(text("ALTER TABLE projects ALTER COLUMN project_id TYPE VARCHAR USING project_id::VARCHAR"))
            
            conn.commit()
            print("✅ Migration Successful: All project_id columns converted to VARCHAR.", flush=True)
    except Exception as e:
        print(f"❌ Migration Failed: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    migrate()
