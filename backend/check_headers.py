
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets

def check():
    try:
        ws = google_sheets.get_worksheet("tasks")
        vals = ws.get_all_values()
        if vals:
            print("Headers:", vals[0])
            if len(vals) > 1:
                print("First row:", vals[1])
        else:
            print("Sheet is empty")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
