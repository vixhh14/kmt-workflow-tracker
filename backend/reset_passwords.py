"""
Script to reset demo user passwords with new bcrypt implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password

def reset_passwords():
    """Reset passwords for all demo users."""
    
    demo_users = [
        {"username": "admin", "password": "admin123"},
        {"username": "operator", "password": "operator123"},
        {"username": "supervisor", "password": "supervisor123"},
        {"username": "planning", "password": "planning123"}
    ]
    
    print("Resetting user passwords...")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        for user_data in demo_users:
            username = user_data['username']
            password = user_data['password']
            
            # Find user
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                # Update password hash
                new_hash = hash_password(password)
                user.password_hash = new_hash
                user.approval_status = 'approved'
                print(f"Updated password for: {username}")
            else:
                print(f"User not found: {username}")
        
        db.commit()
        print("-" * 50)
        print("Password reset completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()
