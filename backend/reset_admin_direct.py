"""
Simple script to reset admin password - bypassing passlib issues
"""
import sqlite3
import bcrypt

def reset_admin():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('workflow.db')
        cursor = conn.cursor()
        
        # Hash the password directly with bcrypt
        password = "admin123"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Update admin user
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, approval_status = 'approved'
            WHERE username = 'admin'
        """, (hashed.decode('utf-8'),))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print("✅ Admin password reset successfully!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Hash: {hashed.decode('utf-8')[:20]}...")
        else:
            print("❌ Admin user not found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_admin()
