import sqlite3

# Connect to database
conn = sqlite3.connect('workflow.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

print("Current users table columns:")
for col in columns:
    print(f"  - {col}")

# Add machine_types if it doesn't exist
if 'machine_types' not in columns:
    print("\nAdding machine_types column...")
    cursor.execute("ALTER TABLE users ADD COLUMN machine_types TEXT")
    conn.commit()
    print("✓ machine_types column added successfully!")
else:
    print("\n✓ machine_types column already exists!")

# Verify
cursor.execute("PRAGMA table_info(users)")
print("\nUpdated schema:")
for col in cursor.fetchall():
    print(f"  - {col[1]} ({col[2]})")

conn.close()
print("\n✅ Done!")
