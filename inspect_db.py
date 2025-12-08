import sqlite3
import os

db_path = 'backend/workflow.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"Successfully opened database: {db_path}")
print("\n--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(f"- {t[0]}")

print("\n--- Users (Sample) ---")
try:
    cursor.execute("SELECT username, role, approval_status FROM users LIMIT 5")
    users = cursor.fetchall()
    for u in users:
        print(f"User: {u[0]}, Role: {u[1]}, Status: {u[2]}")
except Exception as e:
    print(f"Could not read users: {e}")

conn.close()
