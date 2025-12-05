"""
Database Migration Script - Add New Fields
This script adds new columns to existing tables and creates the planning_tasks table.
"""
import sqlite3
from datetime import datetime

def migrate_database():
    print("Starting database migration...")
    
    # Connect to database
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    
    try:
        # 1. Add new columns to users table
        print("\n1. Updating users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            print("   ✓ Added updated_at to users")
        except sqlite3.OperationalError as e:
            print(f"   - updated_at already exists in users: {e}")
        
        # 2. Add new columns to machines table
        print("\n2. Updating machines table...")
        try:
            cursor.execute("ALTER TABLE machines ADD COLUMN current_operator TEXT")
            print("   ✓ Added current_operator to machines")
        except sqlite3.OperationalError as e:
            print(f"   - current_operator already exists: {e}")
        
        try:
            cursor.execute("ALTER TABLE machines ADD COLUMN updated_at TIMESTAMP")
            print("   ✓ Added updated_at to machines")
        except sqlite3.OperationalError as e:
            print(f"   - updated_at already exists in machines: {e}")
        
        # 3. Add new columns to tasks table
        print("\n3. Updating tasks table...")
        new_task_columns = [
            ("project", "TEXT"),
            ("part_item", "TEXT"),
            ("nos_unit", "TEXT"),
            ("assigned_by", "TEXT")
        ]
        
        for column_name, column_type in new_task_columns:
            try:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}")
                print(f"   ✓ Added {column_name} to tasks")
            except sqlite3.OperationalError as e:
                print(f"   - {column_name} already exists: {e}")
        
        # 4. Add new columns to outsource_items table
        print("\n4. Updating outsource_items table...")
        new_outsource_columns = [
            ("task_id", "TEXT"),
            ("dc_generated", "INTEGER DEFAULT 0"),  # Boolean as INTEGER
            ("transport_status", "TEXT DEFAULT 'pending'"),
            ("follow_up_time", "TIMESTAMP"),
            ("pickup_status", "TEXT DEFAULT 'pending'"),
            ("updated_at", "TIMESTAMP")
        ]
        
        for column_name, column_type in new_outsource_columns:
            try:
                cursor.execute(f"ALTER TABLE outsource_items ADD COLUMN {column_name} {column_type}")
                print(f"   ✓ Added {column_name} to outsource_items")
            except sqlite3.OperationalError as e:
                print(f"   - {column_name} already exists: {e}")
        
        # 5. Create planning_tasks table
        print("\n5. Creating planning_tasks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planning_tasks (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                project_name TEXT,
                task_sequence INTEGER,
                assigned_supervisor TEXT,
                status TEXT,
                updated_at TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        print("   ✓ Created planning_tasks table")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show updated schema
        print("\n" + "="*60)
        print("UPDATED DATABASE SCHEMA")
        print("="*60)
        
        tables = ['users', 'machines', 'tasks', 'outsource_items', 'planning_tasks']
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table.upper()}:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION - ADD NEW FIELDS")
    print("="*60)
    print("\nThis will add new columns to existing tables.")
    print("Your data will be preserved.")
    print("\nBackup location: workflow_backup_before_schema_update.db")
    
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() == 'yes':
        migrate_database()
    else:
        print("Migration cancelled.")
