"""
Database migration: Add onboarding system tables and fields
Creates: units, machine_categories, user_machines, user_approvals tables
Updates: users and machines tables
"""

import sqlite3
import os
from datetime import datetime

def migrate_onboarding_system():
    db_path = os.path.join(os.path.dirname(__file__), 'workflow.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Create units table
        print("\n1. Creating units table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Units table created")
        
        # 2. Create machine_categories table
        print("\n2. Creating machine_categories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machine_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Machine categories table created")
        
        # 3. Create user_machines table (junction table with skill levels)
        print("\n3. Creating user_machines table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                skill_level TEXT DEFAULT 'intermediate',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (machine_id) REFERENCES machines(id),
                UNIQUE(user_id, machine_id)
            )
        """)
        print("✓ User machines table created")
        
        # 4. Create user_approvals table
        print("\n4. Creating user_approvals table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (approved_by) REFERENCES users(user_id)
            )
        """)
        print("✓ User approvals table created")
        
        # 5. Add new fields to users table
        print("\n5. Updating users table...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'date_of_birth' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN date_of_birth DATE")
            print("  ✓ Added date_of_birth column")
        
        if 'address' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
            print("  ✓ Added address column")
        
        if 'contact_number' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN contact_number TEXT")
            print("  ✓ Added contact_number column")
        
        if 'unit_id' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN unit_id INTEGER REFERENCES units(id)")
            print("  ✓ Added unit_id column")
        
        if 'approval_status' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN approval_status TEXT DEFAULT 'approved'")
            print("  ✓ Added approval_status column")
        
        # 6. Add new fields to machines table
        print("\n6. Updating machines table...")
        cursor.execute("PRAGMA table_info(machines)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'unit_id' not in columns:
            cursor.execute("ALTER TABLE machines ADD COLUMN unit_id INTEGER REFERENCES units(id)")
            print("  ✓ Added unit_id column")
        
        if 'category_id' not in columns:
            cursor.execute("ALTER TABLE machines ADD COLUMN category_id INTEGER REFERENCES machine_categories(id)")
            print("  ✓ Added category_id column")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Display final schema
        print("\n" + "="*50)
        print("FINAL DATABASE SCHEMA")
        print("="*50)
        
        for table in ['units', 'machine_categories', 'user_machines', 'user_approvals', 'users', 'machines']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table.upper()} table:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_onboarding_system()
