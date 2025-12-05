import sqlite3
import json

try:
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=== TABLES ===")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n=== DATA COUNTS ===")
    
    # Count users
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"Users: {cursor.fetchone()[0]}")
    
    # Count tasks
    try:
        cursor.execute("SELECT COUNT(*) FROM tasks")
        print(f"Tasks: {cursor.fetchone()[0]}")
    except:
        print("Tasks: Table doesn't exist")
    
    # Count machines
    try:
        cursor.execute("SELECT COUNT(*) FROM machines")
        print(f"Machines: {cursor.fetchone()[0]}")
    except:
        print("Machines: Table doesn't exist")
    
    # Show sample tasks
    print("\n=== SAMPLE TASKS ===")
    try:
        cursor.execute("SELECT id, title, status, assigned_to FROM tasks LIMIT 5")
        tasks = cursor.fetchall()
        if tasks:
            for task in tasks:
                print(f"  ID: {task[0]}, Title: {task[1]}, Status: {task[2]}, Assigned: {task[3]}")
        else:
            print("  No tasks found")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Show sample users
    print("\n=== SAMPLE USERS ===")
    cursor.execute("SELECT user_id, username, role FROM users LIMIT 5")
    users = cursor.fetchall()
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
    
    conn.close()
    print("\n✅ Database check complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
