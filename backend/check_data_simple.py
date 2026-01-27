
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.repositories.sheets_repository import sheets_repo

def check_sheets():
    print("Fetching users...")
    users = sheets_repo.get_all("users", include_deleted=True)
    print(f"Total Users: {len(users)}")
    for u in users:
        print(f"  - {u.get('username')} | ID: {u.get('user_id')} | Role: {u.get('role')} | is_deleted: {u.get('is_deleted')} | active: {u.get('active')}")

    print("\nFetching attendance...")
    att = sheets_repo.get_all("attendance")
    print(f"Total Attendance Records: {len(att)}")
    for a in att:
        print(f"  - UserID: {a.get('user_id')} | Date: {a.get('date')} | Status: {a.get('status')}")

if __name__ == "__main__":
    check_sheets()
