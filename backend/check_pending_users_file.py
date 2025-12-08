import sqlite3
import os

def check_pending_users():
    db_path = 'workflow.db'
    output_file = 'db_check_output.txt'
    
    with open(output_file, 'w') as f:
        if not os.path.exists(db_path):
            f.write(f"Database not found at {db_path}\n")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT username, approval_status, created_at FROM users WHERE approval_status = 'pending'")
            users = cursor.fetchall()
            
            if users:
                f.write(f"Found {len(users)} pending users:\n")
                for user in users:
                    f.write(f"  User: {user[0]}, Status: {user[1]}, Created At: {user[2]}\n")
            else:
                f.write("No pending users found in the database.\n")
                
            # Also check all users to see what statuses exist
            cursor.execute("SELECT approval_status, COUNT(*) FROM users GROUP BY approval_status")
            stats = cursor.fetchall()
            f.write("\nUser Status Summary:\n")
            for stat in stats:
                f.write(f"  {stat[0]}: {stat[1]}\n")
                
        except Exception as e:
            f.write(f"Error querying database: {e}\n")
        finally:
            conn.close()

if __name__ == "__main__":
    check_pending_users()
