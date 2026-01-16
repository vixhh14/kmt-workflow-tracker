
import os
import json
from app.services.google_sheets import google_sheets
from app.core.sheets_db import SHEETS_SCHEMA

def audit_headers():
    for sheet_name in SHEETS_SCHEMA.keys():
        try:
            ws = google_sheets.get_worksheet(sheet_name)
            headers = ws.row_values(1)
            print(f"Sheet: {sheet_name}")
            print(f"  Expected: {SHEETS_SCHEMA[sheet_name]}")
            print(f"  Actual:   {headers}")
        except Exception as e:
            print(f"Error checking {sheet_name}: {e}")

if __name__ == "__main__":
    audit_headers()
