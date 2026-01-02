from app.models.models_db import User
from app.core.database import SessionLocal
from sqlalchemy import or_

def check_users():
    session = SessionLocal()
    try:
        print("--- ALL USERS ---")
        users = session.query(User).all()
        for u in users:
            print(f"ID: {u.user_id}, Name: {u.full_name}, Role: {u.role}, Deleted: {u.is_deleted}")
            
        print("\n--- TRACKED ROLES (FILTERED) ---")
        tracked_roles = ['operator', 'supervisor', 'planning', 'admin', 'file_master', 'fab_master']
        filtered = session.query(User).filter(
            or_(User.is_deleted == False, User.is_deleted == None),
            User.role.in_(tracked_roles)
        ).all()
        for u in filtered:
            print(f"ID: {u.user_id}, Name: {u.full_name}, Role: {u.role}")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_users()
