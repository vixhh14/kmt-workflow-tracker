
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets

def check_attendance():
    ws = google_sheets.get_worksheet("attendance")
    rows = ws.get_all_values()
    print(f"Total attendance rows: {len(rows)}")
    if len(rows) > 0:
        print(f"Headers: {rows[0]}")
    for i, row in enumerate(rows[1:]):
        print(f"Row {i+2}: {row}")

if __name__ == "__main__":
    check_attendance()
