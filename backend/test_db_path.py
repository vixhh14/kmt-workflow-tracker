"""
Quick test script to verify database path is correctly resolved.
Run from any directory to test the fix.
"""
import sys
import os

# Add backend to path so we can import the database module
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app.core.database import SQLALCHEMY_DATABASE_URL, DEFAULT_DB_PATH, DB_PATH, get_db_connection

print("=" * 60)
print("DATABASE PATH VERIFICATION")
print("=" * 60)
print(f"\nDEFAULT_DB_PATH: {DEFAULT_DB_PATH}")
print(f"DB_PATH export:  {DB_PATH}")
print(f"SQLALCHEMY_DATABASE_URL: {SQLALCHEMY_DATABASE_URL}")

# Check if file exists
if os.path.exists(DEFAULT_DB_PATH):
    stat = os.stat(DEFAULT_DB_PATH)
    import datetime
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    print(f"\n[OK] Database file EXISTS")
    print(f"   Size: {stat.st_size:,} bytes")
    print(f"   Last modified: {mtime}")
else:
    print(f"\n[ERROR] Database file NOT FOUND at: {DEFAULT_DB_PATH}")

# Test direct connection
print("\n" + "-" * 60)
print("Testing get_db_connection()...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"[OK] Connected successfully! Found {len(tables)} tables:")
    for row in tables:
        print(f"   - {row[0]}")
    conn.close()
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
