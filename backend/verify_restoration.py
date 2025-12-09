"""
Verify that machines were seeded correctly and persistence is working.
"""
import sys
import os
import sqlite3

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app.core.database import DEFAULT_DB_PATH

print("="*60)
print("DATA RESTORATION VERIFICATION")
print("="*60)
print(f"📂 DB Path: {DEFAULT_DB_PATH}")

if not os.path.exists(DEFAULT_DB_PATH):
    print("❌ Database file not found!")
    sys.exit(1)

try:
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()
    
    # Check machines count
    cursor.execute("SELECT count(*) FROM machines")
    count = cursor.fetchone()[0]
    
    print(f"✅ Found {count} machines in database")
    
    if count > 0:
        print("\nSample Machines:")
        cursor.execute("SELECT name, category_id, unit_id FROM machines LIMIT 5")
        for row in cursor.fetchall():
            print(f"   - {row[0]} (Unit {row[2]})")
            
        if count >= 39:
            print("\n🎉 SUCCESS: Standard machine list restored!")
        else:
            print("\n⚠️ WARNING: Machine count is lower than expected (39).")
    else:
        print("\n❌ ERROR: Machine table is empty!")
        
    conn.close()
    
except Exception as e:
    print(f"❌ Error reading DB: {e}")
