import sqlite3
import sys
sys.path.insert(0, 'backend')

from app.core.auth_utils import verify_password

# Connect to database
conn = sqlite3.connect('backend/workflow.db')
cursor = conn.cursor()

# Get admin user
cursor.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
user = cursor.fetchone()

if user:
    username, password_hash = user
    print(f"Username: {username}")
    print(f"Password hash: {password_hash}")
    print(f"Hash starts with $2b$: {password_hash.startswith('$2b$')}")
    
    # Test password verification
    test_password = "admin123"
    is_valid = verify_password(test_password, password_hash)
    print(f"\nPassword '{test_password}' is valid: {is_valid}")
else:
    print("Admin user not found!")

conn.close()
