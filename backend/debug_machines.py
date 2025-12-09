"""
Script to dump all machine data from the database to debug missing data issues.
"""
import sys
import os
import sqlite3

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app.core.database import DEFAULT_DB_PATH

print(f"Checking database at: {DEFAULT_DB_PATH}")

if not os.path.exists(DEFAULT_DB_PATH):
    print("❌ Database file not found!")
    sys.exit(1)

try:
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='machines'")
    if not cursor.fetchone():
        print("❌ 'machines' table does not exist!")
        sys.exit(1)
        
    # Get all machines
    cursor.execute("SELECT * FROM machines")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    print(f"\nFound {len(rows)} machines:")
    print("-" * 60)
    
    if rows:
        # Print header
        print(f"{'ID':<25} | {'Name':<30} | {'Status':<10}")
        print("-" * 60)
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(f"{str(row_dict.get('id', '')):<25} | {str(row_dict.get('name', '')):<30} | {str(row_dict.get('status', '')):<10}")
            
    else:
        print("Table is empty.")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
