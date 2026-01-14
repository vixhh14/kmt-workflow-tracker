
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import socket

load_dotenv()

# Set timeout
socket.setdefaulttimeout(10)

CREDENTIALS_FILE = "service_account.json"
# The user provided ID:
SHEET_ID = "1ul_L4G-z-jkcUUYu4cCJfxtytpCx6bz5TeIJPjVuOz8"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def test():
    print("RUNNING WITH TIMEOUT...")
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("Authorized.")
        sh = client.open_by_key(SHEET_ID)
        print(f"Opened: {sh.title}")
        ws = sh.worksheet("Users")
        headers = ws.row_values(1)
        print(f"HEADERS: {headers}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test()
