#!/usr/bin/env python3
"""
Fast user creation - adds demo users to Google Sheets with immediate feedback
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_users_fast():
    """Create users with immediate feedback"""
    print("🚀 Starting fast user creation...")
    
    # Import here to avoid slow startup
    from app.services.google_sheets import google_sheets
    from app.core.auth_utils import hash_password
    
    users_to_create = [
        ("admin", "Admin@Demo2025!", "admin", "System Admin"),
        ("operator", "Operator@Demo2025!", "operator", "Operator User"),
        ("supervisor", "Supervisor@Demo2025!", "supervisor", "Supervisor User"),
        ("planning", "Planning@Demo2025!", "planning", "Planning User"),
        ("file_master", "File@Demo2025!", "file_master", "File Master"),
        ("fab_master", "Fab@Demo2025!", "fab_master", "Fabrication Master"),
    ]
    
    print(f"\n📝 Creating {len(users_to_create)} users...")
    print("=" * 60)
    
    for username, password, role, full_name in users_to_create:
        try:
            print(f"\n🔨 Creating: {username} ({role})...", end=" ", flush=True)
            
            user_data = {
                "user_id": str(uuid.uuid4()),
                "username": username,
                "password_hash": hash_password(password),
                "email": f"{username}@kmt.com",
                "role": role,
                "full_name": full_name,
                "approval_status": "approved",
                "active": "TRUE",
                "is_deleted": "FALSE",
                "created_at": datetime.now().isoformat()
            }
            
            google_sheets.insert_row("Users", user_data)
            print("✅ DONE")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ USER CREATION COMPLETE!")
    print("\n🔑 Login Credentials:")
    print("-" * 60)
    for username, password, role, _ in users_to_create:
        print(f"  {role:15} | {username:15} | {password}")
    print("-" * 60)

if __name__ == "__main__":
    try:
        create_users_fast()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
