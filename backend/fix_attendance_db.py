import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment.")
    exit(1)

# Fix Render-style postgres:// URL → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def fix_attendance_table():
    print(f"🔌 Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    sql_commands = [
        # 1. Drop the default value (detach old sequence if any)
        "ALTER TABLE attendance ALTER COLUMN id DROP DEFAULT;",
        
        # 2. Drop the primary key constraint (if exists)
        "ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_pkey;",
        
        # 3. Create a new sequence (if not exists)
        "CREATE SEQUENCE IF NOT EXISTS attendance_id_seq;",
        
        # 4. Alter the column to BigInt (safe for future growth)
        "ALTER TABLE attendance ALTER COLUMN id TYPE BIGINT;",
        
        # 5. Set the default value to the new sequence
        "ALTER TABLE attendance ALTER COLUMN id SET DEFAULT nextval('attendance_id_seq');",
        
        # 6. Sync the sequence to the max id
        "SELECT setval('attendance_id_seq', (SELECT COALESCE(MAX(id), 0) FROM attendance) + 1, false);",
        
        # 7. Re-add primary key
        "ALTER TABLE attendance ADD PRIMARY KEY (id);"
    ]
    
    with engine.connect() as connection:
        print("🛠️ Applying fixes to 'attendance' table...")
        transaction = connection.begin()
        try:
            for cmd in sql_commands:
                print(f"   Running: {cmd}")
                connection.execute(text(cmd))
            
            transaction.commit()
            print("✅ Attendance table fixed successfully!")
            
            # Verification
            result = connection.execute(text("SELECT column_default FROM information_schema.columns WHERE table_name = 'attendance' AND column_name = 'id';"))
            default_val = result.scalar()
            print(f"   Current default for id: {default_val}")
            
            result = connection.execute(text("SELECT last_value FROM attendance_id_seq;"))
            seq_val = result.scalar()
            print(f"   Current sequence value: {seq_val}")
            
        except Exception as e:
            transaction.rollback()
            print(f"❌ Error applying fixes: {e}")
            raise

if __name__ == "__main__":
    fix_attendance_table()
