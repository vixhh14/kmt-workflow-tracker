import os

files = [
    r"d:/KMT/workflow_tracker2/backend/test_sheets.py",
    r"d:/KMT/workflow_tracker2/backend/migrate_sheets_to_db.py",
    r"d:/KMT/workflow_tracker2/backend/list_users.py"
]

for f in files:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")
        else:
            print(f"File not found: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")
