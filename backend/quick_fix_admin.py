"""
Ultra-simple password reset using raw SQL
"""
import sqlite3

# Pre-generated bcrypt hash for "admin123"
# Generated with: bcrypt.hashpw(b"admin123", bcrypt.gensalt())
ADMIN_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqRfQNy/mG"

try:
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    
    # Update admin password
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?, approval_status = 'approved'
        WHERE username = 'admin'
    """, (ADMIN_HASH,))
    
    conn.commit()
    
    if cursor.rowcount > 0:
        print("✅ Admin password reset successfully!")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("❌ Admin user not found")
        # Try to create admin user
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, email, role, full_name, approval_status)
            VALUES ('admin-001', 'admin', ?, 'admin@workflow.com', 'admin', 'Admin User', 'approved')
        """, (ADMIN_HASH,))
        conn.commit()
        print("✅ Admin user created!")
    
    conn.close()
    print("\n🎉 You can now login with: admin / admin123")
    
except Exception as e:
    print(f"❌ Error: {e}")
