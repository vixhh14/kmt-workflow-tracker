"""
Verify Database Users Script
=============================
This script checks all users in the database and verifies their credentials.
"""

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import verify_password

def verify_users():
    db = SessionLocal()
    try:
        print("\n" + "="*60)
        print("DATABASE USERS VERIFICATION")
        print("="*60 + "\n")
        
        users = db.query(User).filter(User.is_deleted == False).all()
        
        if not users:
            print("❌ No users found in database!")
            return
        
        print(f"Found {len(users)} active users:\n")
        
        for user in users:
            print(f"Username: {user.username}")
            print(f"  - User ID: {user.user_id}")
            print(f"  - Email: {user.email}")
            print(f"  - Role: {user.role}")
            print(f"  - Full Name: {user.full_name}")
            print(f"  - Approval Status: {getattr(user, 'approval_status', 'N/A')}")
            print(f"  - Has Password Hash: {'✅ Yes' if user.password_hash else '❌ No'}")
            
            # Check if password hash is valid bcrypt format
            if user.password_hash:
                if user.password_hash.startswith('$2b$'):
                    print(f"  - Password Hash Format: ✅ Valid bcrypt")
                else:
                    print(f"  - Password Hash Format: ❌ Invalid (not bcrypt)")
            
            print()
        
        print("="*60)
        print("\nTo test login, use these credentials:")
        print("  - admin / Admin@Demo2025!")
        print("  - [other users with their respective passwords]")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_users()
