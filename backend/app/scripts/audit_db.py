
import sys
import os
import time

print("Script started..")
# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

print("Importing dotenv...")
from dotenv import load_dotenv
load_dotenv()

print("Importing sqlalchemy...")
from sqlalchemy import inspect, create_engine
from app.core import database # Force load of database module logic

print(f"DATABASE_URL is set: {bool(database.DATABASE_URL)}")
if database.DATABASE_URL:
    masked = database.DATABASE_URL.split("@")[-1] if "@" in database.DATABASE_URL else "NO_AT_SYMBOL"
    print(f"Connecting to: ...@{masked}")

def audit_db():
    try:
        print("Creating inspector...")
        # Re-create engine here to be sure, or use database.engine
        inspector = inspect(database.engine)
        print("Fetching table names...")
        tables = inspector.get_table_names()
        print("EXISTING TABLES:", tables)
        
        target_tables = ['users', 'machines', 'tasks', 'projects', 'units', 'machine_categories', 'attendance']
        
        for table in target_tables:
            if table in tables:
                print(f"\n--- TABLE: {table} ---")
                columns = inspector.get_columns(table)
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
            else:
                print(f"\n! MISSING TABLE: {table}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("Starting DB Audit...")
    audit_db()
