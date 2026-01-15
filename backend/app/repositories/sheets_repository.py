import time
import uuid
from typing import List, Dict, Any, Optional
from app.services.google_sheets import google_sheets
from app.core.time_utils import get_current_time_ist

# Global cache to persist across requests but within process
# Using a simple dict. In a production multi-worker environment like Gunicorn, 
# this would be per-worker. For Render free tier, it's usually one worker.
_GLOBAL_CACHE = {}
_CACHE_EXPIRY = {}
CACHE_TTL = 60  # Seconds

class SheetsRepository:
    def __init__(self):
        pass

    def _get_sheet_data(self, sheet_name: str) -> List[Dict[str, Any]]:
        now = time.time()
        # Check if we have valid cache
        if sheet_name not in _GLOBAL_CACHE or now > _CACHE_EXPIRY.get(sheet_name, 0):
            try:
                # One bulk read per sheet
                data = google_sheets.read_all(sheet_name)
                _GLOBAL_CACHE[sheet_name] = data
                _CACHE_EXPIRY[sheet_name] = now + CACHE_TTL
                print(f"🔄 [SheetsRepo] Cache Refreshed: {sheet_name} ({len(data)} rows)")
            except Exception as e:
                print(f"❌ [SheetsRepo] Failed to fetch {sheet_name}: {e}")
                # Fallback to expired cache if available
                if sheet_name in _GLOBAL_CACHE:
                    return _GLOBAL_CACHE[sheet_name]
                return []
        return _GLOBAL_CACHE[sheet_name]

    def get_all(self, sheet_name: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Returns all rows from a sheet, optionally filtering deleted ones."""
        data = self._get_sheet_data(sheet_name)
        if include_deleted:
            return [dict(row) for row in data]
        
        # Filter is_deleted
        return [
            dict(row) for row in data 
            if str(row.get("is_deleted", "")).upper() not in ["TRUE", "1", "YES"]
        ]

    def get_by_id(self, sheet_name: str, id_value: Any) -> Optional[Dict[str, Any]]:
        """Finds a single row by its ID."""
        headers = self.get_headers(sheet_name)
        id_col = headers[0] if headers else "id"
        
        data = self._get_sheet_data(sheet_name)
        for row in data:
            if str(row.get(id_col)) == str(id_value):
                return dict(row)
        return None

    def get_headers(self, sheet_name: str) -> List[str]:
        """Returns headers for a sheet from the schema."""
        from app.core.sheets_db import SHEETS_SCHEMA
        return SHEETS_SCHEMA.get(sheet_name, [])

    def insert(self, sheet_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts a new row and invalidates cache."""
        headers = self.get_headers(sheet_name)
        id_col = headers[0] if headers else "id"
        
        # Ensure default fields
        if id_col not in data or not data[id_col]:
            data[id_col] = str(uuid.uuid4())
            
        now_ist = get_current_time_ist().isoformat()
        if "created_at" not in data or not data["created_at"]:
            data["created_at"] = now_ist
        if "updated_at" not in data:
            data["updated_at"] = now_ist
        if "is_deleted" not in data:
            data["is_deleted"] = False

        google_sheets.insert_row(sheet_name, data)
        
        # Invalidate cache to force re-read on next access
        if sheet_name in _GLOBAL_CACHE:
            del _GLOBAL_CACHE[sheet_name]
            
        return data

    def update(self, sheet_name: str, id_value: Any, data: Dict[str, Any]) -> bool:
        """Updates a row and invalidates cache."""
        if not id_value:
            return False
            
        if "updated_at" not in data:
            data["updated_at"] = get_current_time_ist().isoformat()

        success = google_sheets.update_row(sheet_name, str(id_value), data)
        
        # Invalidate cache
        if success and sheet_name in _GLOBAL_CACHE:
            del _GLOBAL_CACHE[sheet_name]
            
        return success

    def soft_delete(self, sheet_name: str, id_value: Any) -> bool:
        """Sets is_deleted=True for a row."""
        return self.update(sheet_name, id_value, {"is_deleted": True})

    def clear_cache(self, sheet_name: Optional[str] = None):
        """Clears cache for one or all sheets."""
        global _GLOBAL_CACHE, _CACHE_EXPIRY
        if sheet_name:
            if sheet_name in _GLOBAL_CACHE:
                del _GLOBAL_CACHE[sheet_name]
            if sheet_name in _CACHE_EXPIRY:
                del _CACHE_EXPIRY[sheet_name]
        else:
            _GLOBAL_CACHE = {}
            _CACHE_EXPIRY = {}

# Singleton instance
sheets_repo = SheetsRepository()
