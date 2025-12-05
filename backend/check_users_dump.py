import sqlite3
import sys

def dump_users():
    try:
        with open("users_dump.txt", "w") as f:
            conn = sqlite3.connect('workflow.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                f.write("Table 'users' does not exist.\n")
                return

            cursor.execute("SELECT username, role, approval_status, password_hash FROM users")
            users = cursor.fetchall()
            
            f.write(f"Found {len(users)} users in SQLite DB:\n")
            for user in users:
                f.write(f"Username: {user[0]}, Role: {user[1]}, Status: {user[2]}, Hash: {user[3]}\n")
                
            conn.close()
            print("Dumped users to users_dump.txt")
    except Exception as e:
        with open("users_dump.txt", "w") as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    dump_users()
