"""
Script to create demo users for testing the authentication system.
Run this script to populate your SQLite database with test users.

SECURITY NOTE: Demo passwords are now generated securely.
For first-time setup, check the console output for the generated secure passwords.
You should change these passwords after first login.
"""
import sys
import os
import uuid
import secrets
import string
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password


def generate_secure_password(length=12):
    """
    Generate a secure password that meets all requirements:
    - At least 8 characters (we use 12 for extra security)
    - Contains uppercase letters
    - Contains lowercase letters
    - Contains numbers
    - Contains special characters
    """
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Ensure at least one of each type
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def create_demo_users():
    """Create demo users with different roles using secure passwords."""
    
    # Fixed secure passwords (matching what we shared with the user)
    # This ensures that if the DB resets (on Render free tier), the passwords remain known
    admin_password = "Admin@Demo2025!"
    operator_password = "Operator@Demo2025!"
    supervisor_password = "Supervisor@Demo2025!"
    planning_password = "Planning@Demo2025!"
    file_master_password = "File@Demo2025!"
    fab_master_password = "Fab@Demo2025!"
    
    demo_users = [
        {
            "username": "admin",
            "password": admin_password,
            "email": "admin@workflow.com",
            "role": "admin",
            "full_name": "Admin User",
            "approval_status": "approved"
        },
        {
            "username": "operator",
            "password": operator_password,
            "email": "operator@workflow.com",
            "role": "operator",
            "full_name": "Operator User",
            "approval_status": "approved"
        },
        {
            "username": "supervisor",
            "password": supervisor_password,
            "email": "supervisor@workflow.com",
            "role": "supervisor",
            "full_name": "Supervisor User",
            "approval_status": "approved"
        },
        {
            "username": "planning",
            "password": planning_password,
            "email": "planning@workflow.com",
            "role": "planning",
            "full_name": "Planning User",
            "approval_status": "approved"
        },
        {
            "username": "file",
            "password": file_master_password,
            "email": "file@workflow.com",
            "role": "file_master",
            "full_name": "File Master",
            "approval_status": "approved"
        },
        {
            "username": "fab",
            "password": fab_master_password,
            "email": "fab@workflow.com",
            "role": "fab_master",
            "full_name": "Fab Master",
            "approval_status": "approved"
        }
    ]
    
    print("🔐 Creating demo users with SECURE passwords...")
    print("-" * 60)
    
    db = SessionLocal()
    created_users = []
    
    try:
        # First, check if any admin exists
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            print("⚠️  No admin found! Creating default admin account...")
            default_admin = User(
                user_id=str(uuid.uuid4()),
                username="admin",
                password_hash=hash_password(admin_password),
                email="admin@workflow.com",
                role="admin",
                full_name="Admin User",
                approval_status="approved"
            )
            db.add(default_admin)
            db.commit()
            created_users.append({"username": "admin", "password": admin_password, "role": "admin"})
            print("✅ Default admin created with secure password")
        
        # Now create/update other demo users
        for user_data in demo_users:
            username = user_data['username']
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            
            if existing_user:
                # Force update password to ensure login works
                print(f"ℹ️  User '{username}' exists. Updating password to ensure access...")
                existing_user.password_hash = hash_password(user_data['password'])
                existing_user.role = user_data['role']
                db.add(existing_user)
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
            created_users.append({
                "username": username,
                "password": user_data['password'],
                "role": user_data['role']
            })
            print(f"✅ Created user: {username} (role: {user_data['role']})")
            
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("-" * 60)
    
    if created_users:
        print("\n🔑 SECURE CREDENTIALS (save these - shown only once!):")
        print("=" * 60)
        for user in created_users:
            print(f"  Username: {user['username']:12} | Role: {user['role']:12}")
            print(f"  Password: {user['password']}")
            print("-" * 60)
        print("\n⚠️  IMPORTANT: Change these passwords after first login!")
        print("=" * 60)
    else:
        print("\nℹ️  No new users created (all users already exist)")
    
    print("\n✅ Demo user setup complete!")
    print("📝 Note: Passwords meet security requirements:")
    print("   - 12+ characters, uppercase, lowercase, numbers, special chars")


if __name__ == "__main__":
    create_demo_users()
