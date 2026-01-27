
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def clear_all_tasks():
    print("--- CLEARING ALL TASKS FROM GOOGLE SHEETS ---")
    
    # Sheets to clear
    task_sheets = ["tasks", "fabricationtasks", "filingtasks", "planningtasks"]
    
    for sheet_name in task_sheets:
        try:
            print(f"Clearing sheet: {sheet_name}...")
            ws = google_sheets.get_worksheet(sheet_name)
            
            # Get canonical headers
            headers = SHEETS_SCHEMA.get(sheet_name)
            if not headers:
                print(f"No schema found for {sheet_name}, skipping.")
                continue
                
            # Clear and write only headers
            ws.clear()
            ws.update(values=[headers], range_name='A1')
            print(f"OK: Repaired {sheet_name} (kept headers, deleted all data).")
            
        except Exception as e:
            print(f"ERROR clearing {sheet_name}: {e}")

    print("\n--- DONE: Dashboard should now be empty ---")

if __name__ == "__main__":
    clear_all_tasks()
