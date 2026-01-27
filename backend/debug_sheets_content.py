
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets
from app.core.sheets_config import SHEETS_SCHEMA

def analyze_sheets():
    sheets = ["tasks", "filingtasks", "fabricationtasks", "users", "attendance"]
    for s_name in sheets:
        print(f"\n--- ANALYZING SHEET: {s_name} ---")
        try:
            ws = google_sheets.get_worksheet(s_name)
            all_values = ws.get_all_values()
            if not all_values:
                print("Empty.")
                continue
            
            headers = [h.strip().lower() for h in all_values[0]]
            rows = all_values[1:]
            print(f"Headers: {headers}")
            print(f"Total rows: {len(rows)}")
            
            # Check for undefined or empty IDs
            id_col = headers[0] # Usually the ID
            undefined_indices = []
            for i, row in enumerate(rows):
                val = str(row[0]).strip().lower() if row else ""
                if val == "undefined" or val == "" or val == "none":
                    undefined_indices.append(i + 2)
            
            if undefined_indices:
                print(f"❌ FOUND UNDEFINED IDs at rows: {undefined_indices}")
            else:
                print("✅ All IDs seem valid (not 'undefined').")

            # For users and attendance, check for sample data to verify format
            if s_name in ["users", "attendance"] and rows:
                 print(f"Sample row 1: {rows[0]}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    analyze_sheets()
