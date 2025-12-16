
import sys
import os
import sqlalchemy
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv()

from app.core import database

def audit_tasks_table():
    print(f"Connecting to DB...")
    inspector = inspect(database.engine)
    
    print("\n--- TABLE: tasks ---")
    try:
        columns = inspector.get_columns('tasks')
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    except Exception as e:
        print(f"Error inspecting tasks: {e}")

if __name__ == "__main__":
    audit_tasks_table()
