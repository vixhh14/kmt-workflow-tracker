
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = "service_account.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def test():
    print(f"Testing connection to {SHEET_ID}...")
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"File missing: {CREDENTIALS_FILE}")
            return
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("Authorized.")
        sh = client.open_by_key(SHEET_ID)
        print(f"Opened spreadsheet: {sh.title}")
        ws = sh.worksheet("Users")
        print(f"Found worksheet: {ws.title}")
        rows = ws.get_all_records()
        print(f"Found {len(rows)} records in Users.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test()
