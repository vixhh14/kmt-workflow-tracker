
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

CREDENTIALS_FILE = "service_account.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

print(f"SHEET_ID present: {bool(SHEET_ID)}")

try:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)
    
    sheets_to_check = ["users", "machines", "projects", "tasks"]
    for name in sheets_to_check:
        try:
            ws = sh.worksheet(name)
            headers = ws.row_values(1)
            print(f"{name}: {headers}")
        except Exception as e:
            print(f"{name} ERROR: {e}")
            
except Exception as e:
    print(f"FATAL ERROR: {e}")
