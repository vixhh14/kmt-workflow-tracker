import sys
import os
# Add backend to path to import app modules if needed, but we'll try to keep it standalone imports or setup
sys.path.append(os.path.join(os.getcwd(), 'app'))

from app.core.sheets_db import SHEETS_SCHEMA
from app.services.google_sheets import google_sheets

def ensure_sheets():
    print("Checking for missing worksheets...")
    spreadsheet = google_sheets._get_spreadsheet()
    existing_titles = [s.title for s in spreadsheet.worksheets()]
    print(f"Existing sheets: {existing_titles}")

    for sheet_name, headers in SHEETS_SCHEMA.items():
        if sheet_name not in existing_titles:
            print(f"Creating missing sheet: {sheet_name}")
            try:
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers) + 5)
                # Add headers
                worksheet.append_row(headers)
                print(f"✅ Created {sheet_name} with headers.")
            except Exception as e:
                print(f"❌ Failed to create {sheet_name}: {e}")
        else:
            print(f"Found {sheet_name}.")

if __name__ == "__main__":
    ensure_sheets()
