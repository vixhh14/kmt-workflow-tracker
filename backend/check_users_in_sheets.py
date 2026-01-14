#!/usr/bin/env python3
"""
Check what users are actually in Google Sheets
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the GOOGLE_SHEET_ID
os.environ['GOOGLE_SHEET_ID'] = '1ul_L4G-z-jkcUUYu4cCJfxtytpCx6bz5TeIJPjVuOz8'

def check_users():
    """Check all users in Google Sheets"""
    print("🔍 Checking users in Google Sheets...")
    print("=" * 100)
    
    from app.services.google_sheets import google_sheets
    
    # Get all users
    users = google_sheets.read_all("Users")
    print(f"\n✅ Found {len(users)} users\n")
    
    print("📋 USER DETAILS:")
    print("-" * 100)
    print(f"{'Username':<15} | {'user_id':<38} | {'is_deleted':<12} | {'approval_status':<15}")
    print("-" * 100)
    
    for user in users:
        username = user.get('username', 'N/A')
        user_id = user.get('user_id', 'N/A')
        is_deleted = user.get('is_deleted', 'N/A')
        approval = user.get('approval_status', 'N/A')
        
        print(f"{username:<15} | {user_id:<38} | {is_deleted:<12} | {approval:<15}")
    
    print("-" * 100)
    
    # Check for admin specifically
    print("\n🔍 Looking for 'admin' user...")
    admin_users = [u for u in users if str(u.get('username', '')).lower() == 'admin']
    
    if admin_users:
        admin = admin_users[0]
        print("✅ Admin user found!")
        print(f"   Username: '{admin.get('username')}'")
        print(f"   user_id: {admin.get('user_id')}")
        print(f"   is_deleted: '{admin.get('is_deleted')}'")
        print(f"   approval_status: '{admin.get('approval_status')}'")
        print(f"   Has password_hash: {bool(admin.get('password_hash'))}")
        
        # Check if is_deleted is causing the issue
        is_deleted_val = admin.get('is_deleted', '')
        if str(is_deleted_val).upper() == 'TRUE' or is_deleted_val == True:
            print("\n❌ PROBLEM: is_deleted is TRUE!")
            print("   You need to change this to FALSE in Google Sheets")
    else:
        print("❌ Admin user NOT found!")
        print("\n📋 Available usernames:")
        for u in users:
            print(f"   - '{u.get('username')}'")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    try:
        check_users()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
