import os
import sys
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Path adjustments
BASE_DIR = os.getcwd()
sys.path.append(os.path.join(BASE_DIR, 'backend'))

# Load environment
dotenv_path = os.path.join(BASE_DIR, 'backend', '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def drop_constraints():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
        
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Dropping foreign key constraints for assigned_to...")
        
        # We know the names from the error message or common naming patterns
        # Constraint error said: filing_tasks_assigned_to_fkey
        
        statements = [
            "ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_assigned_to_fkey;",
            "ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_assigned_to_fkey;"
        ]
        
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"Executed: {stmt}")
            except Exception as e:
                print(f"Error executing {stmt}: {e}")

if __name__ == "__main__":
    drop_constraints()
