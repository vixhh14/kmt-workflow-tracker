#!/usr/bin/env python3
"""
Emergency user fix script - adds demo users directly to Google Sheets
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.google_sheets import google_sheets
from app.core.auth_utils import hash_password

def fix_users():
    """Add/update demo users directly in Google Sheets"""
    
    demo_users = [
        {
            "user_id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": hash_password("Admin@Demo2025!"),
            "email": "admin@kmt.com",
            "role": "admin",
            "full_name": "System Admin",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "operator",
            "password_hash": hash_password("Operator@Demo2025!"),
            "email": "operator@kmt.com",
            "role": "operator",
            "full_name": "Operator User",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "supervisor",
            "password_hash": hash_password("Supervisor@Demo2025!"),
            "email": "supervisor@kmt.com",
            "role": "supervisor",
            "full_name": "Supervisor User",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "planning",
            "password_hash": hash_password("Planning@Demo2025!"),
            "email": "planning@kmt.com",
            "role": "planning",
            "full_name": "Planning User",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "file_master",
            "password_hash": hash_password("File@Demo2025!"),
            "email": "file_master@kmt.com",
            "role": "file_master",
            "full_name": "File Master",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "fab_master",
            "password_hash": hash_password("Fab@Demo2025!"),
            "email": "fab_master@kmt.com",
            "role": "fab_master",
            "full_name": "Fabrication Master",
            "approval_status": "approved",
            "active": "TRUE",
            "is_deleted": "FALSE",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    print("🔧 EMERGENCY USER FIX - Adding users to Google Sheets...")
    print("=" * 60)
    
    try:
        # Get current users
        existing_records = google_sheets.read_all("Users")
        existing_usernames = {str(r.get("username", "")).lower() for r in existing_records}
        
        print(f"Found {len(existing_records)} existing users")
        
        for user_data in demo_users:
            username = user_data["username"]
            
            if username.lower() in existing_usernames:
                print(f"⚠️  User '{username}' exists - finding and updating...")
                
                # Find the user_id
                user_record = next((r for r in existing_records if str(r.get("username", "")).lower() == username.lower()), None)
                
                if user_record and user_record.get("user_id"):
                    # Update existing user
                    update_data = {
                        "password_hash": user_data["password_hash"],
                        "role": user_data["role"],
                        "approval_status": "approved",
                        "is_deleted": "FALSE",
                        "active": "TRUE"
                    }
                    google_sheets.update_row("Users", user_record["user_id"], update_data)
                    print(f"   ✅ Updated '{username}' with new password")
                else:
                    print(f"   ⚠️  Could not find user_id for '{username}', skipping update")
            else:
                # Insert new user
                google_sheets.insert_row("Users", user_data)
                print(f"✅ Created new user: '{username}'")
        
        print("=" * 60)
        print("✅ USER FIX COMPLETE!")
        print("\n🔑 You can now login with:")
        print("   Username: admin | Password: Admin@Demo2025!")
        print("   Username: operator | Password: Operator@Demo2025!")
        print("   Username: supervisor | Password: Supervisor@Demo2025!")
        print("   Username: planning | Password: Planning@Demo2025!")
        print("   Username: file_master | Password: File@Demo2025!")
        print("   Username: fab_master | Password: Fab@Demo2025!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fix_users()
