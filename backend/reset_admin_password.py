import os
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password

def reset_admin_password():
    db: Session = SessionLocal()
    try:
        print("🔍 Checking for 'admin' user...")
        user = db.query(User).filter(User.username == "admin").first()
        
        if not user:
            print("❌ Admin user not found! Creating one...")
            # Ideally we shouldn't create if not asked, but the task implies fixing login for admin.
            # But the prompt says "The 'admin' user record exists in the database. If ... missing ... correct it."
            # So I will create it if missing.
            import uuid
            user = User(
                user_id=str(uuid.uuid4()),
                username="admin",
                email="admin@example.com",
                role="admin",
                full_name="System Admin",
                approval_status="approved"
            )
            db.add(user)
        
        print("🔐 Resetting password...")
        new_password = "Admin@Demo2025!"
        user.password_hash = hash_password(new_password)
        
        db.commit()
        print(f"✅ Password for user '{user.username}' has been reset to: {new_password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
