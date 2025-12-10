import os
from dotenv import load_dotenv

# Explicitly load .env.production to get the correct DATABASE_URL
load_dotenv('.env.production')

from app.core.hashing import pwd_context
from app.core.database import engine
from sqlalchemy import text

# Generate bcrypt hashes for the required passwords
users = {
    'admin': 'Admin@Demo2025!',
    'operator': 'Operator@Demo2025!',
    'supervisor': 'Supervisor@Demo2025!',
    'planning': 'Planning@Demo2025!'
}

print(f"Using DATABASE_URL: {os.getenv('DATABASE_URL')}")

try:
    with engine.connect() as conn:
        for username, password in users.items():
            new_hash = pwd_context.hash(password)
            stmt = text("UPDATE users SET password_hash = :hash WHERE username = :uname")
            conn.execute(stmt, {"hash": new_hash, "uname": username})
            print(f"Updated {username} with hash {new_hash}")
        conn.commit()
    print("✅ Password update complete.")
except Exception as e:
    print(f"❌ Error updating passwords: {e}")
