
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = "service_account.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def test():
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Users")
        headers = ws.row_values(1)
        print(f"HEADERS: {headers}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test()
