
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets

def check_ids():
    for sheet in ["tasks", "filingtasks", "fabricationtasks"]:
        print(f"Checking {sheet}...")
        try:
            ws = google_sheets.get_worksheet(sheet)
            rows = ws.get_all_values()
            if len(rows) < 2:
                print(f"  Empty.")
                continue
            headers = rows[0]
            first_row = rows[1]
            print(f"  Headers: {headers[:5]}")
            print(f"  First Row ID: '{first_row[0]}'")
            
            # Check for literal 'undefined'
            undefined_count = 0
            for r in rows[1:]:
                if r and r[0].strip().lower() == 'undefined':
                    undefined_count += 1
            print(f"  Total 'undefined' IDs: {undefined_count}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    check_ids()
