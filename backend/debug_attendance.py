
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import get_db
from app.services.attendance_service import get_attendance_summary

def debug_attendance():
    db = get_db()
    summary = get_attendance_summary(db)
    print("\n--- ATTENDANCE SUMMARY RESULT ---")
    print(f"Success: {summary.get('success')}")
    print(f"Present Count: {summary.get('present_count')}")
    print(f"Absent Count: {summary.get('absent_count')}")
    print(f"Total Tracked: {summary.get('total_tracked')}")
    
    print("\nPresent records data:")
    for r in summary.get('present_users', []):
        print(f"  - {r.get('username')} (ID: {r.get('user_id')}, Role: {r.get('role')})")

    print("\nAbsent records data:")
    for r in summary.get('absent_users', []):
        print(f"  - {r.get('username')} (ID: {r.get('user_id')}, Role: {r.get('role')})")

if __name__ == "__main__":
    debug_attendance()
