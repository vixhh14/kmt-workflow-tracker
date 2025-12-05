import sqlite3

# Connect to database
conn = sqlite3.connect('workflow.db')
cursor = conn.cursor()

try:
    # Check if columns exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Current columns: {columns}")
    
    # Add security_question if it doesn't exist
    if 'security_question' not in columns:
        print("Adding security_question column...")
        cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        print("Added security_question column")
    else:
        print("security_question column already exists")
    
    # Add security_answer if it doesn't exist
    if 'security_answer' not in columns:
        print("Adding security_answer column...")
        cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")
        print("Added security_answer column")
    else:
        print("security_answer column already exists")
    
    conn.commit()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
