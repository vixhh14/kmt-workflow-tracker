import sys
import os
from sqlalchemy import create_engine, text

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.app.core.config import settings

def add_columns():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Check if columns exist
        try:
            # 1. ended_by
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN ended_by VARCHAR"))
                print("✅ Added 'ended_by' column to tasks table.")
            except Exception as e:
                print(f"ℹ️ 'ended_by' column likely exists or error: {e}")

            # 2. end_reason
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN end_reason VARCHAR"))
                print("✅ Added 'end_reason' column to tasks table.")
            except Exception as e:
                print(f"ℹ️ 'end_reason' column likely exists or error: {e}")

        except Exception as e:
            print(f"❌ unexpected error: {e}")

if __name__ == "__main__":
    add_columns()
