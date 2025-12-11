import os
import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Configuration
DATABASE_URL = "postgresql://kmt_workflow_db_user:drLPu2Dc5z847of8xnaDpz1HG8fbfU43@dpg-d4s11o7diees73dhifvg-a.oregon-postgres.render.com:5432/kmt_workflow_db"
USERS_TO_FIX = {
    "Admin": "Admin@Demo2025!",
    "Operator": "Operator@Demo2025!",
    "Supervisor": "Supervisor@Demo2025!",
    "Planning": "Planning@Demo2025!"
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def fix_users():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("Connected successfully.")
            
            # Verify users table exists
            result = connection.execute(text("SELECT to_regclass('public.users');"))
            if not result.scalar():
                print("Error: 'users' table does not exist!")
                return

            for username, password in USERS_TO_FIX.items():
                print(f"Checking user: {username}")
                # Check if user exists
                result = connection.execute(text("SELECT id, username, password_hash FROM users WHERE username = :username"), {"username": username})
                user = result.fetchone()
                
                new_hash = get_password_hash(password)
                
                if user:
                    print(f"User {username} found (ID: {user[0]}). Updating password hash...")
                    connection.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), {"hash": new_hash, "id": user[0]})
                    print(f"User {username} updated.")
                else:
                    print(f"User {username} NOT found. Creating...")
                    role = username.lower() if username.lower() in ["admin", "operator", "supervisor", "planning"] else "operator"
                    if username == "Admin": role = "admin"
                    
                    try:
                        connection.execute(text("INSERT INTO users (username, password_hash, role, full_name) VALUES (:username, :hash, :role, :full_name)"), 
                                           {"username": username, "hash": new_hash, "role": role, "full_name": f"{username} User"})
                        print(f"User {username} created.")
                    except Exception as e:
                        print(f"Failed to create user {username}: {e}")

            connection.commit()
            print("All users processed.")
            
            # List all users
            print("\nCurrent Users in DB:")
            result = connection.execute(text("SELECT id, username, role FROM users"))
            for row in result:
                print(f"ID: {row[0]}, Username: {row[1]}, Role: {row[2]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_users()
