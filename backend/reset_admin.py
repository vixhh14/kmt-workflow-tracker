"""
Quick script to reset admin password with proper bcrypt hash
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_password():
    db = SessionLocal()
    try:
        # Find admin user
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            # Hash the password properly
            new_hash = pwd_context.hash("admin123")
            admin.password_hash = new_hash
            admin.approval_status = "approved"
            db.commit()
            print(f"✅ Admin password reset successfully!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Hash starts with: {new_hash[:10]}...")
        else:
            print("❌ Admin user not found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
