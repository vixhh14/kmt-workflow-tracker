import sqlite3

def check_test_user():
    conn = sqlite3.connect('backend/workflow.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, approval_status, unit_id, machine_types FROM users WHERE username LIKE 'testuser_%'")
    users = cursor.fetchall()
    
    if users:
        print(f"Found {len(users)} test users:")
        for user in users:
            print(f"  User: {user[0]}, Status: {user[1]}, Unit: {user[2]}, Machines: {user[3]}")
    else:
        print("No test users found.")
        
    conn.close()

if __name__ == "__main__":
    check_test_user()
