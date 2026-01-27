
import os
import sys
import uuid

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def repair_all_sheets():
    sheets = ["tasks", "filingtasks", "fabricationtasks", "users", "attendance"]
    
    for s_name in sheets:
        print(f"\n--- REPAIRING SHEET: {s_name} ---")
        try:
            ws = google_sheets.get_worksheet(s_name)
            all_values = ws.get_all_values()
            if not all_values or len(all_values) < 2:
                print("Empty or no data.")
                continue
            
            headers = all_values[0]
            rows = all_values[1:]
            
            # Find ID column (usually the first one)
            id_col_idx = 0
            id_header_name = headers[0]
            
            # For attendance, it might be attendance_id
            updates = []
            for i, row in enumerate(rows):
                if not row: continue
                current_id = str(row[0]).strip()
                
                needs_repair = False
                if not current_id or current_id.lower() in ["undefined", "none", "null", ""]:
                    needs_repair = True
                
                if needs_repair:
                    new_id = f"REF-{s_name[:3].upper()}-{uuid.uuid4().hex[:6]}"
                    print(f"  Row {i+2}: '{current_id}' -> '{new_id}'")
                    # Update only the ID cell
                    ws.update_cell(i + 2, 1, new_id)
                    
            print(f"✅ Finished check for {s_name}")

        except Exception as e:
            print(f"Error in {s_name}: {e}")

if __name__ == "__main__":
    repair_all_sheets()
