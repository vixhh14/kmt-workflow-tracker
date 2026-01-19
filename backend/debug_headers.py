from app.services.google_sheets import google_sheets
import os

def check_sheets():
    sheets = ["users", "machines"]
    for s in sheets:
        try:
            print(f"Checking sheet: {s}")
            ws = google_sheets.get_worksheet(s)
            headers = ws.row_values(1)
            print(f"Headers for {s}: {headers}")
        except Exception as e:
            print(f"Error checking {s}: {e}")

if __name__ == "__main__":
    check_sheets()
