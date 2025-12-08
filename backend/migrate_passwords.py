"""
Password Migration Script
Updates existing demo user passwords to secure, randomly generated ones.

Run this script ONCE after deploying the password security updates.
It will:
1. Generate new secure passwords for demo users
2. Update the database with new password hashes
3. Print the new credentials (save them!)

Usage:
    cd backend
    python migrate_passwords.py
"""
import sys
import os
import secrets
import string

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password


def generate_secure_password(length=12):
    """Generate a secure password meeting all requirements."""
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
    
    # Fill the rest with random characters
    all_chars = uppercase + lowercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def migrate_passwords():
    """Update demo user passwords to secure ones."""
    
    # Demo usernames to update
    demo_usernames = ['admin', 'operator', 'supervisor', 'planning']
    
    print("=" * 60)
    print("🔐 PASSWORD MIGRATION SCRIPT")
    print("=" * 60)
    print("\nThis will update demo user passwords to secure ones.")
    print("Make sure to SAVE the new credentials!\n")
    
    db = SessionLocal()
    updated_users = []
    
    try:
        for username in demo_usernames:
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                # Generate new secure password
                new_password = generate_secure_password()
                
                # Update the hash
                user.password_hash = hash_password(new_password)
                
                updated_users.append({
                    'username': username,
                    'password': new_password,
                    'role': user.role,
                    'email': user.email
                })
                
                print(f"✅ Updated password for: {username}")
            else:
                print(f"⚠️  User not found: {username}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("🔑 NEW SECURE CREDENTIALS")
        print("=" * 60)
        print("\n⚠️  SAVE THESE NOW - They won't be shown again!\n")
        
        for user in updated_users:
            print("-" * 60)
            print(f"  Username: {user['username']}")
            print(f"  Password: {user['password']}")
            print(f"  Role:     {user['role']}")
            print(f"  Email:    {user['email']}")
        
        print("-" * 60)
        print("\n✅ Migration complete!")
        print("\n📝 Password requirements now enforced:")
        print("   - 8+ characters")
        print("   - Uppercase letter (A-Z)")
        print("   - Lowercase letter (a-z)")
        print("   - Number (0-9)")
        print("   - Special character (!@#$%^&*)")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    return updated_users


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will change all demo user passwords!")
    print("    Make sure you're ready to save the new credentials.\n")
    
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        migrate_passwords()
    else:
        print("\n❌ Migration cancelled.")
