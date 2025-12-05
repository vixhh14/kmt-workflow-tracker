"""
Simple admin password fix - no external dependencies
"""
import sqlite3
import sys

# Pre-generated bcrypt hash for "admin123"
ADMIN_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqRfQNy/mG"

print("=" * 50)
print("Admin Password Reset Tool")
print("=" * 50)

try:
    # Connect to database
    print("\n1. Connecting to database...")
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    print("   ✅ Connected")
    
    # Check if admin exists
    print("\n2. Checking for admin user...")
    cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        print(f"   ✅ Found admin user")
        
        # Update password
        print("\n3. Updating password...")
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, approval_status = 'approved'
            WHERE username = 'admin'
        """, (ADMIN_HASH,))
        conn.commit()
        print("   ✅ Password updated")
        
    else:
        print("   ⚠️  Admin user not found, creating...")
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, email, role, full_name, approval_status)
            VALUES ('admin-001', 'admin', ?, 'admin@workflow.com', 'admin', 'Admin User', 'approved')
        """, (ADMIN_HASH,))
        conn.commit()
        print("   ✅ Admin user created")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ SUCCESS!")
    print("=" * 50)
    print("\nYou can now login with:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nNext step: Run 'uvicorn app.main:app --reload'")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nFull error details:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
