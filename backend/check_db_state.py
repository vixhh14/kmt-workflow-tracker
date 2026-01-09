
from app.core.database import SessionLocal, engine
from sqlalchemy import inspect
import os

def check_db():
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('users')
        print("Columns in 'users' table:")
        for column in columns:
            print(f" - {column['name']}: {column['type']}")
        
        from app.models.models_db import User
        db = SessionLocal()
        admin = db.query(User).filter(User.username == 'admin').first()
        if admin:
            print(f"Admin user found: {admin.username}, role: {admin.role}")
        else:
            print("Admin user NOT found")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
