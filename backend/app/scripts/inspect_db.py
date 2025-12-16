from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL

def inspect_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("\n--- MACHINES TABLE ---")
        result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'machines'"))
        for row in result:
            print(f"{row.column_name}: {row.data_type} (Nullable: {row.is_nullable})")
            
        print("\n--- TASKS TABLE ---")
        result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'tasks'"))
        for row in result:
            print(f"{row.column_name}: {row.data_type} (Nullable: {row.is_nullable})")

if __name__ == "__main__":
    inspect_schema()
