from app.core.database import SessionLocal
from sqlalchemy import text

def run_normalization():
    db = SessionLocal()
    try:
        print("Running normalization...")
        with open("normalize_db.sql", "r") as f:
            sql_script = f.read()
            
        # Split by statements
        statements = sql_script.split(';')
        for stmt in statements:
            if stmt.strip():
                print(f"Executing: {stmt.strip()[:50]}...")
                db.execute(text(stmt))
        
        db.commit()
        print("Normalization complete.")
    except Exception as e:
        db.rollback()
        print(f"Error during normalization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_normalization()
