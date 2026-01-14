#!/usr/bin/env python3
"""
Reset all user passwords in Google Sheets
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import bcrypt directly
import bcrypt

def hash_password_direct(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def reset_all_passwords():
    """Reset all user passwords"""
    print("🔧 Resetting all user passwords in Google Sheets...")
    print("=" * 80)
    
    # Import Google Sheets service
    from app.services.google_sheets import google_sheets
    
    # User credentials
    users_passwords = {
        "admin": "Admin@Demo2025!",
        "operator": "Operator@Demo2025!",
        "supervisor": "Supervisor@Demo2025!",
        "planning": "Planning@Demo2025!",
        "file_master": "File@Demo2025!",
        "fab_master": "Fab@Demo2025!",
    }
    
    # Get all users
    print("\n📊 Fetching users from Google Sheets...")
    users = google_sheets.read_all("Users")
    print(f"✅ Found {len(users)} users\n")
    
    # Update each user
    updated_count = 0
    for idx, user in enumerate(users):
        username = user.get('username', '').lower()
        
        if username in users_passwords:
            password = users_passwords[username]
            new_hash = hash_password_direct(password)
            
            print(f"🔐 Updating {username}...")
            print(f"   Password: {password}")
            print(f"   New hash: {new_hash[:30]}...")
            
            # Get the user_id to update
            user_id = user.get('user_id')
            if not user_id:
                print(f"   ⚠️  No user_id found, skipping...")
                continue
            
            # Update user data
            update_data = {
                'password_hash': new_hash,
                'approval_status': 'approved',
                'is_deleted': 'FALSE',
                'active': 'TRUE'
            }
            
            # Update in sheets using user_id
            google_sheets.update_row("Users", user_id, update_data)
            print(f"   ✅ Updated!\n")
            updated_count += 1
    
    print("=" * 80)
    print(f"✅ Updated {updated_count} users!")
    print("\n🔑 Login Credentials:")
    print("-" * 80)
    for username, password in users_passwords.items():
        print(f"  {username:15} | {password}")
    print("-" * 80)
    
    # Verify
    print("\n🧪 Verifying passwords...")
    users_updated = google_sheets.read_all("Users")
    
    for user in users_updated:
        username = user.get('username', '').lower()
        if username in users_passwords:
            password = users_passwords[username]
            stored_hash = user.get('password_hash', '')
            
            if stored_hash:
                try:
                    is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                    status = "✅ PASS" if is_valid else "❌ FAIL"
                    print(f"  {username:15} | {status}")
                except Exception as e:
                    print(f"  {username:15} | ❌ Error: {e}")
    
    print("\n✅ DONE! You can now log in with the credentials above.")

if __name__ == "__main__":
    try:
        reset_all_passwords()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
