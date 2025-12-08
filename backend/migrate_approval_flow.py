import sqlite3

def migrate():
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    
    print("Checking for missing columns in 'users' table...")
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Columns to add
    new_columns = {
        'approval_status': 'TEXT DEFAULT "pending"',
        'unit_id': 'TEXT',
        'machine_types': 'TEXT',
        'contact_number': 'TEXT',
        'address': 'TEXT',
        'date_of_birth': 'TEXT'
    }
    
    for col, definition in new_columns.items():
        if col not in columns:
            print(f"Adding column: {col}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                print(f"  ✅ Added {col}")
            except Exception as e:
                print(f"  ❌ Failed to add {col}: {e}")
        else:
            print(f"  ✅ {col} already exists")

    print("\nChecking for 'user_approvals' table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_approvals'")
    if not cursor.fetchone():
        print("Creating 'user_approvals' table...")
        cursor.execute("""
            CREATE TABLE user_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        print("  ✅ Created 'user_approvals' table")
    else:
        print("  ✅ 'user_approvals' table already exists")

    conn.commit()
    conn.close()
    print("\nMigration complete.")

if __name__ == "__main__":
    migrate()
