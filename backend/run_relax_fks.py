import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_relax_fks():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    with open("relax_fks.sql", "r") as f:
        sql_content = f.read()
    
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    with engine.connect() as connection:
        for stmt in statements:
            print(f"Executing: {stmt}")
            try:
                connection.execute(text(stmt))
                connection.commit()
                print("Success.")
            except Exception as e:
                print(f"Error executing statement: {e}")
                connection.rollback()

if __name__ == "__main__":
    run_relax_fks()
