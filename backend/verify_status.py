import os
import sys

# Verify .env content
print("--- .env CONTENT ---")
try:
    with open(".env", "r") as f:
        print(f.read())
except Exception as e:
    print(f"Error reading .env: {e}")

print("\n--- APP STARTUP CHECK ---")
sys.path.append(os.getcwd())
from app.core.sheets_db import get_sheets_db
from app.models.models_db import Machine

try:
    db = get_sheets_db()
    machines = db.query(Machine).all()
    print(f"✅ DB Connection Successful")
    print(f"✅ Machine Count: {len(machines)}")
    if len(machines) > 0:
        print(f"   First Machine: {machines[0].machine_name} (Unit: {machines[0].unit_id})")
    else:
        print("⚠️ No machines found in DB (Cache/Sheet empty?)")
except Exception as e:
    print(f"❌ DB Check Failed: {e}")
