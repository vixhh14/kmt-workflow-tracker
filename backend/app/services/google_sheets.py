
import os
import json
import gspread
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
    
    def __new__(cls):
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
                    raise FileNotFoundError(error_msg)
                
                creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
                self._client = gspread.authorize(creds)
                print(f"✅ Authenticated using credentials file: {SERVICE_ACCOUNT_PATH}")
                
        return self._client

    def _get_spreadsheet(self):
        if not self._spreadsheet:
            client = self._get_client()
            if not SHEET_ID:
                raise ValueError("GOOGLE_SHEET_ID environment variable is not set")
            self._spreadsheet = client.open_by_key(SHEET_ID)
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

    def read_all(self, name: str) -> List[Dict[str, Any]]:
        """Reads all records and injects _row_idx for faster updates."""
        worksheet = self.get_worksheet(name)
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

    def ensure_headers(self, name: str, expected_headers: List[str]):
        """Ensures that all expected headers exist in row 1."""
        worksheet = self.get_worksheet(name)
        existing_headers = worksheet.row_values(1)
        
        missing = [h for h in expected_headers if h not in existing_headers]
        if missing:
            print(f"Adding missing headers to {name}: {missing}")
            next_col = len(existing_headers) + 1
            for header in missing:
                worksheet.update_cell(1, next_col, header)
                next_col += 1
        return True

    def insert_row(self, name: str, data: Dict[str, Any]):
        """Inserts a new row into the specified worksheet."""
        from app.core.sheets_db import SHEETS_SCHEMA
        if name in SHEETS_SCHEMA:
            self.ensure_headers(name, SHEETS_SCHEMA[name])
            
        worksheet = self.get_worksheet(name)
        headers = worksheet.row_values(1)
        
        # Prepare row values based on headers
        row = []
        for header in headers:
            val = data.get(header, "")
            # Format datetime objects naturally
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            row.append(str(val))
        
        worksheet.append_row(row)
        return True
        
    def update_row(self, name: str, row_id: str, data: Dict[str, Any]):
        """Updates a row identified by its ID or _row_idx using batch update."""
        worksheet = self.get_worksheet(name)
        headers = worksheet.row_values(1)
        
        row_idx = data.get("_row_idx")
        
        if not row_idx:
            # Fallback: must find row_idx by searching
            records = self.read_all(name)
            id_col_name = headers[0]
            for rec in records:
                if str(rec.get(id_col_name)) == str(row_id):
                    row_idx = rec.get("_row_idx")
                    break
        
        if not row_idx:
            print(f"⚠️ Warning: Record with ID {row_id} not found in {name}")
            return False
        
        cells_to_update = []
        for key, value in data.items():
            if key in headers:
                col_idx = headers.index(key) + 1
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                
                cell = gspread.cell.Cell(row=row_idx, col=col_idx, value=str(value))
                cells_to_update.append(cell)
        
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
        
        return True

    def soft_delete_row(self, name: str, row_id: str):
        """Sets is_deleted to TRUE for the record with the given ID."""
        return self.update_row(name, row_id, {"is_deleted": "TRUE"})

    def hard_delete_row(self, name: str, row_id: str):
        """Physically removes the row from the worksheet."""
        worksheet = self.get_worksheet(name)
        records = worksheet.get_all_records()
        headers = worksheet.row_values(1)
        id_col_name = headers[0]
        
        row_idx = -1
        for i, record in enumerate(records):
            if str(record.get(id_col_name)) == str(row_id):
                row_idx = i + 2
                break
        
        if row_idx != -1:
            worksheet.delete_rows(row_idx)
            return True
        return False

# Global instance
google_sheets = GoogleSheetsService()
