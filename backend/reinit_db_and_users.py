import os
import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 1. Load Environment Variables
# We load .env.production because that's where we put the correct URL
load_dotenv(os.path.join("backend", ".env.production"))
DATABASE_URL = os.getenv("DATABASE_URL")

print("🔍 Checking Environment Configuration...")
if not DATABASE_URL:
    print("❌ DATABASE_URL is MISSING in environment variables!")
    # Fallback to .env just in case
    load_dotenv(os.path.join("backend", ".env"))
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL is MISSING in .env as well!")
        sys.exit(1)

# Handle Render's postgres:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"✅ DATABASE_URL found: {DATABASE_URL.split('@')[-1]}") 

# 2. Setup Database Connection
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("✅ Connected to Database successfully.")
except Exception as e:
    print(f"❌ Failed to connect to database: {e}")
    sys.exit(1)

# Import models
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.models.models_db import Base, User
from app.core.auth_utils import hash_password

def reinit_db_and_users():
    try:
        print("\n🏗️ Creating all tables (if not exist)...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables verified/created.")

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

        print("\n🔐 Upserting Default Users...")

        for user_data in users_to_process:
            username = user_data["username"]
            password = user_data["password"]
            role = user_data["role"]
            
            print(f"\n👤 Processing user: {username}")
            
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
                print(f"   ✅ User exists. Updating password...")
            
            # Always reset password to ensure it's correct
            user.password_hash = hash_password(password)
            db.commit()
            print(f"   ✅ Password set/updated.")

        print("\n🎉 Database initialized and users created.")

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reinit_db_and_users()
