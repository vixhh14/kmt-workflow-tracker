
import os
import sys
import uuid

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def force_repair_tasks():
    print("--- FORCE REPAIRING TASKS SHEET ---")
    try:
        ws = google_sheets.get_worksheet("tasks")
        all_values = ws.get_all_values()
        if not all_values:
            print("Sheet is empty.")
            return

        current_headers = [str(h).strip().lower() for h in all_values[0]]
        rows = all_values[1:]
        
        target_headers = SHEETS_SCHEMA["tasks"]
        
        # Detect shifts
        # If 'project' is at index 3 instead of 27
        proj_idx = -1
        if "project" in current_headers:
            proj_idx = current_headers.index("project")
            print(f"Found 'project' at index {proj_idx}")

        new_rows = []
        for i, row in enumerate(rows):
            # Map current row to a dict
            row_dict = {}
            for j, val in enumerate(row):
                if j < len(current_headers):
                    row_dict[current_headers[j]] = val
            
            # 1. FIX: Generate missing task_id
            t_id = str(row_dict.get("task_id", "")).strip()
            if not t_id or t_id.lower() == "undefined":
                t_id = f"T-{uuid.uuid4().hex[:8]}"
                print(f"Row {i+2}: Generated ID {t_id}")
            
            # 2. Map fields carefully
            final_row = {}
            for h in target_headers:
                final_row[h] = row_dict.get(h, "")
            
            # Override task_id with fixed one
            final_row["task_id"] = t_id
            
            # 3. Handle shifted data if 'project' was at index 3
            # In current_headers: (task_id, title, project_id, project, assigned_to...)
            # In target_headers: (task_id, title, project_id, assigned_to, assigned_by...)
            if proj_idx == 3:
                # If project was at 3, then what we read into 'assigned_to' was actually 'project'
                # And what we read into 'assigned_by' was 'assigned_to'
                # Let's fix this mapping
                # We can use the column names from current_headers to re-map
                pass # Already handled by row_dict.get(h) if headers are named correctly
            
            # Build the list in correct order
            new_rows.append([final_row.get(h, "") for h in target_headers])

        # Overwrite with correct structure
        ws.clear()
        ws.update('A1', [target_headers] + new_rows)
        print(f"✅ Successfully wrote {len(new_rows)} rows to 'tasks' with corrected structure.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_repair_tasks()
