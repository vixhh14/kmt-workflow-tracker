"""
Initialize the SQLite database and seed demo users.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.models.models_db import User, Machine, Task, OutsourceItem, TaskTimeLog, PlanningTask
import hashlib
import uuid

def init_db():
    print("Dropping existing tables (if any)...")
    Base.metadata.drop_all(bind=engine)
    print("Creating database tables with updated schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if users exist
    if db.query(User).first():
        print("Users already exist. Skipping seed.")
        db.close()
        return

    print("Seeding demo users...")
    
    # Removed vendor user - vendor functionality accessible by admin and planning only
    demo_users = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@workflow.com",
            "role": "admin",
            "full_name": "Admin User"
        },
        {
            "username": "operator",
            "password": "operator123",
            "email": "operator@workflow.com",
            "role": "operator",
            "full_name": "Operator User"
        },
        {
            "username": "supervisor",
            "password": "supervisor123",
            "email": "supervisor@workflow.com",
            "role": "supervisor",
            "full_name": "Supervisor User"
        },
        {
            "username": "planning",
            "password": "planning123",
            "email": "planning@workflow.com",
            "role": "planning",
            "full_name": "Planning User"
        }
    ]
    
    for user_data in demo_users:
        # Hash password
        password_hash = hashlib.sha256(user_data['password'].encode()).hexdigest()
        
        user = User(
            user_id=str(uuid.uuid4()),
            username=user_data['username'],
            email=user_data['email'],
            password_hash=password_hash,
            role=user_data['role'],
            full_name=user_data['full_name'],
            approval_status='approved'  # Demo users are pre-approved
        )
        db.add(user)
        print(f"✅ Added user: {user.username}")
        
    db.commit()
    db.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
