import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(os.path.join("backend", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)
    if not cursor.fetchone()[0]:
        print("❌ Users table does not exist!")
    else:
        cursor.execute("SELECT username, role, approval_status FROM users")
        users = cursor.fetchall()
        print(f"✅ Found {len(users)} users in database:")
        print("-" * 60)
        for u in users:
            print(f"Username: {u[0]:15} | Role: {u[1]:12} | Status: {u[2]}")
        print("-" * 60)
        
        if len(users) == 0:
            print("\n⚠️  No users found! Run: python backend/create_demo_users.py")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
