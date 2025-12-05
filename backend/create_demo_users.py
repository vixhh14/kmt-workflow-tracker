"""
Script to create demo users for testing the authentication system.
Run this script to populate your SQLite database with test users.
"""
import sys
import os
import uuid
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password

def create_demo_users():
    """Create demo users with different roles."""
    
    demo_users = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@workflow.com",
            "role": "admin",
            "full_name": "Admin User",
            "approval_status": "approved"
        },
        {
            "username": "operator",
            "password": "operator123",
            "email": "operator@workflow.com",
            "role": "operator",
            "full_name": "Operator User",
            "approval_status": "approved"
        },
        {
            "username": "supervisor",
            "password": "supervisor123",
            "email": "supervisor@workflow.com",
            "role": "supervisor",
            "full_name": "Supervisor User",
            "approval_status": "approved"
        },
        {
            "username": "planning",
            "password": "planning123",
            "email": "planning@workflow.com",
            "role": "planning",
            "full_name": "Planning User",
            "approval_status": "approved"
        }
    ]
    
    print("Creating demo users...")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        # First, check if any admin exists
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            print("⚠️  No admin found! Creating default admin account...")
            default_admin = User(
                user_id=str(uuid.uuid4()),
                username="admin",
                password_hash=hash_password("admin123"),
                email="admin@workflow.com",
                role="admin",
                full_name="Admin User",
                approval_status="approved"
            )
            db.add(default_admin)
            db.commit()
            print("✅ Default admin created: admin / admin123")
        
        # Now create/update other demo users
        for user_data in demo_users:
            username = user_data['username']
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            
            if existing_user:
                print(f"⚠️  User '{username}' already exists, updating password...")
                existing_user.password_hash = hash_password(user_data['password'])
                existing_user.approval_status = user_data['approval_status'] # Ensure status is correct
                continue
            
            # Create new user
            new_user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                password_hash=hash_password(user_data['password']),
                email=user_data['email'],
                role=user_data['role'],
                full_name=user_data['full_name'],
                approval_status=user_data['approval_status']
            )
            
            db.add(new_user)
            print(f"✅ Created user: {username} (role: {user_data['role']})")
            
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("-" * 50)
    print("\n📋 Demo User Credentials:")
    print("-" * 50)
    for user_data in demo_users:
        print(f"Username: {user_data['username']:12} | Password: {user_data['password']:15} | Role: {user_data['role']}")
    print("-" * 50)
    print("\n✅ Demo users created successfully!")
    print("You can now login at http://localhost:5173/login")

if __name__ == "__main__":
    create_demo_users()
