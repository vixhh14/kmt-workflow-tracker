import sqlite3
import os

def migrate_add_machine_types():
    """Add machine_types column to users table"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'workflow.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'machine_types' in columns:
            print("✓ machine_types column already exists in users table")
        else:
            # Add machine_types column
            print("Adding machine_types column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN machine_types TEXT
            """)
            conn.commit()
            print("✓ Successfully added machine_types column")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nCurrent users table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_machine_types()
