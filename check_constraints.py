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

def check_constraints():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
        
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking constraints for filing_tasks and fabrication_tasks...")
        
        # Query to find foreign key constraints
        query = text("""
            SELECT conname, conrelid::regclass, confrelid::regclass
            FROM pg_constraint
            WHERE contype = 'f' 
            AND (conrelid::regclass::text = 'filing_tasks' OR conrelid::regclass::text = 'fabrication_tasks')
            AND (array_to_string(conkey, ',') IN (
                SELECT array_to_string(attnum, ',')
                FROM pg_attribute
                WHERE attrelid = conrelid AND attname = 'assigned_to'
            ));
        """)
        
        result = conn.execute(query).fetchall()
        for row in result:
            print(f"Constraint Found: {row[0]} on table {row[1]} referencing {row[2]}")

if __name__ == "__main__":
    check_constraints()
