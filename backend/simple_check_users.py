import sqlite3

try:
    conn = sqlite3.connect('backend/workflow.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, approval_status FROM users")
    users = cursor.fetchall()
    print(f"Found {len(users)} users:")
    for u in users:
        print(f"User: {u[0]}, Role: {u[1]}, Status: {u[2]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
