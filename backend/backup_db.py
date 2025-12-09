"""
Script to create a timestamped backup of the SQLite database.
Can be run manually or scheduled.
"""
import os
import shutil
import datetime
import sys

# Define paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_DIR, "workflow.db")
BACKUP_DIR = os.path.join(BACKEND_DIR, "backups")

def create_backup():
    print("="*60)
    print("DATABASE BACKUP SYSTEM")
    print("="*60)
    
    # 1. Check if DB exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return False
        
    # 2. Create backup directory
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            print(f"📁 Created backup directory: {BACKUP_DIR}")
        except Exception as e:
            print(f"❌ Failed to create backup directory: {e}")
            return False
            
    # 3. Generate backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"workflow_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # 4. Copy file
    try:
        shutil.copy2(DB_PATH, backup_path)
        size = os.path.getsize(backup_path)
        print(f"✅ Backup created successfully!")
        print(f"   Source: {DB_PATH}")
        print(f"   Dest:   {backup_path}")
        print(f"   Size:   {size:,} bytes")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

if __name__ == "__main__":
    success = create_backup()
    sys.exit(0 if success else 1)
