import sqlite3

print("="*60)
print("MIGRATING WORKFLOW.DB - ADDING NEW COLUMNS")
print("="*60)

conn = sqlite3.connect('workflow.db')
cursor = conn.cursor()

migrations = [
    # Users table
    ("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP", "users.updated_at"),
    ("ALTER TABLE users ADD COLUMN security_question TEXT", "users.security_question"),
    ("ALTER TABLE users ADD COLUMN security_answer TEXT", "users.security_answer"),

    # Machines table
    ("ALTER TABLE machines ADD COLUMN current_operator TEXT", "machines.current_operator"),
    ("ALTER TABLE machines ADD COLUMN updated_at TIMESTAMP", "machines.updated_at"),
    
    # Tasks table
    ("ALTER TABLE tasks ADD COLUMN project TEXT", "tasks.project"),
    ("ALTER TABLE tasks ADD COLUMN part_item TEXT", "tasks.part_item"),
    ("ALTER TABLE tasks ADD COLUMN nos_unit TEXT", "tasks.nos_unit"),
    ("ALTER TABLE tasks ADD COLUMN assigned_by TEXT", "tasks.assigned_by"),
    
    # Outsource items table
    ("ALTER TABLE outsource_items ADD COLUMN task_id TEXT", "outsource_items.task_id"),
    ("ALTER TABLE outsource_items ADD COLUMN dc_generated INTEGER DEFAULT 0", "outsource_items.dc_generated"),
    ("ALTER TABLE outsource_items ADD COLUMN transport_status TEXT DEFAULT 'pending'", "outsource_items.transport_status"),
    ("ALTER TABLE outsource_items ADD COLUMN follow_up_time TIMESTAMP", "outsource_items.follow_up_time"),
    ("ALTER TABLE outsource_items ADD COLUMN pickup_status TEXT DEFAULT 'pending'", "outsource_items.pickup_status"),
    ("ALTER TABLE outsource_items ADD COLUMN updated_at TIMESTAMP", "outsource_items.updated_at"),
]

print("\nAdding columns to existing tables...")
for sql, column_name in migrations:
    try:
        cursor.execute(sql)
        print(f"  ✅ Added {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  ✓ {column_name} already exists")
        else:
            print(f"  ❌ Error adding {column_name}: {e}")

# Create planning_tasks table
print("\nCreating planning_tasks table...")
try:
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
    print("  ✅ Created planning_tasks table")
except Exception as e:
    print(f"  ❌ Error: {e}")

conn.commit()
conn.close()

print("\n" + "="*60)
print("MIGRATION COMPLETE!")
print("="*60)
print("\nRun 'python verify_schema.py' to verify all columns were added.")
