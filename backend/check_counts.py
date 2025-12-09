import sqlite3
import os

db_path = 'workflow.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM machines")
        total = cursor.fetchone()[0]
        print(f"Total machines: {total}")
        
        cursor.execute("SELECT name FROM units")
        units = cursor.fetchall()
        for unit in units:
            u_name = unit[0]
            cursor.execute("SELECT id FROM units WHERE name=?", (u_name,))
            u_id = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM machines WHERE unit_id=?", (u_id,))
            count = cursor.fetchone()[0]
            print(f"Machines in {u_name}: {count}")
            
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")
else:
    print("DB not found")
