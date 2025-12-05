import sqlite3

def list_users_sqlite():
    try:
        conn = sqlite3.connect('workflow.db')
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Table 'users' does not exist.")
            return

        cursor.execute("SELECT username, role, approval_status, password_hash FROM users")
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users in SQLite DB:")
        for user in users:
            print(f"Username: {user[0]}, Role: {user[1]}, Status: {user[2]}, Hash: {user[3][:10]}...")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_users_sqlite()
