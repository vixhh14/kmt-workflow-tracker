
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Any, Optional

class GoogleSheetsClient:
    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.client = None
        self.spreadsheet = None

    def _get_client(self):
        if self.client:
            return self.client
        
        if not self.credentials_json:
            # Fallback to local file for dev
            creds_path = "service_account.json"
            if os.path.exists(creds_path):
                self.client = gspread.service_account(filename=creds_path)
            else:
                raise Exception("Missing GOOGLE_SHEETS_CREDENTIALS environment variable or service_account.json")
        else:
            try:
                # Handle JSON string from env
                creds_dict = json.loads(self.credentials_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
                self.client = gspread.authorize(creds)
            except Exception as e:
                raise Exception(f"Failed to initialize Google Sheets client: {str(e)}")
        
        return self.client

    def _get_spreadsheet(self):
        if self.spreadsheet:
            return self.spreadsheet
        
        client = self._get_client()
        if not self.spreadsheet_id:
            raise Exception("Missing GOOGLE_SHEET_ID environment variable")
        
        self.spreadsheet = client.open_by_key(self.spreadsheet_id)
        return self.spreadsheet

    def get_sheet(self, sheet_name: str):
        spreadsheet = self._get_spreadsheet()
        try:
            return spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create sheet if it doesn't exist? (Optional, maybe safer to fail)
            raise Exception(f"Sheet '{sheet_name}' not found in spreadsheet {self.spreadsheet_id}")

    def read_all(self, sheet_name: str) -> List[Dict[str, Any]]:
        sheet = self.get_sheet(sheet_name)
        return sheet.get_all_records()

    def append_row(self, sheet_name: str, row_dict: Dict[str, Any], columns: List[str]):
        sheet = self.get_sheet(sheet_name)
        # Ensure row values match column order
        row_values = []
        for col in columns:
            val = row_dict.get(col, "")
            # Handle datetime/date
            if isinstance(val, datetime):
                val = val.isoformat()
            row_values.append(val)
        
        sheet.append_row(row_values)

    def update_row_by_id(self, sheet_name: str, id_col: str, id_val: str, new_data: Dict[str, Any]):
        sheet = self.get_sheet(sheet_name)
        data = sheet.get_all_records()
        
        # Find row index (1-indexed, +1 for header)
        row_idx = -1
        for i, row in enumerate(data):
            if str(row.get(id_col)) == str(id_val):
                row_idx = i + 2 # +1 for 0-index -> 1-index, +1 for header
                break
        
        if row_idx == -1:
            raise Exception(f"Record with {id_col}={id_val} not found in {sheet_name}")

        # Map new data to column indices
        headers = sheet.row_values(1)
        updates = []
        for col_name, val in new_data.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                if isinstance(val, datetime):
                    val = val.isoformat()
                updates.append({
                    'range': gspread.utils.rowcol_to_a1(row_idx, col_idx),
                    'values': [[val]]
                })
        
        if updates:
            sheet.batch_update(updates)

    def delete_row_by_id(self, sheet_name: str, id_col: str, id_val: str):
        """Soft delete actually sets is_deleted=TRUE"""
        self.update_row_by_id(sheet_name, id_col, id_val, {"is_deleted": "TRUE"})

# Global client Instance
sheets_client = GoogleSheetsClient()
