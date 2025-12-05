"""
Add sample test data to the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import Task, Machine, User
import uuid
from datetime import datetime, timedelta

def add_sample_data():
    db = SessionLocal()
    try:
        print("Adding sample data...")
        
        # Get users
        admin = db.query(User).filter(User.username == "admin").first()
        operator = db.query(User).filter(User.username == "operator").first()
        
        if not admin or not operator:
            print("❌ Users not found. Please run create_demo_users.py first")
            return
        
        # Add sample machines
        print("\n1. Adding machines...")
        machines = [
            Machine(
                id=str(uuid.uuid4()),
                name="CNC Machine 1",
                status="active",
                hourly_rate=150.0,
                last_maintenance="2024-11-01"
            ),
            Machine(
                id=str(uuid.uuid4()),
                name="Lathe Machine 1",
                status="active",
                hourly_rate=120.0,
                last_maintenance="2024-11-15"
            ),
            Machine(
                id=str(uuid.uuid4()),
                name="Milling Machine 1",
                status="active",
                hourly_rate=140.0,
                last_maintenance="2024-11-20"
            ),
        ]
        
        for machine in machines:
            existing = db.query(Machine).filter(Machine.name == machine.name).first()
            if not existing:
                db.add(machine)
                print(f"   ✅ Added: {machine.name}")
            else:
                print(f"   ⚠️  Already exists: {machine.name}")
        
        db.commit()
        
        # Get first machine for tasks
        first_machine = db.query(Machine).first()
        
        # Add sample tasks
        print("\n2. Adding tasks...")
        tasks = [
            Task(
                id=str(uuid.uuid4()),
                title="Manufacture Part A-001",
                description="Create 50 units of Part A-001 for Project Alpha",
                project="Project Alpha",
                part_item="A-001",
                nos_unit=50,
                status="pending",
                priority="high",
                assigned_by=admin.user_id,
                assigned_to=operator.user_id,
                machine_id=first_machine.id if first_machine else None,
                due_date=(datetime.now() + timedelta(days=7)).date(),
                created_at=datetime.now()
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Quality Check - Batch 123",
                description="Perform quality inspection on batch 123",
                project="Project Beta",
                part_item="B-002",
                nos_unit=100,
                status="pending",
                priority="medium",
                assigned_by=admin.user_id,
                assigned_to=operator.user_id,
                machine_id=first_machine.id if first_machine else None,
                due_date=(datetime.now() + timedelta(days=3)).date(),
                created_at=datetime.now()
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Machine Maintenance",
                description="Regular maintenance of CNC Machine",
                project="Maintenance",
                part_item="N/A",
                nos_unit=1,
                status="in_progress",
                priority="low",
                assigned_by=admin.user_id,
                assigned_to=operator.user_id,
                machine_id=first_machine.id if first_machine else None,
                due_date=datetime.now().date(),
                created_at=datetime.now() - timedelta(days=1),
                started_at=datetime.now() - timedelta(hours=2)
            ),
        ]
        
        for task in tasks:
            db.add(task)
            print(f"   ✅ Added: {task.title}")
        
        db.commit()
        
        print("\n" + "="*50)
        print("✅ Sample data added successfully!")
        print("="*50)
        print("\nYou should now see:")
        print(f"  - {len(machines)} machines")
        print(f"  - {len(tasks)} tasks")
        print("\nRefresh your dashboard to see the data!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()
