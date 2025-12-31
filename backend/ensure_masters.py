import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.security import get_password_hash

import uuid

def ensure_masters():
    db = SessionLocal()
    masters = [("FILE_MASTER", "file_master"), ("FAB_MASTER", "fab_master")]
    
    for username, role in masters:
        # Check by username (ensure case insensitive check to be safe)
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Creating user {username}...")
            # Create user with default password 'password123'
            new_user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                full_name=f"{username.replace('_', ' ').title()}",
                role=role,
                password_hash=get_password_hash("password123"),
                approval_status='approved'
            )
            db.add(new_user)
            db.commit()
            print(f"Created {username}")
        else:
            print(f"User {username} exists with role {user.role}.")
            if user.role != role:
                print(f"Updating role for {username} to {role}")
                user.role = role
                db.commit()

if __name__ == "__main__":
    try:
        ensure_masters()
    except Exception as e:
        print(f"Error: {e}")
