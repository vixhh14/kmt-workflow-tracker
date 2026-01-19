
import os
import uuid
import gspread
from typing import List, Dict, Any, Optional, Type
from app.services.google_sheets import google_sheets
from app.core.time_utils import get_current_time_ist

from app.core.sheets_config import SHEETS_SCHEMA, normalize_row

# Mapping of Model names to Worksheet names for convenience
MODEL_MAP = {
    "Project": "projects",
    "Task": "tasks",
    "User": "users",
    "Attendance": "attendance",
    "FabricationTask": "fabricationtasks",
    "FilingTask": "filingtasks",
    "Machine": "machines",
    "TaskTimeLog": "tasktimelog",
    "TaskHold": "taskhold",
    "MachineRuntimeLog": "machineruntimelog",
    "UserWorkLog": "userworklog",
    "RescheduleRequest": "reschedulerequests",
    "PlanningTask": "planningtasks",
    "Unit": "units",
    "MachineCategory": "machinecategories"
}

from app.repositories.sheets_repository import sheets_repo

class SheetRow:
    """A row proxy that tracks changes for later commit."""
    def __init__(self, data: Dict[str, Any], table_name: str, db=None):
        self._db = db
        # Trim all string values immediately on load
        self._data = {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}
        self._name = table_name.lower()
        self.__tablename__ = table_name.lower()
        self._dirty_fields = set()

    def __getattr__(self, key):
        # 1. Exact match
        if key in self._data:
            value = self._data[key]
            if isinstance(value, str):
                low_val = value.lower()
                if low_val in ['true', '1', 'yes']: return True
                if low_val in ['false', '0', 'no', '']: return False
            return value
        
        # 2. Aliases for common keys
        aliases = {
            "id": ["user_id", "machine_id", "task_id", "project_id"],
            "password_hash": ["password"],
            "active": ["is_active"],
            "is_active": ["active"]
        }
        
        # Check if the requested key is a core key with potential aliases in data
        for core, alt_list in aliases.items():
            if key == core:
                for alt in alt_list:
                    if alt in self._data: return self.__getattr__(alt)
            if key in alt_list:
                if core in self._data: return self.__getattr__(core)

        # 3. Special case for generic 'id' and legacy names
        prefix = self._name.lower()
        if prefix.endswith('s'): prefix = prefix[:-1]
        legacy_id_key = f"{prefix}_id"
        
        if key == 'id':
            if legacy_id_key in self._data: return self._data[legacy_id_key]
        if key == legacy_id_key:
            if 'id' in self._data: return self._data['id']
            
        return None


    def __getitem__(self, key):
        return self.__getattr__(key)
    
    def __setitem__(self, key, value):
        self._data[key] = value
        self._dirty_fields.add(key)
        if self._db: self._db._mark_dirty(self)

    def __setattr__(self, key, value):
        if key.startswith("_") or key == "__tablename__":
            super().__setattr__(key, value)
        else:
            self._data[key] = value
            self._dirty_fields.add(key)
            if self._db: self._db._mark_dirty(self)

    def dict(self):
        d = dict(self._data)
        # Ensure 'id' is present for frontend compatibility
        if 'id' not in d:
            d['id'] = self.__getattr__('id')
        return d

class QueryWrapper:
    def __init__(self, data: List[SheetRow], table_name: str):
        self._data = data
        self._table_name = table_name

    def filter(self, *args, **kwargs):
        filtered = list(self._data)
        
        # 1. Handle Keyword Filters
        for key, value in kwargs.items():
            def match_kw(row, k, filter_val):
                row_val = getattr(row, k, None)
                
                if row_val is None:
                     return filter_val is None or str(filter_val).upper() in ["NONE", "NULL", ""]

                if filter_val is None or str(filter_val).upper() in ["NONE", "NULL", ""]:
                    return row_val is None or str(row_val).upper() in ["NONE", "NULL", ""]
                
                if isinstance(filter_val, bool):
                    if isinstance(row_val, str):
                        low = row_val.lower()
                        row_val = low in ['true', '1', 'yes']
                    return bool(row_val) == filter_val
                
                return str(row_val) == str(filter_val)
            
            filtered = [row for row in filtered if match_kw(row, key, value)]
        
        # 2. Handle Positional Expression Filters
        for arg in args:
            arg_str = str(arg)
            if " == " in arg_str:
                parts = arg_str.split(" == ")
                left = parts[0].strip().split(".")[-1] 
                right = parts[1].strip().strip("'\"")
                filtered = [row for row in filtered if str(getattr(row, left, None)) == str(right)]
            elif " != " in arg_str:
                parts = arg_str.split(" != ")
                left = parts[0].strip().split(".")[-1]
                right = parts[1].strip().strip("'\"")
                filtered = [row for row in filtered if str(getattr(row, left, None)) != str(right)]
            elif "is_deleted" in arg_str.lower():
                is_false = "false" in arg_str.lower()
                filtered = [row for row in filtered if bool(getattr(row, "is_deleted", False)) != is_false]
            elif "is_active" in arg_str.lower() or "active" in arg_str.lower():
                is_true = "true" in arg_str.lower()
                # Check both aliases
                filtered = [row for row in filtered if bool(getattr(row, "active", True)) == is_true]

        return QueryWrapper(filtered, self._table_name)

    def first(self) -> Optional[SheetRow]:
        return self._data[0] if self._data else None

    def all(self) -> List[SheetRow]:
        return self._data

    def count(self) -> int:
        return len(self._data)

class SheetsDB:
    def __init__(self):
        self._dirty_rows = []

    def _get_sheet_name(self, model):
        if isinstance(model, str):
            return MODEL_MAP.get(model, model)
        name = model.__name__ if hasattr(model, "__name__") else str(model)
        if hasattr(model, "__tablename__"):
            name = model.__tablename__
        return MODEL_MAP.get(name, name)

    def _mark_dirty(self, row: SheetRow):
        if row not in self._dirty_rows:
            self._dirty_rows.append(row)

    def query(self, model) -> QueryWrapper:
        sheet_name = self._get_sheet_name(model)
        raw_data = sheets_repo.get_all(sheet_name, include_deleted=True)
        rows = [SheetRow(row, sheet_name, self) for row in raw_data]
        return QueryWrapper(rows, sheet_name)

    def add(self, obj):
        sheet_name = self._get_sheet_name(obj)
        data = obj.dict() if hasattr(obj, "dict") else obj
        if "__tablename__" in data: del data["__tablename__"]
        sheets_repo.insert(sheet_name, data)

    def commit(self):
        """Batch-updates all dirty tracked rows to minimize API calls."""
        if not self._dirty_rows: return
        
        # Group by sheet
        by_sheet = {}
        for row in self._dirty_rows:
            if row._name not in by_sheet: by_sheet[row._name] = []
            by_sheet[row._name].append(row)
        
        for sheet_name, rows in by_sheet.items():
            if not rows: continue
            
            headers = sheets_repo.get_headers(sheet_name)
            id_col = "id"
            if "id" not in headers:
                for h in headers:
                    if h.endswith("_id"):
                        id_col = h
                        break
            
            updates = []
            for row in rows:
                id_val = getattr(row, id_col)
                # Build update dict with internal row index
                update_entry = {"_row_idx": row._data.get("_row_idx")}
                for f in row._dirty_fields:
                    if f in headers or f == id_col:
                        update_entry[f] = getattr(row, f)
                
                # Always sync updated_at
                update_entry["updated_at"] = get_current_time_ist().isoformat()
                updates.append(update_entry)
            
            if updates:
                sheets_repo.batch_update(sheet_name, updates)
        
        self._dirty_rows = []

    def delete(self, obj, soft=True):
        sheet_name = self._get_sheet_name(obj)
        headers = sheets_repo.get_headers(sheet_name)
        id_col = "id"
        if "id" not in headers:
            for h in headers:
                if h.endswith("_id"):
                    id_col = h
                    break
        id_val = getattr(obj, id_col) if hasattr(obj, id_col) else obj.get(id_col)
        
        if soft:
            sheets_repo.soft_delete(sheet_name, id_val)
        else:
            sheets_repo.hard_delete(sheet_name, id_val)

    def rollback(self):
        self._dirty_rows = []

    def refresh(self, obj):
        pass

def get_sheets_db():
    return SheetsDB()

def verify_sheets_structure():
    """
    Mandatory startup verification: Perform strict header validation.
    Refuses to start if schemas do not match.
    """
    print("[Startup] Verifying Google Sheets structure (STRICT MODE)...")
    try:
        errs = []
        for sheet_name, expected_headers in SHEETS_SCHEMA.items():
            print(f"  Checking {sheet_name}...")
            try:
                # 1. Ensure sheet exists
                worksheet = google_sheets.get_worksheet(sheet_name)
                
                # 2. Validate Headers
                all_vals = worksheet.get_all_values()
                actual_headers = all_vals[0] if all_vals else []
                
                # Compare only the count of columns requested at minimum
                # OR do exact match of first N columns
                match = True
                if len(actual_headers) < len(expected_headers):
                    match = False
                else:
                    for i, h in enumerate(expected_headers):
                        if actual_headers[i].strip().lower() != h.strip().lower():
                            match = False
                            break
                
                if not match:
                    err_msg = f"❌ Header mismatch for '{sheet_name}'. Expected: {expected_headers}, Found: {actual_headers[:len(expected_headers)]}"
                    print(err_msg)
                    errs.append(err_msg)
            except Exception as e:
                if "WorksheetNotFound" in str(e):
                    # One-time auto-creation is allowed if missing completely
                    print(f"  ⚡ Sheet {sheet_name} missing. Creating with canonical headers...")
                    google_sheets.ensure_worksheet(sheet_name, expected_headers)
                else:
                    errs.append(f"Failed to verify {sheet_name}: {e}")

        if errs:
              print("\n🔴 CRITICAL SCHEMA ERRORS DETECTED. PREVENTING STARTUP.")
              for e in errs: print(f" - {e}")
              raise RuntimeError("Startup failed due to Google Sheets schema drift. Please repair headers manually.")

        # 2. Trigger a Bootstrap Batch Read to pre-warm the cache
        print("[Startup] Pre-warming Cache via Bootstrap...")
        sheets_repo.get_all("machines", include_deleted=True) 
        
        print("[Startup] All required sheets verified, accessible, and cached.")
    except RuntimeError: raise
    except Exception as e:
        print(f"❌ [Startup] Critical Error verifying sheets: {e}")
        raise RuntimeError(f"Startup failed: Google Sheets structure is invalid or inaccessible: {e}")

