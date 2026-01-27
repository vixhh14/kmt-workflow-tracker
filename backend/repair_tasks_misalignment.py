
import os
import sys
import uuid

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def repair_tasks_sheet():
    print("--- REPAIRING TASKS SHEET ---")
    try:
        ws = google_sheets.get_worksheet("tasks")
        all_values = ws.get_all_values()
        if not all_values:
            print("Sheet is empty.")
            return

        headers = all_values[0]
        rows = all_values[1:]
        
        expected_headers = SHEETS_SCHEMA["tasks"]
        
        print(f"Current headers: {headers}")
        print(f"Expected headers: {expected_headers}")
        
        # 1. Identify where 'project' and 'due_date' are in the actual sheet
        try:
            proj_idx = headers.index("project")
            print(f"'project' found at index {proj_idx}")
        except ValueError:
            proj_idx = -1
            
        try:
            due_idx = headers.index("due_date")
            print(f"'due_date' found at index {due_idx}")
        except ValueError:
            due_idx = -1

        # 2. Check if they are early in the sheet (index < 20)
        # If they are at index 3 or 4, they cause misalignment.
        needs_migration = (proj_idx != -1 and proj_idx < 20) or (due_idx != -1 and due_idx < 20)
        
        new_rows = []
        repaired_count = 0
        deleted_junk_count = 0
        
        for i, row in enumerate(rows):
            # Pad row if it's shorter than headers
            while len(row) < len(headers):
                row.append("")
                
            # Convert row to dict based on ACTUAL headers
            row_dict = dict(zip(headers, row))
            
            # 3. Handle rows with missing task_id
            t_id = str(row_dict.get("task_id", "")).strip()
            title = str(row_dict.get("title", "")).strip()
            
            if not t_id:
                if not title or title.lower() == "untitled":
                    print(f"🗑️ Row {i+2} has no ID and no Title. Deleting junk.")
                    deleted_junk_count += 1
                    continue
                else:
                    t_id = f"task_{uuid.uuid4().hex[:8]}"
                    print(f"🔧 Row {i+2} ('{title}') missing ID. Generated: {t_id}")
                    row_dict["task_id"] = t_id
                    repaired_count += 1
            
            # 4. Map values to canonical schema
            canonical_row = []
            for h in expected_headers:
                val = row_dict.get(h, "")
                # If we found a shifted value (like HMT in assigned_to)
                # assigned_to is index 3 in expected_headers
                canonical_row.append(val)
                
            new_rows.append(canonical_row)

        # 5. Overwrite sheet with repaired data
        print(f"Syncing {len(new_rows)} rows back to Google Sheets...")
        
        # Clear sheet and write headers + rows
        ws.clear()
        ws.update('A1', [expected_headers] + new_rows)
        
        print(f"✅ Repair complete. {repaired_count} IDs fixed, {deleted_junk_count} junk rows removed.")
        
    except Exception as e:
        print(f"❌ Error during repair: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    repair_tasks_sheet()
