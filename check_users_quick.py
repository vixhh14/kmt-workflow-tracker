import sqlite3

try:
    conn = sqlite3.connect('backend/workflow.db')
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("❌ Users table does not exist!")
    else:
        cursor.execute("SELECT username, role, approval_status FROM users")
        users = cursor.fetchall()
        print(f"✅ Found {len(users)} users in database:")
        print("-" * 60)
        for u in users:
            print(f"Username: {u[0]:15} | Role: {u[1]:12} | Status: {u[2]}")
        print("-" * 60)
        
        if len(users) == 0:
            print("\n⚠️  No users found! Run: python backend/create_demo_users.py")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
