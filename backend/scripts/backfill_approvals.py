
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sheets_db import SheetsDB

def backfill_approvals():
    print("🔄 Connecting to SheetsDB...")
    db = SheetsDB()
    
    users = db.query('users').all()
    print(f"found {len(users)} users.")
    
    updates = 0
    for u in users:
        current_status = getattr(u, 'approval_status', '')
        u_id = getattr(u, 'user_id', getattr(u, 'id', ''))
        
        # If status is missing, empty, or None for an ACTIVE user, set it to approved
        if not current_status or str(current_status).strip() == '':
            print(f"🛠 Fixing user {getattr(u, 'username', 'Unknown')} ({u_id})... setting approval_status='approved'")
            
            # We use the repository/db update method
            # Since SheetsDB objects are read-only views, we write back using the repo approach or direct update
            # Here we simulate the direct update payload
            
            # Using the low-level update
            db.update('users', u_id, {'approval_status': 'approved'})
            updates += 1

    print(f"✅ Backfill complete. Updated {updates} users.")

if __name__ == "__main__":
    backfill_approvals()
