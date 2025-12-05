import sqlite3

def migrate_db():
    try:
        conn = sqlite3.connect('workflow.db')
        cursor = conn.cursor()
        
        print("Checking for new columns...")
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'security_question' not in columns:
            print("Adding security_question column...")
            cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        else:
            print("security_question column already exists.")
            
        if 'security_answer' not in columns:
            print("Adding security_answer column...")
            cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")
        else:
            print("security_answer column already exists.")
            
        conn.commit()
        conn.close()
        print("✅ Database migration complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    migrate_db()
