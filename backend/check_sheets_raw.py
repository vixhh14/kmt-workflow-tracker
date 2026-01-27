
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = "service_account.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def check_raw():
    try:
        if os.path.exists(CREDENTIALS_FILE):
             creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        else:
             google_json = os.getenv("GOOGLE_SHEETS_JSON", "").strip()
             info = json.loads(google_json)
             creds = Credentials.from_service_account_info(info, scopes=SCOPES)
             
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        print("--- USERS SHEET ---")
        ws_users = sh.worksheet("users")
        users_vals = ws_users.get_all_values()
        if users_vals:
            print(f"Headers: {users_vals[0]}")
            for row in users_vals[1:]:
                print(f"Row: {row}")
        else:
            print("Users sheet is empty")
            
        print("\n--- ATTENDANCE SHEET ---")
        ws_att = sh.worksheet("attendance")
        att_vals = ws_att.get_all_values()
        if att_vals:
            print(f"Headers: {att_vals[0]}")
            for row in att_vals[1:]:
                print(f"Row: {row}")
        else:
            print("Attendance sheet is empty")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_raw()
