import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.core.database import engine

def check():
    try:
        with engine.connect() as conn:
            print("Connecting...")
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"Connection successful: {result}")
            
            # Check column type for tasks
            res = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='tasks' AND column_name='due_date'")).scalar()
            print(f"Current tasks.due_date type: {res}")
            
            # Check column type for filing_tasks
            res2 = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='filing_tasks' AND column_name='due_date'")).scalar()
            print(f"Current filing_tasks.due_date type: {res2}")

            # Check column type for fabrication_tasks
            res3 = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='fabrication_tasks' AND column_name='due_date'")).scalar()
            print(f"Current fabrication_tasks.due_date type: {res3}")

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    check()
