
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets

def dump_tasks():
    for sheet in ["tasks", "filingtasks", "fabricationtasks"]:
        print(f"\n--- {sheet.upper()} ---")
        ws = google_sheets.get_worksheet(sheet)
        rows = ws.get_all_values()
        if not rows: continue
        headers = rows[0]
        for i, row in enumerate(rows[1:]):
            # Print row index and the first few columns including WO and Title
            print(f"Row {i+2}: {row[:5]}")

if __name__ == "__main__":
    dump_tasks()
