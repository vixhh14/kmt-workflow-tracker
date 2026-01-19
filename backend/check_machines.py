import sys
from app.core.sheets_db import get_sheets_db
from app.models.models_db import Machine

try:
    db = get_sheets_db()
    machines = db.query(Machine).all()
    print(f"MACHINES_COUNT={len(machines)}")
except Exception as e:
    print(f"ERROR={e}")
