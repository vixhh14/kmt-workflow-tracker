
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.attendance_service import get_attendance_summary
from app.core.database import db

if __name__ == "__main__":
    print("Testing get_attendance_summary...")
    summary = get_attendance_summary(db)
    print("\nSUMMARY RESULT:")
    print(f"Success: {summary.get('success')}")
    print(f"Present Count: {summary.get('present_count')}")
    print(f"Absent Count: {summary.get('absent_count')}")
    print(f"Present Users: {len(summary.get('present_users', []))}")
    print(f"Total Tracked: {summary.get('total_tracked')}")
    
    if summary.get('present_users'):
        print(f"First Present User: {summary['present_users'][0]['username']}")
    
    if summary.get('absent_users'):
        print(f"First Absent User: {summary['absent_users'][0]['username']}")
