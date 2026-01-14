"""
Script to find ALL .db files and check for machine data.
"""
import os
import sqlite3

ROOT_DIR = r"d:\KMT\workflow_tracker2"

print(f"Searching for .db files in: {ROOT_DIR}")
print("-" * 60)

db_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith(".db") or file.endswith(".sqlite"):
            full_path = os.path.join(root, file)
            db_files.append(full_path)
            print(f"Found DB: {full_path}")

print("-" * 60)

for db_path in db_files:
    print(f"\nChecking: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for machines table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='machines'")
        if cursor.fetchone():
            cursor.execute("SELECT count(*) FROM machines")
            count = cursor.fetchone()[0]
            print(f"✅ Found 'machines' table with {count} records")
            
            if count > 0:
                cursor.execute("SELECT id, name, status FROM machines LIMIT 5")
                rows = cursor.fetchall()
                for row in rows:
                    print(f"   - {row}")
        else:
            print("❌ No 'machines' table found")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error reading DB: {e}")

print("\nDone.")
