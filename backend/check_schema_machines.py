import sqlite3
import os

db_path = 'workflow.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='machines'")
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print("Table 'machines' not found.")
conn.close()
