from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    try:
        url = settings.DATABASE_URL
        print(f"Connecting to: {url}")
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_assigned_to_fkey;"))
            conn.execute(text("ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_assigned_to_fkey;"))
            conn.commit()
            print("Constraints dropped successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
