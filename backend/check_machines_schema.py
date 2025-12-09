import sqlite3
import os

db_path = 'workflow.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(machines)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Columns in machines table: {columns}")

if 'created_at' not in columns:
    print("created_at column missing.")
else:
    print("created_at column exists.")
conn.close()
