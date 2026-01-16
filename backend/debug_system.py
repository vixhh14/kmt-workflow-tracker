
import sys
import os
sys.path.append(os.getcwd())

from app.core.sheets_db import get_sheets_db
from app.models.models_db import Machine, User, Task, Unit, MachineCategory

def debug_system():
    print("🔍 DEBUGGING SYSTEM STATE...")
    
    db = get_sheets_db()
    
    # 1. Check Units and Categories first (dependencies)
    print("\n--- UNITS ---")
    try:
        units = db.query(Unit).all()
        print(f"Found {len(units)} units")
        if units: print(f"Sample: {units[0].dict()}")
    except Exception as e:
        print(f"❌ Failed to fetch Units: {e}")

    print("\n--- CATEGORIES ---")
    try:
        cats = db.query(MachineCategory).all()
        print(f"Found {len(cats)} categories")
        if cats: print(f"Sample: {cats[0].dict()}")
    except Exception as e:
        print(f"❌ Failed to fetch Categories: {e}")

    # 2. Check Machines
    print("\n--- MACHINES ---")
    try:
        machines = db.query(Machine).all()
        print(f"Found {len(machines)} machines")
        if len(machines) == 0:
            print("⚠️ WARNING: Machine list is empty!")
            from app.services.google_sheets import google_sheets
            print("Attempting raw read from Google Sheets 'Machines'...")
            try:
                raw_data = google_sheets.read_all_bulk("Machines")
                print(f"Raw read returned {len(raw_data)} rows.")
            except Exception as re:
                print(f"❌ Raw read failed: {re}")
        else:
             print(f"Sample: {machines[0].dict()}")
    except Exception as e:
        print(f"❌ Failed to fetch Machines: {e}")

    # 3. Check Users
    print("\n--- USERS ---")
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users")
        if len(users) == 0:
             print("⚠️ WARNING: User list is empty!")
    except Exception as e:
        print(f"❌ Failed to fetch Users: {e}")
        
    print("\n--- DIAGNOSTICS COMPLETE ---")

if __name__ == "__main__":
    debug_system()
