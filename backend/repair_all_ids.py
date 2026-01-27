
import os
import sys
import uuid

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def repair_sheet(sheet_name):
    print(f"--- REPAIRING {sheet_name.upper()} ---")
    try:
        ws = google_sheets.get_worksheet(sheet_name)
        all_values = ws.get_all_values()
        if not all_values:
            print(f"Sheet {sheet_name} is empty.")
            return

        current_headers = [str(h).strip().lower() for h in all_values[0]]
        rows = all_values[1:]
        
        target_headers = SHEETS_SCHEMA[sheet_name]
        id_col = target_headers[0] # e.g. task_id, filing_task_id
        
        new_rows = []
        for i, row in enumerate(rows):
            row_dict = {}
            for j, val in enumerate(row):
                if j < len(current_headers):
                    row_dict[current_headers[j]] = val
            
            # 1. FIX: Generate missing IDs
            t_id = str(row_dict.get(id_col, "")).strip()
            if not t_id or t_id.lower() == "undefined" or t_id == "":
                t_id = f"T-{uuid.uuid4().hex[:8]}"
                print(f"{sheet_name} Row {i+2}: Generated missing ID {t_id}")
            
            # 2. Map fields strictly
            ordered_row = []
            for h in target_headers:
                val = row_dict.get(h, "")
                if h == id_col:
                    val = t_id
                ordered_row.append(val)
            
            new_rows.append(ordered_row)

        # Overwrite
        ws.clear()
        ws.update('A1', [target_headers] + new_rows)
        print(f"✅ Successfully repaired {len(new_rows)} rows in '{sheet_name}'.")

    except Exception as e:
        print(f"❌ Error repairing {sheet_name}: {e}")

if __name__ == "__main__":
    for sheet in ["tasks", "filingtasks", "fabricationtasks", "subtasks"]:
        repair_sheet(sheet)
