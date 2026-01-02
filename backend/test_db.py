from app.core.database import engine
from sqlalchemy import text
print("Testing DB connection...")
try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).fetchone()
        print(f"Connection successful: {res}")
except Exception as e:
    print(f"Connection failed: {e}")
