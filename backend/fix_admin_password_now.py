#!/usr/bin/env python3
"""
Fix admin password immediately
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_admin_password():
    """Fix admin password in Google Sheets"""
    print("🔧 Fixing admin password...")
    
    from app.services.google_sheets import google_sheets
    from app.core.auth_utils import hash_password, verify_password
    
    # Get all users
    users = google_sheets.get_all_rows("Users")
    
    # Find admin
    admin_row_index = None
    for idx, user in enumerate(users):
        if user.get('username', '').lower() == 'admin':
            admin_row_index = idx
            break
    
    if admin_row_index is None:
        print("❌ Admin user not found!")
        return
    
    print(f"✅ Found admin at row {admin_row_index + 2}")  # +2 for header and 1-indexing
    
    # Generate new password hash
    new_password = "Admin@Demo2025!"
    new_hash = hash_password(new_password)
    
    print(f"🔐 Generated new hash: {new_hash[:30]}...")
    
    # Update the user
    admin_user = users[admin_row_index]
    admin_user['password_hash'] = new_hash
    admin_user['approval_status'] = 'approved'
    admin_user['is_deleted'] = 'FALSE'
    admin_user['active'] = 'TRUE'
    
    # Update in sheets (row index + 2 for header and 1-indexing)
    google_sheets.update_row("Users", admin_row_index + 2, admin_user)
    
    print("✅ Password updated in Google Sheets!")
    
    # Verify
    print("\n🧪 Verifying...")
    users_updated = google_sheets.get_all_rows("Users")
    admin_updated = next((u for u in users_updated if u.get('username', '').lower() == 'admin'), None)
    
    if admin_updated:
        stored_hash = admin_updated.get('password_hash', '')
        is_valid = verify_password(new_password, stored_hash)
        print(f"  Password verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
        print(f"  Username: {admin_updated.get('username')}")
        print(f"  Role: {admin_updated.get('role')}")
        print(f"  Approval: {admin_updated.get('approval_status')}")
        print(f"  Is Deleted: {admin_updated.get('is_deleted')}")
    
    print("\n✅ DONE! Try logging in with:")
    print(f"  Username: admin")
    print(f"  Password: {new_password}")

if __name__ == "__main__":
    try:
        fix_admin_password()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
