
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.repositories.sheets_repository import sheets_repo

if __name__ == "__main__":
    print("Clearing backend cache...")
    sheets_repo.clear_cache()
    print("Cache cleared. Next request will fetch fresh data from Google Sheets.")
