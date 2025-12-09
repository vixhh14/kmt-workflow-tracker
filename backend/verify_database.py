"""
Database verification script to check data integrity and timestamps.
Run this script to verify that data entered through the application
is correctly stored in the database.

Usage: python verify_database.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.models_db import User, Machine, Task, Unit, MachineCategory, TaskTimeLog, Attendance
from datetime import datetime

def verify_database():
    """Verify database contents and timestamps."""
    db = next(get_db())
    
    print("=" * 60)
    print("DATABASE VERIFICATION REPORT")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Local)")
    print(f"UTC Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check Users
    print("\n📋 USERS TABLE")
    print("-" * 40)
    users = db.query(User).all()
    print(f"Total Users: {len(users)}")
    if users:
        print("\nRecent Users (last 5):")
        for user in users[-5:]:
            print(f"  • {user.username} ({user.role})")
            print(f"    Created: {user.created_at}")
            print(f"    Updated: {user.updated_at}")
            print(f"    Status: {user.approval_status}")
    
    # Check Units
    print("\n📋 UNITS TABLE")
    print("-" * 40)
    units = db.query(Unit).all()
    print(f"Total Units: {len(units)}")
    for unit in units:
        print(f"  • ID {unit.id}: {unit.name} | Created: {unit.created_at}")
    
    # Check Categories
    print("\n📋 MACHINE CATEGORIES TABLE")
    print("-" * 40)
    categories = db.query(MachineCategory).all()
    print(f"Total Categories: {len(categories)}")
    for cat in categories[:10]:  # Show first 10
        print(f"  • ID {cat.id}: {cat.name}")
    if len(categories) > 10:
        print(f"  ... and {len(categories) - 10} more")
    
    # Check Machines
    print("\n📋 MACHINES TABLE")
    print("-" * 40)
    machines = db.query(Machine).all()
    print(f"Total Machines: {len(machines)}")
    
    # Group by unit
    unit_counts = {}
    for m in machines:
        unit_id = m.unit_id or "No Unit"
        unit_counts[unit_id] = unit_counts.get(unit_id, 0) + 1
    
    print("\nMachines by Unit:")
    for unit_id, count in unit_counts.items():
        unit_name = next((u.name for u in units if u.id == unit_id), str(unit_id))
        print(f"  • {unit_name}: {count} machines")
    
    print("\nLast 5 Machines Added:")
    for m in machines[-5:]:
        print(f"  • {m.name}")
        print(f"    Status: {m.status} | Unit ID: {m.unit_id} | Category ID: {m.category_id}")
        print(f"    Updated: {m.updated_at}")
    
    # Check Tasks
    print("\n📋 TASKS TABLE")
    print("-" * 40)
    tasks = db.query(Task).all()
    print(f"Total Tasks: {len(tasks)}")
    
    # Status breakdown
    status_counts = {}
    for t in tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
    
    print("\nTasks by Status:")
    for status, count in status_counts.items():
        print(f"  • {status}: {count}")
    
    print("\nLast 5 Tasks:")
    for t in tasks[-5:]:
        print(f"  • {t.title} ({t.status})")
        print(f"    Created: {t.created_at}")
        if t.started_at:
            print(f"    Started: {t.started_at}")
        if t.completed_at:
            print(f"    Completed: {t.completed_at}")
    
    # Check Task Time Logs
    print("\n📋 TASK TIME LOGS TABLE")
    print("-" * 40)
    time_logs = db.query(TaskTimeLog).all()
    print(f"Total Time Logs: {len(time_logs)}")
    
    if time_logs:
        print("\nLast 10 Time Logs:")
        for log in time_logs[-10:]:
            print(f"  • Task {log.task_id[:8]}... | {log.action} | {log.timestamp}")
            if log.reason:
                print(f"    Reason: {log.reason}")
    
    # Check Attendance
    print("\n📋 ATTENDANCE TABLE")
    print("-" * 40)
    attendance = db.query(Attendance).all()
    print(f"Total Attendance Records: {len(attendance)}")
    
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    today_attendance = [a for a in attendance if a.date == today_str]
    print(f"Today's Attendance: {len(today_attendance)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Users: {len(users)}")
    print(f"Units: {len(units)}")
    print(f"Categories: {len(categories)}")
    print(f"Machines: {len(machines)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Time Logs: {len(time_logs)}")
    print(f"Attendance: {len(attendance)}")
    print("=" * 60)
    print("\n✅ Database verification complete!")
    print("\nNOTE: All timestamps are stored in UTC.")
    print("Your local timezone offset: IST (UTC+5:30)")
    
    db.close()


if __name__ == "__main__":
    verify_database()
