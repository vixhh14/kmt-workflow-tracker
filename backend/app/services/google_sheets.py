
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
                cls._instance._worksheets = {}  # Cache worksheet objects
            return cls._instance

    def _get_client(self):
        if self._client:
            return self._client
            
        # 1. PRIMARY: Try to load from environment variable (Full JSON string)
        # This is the ONLY reliable way for Render/Cloud without committing secrets
        google_json = os.getenv("GOOGLE_SHEETS_JSON", "").strip()
        
        if google_json:
            try:
                info = json.loads(google_json)
                creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                self._client = gspread.authorize(creds)
                print("[GoogleSheets] Authenticated successfully using GOOGLE_SHEETS_JSON environment variable.")
                return self._client
            except Exception as e:
                print(f"[GoogleSheets] Failed to parse GOOGLE_SHEETS_JSON: {e}")
                # We don't raise here yet, we might try fallback if local, 
                # but usually if JSON is set and fails, it's a configuration error.
        
        # 2. SECONDARY: Fallback to local service_account.json file
        # ONLY used if GOOGLE_SHEETS_JSON is missing or invalid
        if os.path.exists(SERVICE_ACCOUNT_PATH):
            try:
                creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
                self._client = gspread.authorize(creds)
                print(f"[GoogleSheets] Authenticated successfully using file: {SERVICE_ACCOUNT_PATH}")
                return self._client
            except Exception as e:
                print(f"[GoogleSheets] Failed to authorize with service account file: {e}")
                raise
        
        # 3. TERMINAL FAILURE: No credentials found anywhere
        error_msg = (
            "GOOGLE SHEETS AUTHENTICATION FAILED!\n"
            "------------------------------------\n"
            "ROOT CAUSE: No valid service account credentials found.\n"
            "ACTION REQUIRED:\n"
            "  - PROD (Render): Set 'GOOGLE_SHEETS_JSON' environment variable to the content of your service_account.json.\n"
            "  - LOCAL: Ensure 'service_account.json' exists at: " + SERVICE_ACCOUNT_PATH + "\n"
            "------------------------------------"
        )
        print(f"CRITICAL: {error_msg}")
        raise RuntimeError(error_msg)

    def _get_spreadsheet(self):
        if not self._spreadsheet:
            client = self._get_client()
            if not SHEET_ID:
                raise ValueError("GOOGLE_SHEET_ID environment variable is not set")
            try:
                self._spreadsheet = client.open_by_key(SHEET_ID)
            except Exception as e:
                print(f"Failed to open spreadsheet with ID {SHEET_ID}: {e}")
                raise
        return self._spreadsheet

    def get_worksheet(self, name: str):
        """Returns a gspread Worksheet object by name (exact or case-insensitive fallback)."""
        with self._lock:
            if name in self._worksheets:
                return self._worksheets[name]
                
        spreadsheet = self._get_spreadsheet()
        try:
            ws = spreadsheet.worksheet(name)
            with self._lock:
                self._worksheets[name] = ws
            return ws
        except gspread.WorksheetNotFound:
            # Try case-insensitive fallback
            for sheet in spreadsheet.worksheets():
                if sheet.title.lower() == name.lower():
                    with self._lock:
                        self._worksheets[name] = sheet
                    return sheet
            raise
        except Exception as e:
            print(f"❌ Error getting worksheet {name}: {e}")
            raise

    def batch_get_all(self, names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetches multiple sheets in a single call using values_batch_get."""
        spreadsheet = self._get_spreadsheet()
        ranges = [f"'{name}'!A1:AZ5000" for name in names]
        try:
            batch_results = spreadsheet.values_batch_get(ranges)
            value_ranges = batch_results.get('valueRanges', [])
            
            results = {}
            for name, v_range in zip(names, value_ranges):
                values = v_range.get('values', [])
                results[name] = self._process_values_to_records(values)
            return results
        except Exception as e:
            print(f"❌ Error in batch_get_all: {e}")
            raise

    def _process_values_to_records(self, all_values: List[List[Any]]) -> List[Dict[str, Any]]:
        """Helper to convert raw grid values to normalized record dicts."""
        if not all_values:
            return []
        
        raw_headers = all_values[0]
        normalized_headers = [self._normalize_header(h) for h in raw_headers]
        
        records = []
        for i, values in enumerate(all_values[1:]):
            padded_values = values + [""] * (len(raw_headers) - len(values))
            record = {}
            for rh, nh, val in zip(raw_headers, normalized_headers, padded_values):
                record[nh] = val
                record[f"_orig_{nh}"] = rh
            
            record["_row_idx"] = i + 2
            records.append(record)
        return records

    def ensure_worksheet(self, name: str, expected_headers: List[str], force_headers: bool = False):
        """Verifies worksheet exists; creates it with headers if missing OR forced."""
        try:
            # First, check if it exists (case-insensitive)
            try:
                ws = self.get_worksheet(name)
                # Verify headers if empty or forced
                if force_headers:
                     ws.update('A1', [expected_headers])
                elif ws.row_count < 1:
                     # Only append if totally empty
                     ws.append_row(expected_headers)
                print(f"✅ Worksheet verified: {ws.title}")
                return ws
            except gspread.WorksheetNotFound:
                # Create it
                print(f"✨ Creating missing worksheet: {name}")
                spreadsheet = self._get_spreadsheet()
                ws = spreadsheet.add_worksheet(title=name, rows="5000", cols=str(max(26, len(expected_headers))))
                # Add headers immediately
                ws.append_row(expected_headers)
                print(f"🚀 Worksheet '{name}' created.")
                return ws
        except Exception as e:
            print(f"❌ Critical error ensuring worksheet {name}: {e}")
            raise

    def _normalize_header(self, h: str) -> str:
        """Normalizes a header for comparison (e.g., 'Project Name ' -> 'project_name')."""
        import re
        if not h: return ""
        s = str(h).strip().lower()
        s = re.sub(r'[^a-z0-9]+', '_', s)
        return s.strip('_')

    def read_all_bulk(self, name: str) -> List[Dict[str, Any]]:
        """Reads all records in one call and returns as list of dicts."""
        worksheet = self.get_worksheet(name)
        try:
            all_values = worksheet.get_all_values()
            return self._process_values_to_records(all_values)
        except Exception as e:
            print(f"❌ [GS] Error reading all values from {name}: {e}")
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
