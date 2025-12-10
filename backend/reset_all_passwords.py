import os
import sys
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password

def reset_all_passwords():
    db: Session = SessionLocal()
    try:
        users_to_reset = [
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

        print("🔐 Starting Password Reset Process...")

        for user_data in users_to_reset:
            username = user_data["username"]
            new_password = user_data["password"]
            role = user_data["role"]
            
            print(f"\n🔍 Checking for '{username}' ({role})...")
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"   ❌ User '{username}' not found! Creating new user...")
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
                print(f"   ✅ User '{username}' found.")
                # Ensure role is correct (per requirements "Roles must remain unchanged", 
                # but if we are fixing/creating, we should ensure consistency for the demo users)
                # The requirement says "Roles must remain unchanged" for existing users.
                # I will NOT update the role if user exists, to be safe, unless it's a mismatch that breaks things?
                # User said "If any user does not exist ... create them with the correct role."
                # User said "Roles must remain unchanged." -> Implies for existing users.
                pass 

            # Reset Password
            user.password_hash = hash_password(new_password)
            print(f"   🔑 Password set to: {new_password}")

        db.commit()
        print("\n✅ All passwords have been successfully reset!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_passwords()
