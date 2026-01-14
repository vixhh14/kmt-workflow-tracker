
import sys
import os
import uuid
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.models_db import User
from app.core.auth_utils import hash_password

def create_demo_users_sheets():
    """Create demo users with different roles for SheetsDB."""
    
    # Target credentials
    demo_users = [
        {
            "username": "admin",
            "password": "Admin@Demo2025!",
            "email": "admin@kmt.com",
            "role": "admin",
            "full_name": "System Admin",
            "approval_status": "approved"
        },
        {
            "username": "operator",
            "password": "Operator@Demo2025!",
            "email": "operator@kmt.com",
            "role": "operator",
            "full_name": "Operator User",
            "approval_status": "approved"
        },
        {
            "username": "supervisor",
            "password": "Supervisor@Demo2025!",
            "email": "supervisor@kmt.com",
            "role": "supervisor",
            "full_name": "Supervisor User",
            "approval_status": "approved"
        },
        {
            "username": "planning",
            "password": "Planning@Demo2025!",
            "email": "planning@kmt.com",
            "role": "planning",
            "full_name": "Planning User",
            "approval_status": "approved"
        },
        {
            "username": "file_master",
            "password": "File@Demo2025!",
            "email": "file_master@kmt.com",
            "role": "file_master",
            "full_name": "File Master",
            "approval_status": "approved"
        },
        {
            "username": "fab_master",
            "password": "Fab@Demo2025!",
            "email": "fab_master@kmt.com",
            "role": "fab_master",
            "full_name": "Fabrication Master",
            "approval_status": "approved"
        }
    ]
    
    # Get DB (SheetsDB)
    # Since get_db is a generator for FastAPI, we can't just call it.
    # We use SheetsDB directly.
    from app.core.sheets_db import SheetsDB
    db = SheetsDB()
    
    print("🔐 Seeding demo users to Google Sheets...")
    
    # Fetch all current users (to check if they exist)
    all_users = db.query(User).all()
    
    for u_data in demo_users:
        existing = next((u for u in all_users if str(u.username).lower() == u_data["username"].lower()), None)
        
        if existing:
            print(f"Update existing user: {u_data['username']}")
            existing.password_hash = hash_password(u_data["password"])
            existing.role = u_data["role"]
            existing.approval_status = u_data["approval_status"]
            existing.is_deleted = False # Ensure not deleted
        else:
            print(f"Creating new user: {u_data['username']}")
            new_user = User(
                user_id=str(uuid.uuid4()),
                username=u_data["username"],
                password_hash=hash_password(u_data["password"]),
                email=u_data["email"],
                role=u_data["role"],
                full_name=u_data["full_name"],
                approval_status=u_data["approval_status"],
                active="TRUE",
                created_at=datetime.now().isoformat()
            )
            db.add(new_user)
            
    db.commit()
    print("✅ Demo users have been seeded successfully.")

if __name__ == "__main__":
    create_demo_users_sheets()
