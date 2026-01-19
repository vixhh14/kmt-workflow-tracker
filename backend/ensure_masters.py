import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import get_db
from app.models.models_db import User
from app.core.auth_utils import hash_password

import uuid

def ensure_masters():
    # Since get_db is a generator, we need to handle it
    db_gen = get_db()
    db = next(db_gen)
    
    # 1. Standard Masters
    masters = [
        ("FILE_MASTER", "file_master"), 
        ("FAB_MASTER", "fab_master"),
        ("admin", "admin") # Add standard admin
    ]
    
    for username, role in masters:
        # Check by username
        all_users = db.query(User).all()
        user = next((u for u in all_users if str(getattr(u, 'username', '')).strip().lower() == username.lower()), None)
        
        if not user:
            print(f"Creating user {username}...")
            # Create user with default password 'password123'
            new_user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                full_name=f"{username.replace('_', ' ').title()}",
                role=role,
                password_hash=hash_password("password123"),
                approval_status='approved',
                is_active=True,
                is_deleted=False
            )
            db.add(new_user)
            db.commit()
            print(f"Created {username}")
        else:
            print(f"User {username} exists with role {getattr(user, 'role', '')}.")
            # Ensure is_active is True for existing ones
            if not getattr(user, 'is_active', False):
                print(f"Activating {username}")
                setattr(user, 'is_active', True)
            
            if str(getattr(user, 'role', '')).lower().strip() != role.lower():
                print(f"Updating role for {username} to {role}")
                setattr(user, 'role', role)
            
            db.commit()

if __name__ == "__main__":
    try:
        ensure_masters()
        print("✅ Master users verification complete.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
