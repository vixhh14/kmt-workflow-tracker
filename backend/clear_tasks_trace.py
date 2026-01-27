
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def clear_all_tasks():
    with open("clear_log.txt", "w") as f:
        f.write("Starting...\n")
        # Sheets to clear
        task_sheets = ["tasks", "fabricationtasks", "filingtasks", "planningtasks"]
        
        for sheet_name in task_sheets:
            try:
                f.write(f"Clearing sheet: {sheet_name}...\n")
                ws = google_sheets.get_worksheet(sheet_name)
                headers = SHEETS_SCHEMA.get(sheet_name)
                if not headers:
                    f.write(f"No schema found for {sheet_name}\n")
                    continue
                ws.clear()
                ws.update('A1', [headers])
                f.write(f"OK: {sheet_name}\n")
            except Exception as e:
                f.write(f"ERR: {sheet_name}: {e}\n")
        f.write("DONE\n")

if __name__ == "__main__":
    clear_all_tasks()
