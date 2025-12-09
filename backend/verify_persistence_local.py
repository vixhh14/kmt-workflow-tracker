import sqlite3
import os
from app.core.database import DEFAULT_DB_PATH
from app.core.init_data import init_db_data

def verify_local_persistence():
    print(f"Verifying local persistence at: {DEFAULT_DB_PATH}")
    
    # 1. Run initialization (simulating startup)
    try:
        init_db_data()
        print("✅ Initialization ran successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    # 2. Check if data exists in SQLite
    if not os.path.exists(DEFAULT_DB_PATH):
        print("❌ Database file not found!")
        return
        
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check Machines
        cursor.execute("SELECT COUNT(*) FROM machines")
        machine_count = cursor.fetchone()[0]
        print(f"Machines count: {machine_count}")
        
        if machine_count > 0:
            print("✅ Machines persisted")
        else:
            print("❌ No machines found")
            
        # Check Users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users count: {user_count}")
        
        if user_count > 0:
            print("✅ Users persisted")
        else:
            print("⚠️ No users found (might need to run create_demo_users)")
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_local_persistence()
