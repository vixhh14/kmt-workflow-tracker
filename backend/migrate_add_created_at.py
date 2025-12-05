"""
Migration script to add created_at column to users table
"""
import sqlite3
from datetime import datetime

def migrate_add_created_at():
    conn = sqlite3.connect('backend/workflow.db')
    cursor = conn.cursor()
    
    try:
        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'created_at' not in columns:
            print("Adding created_at column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
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
    migrate_add_created_at()
