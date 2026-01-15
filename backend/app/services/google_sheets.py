
import os
import json
import gspread
import threading
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.time_utils import get_current_time_ist

# Load Env
from dotenv import load_dotenv
load_dotenv()

# Config
CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "service_account.json")
# Ensure path is absolute relative to project root (backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICE_ACCOUNT_PATH = os.path.join(PROJECT_ROOT, CREDENTIALS_FILE)
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GoogleSheetsService, cls).__new__(cls)
                cls._instance._client = None
                cls._instance._spreadsheet = None
            return cls._instance

    def _get_client(self):
        if not self._client:
            # 1. Try to load from environment variable (JSON string) - Best for Render/Cloud
            google_json = os.getenv("GOOGLE_SHEETS_JSON")
            
            if google_json:
                try:
                    info = json.loads(google_json)
                    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                    self._client = gspread.authorize(creds)
                    print("✅ Authenticated using GOOGLE_SHEETS_JSON environment variable")
                except Exception as e:
                    print(f"❌ Failed to parse GOOGLE_SHEETS_JSON: {e}")
                    raise
            
            # 2. Fallback to service_account.json file - Best for Local
            else:
                if not os.path.exists(SERVICE_ACCOUNT_PATH):
                    # Provide an informative error for Render/Prod
                    error_msg = (
                        f"Credentials not found! \n"
                        f"LOCAL: Ensure '{CREDENTIALS_FILE}' exists in the backend/ directory.\n"
                        f"PROD (Render): Set the 'GOOGLE_SHEETS_JSON' Environment Variable with your service account JSON content.\n"
                        f"Path checked: {SERVICE_ACCOUNT_PATH}"
                    )
                    print(f"❌ {error_msg}")
                    # If we don't have it, we can't continue
                    raise FileNotFoundError(error_msg)
                
                try:
                    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
                    self._client = gspread.authorize(creds)
                    print(f"✅ Authenticated using credentials file: {SERVICE_ACCOUNT_PATH}")
                except Exception as e:
                    print(f"❌ Failed to authorize with service account file: {e}")
                    raise
                
        return self._client

    def _get_spreadsheet(self):
        if not self._spreadsheet:
            client = self._get_client()
            if not SHEET_ID:
                raise ValueError("GOOGLE_SHEET_ID environment variable is not set")
            try:
                self._spreadsheet = client.open_by_key(SHEET_ID)
            except Exception as e:
                print(f"❌ Failed to open spreadsheet with ID {SHEET_ID}: {e}")
                raise
        return self._spreadsheet

    def get_worksheet(self, name: str):
        """Returns a gspread Worksheet object by name."""
        try:
            return self._get_spreadsheet().worksheet(name)
        except gspread.WorksheetNotFound:
            print(f"⚠️ Worksheet '{name}' not found. Attempting to find by title case or lowercase...")
            # Try case-insensitive fallback
            for sheet in self._get_spreadsheet().worksheets():
                if sheet.title.lower() == name.lower():
                    return sheet
            raise
        except Exception as e:
            print(f"❌ Error getting worksheet {name}: {e}")
            raise

    def read_all_bulk(self, name: str) -> List[Dict[str, Any]]:
        """Reads all records in one call and returns as list of dicts."""
        worksheet = self.get_worksheet(name)
        # get_all_records is more direct than get_all_values then manual zip
        # but manual zip allows us to handle missing values and _row_idx
        try:
            all_values = worksheet.get_all_values()
            if not all_values:
                return []
            
            headers = all_values[0]
            records = []
            for i, values in enumerate(all_values[1:]):
                # Create dict and pad with empty strings if row is shorter than headers
                padded_values = values + [""] * (len(headers) - len(values))
                record = dict(zip(headers, padded_values))
                record["_row_idx"] = i + 2 # 1-indexed, +1 for header
                records.append(record)
            return records
        except Exception as e:
            print(f"❌ Error reading all values from {name}: {e}")
            raise

    def insert_row(self, name: str, data: Dict[str, Any], headers: List[str]):
        """Inserts a new row into the specified worksheet."""
        worksheet = self.get_worksheet(name)
        
        # Prepare row values based on provided headers
        row = []
        for header in headers:
            val = data.get(header, "")
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            row.append(str(val))
        
        try:
            worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"❌ Error inserting row into {name}: {e}")
            return False
            
    def update_row_by_idx(self, name: str, row_idx: int, data: Dict[str, Any], headers: List[str]):
        """Updates a row by its index using batch update."""
        worksheet = self.get_worksheet(name)
        
        cells_to_update = []
        for key, value in data.items():
            if key in headers:
                col_idx = headers.index(key) + 1
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                
                cell = gspread.cell.Cell(row=row_idx, col=col_idx, value=str(value))
                cells_to_update.append(cell)
        
        if cells_to_update:
            try:
                worksheet.update_cells(cells_to_update)
                return True
            except Exception as e:
                print(f"❌ Error updating row {row_idx} in {name}: {e}")
                return False
    def delete_row_by_idx(self, name: str, row_idx: int):
        """Physically removes a row from the worksheet."""
        worksheet = self.get_worksheet(name)
        try:
            worksheet.delete_rows(row_idx)
            return True
        except Exception as e:
            print(f"❌ Error deleting row {row_idx} from {name}: {e}")
            return False

# Global instance
google_sheets = GoogleSheetsService()
