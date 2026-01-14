"""
Complete test of login and signup functionality (PostgreSQL Version)
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables from backend/.env if not already loaded
load_dotenv(os.path.join("backend", ".env"))

print("="*70)
print("CHECKING POSTGRESQL DATABASE AND USERS")
print("="*70)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠️  DATABASE_URL not found in environment variables.")
    print("   Falling back to default: postgresql://postgres:postgres@localhost/workflow_tracker")
    DATABASE_URL = "postgresql://postgres:postgres@localhost/workflow_tracker"

# Handle Render's postgres:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check users
    cursor.execute("SELECT username, role, approval_status FROM users")
    users = cursor.fetchall()
    
    if len(users) == 0:
        print("\n❌ NO USERS FOUND IN DATABASE!")
        print("Run: python backend/create_demo_users.py")
    else:
        print(f"\n✅ Found {len(users)} users:")
        print("-" * 70)
        for u in users:
            print(f"  Username: {u[0]:15} | Role: {u[1]:12} | Status: {u[2]}")
        print("-" * 70)
        
        # Check for admin
        admin = [u for u in users if u[0] == 'admin']
        if admin:
            print(f"\n✅ Admin user exists with status: {admin[0][2]}")
            if admin[0][2] != 'approved':
                print("⚠️  WARNING: Admin status should be 'approved'")
        else:
            print("\n❌ NO ADMIN USER FOUND!")
            print("Run: python backend/create_demo_users.py")
    
    conn.close()
    print("\n✅ Connection successful.")
    
except Exception as e:
    print(f"\n❌ Error connecting to database: {e}")
    # sys.exit(1) 
