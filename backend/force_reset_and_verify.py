import os
import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv(os.path.join("backend", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

print("🔍 Checking Environment Configuration...")
if not DATABASE_URL:
    print("❌ DATABASE_URL is MISSING in environment variables!")
    sys.exit(1)

# Handle Render's postgres:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"✅ DATABASE_URL found: {DATABASE_URL.split('@')[-1]}") # Print only host part for security

# 2. Setup Database Connection
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("✅ Connected to Database successfully.")
except Exception as e:
    print(f"❌ Failed to connect to database: {e}")
    sys.exit(1)

# Import models and utils
# We need to make sure app is in python path
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.models.models_db import User
from app.core.auth_utils import hash_password, verify_password

def force_reset_and_verify():
    try:
        users_to_process = [
            {
                "username": "admin",
                "password": "Admin@Demo2025!",
                "role": "admin",
                "email": "admin@example.com",
                "full_name": "System Admin"
            },
            {
                "username": "operator",
                "password": "Operator@Demo2025!",
                "role": "operator",
                "email": "operator@example.com",
                "full_name": "Machine Operator"
            },
            {
                "username": "supervisor",
                "password": "Supervisor@Demo2025!",
                "role": "supervisor",
                "email": "supervisor@example.com",
                "full_name": "Floor Supervisor"
            },
            {
                "username": "planning",
                "password": "Planning@Demo2025!",
                "role": "planning",
                "email": "planning@example.com",
                "full_name": "Production Planner"
            }
        ]

        print("\n🔐 Starting User Upsert & Password Reset...")

        for user_data in users_to_process:
            username = user_data["username"]
            password = user_data["password"]
            role = user_data["role"]
            
            print(f"\n👤 Processing user: {username}")
            
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"   ⚠️ User not found. Creating new user...")
                user = User(
                    user_id=str(uuid.uuid4()),
                    username=username,
                    email=user_data["email"],
                    role=role,
                    full_name=user_data["full_name"],
                    approval_status="approved"
                )
                db.add(user)
            else:
                print(f"   ✅ User exists.")
            
            # Reset Password
            print(f"   🔑 Resetting password...")
            user.password_hash = hash_password(password)
            db.commit()
            db.refresh(user)
            
            # Verify immediately
            print(f"   🕵️ Verifying login logic...")
            if verify_password(password, user.password_hash):
                print(f"   ✅ Login Verification SUCCESSFUL for {username}")
            else:
                print(f"   ❌ Login Verification FAILED for {username}")

        print("\n🎉 All operations completed.")

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_reset_and_verify()
