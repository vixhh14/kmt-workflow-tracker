import os
import sys
from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import verify_password

def verify_login():
    db = SessionLocal()
    try:
        print("🔍 Verifying login credentials...")
        username = "admin"
        password = "Admin@Demo2025!"
        
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print("❌ Admin user not found in DB!")
            return
            
        print(f"👤 Found user: {user.username}")
        
        is_valid = verify_password(password, user.password_hash)
        
        if is_valid:
            print("✅ Login Verification SUCCESSFUL!")
            print("   The password matches the hash in the database.")
            print("   Authentication logic is working correctly.")
        else:
            print("❌ Login Verification FAILED!")
            print("   Password does not match the hash.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_login()
