
import time
import uuid
import threading
from typing import List, Dict, Any, Optional
from app.services.google_sheets import google_sheets
from app.core.time_utils import get_current_time_ist

# Global cache to persist across requests but within process
# Thread-safe dictionary-based cache
_GLOBAL_CACHE = {}
_CACHE_EXPIRY = {}
_RAW_HEADERS = {} # Store actual sheet headers for mapping
_CACHE_LOCK = threading.Lock()
CACHE_TTL = 45  # Seconds (between 30-60 as requested)

class SheetsRepository:
    def __init__(self):
        pass

    def _get_sheet_data(self, sheet_name: str) -> List[Dict[str, Any]]:
        now = time.time()
        
        # Check if we have valid cache
        with _CACHE_LOCK:
            if sheet_name in _GLOBAL_CACHE and now < _CACHE_EXPIRY.get(sheet_name, 0):
                return _GLOBAL_CACHE[sheet_name]

        # Cache expired or missing, refresh it
        try:
            # One bulk read per sheet
            data = google_sheets.read_all_bulk(sheet_name)
            
            # Extract raw headers for mapping
            raw_headers = []
            if data:
                first = data[0]
                # Filter out internal keys like _row_idx, etc.
                raw_headers = [v for k, v in first.items() if k.startswith("_orig_")]
            
            with _CACHE_LOCK:
                _GLOBAL_CACHE[sheet_name] = data
                _CACHE_EXPIRY[sheet_name] = now + CACHE_TTL
                if raw_headers:
                    _RAW_HEADERS[sheet_name] = raw_headers
                else:
                    # Fallback if sheet is empty but we need headers
                    # This might happen on first run with empty sheet
                    try:
                        worksheet = google_sheets.get_worksheet(sheet_name)
                        _RAW_HEADERS[sheet_name] = worksheet.row_values(1)
                    except:
                        pass
                print(f"🔄 [SheetsRepo] Cache Refreshed: {sheet_name} ({len(data)} rows)")
            return data
        except Exception as e:
            print(f"❌ [SheetsRepo] Failed to fetch {sheet_name}: {e}")
            with _CACHE_LOCK:
                # Fallback to expired cache if available
                if sheet_name in _GLOBAL_CACHE:
                    return _GLOBAL_CACHE[sheet_name]
                return []

    def get_cached_records(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Implementation of mandatory task: Reads entire worksheet from cache."""
        return self.get_all(sheet_name)

    def get_headers(self, sheet_name: str) -> List[str]:
        """Returns normalized headers for the sheet."""
        # Using a fixed mapping or fetching from raw headers
        raw = self.get_raw_headers(sheet_name)
        return [google_sheets._normalize_header(h) for h in raw]

    def get_all(self, sheet_name: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Returns all rows from a sheet from cache, optionally filtering deleted ones."""
        data = self._get_sheet_data(sheet_name)
        
        # Always return deep copies to prevent external modification of cache
        if include_deleted:
            return [dict(row) for row in data]
        
        # Filter is_deleted
        return [
            dict(row) for row in data 
            if str(row.get("is_deleted", "")).upper() not in ["TRUE", "1", "YES"]
        ]

    def get_by_id(self, sheet_name: str, id_value: Any) -> Optional[Dict[str, Any]]:
        """Finds a single row by its ID from cached data."""
        data = self._get_sheet_data(sheet_name)
        # Try 'id' first, then any key ending in '_id'
        headers = self.get_headers(sheet_name)
        id_col = "id"
        if "id" not in headers:
            for h in headers:
                if h.endswith("_id"):
                    id_col = h
                    break

        for row in data:
            if str(row.get(id_col)) == str(id_value):
                return dict(row)
        return None

    def get_raw_headers(self, sheet_name: str) -> List[str]:
        """Returns the actual raw headers from the sheet from cache."""
        with _CACHE_LOCK:
            if sheet_name in _RAW_HEADERS:
                return list(_RAW_HEADERS[sheet_name])
        
        # Fallback: trigger a read to get headers
        self._get_sheet_data(sheet_name)
        with _CACHE_LOCK:
            return list(_RAW_HEADERS.get(sheet_name, []))

    def insert(self, sheet_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts a new row, updates Sheets, and updates cache immediately."""
        headers = self.get_headers(sheet_name)
        raw_headers = self.get_raw_headers(sheet_name)
        
        # Identify ID column
        id_col = "id"
        if "id" not in headers:
            for h in headers:
                if h.endswith("_id"):
                    id_col = h
                    break
        
        # Ensure default fields
        if id_col not in data or not data[id_col]:
            data[id_col] = str(uuid.uuid4())
            
        now_ist = get_current_time_ist().isoformat()
        if "created_at" not in data or not data["created_at"]:
            data["created_at"] = now_ist
        if "updated_at" not in data or not data["updated_at"]:
            data["updated_at"] = now_ist
        if "is_deleted" not in data:
            data["is_deleted"] = False

        # 1. Update Sheets
        success = google_sheets.insert_row(sheet_name, data, raw_headers)
        
        if success:
            # 2. Update Cache immediately (add to end)
            with _CACHE_LOCK:
                if sheet_name in _GLOBAL_CACHE:
                    # Determine new row index
                    max_idx = 1
                    for r in _GLOBAL_CACHE[sheet_name]:
                        if r.get("_row_idx", 0) > max_idx:
                            max_idx = r["_row_idx"]
                    
                    data_with_idx = dict(data)
                    data_with_idx["_row_idx"] = max_idx + 1
                    # Add original headers mapping for consistency
                    for h, rh in zip(headers, raw_headers):
                        data_with_idx[f"_orig_{h}"] = rh
                        
                    _GLOBAL_CACHE[sheet_name].append(data_with_idx)
                    print(f"✅ [SheetsRepo] Cache Updated (Insert): {sheet_name}")
                else:
                    # If cache was empty, might as well trigger a reload
                    # to ensure everything is set up correctly
                    self.clear_cache(sheet_name)
        
        return data

    def update(self, sheet_name: str, id_value: Any, data: Dict[str, Any]) -> bool:
        """Updates a row, updates Sheets, and updates cache immediately."""
        if not id_value: return False
            
        headers = self.get_headers(sheet_name)
        raw_headers = self.get_raw_headers(sheet_name)
        
        id_col = "id"
        if "id" not in headers:
            for h in headers:
                if h.endswith("_id"):
                    id_col = h
                    break
        
        # Find the record in cache to get _row_idx
        cached_row = None
        cached_idx_in_list = -1
        
        with _CACHE_LOCK:
            if sheet_name in _GLOBAL_CACHE:
                for i, row in enumerate(_GLOBAL_CACHE[sheet_name]):
                    if str(row.get(id_col)) == str(id_value):
                        cached_row = row
                        cached_idx_in_list = i
                        break
        
        if not cached_row:
            print(f"⚠️ [SheetsRepo] Update failed: Record {id_value} not found in cache for {sheet_name}")
            return False

        row_idx = cached_row.get("_row_idx")
        if not row_idx: return False

        # Prepare update data
        update_payload = dict(data)
        if "updated_at" not in update_payload:
            update_payload["updated_at"] = get_current_time_ist().isoformat()

        # 1. Update Sheets
        success = google_sheets.update_row_by_idx(sheet_name, row_idx, update_payload, raw_headers)
        
        if success:
            # 2. Update Cache immediately
            with _CACHE_LOCK:
                if sheet_name in _GLOBAL_CACHE and cached_idx_in_list != -1:
                    for k, v in update_payload.items():
                        _GLOBAL_CACHE[sheet_name][cached_idx_in_list][k] = v
                    print(f"✅ [SheetsRepo] Cache Updated (Update): {sheet_name} row {row_idx}")
        return success

    def batch_append(self, sheet_name: str, rows: List[Dict[str, Any]]) -> bool:
        """Updates multiple rows to Sheets and refreshes cache."""
        raw_headers = self.get_raw_headers(sheet_name)
        success = google_sheets.batch_append(sheet_name, rows, raw_headers)
        if success:
            self.clear_cache(sheet_name) # Easier to reload for batch
        return success

    def batch_update(self, sheet_name: str, updates: List[Dict[str, Any]]) -> bool:
        """Updates multiple rows to Sheets and refreshes cache."""
        raw_headers = self.get_raw_headers(sheet_name)
        success = google_sheets.batch_update(sheet_name, updates, raw_headers)
        if success:
            self.clear_cache(sheet_name) # Reload for batch consistency
        return success

    def soft_delete(self, sheet_name: str, id_value: Any) -> bool:
        """Sets is_deleted=True for a row."""
        return self.update(sheet_name, id_value, {"is_deleted": True})

    def hard_delete(self, sheet_name: str, id_value: Any) -> bool:
        """Physically removes a row and synchronizes cache."""
        if not id_value: return False
            
        headers = self.get_headers(sheet_name)
        id_col = "id"
        if "id" not in headers:
            for h in headers:
                if h.endswith("_id"):
                    id_col = h
                    break
        
        cached_idx_in_list = -1
        row_idx = -1
        
        with _CACHE_LOCK:
            if sheet_name in _GLOBAL_CACHE:
                for i, row in enumerate(_GLOBAL_CACHE[sheet_name]):
                    if str(row.get(id_col)) == str(id_value):
                        row_idx = row.get("_row_idx", -1)
                        cached_idx_in_list = i
                        break
        
        if row_idx == -1: return False

        # 1. Update Sheets
        success = google_sheets.delete_row_by_idx(sheet_name, row_idx)
        
        if success:
            # 2. Update Cache immediately - Removal requires re-index or clearing
            self.clear_cache(sheet_name)
            print(f"🗑️ [SheetsRepo] Hard deleted {id_value} from {sheet_name}. Cache cleared.")
        return success

    def clear_cache(self, sheet_name: Optional[str] = None):
        """Clears cache for one or all sheets."""
        with _CACHE_LOCK:
            if sheet_name:
                if sheet_name in _GLOBAL_CACHE:
                    del _GLOBAL_CACHE[sheet_name]
                if sheet_name in _CACHE_EXPIRY:
                    del _CACHE_EXPIRY[sheet_name]
            else:
                _GLOBAL_CACHE.clear()
                _CACHE_EXPIRY.clear()

# Singleton instance
sheets_repo = SheetsRepository()
