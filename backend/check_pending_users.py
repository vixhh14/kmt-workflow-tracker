import sqlite3
import os

def check_pending_users():
    db_path = 'backend/workflow.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT username, approval_status, created_at FROM users WHERE approval_status = 'pending'")
        users = cursor.fetchall()
        
        if users:
            print(f"Found {len(users)} pending users:")
            for user in users:
                print(f"  User: {user[0]}, Status: {user[1]}, Created At: {user[2]}")
        else:
            print("No pending users found in the database.")
            
        # Also check all users to see what statuses exist
        cursor.execute("SELECT approval_status, COUNT(*) FROM users GROUP BY approval_status")
        stats = cursor.fetchall()
        print("\nUser Status Summary:")
        for stat in stats:
            print(f"  {stat[0]}: {stat[1]}")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_pending_users()
