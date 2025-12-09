"""
Script to recover lost data by scanning the entire project directory for SQLite files.
It checks each found DB for 'machines', 'projects', and 'tasks' tables.
"""
import os
import sqlite3
import sys
from datetime import datetime

# Define project root (up one level from backend)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Current main DB
MAIN_DB_PATH = os.path.join(BACKEND_DIR, "workflow.db")

def find_db_files(root_dir):
    """Recursively find all .db and .sqlite files."""
    db_files = []
    print(f"🔍 Scanning {root_dir} for database files...")
    
    for root, dirs, files in os.walk(root_dir):
        # Skip node_modules and .git to speed up search
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite'):
                full_path = os.path.join(root, file)
                db_files.append(full_path)
    
    return db_files

def inspect_db(db_path):
    """Check a DB file for relevant data."""
    print(f"\n📂 Inspecting: {db_path}")
    
    if not os.path.exists(db_path):
        print("   ❌ File not found (might be a broken link)")
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {
            "path": db_path,
            "size": os.path.getsize(db_path),
            "modified": datetime.fromtimestamp(os.path.getmtime(db_path)),
            "tables": [],
            "counts": {}
        }
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        stats["tables"] = tables
        
        # Check specific tables
        target_tables = ['machines', 'projects', 'tasks', 'users']
        for table in target_tables:
            if table in tables:
                try:
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats["counts"][table] = count
                    print(f"   ✅ {table}: {count} rows")
                except:
                    print(f"   ⚠️ Error counting {table}")
            else:
                print(f"   ❌ {table}: Not found")
                
        conn.close()
        return stats
        
    except Exception as e:
        print(f"   ❌ Error opening DB: {e}")
        return None

def main():
    print("="*60)
    print("DATA RECOVERY SCANNER")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Main DB:      {MAIN_DB_PATH}")
    print("-" * 60)
    
    # 1. Find files
    db_files = find_db_files(PROJECT_ROOT)
    print(f"\nFound {len(db_files)} potential database files.")
    
    # 2. Inspect each
    valid_dbs = []
    for db_path in db_files:
        stats = inspect_db(db_path)
        if stats and stats["counts"]:
            valid_dbs.append(stats)
            
    # 3. Summary
    print("\n" + "="*60)
    print("RECOVERY SUMMARY")
    print("="*60)
    
    if not valid_dbs:
        print("❌ No databases with valid data found.")
    else:
        print(f"Found {len(valid_dbs)} databases with data:\n")
        for db in valid_dbs:
            print(f"📄 {db['path']}")
            print(f"   Size: {db['size']:,} bytes")
            print(f"   Modified: {db['modified']}")
            print(f"   Data: {db['counts']}")
            
            if db['path'] == MAIN_DB_PATH:
                print("   (This is the CURRENT main database)")
            else:
                print("   ⚠️ POTENTIAL RECOVERY CANDIDATE")
                
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
