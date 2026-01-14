import os
import sys
from sqlalchemy import inspect, create_engine
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

def run():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
        
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    with open('schema_debug.txt', 'w') as f:
        f.write(f"Tables: {inspector.get_table_names()}\n")
        for table in ['projects', 'tasks', 'fabrication_tasks', 'filing_tasks']:
            f.write(f"\nColumns in {table}:\n")
            cols = inspector.get_columns(table)
            for c in cols:
                f.write(f"- {c['name']} ({c['type']})\n")

if __name__ == "__main__":
    run()
