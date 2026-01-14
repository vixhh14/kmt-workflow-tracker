
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
            if not os.path.exists(SERVICE_ACCOUNT_PATH):
                raise FileNotFoundError(f"Credentials file not found at: {SERVICE_ACCOUNT_PATH}")
            
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            self._client = gspread.authorize(creds)
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
        """Reads all records from a worksheet and returns as a list of dicts."""
        worksheet = self.get_worksheet(name)
        return worksheet.get_all_records()

    def insert_row(self, name: str, data: Dict[str, Any]):
        """Inserts a new row into the specified worksheet."""
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
        """Updates a row identified by its ID (assumes ID is in the first column)."""
        worksheet = self.get_worksheet(name)
        records = worksheet.get_all_records()
        headers = worksheet.row_values(1)
        id_col_name = headers[0]  # Standard: First column is the ID
        
        # Find the row index (gspread is 1-indexed, +1 for header, +1 for row)
        row_idx = -1
        for i, record in enumerate(records):
            if str(record.get(id_col_name)) == str(row_id):
                row_idx = i + 2
                break
        
        if row_idx == -1:
            raise ValueError(f"Record with ID {row_id} not found in {name}")
        
        # Update cells
        for key, value in data.items():
            if key in headers:
                col_idx = headers.index(key) + 1
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                worksheet.update_cell(row_idx, col_idx, str(value))
        
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
