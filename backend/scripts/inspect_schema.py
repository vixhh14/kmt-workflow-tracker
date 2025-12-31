
import sys
import os
from sqlalchemy import create_engine, inspect

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), "backend", ".env")) # Adjust path if needed
# Actually .env might be in root or backend? database.py loads from cwd usually.

def get_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        # Try loading from backend/.env explicitly if not set
        load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
        url = os.getenv("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def inspect_db():
    url = get_db_url()
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        
        with open("schema_info.txt", "w") as f:
            f.write("--- PROJECTS Table ---\n")
            if inspector.has_table("projects"):
                columns = inspector.get_columns("projects")
                for col in columns:
                    f.write(f"{col['name']}: {col['type']}\n")
            else:
                f.write("projects table NOT FOUND\n")

            f.write("\n--- FILING_TASKS Table ---\n")
            if inspector.has_table("filing_tasks"):
                columns = inspector.get_columns("filing_tasks")
                for col in columns:
                    f.write(f"{col['name']}: {col['type']}\n")
            else:
                f.write("filing_tasks table NOT FOUND\n")

            f.write("\n--- FABRICATION_TASKS Table ---\n")
            if inspector.has_table("fabrication_tasks"):
                columns = inspector.get_columns("fabrication_tasks")
                for col in columns:
                    f.write(f"{col['name']}: {col['type']}\n")
            else:
                f.write("fabrication_tasks table NOT FOUND\n")

        print("Schema inspection complete.")
        
    except Exception as e:
        with open("schema_info.txt", "w") as f:
            f.write(f"Error inspecting DB: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
