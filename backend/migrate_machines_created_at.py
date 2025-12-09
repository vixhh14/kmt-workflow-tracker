import sqlite3
import os
from datetime import datetime

def migrate_machines_table():
    db_path = 'workflow.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(machines)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'created_at' not in columns:
            print("Adding created_at column to machines table...")
            cursor.execute("ALTER TABLE machines ADD COLUMN created_at TIMESTAMP")
            
            # Update existing records with current time
            current_time = datetime.utcnow()
            cursor.execute("UPDATE machines SET created_at = ?", (current_time,))
            
            conn.commit()
            print("✅ created_at column added successfully!")
        else:
            print("✅ created_at column already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_machines_table()
