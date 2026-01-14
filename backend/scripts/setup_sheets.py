
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sheets_db import SHEETS_SCHEMA
from app.core.sheets_client import sheets_client

load_dotenv()

def setup():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not found in .env")
        return

    print(f"🛠️ Setting up Google Sheets for ID: {sheet_id}")
    
    # We use the authenticated gspread client
    client = sheets_client._get_client()
    spreadsheet = client.open_by_key(sheet_id)
    
    existing_sheets = {s.title: s for s in spreadsheet.worksheets()}
    
    for sheet_name, columns in SHEETS_SCHEMA.items():
        if sheet_name in existing_sheets:
            print(f"✅ Sheet '{sheet_name}' already exists. Updating headers...")
            sheet = existing_sheets[sheet_name]
        else:
            print(f"✨ Creating sheet '{sheet_name}'...")
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols=str(max(26, len(columns))))
        
        # Set headers
        sheet.update('A1', [columns])
        print(f"   Headers set for {sheet_name}: {columns}")

    print("\n🎉 Google Sheets setup complete! You can now run the migration or start the app.")

if __name__ == "__main__":
    setup()
