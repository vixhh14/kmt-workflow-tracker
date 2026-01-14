#!/usr/bin/env python3
"""
Diagnose login issues - check user data and password hashes
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_login():
    """Check user data and verify password hashing"""
    print("🔍 Diagnosing login issue...")
    print("=" * 80)
    
    # Import here
    from app.services.google_sheets import google_sheets
    from app.core.auth_utils import hash_password, verify_password
    
    # Fetch all users
    print("\n📊 Fetching users from Google Sheets...")
    users = google_sheets.get_all_rows("Users")
    
    if not users:
        print("❌ No users found in Google Sheets!")
        return
    
    print(f"✅ Found {len(users)} users\n")
    
    # Check admin user specifically
    admin_users = [u for u in users if u.get('username', '').lower() == 'admin']
    
    if not admin_users:
        print("❌ No admin user found!")
        print("\n📋 Available usernames:")
        for u in users:
            print(f"  - {u.get('username', 'N/A')}")
        return
    
    admin = admin_users[0]
    print("✅ Admin user found!")
    print("\n📋 Admin User Data:")
    print("-" * 80)
    print(f"  Username:        {admin.get('username', 'N/A')}")
    print(f"  Email:           {admin.get('email', 'N/A')}")
    print(f"  Role:            {admin.get('role', 'N/A')}")
    print(f"  Full Name:       {admin.get('full_name', 'N/A')}")
    print(f"  Approval Status: {admin.get('approval_status', 'N/A')}")
    print(f"  Is Deleted:      {admin.get('is_deleted', 'N/A')}")
    print(f"  Active:          {admin.get('active', 'N/A')}")
    
    # Check password hash
    stored_hash = admin.get('password_hash', '')
    print(f"\n🔐 Password Hash Info:")
    print(f"  Hash exists:     {bool(stored_hash)}")
    print(f"  Hash length:     {len(stored_hash) if stored_hash else 0}")
    print(f"  Hash preview:    {stored_hash[:20] if stored_hash else 'N/A'}...")
    
    # Test password verification
    test_password = "Admin@Demo2025!"
    print(f"\n🧪 Testing password verification...")
    print(f"  Test password:   {test_password}")
    
    if stored_hash:
        is_valid = verify_password(test_password, stored_hash)
        print(f"  Verification:    {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        if not is_valid:
            print("\n⚠️  PASSWORD VERIFICATION FAILED!")
            print("  This means the stored hash doesn't match the expected password.")
            print("\n🔧 Generating new hash for comparison...")
            new_hash = hash_password(test_password)
            print(f"  New hash:        {new_hash[:20]}...")
            print(f"  Stored hash:     {stored_hash[:20]}...")
            print(f"  Hashes match:    {new_hash == stored_hash}")
    else:
        print("  ❌ No password hash stored!")
    
    print("\n" + "=" * 80)
    
    # Check all users for is_deleted status
    print("\n📊 All Users Summary:")
    print("-" * 80)
    for u in users:
        username = u.get('username', 'N/A')
        role = u.get('role', 'N/A')
        is_deleted = u.get('is_deleted', 'N/A')
        approval = u.get('approval_status', 'N/A')
        has_hash = bool(u.get('password_hash', ''))
        print(f"  {username:15} | {role:12} | Deleted: {is_deleted:5} | Approval: {approval:10} | Hash: {has_hash}")
    print("-" * 80)

if __name__ == "__main__":
    try:
        diagnose_login()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
