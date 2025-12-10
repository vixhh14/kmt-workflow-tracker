import os
import sys
from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import verify_password

def verify_all_logins():
    db = SessionLocal()
    try:
        users_to_verify = [
            {"username": "admin", "password": "Admin@Demo2025!"},
            {"username": "operator", "password": "Operator@Demo2025!"},
            {"username": "supervisor", "password": "Supervisor@Demo2025!"},
            {"username": "planning", "password": "Planning@Demo2025!"}
        ]

        print("🔍 Verifying All Logins...")
        all_success = True

        for creds in users_to_verify:
            username = creds["username"]
            password = creds["password"]
            
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"❌ {username}: User NOT FOUND in DB!")
                all_success = False
                continue
                
            is_valid = verify_password(password, user.password_hash)
            
            if is_valid:
                print(f"✅ {username}: Login SUCCESS")
            else:
                print(f"❌ {username}: Login FAILED (Password mismatch)")
                all_success = False

        if all_success:
            print("\n🎉 ALL VERIFICATIONS PASSED!")
        else:
            print("\n⚠️ SOME VERIFICATIONS FAILED.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_all_logins()
