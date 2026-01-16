
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

    def _normalize_header(self, h: str) -> str:
        """Normalizes a header for comparison (e.g., 'Project Name ' -> 'project_name')."""
        import re
        if not h: return ""
        s = str(h).strip().lower()
        s = re.sub(r'[^a-z0-9]+', '_', s)
        return s.strip('_')

    def read_all_bulk(self, name: str) -> List[Dict[str, Any]]:
        """Reads all records in one call and returns as list of dicts with normalized keys."""
        worksheet = self.get_worksheet(name)
        try:
            all_values = worksheet.get_all_values()
            if not all_values:
                return []
            
            raw_headers = all_values[0]
            normalized_headers = [self._normalize_header(h) for h in raw_headers]
            
            # Ensure at least one 'id' key for the primary column
            if "id" not in normalized_headers and len(normalized_headers) > 0:
                # If first column looks like an ID, alias it
                if normalized_headers[0].endswith("_id"):
                    normalized_headers[0] = "id"
            
            records = []
            for i, values in enumerate(all_values[1:]):
                # Pad values to match header length
                padded_values = values + [""] * (len(raw_headers) - len(values))
                record = {}
                for rh, nh, val in zip(raw_headers, normalized_headers, padded_values):
                    record[nh] = val
                    record[f"_orig_{nh}"] = rh
                
                record["_row_idx"] = i + 2
                records.append(record)
            return records
        except Exception as e:
            print(f"❌ Error reading all values from {name}: {e}")
            raise

    def insert_row(self, name: str, data: Dict[str, Any], raw_headers: Optional[List[str]] = None):
        """Inserts a new row using the ACTUAL worksheet headers for placement."""
        worksheet = self.get_worksheet(name)
        try:
            if not raw_headers:
                raw_headers = worksheet.row_values(1)
            
            actual_normalized = [self._normalize_header(h) for h in raw_headers]
            
            row = []
            for nh in actual_normalized:
                val = data.get(nh, "")
                if hasattr(val, "isoformat"): val = val.isoformat()
                row.append(str(val) if val is not None else "")
            
            worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"❌ Error inserting row into {name}: {e}")
            return False
            
    def update_row_by_idx(self, name: str, row_idx: int, data: Dict[str, Any], raw_headers: Optional[List[str]] = None):
        """Updates specific columns in a row based on ACTUAL worksheet match."""
        worksheet = self.get_worksheet(name)
        try:
            if not raw_headers:
                raw_headers = worksheet.row_values(1)
                
            actual_normalized = [self._normalize_header(h) for h in raw_headers]
            
            cells_to_update = []
            for key, value in data.items():
                norm_key = self._normalize_header(key)
                if norm_key in actual_normalized:
                    col_idx = actual_normalized.index(norm_key) + 1
                    if hasattr(value, "isoformat"): value = value.isoformat()
                    cell = gspread.cell.Cell(row=row_idx, col=col_idx, value=str(value) if value is not None else "")
                    cells_to_update.append(cell)
            
            if cells_to_update:
                worksheet.update_cells(cells_to_update)
            return True
        except Exception as e:
            print(f"❌ Error updating row {row_idx} in {name}: {e}")
            return False

    def batch_append(self, name: str, rows_data: List[Dict[str, Any]], raw_headers: Optional[List[str]] = None):
        """Appends multiple rows in one call."""
        if not rows_data: return True
        worksheet = self.get_worksheet(name)
        try:
            if not raw_headers:
                raw_headers = worksheet.row_values(1)
            
            actual_normalized = [self._normalize_header(h) for h in raw_headers]
            
            all_rows = []
            for data in rows_data:
                row = []
                for nh in actual_normalized:
                    val = data.get(nh, "")
                    if hasattr(val, "isoformat"): val = val.isoformat()
                    row.append(str(val) if val is not None else "")
                all_rows.append(row)
            
            worksheet.append_rows(all_rows)
            return True
        except Exception as e:
            print(f"❌ Error batch appending to {name}: {e}")
            return False

    def batch_update(self, name: str, updates: List[Dict[str, Any]], raw_headers: Optional[List[str]] = None):
        """
        Updates multiple rows in one call. 
        Each update dict must contain '_row_idx' and the fields to update.
        """
        if not updates: return True
        worksheet = self.get_worksheet(name)
        try:
            if not raw_headers:
                raw_headers = worksheet.row_values(1)
                
            actual_normalized = [self._normalize_header(h) for h in raw_headers]
            
            cells_to_update = []
            for entry in updates:
                row_idx = entry.get("_row_idx")
                if not row_idx: continue
                
                for key, value in entry.items():
                    if key.startswith("_"): continue
                    norm_key = self._normalize_header(key)
                    if norm_key in actual_normalized:
                        col_idx = actual_normalized.index(norm_key) + 1
                        if hasattr(value, "isoformat"): value = value.isoformat()
                        cell = gspread.cell.Cell(row=row_idx, col=col_idx, value=str(value) if value is not None else "")
                        cells_to_update.append(cell)
            
            if cells_to_update:
                worksheet.update_cells(cells_to_update)
            return True
        except Exception as e:
            print(f"❌ Error batch updating {name}: {e}")
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
