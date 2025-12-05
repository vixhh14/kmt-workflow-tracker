from app.core.database import SessionLocal
from app.models.models_db import User

def list_db_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users in SQLite DB:")
        for user in users:
            print(f"Username: {user.username}, Role: {user.role}, Status: {getattr(user, 'approval_status', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_db_users()
