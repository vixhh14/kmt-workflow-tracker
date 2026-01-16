
import os
import uuid
import gspread
from typing import List, Dict, Any, Optional, Type
from app.services.google_sheets import google_sheets
from app.core.time_utils import get_current_time_ist

# Worksheet names as specified by user
SHEETS_SCHEMA = {
    "Projects": [
        "id", "project_name", "client_name", "project_code", 
        "is_deleted", "created_at", "updated_at"
    ],
    "Tasks": [
        "id", "title", "project_id", "assigned_to", "assigned_by", "status", 
        "priority", "due_datetime", "is_deleted", "created_at", "updated_at",
        "description", "part_item", "nos_unit", "machine_id", "started_at", 
        "completed_at", "total_duration_seconds", "hold_reason", "denial_reason", 
        "actual_start_time", "actual_end_time", "total_held_seconds", 
        "ended_by", "end_reason", "work_order_number", "expected_completion_time"
    ],
    "Users": [
        "id", "username", "role", "email", "active", "created_at",
        "password_hash", "full_name", "machine_types", "date_of_birth", "address", 
        "contact_number", "unit_id", "approval_status", "security_question", 
        "security_answer", "is_deleted", "updated_at"
    ],
    "Attendance": [
        "id", "date", "user_id", "status", "check_in", "check_out", "login_time", "ip_address", "is_deleted", "created_at", "updated_at"
    ],
    "FabricationTasks": [
        "id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "FilingTasks": [
        "id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "Machines": [
        "id", "machine_name", "status", "is_deleted", "hourly_rate", 
        "last_maintenance", "current_operator", "category_id", "unit_id", 
        "created_at", "updated_at"
    ],
    "TaskTimeLog": ["id", "task_id", "action", "timestamp", "reason", "is_deleted", "created_at", "updated_at"],
    "TaskHold": ["id", "task_id", "user_id", "hold_reason", "hold_started_at", "hold_ended_at", "is_deleted", "created_at", "updated_at"],
    "MachineRuntimeLog": ["id", "machine_id", "task_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "UserWorkLog": ["id", "user_id", "task_id", "machine_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "RescheduleRequests": ["id", "task_id", "new_date", "reason", "status", "created_at", "is_deleted", "updated_at"],
    "PlanningTasks": ["id", "title", "description", "status", "created_at", "is_deleted", "updated_at"]
}

# Mapping of Model names to Worksheet names for convenience
MODEL_MAP = {
    "Project": "Projects",
    "Task": "Tasks",
    "User": "Users",
    "Attendance": "Attendance",
    "FabricationTask": "FabricationTasks",
    "FilingTask": "FilingTasks",
    "Machine": "Machines",
    "TaskTimeLog": "TaskTimeLog",
    "TaskHold": "TaskHold",
    "MachineRuntimeLog": "MachineRuntimeLog",
    "UserWorkLog": "UserWorkLog",
    "RescheduleRequest": "RescheduleRequests",
    "PlanningTask": "PlanningTasks"
}

from app.repositories.sheets_repository import sheets_repo

class SheetRow:
    """A row proxy that tracks changes for later commit."""
    def __init__(self, data: Dict[str, Any], table_name: str, db=None):
        self._db = db
        self._data = data
        self._name = table_name
        self.__tablename__ = table_name
        self._dirty_fields = set()

    def __getattr__(self, key):
        if key in self._data:
            value = self._data[key]
            # Convert string boolean values to actual booleans
            if key in ['is_deleted', 'active']:
                if isinstance(value, str):
                    return value.upper() in ['TRUE', '1', 'YES']
                return bool(value)
            return value
        return None

    def __getitem__(self, key):
        return self._data.get(key)
    
    def __setitem__(self, key, value):
        self._data[key] = value
        self._dirty_fields.add(key)
        if self._db: self._db._mark_dirty(self)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            self._data[key] = value
            self._dirty_fields.add(key)
            if self._db: self._db._mark_dirty(self)

    def dict(self):
        return self._data

class QueryWrapper:
    def __init__(self, data: List[SheetRow], table_name: str):
        self._data = data
        self._table_name = table_name

    def filter(self, *args, **kwargs):
        filtered = list(self._data)
        
        # 1. Handle Keyword Filters (e.g., id=val, task_id=val)
        for key, value in kwargs.items():
            def match_kw(row, k, filter_val):
                # Use getattr to get coerced values (especially for booleans)
                row_val = getattr(row, k, None)
                
                if filter_val is None or str(filter_val).upper() in ["NONE", "NULL", ""]:
                    if k in ['is_deleted', 'active'] and not row_val: return True
                    return row_val is None or str(row_val).upper() in ["NONE", "NULL", ""]
                
                # Special boolean comparison
                if isinstance(filter_val, bool):
                    return bool(row_val) == filter_val
                
                return str(row_val) == str(filter_val)
            
            filtered = [row for row in filtered if match_kw(row, key, value)]
        
        # 2. Handle Positional Expression Filters (e.g., Task.id == val)
        for arg in args:
            arg_str = str(arg)
            if " == " in arg_str:
                parts = arg_str.split(" == ")
                left = parts[0].strip().split(".")[-1] 
                right = parts[1].strip().strip("'\"")
                
                def match_eq(row, l, r):
                    rv = getattr(row, l, None)
                    if r.lower() in ["none", "null", "false", "0"] and not rv: return True
                    if r.lower() == "true" and rv: return True
                    return str(rv) == str(r)
                filtered = [row for row in filtered if match_eq(row, left, right)]
            
            elif " != " in arg_str:
                parts = arg_str.split(" != ")
                left = parts[0].strip().split(".")[-1]
                right = parts[1].strip().strip("'\"")
                def match_neq(row, l, r):
                    rv = getattr(row, l, None)
                    if r.lower() in ["none", "null", "false", "0"] and rv: return True
                    return str(rv) != str(r)
                filtered = [row for row in filtered if match_neq(row, left, right)]

            elif "is_deleted" in arg_str.lower():
                is_false = "false" in arg_str.lower() or "none" in arg_str.lower() or "0" in arg_str.lower()
                filtered = [row for row in filtered if bool(getattr(row, "is_deleted", False)) != is_false]

        return QueryWrapper(filtered, self._table_name)

    def order_by(self, *args):
        # Implementation could sort rows here if needed
        return self

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
        # Use repository for cached data
        raw_data = sheets_repo.get_all(sheet_name, include_deleted=True)
        rows = [SheetRow(row, sheet_name, self) for row in raw_data]
        return QueryWrapper(rows, sheet_name)

    def add(self, obj):
        sheet_name = self._get_sheet_name(obj)
        data = obj.dict() if hasattr(obj, "dict") else obj
        if "__tablename__" in data:
            del data["__tablename__"]
        
        # Repository handles insertion and cache invalidation
        sheets_repo.insert(sheet_name, data)

    def commit(self):
        """Saves all dirty tracked rows."""
        for row in self._dirty_rows:
            sheet_name = row._name
            headers = SHEETS_SCHEMA.get(sheet_name, [])
            id_col = headers[0] if headers else "id"
            id_val = getattr(row, id_col)
            
            update_data = {f: getattr(row, f) for f in row._dirty_fields if f in headers}
            if update_data:
                # Repository handles update and cache invalidation
                sheets_repo.update(sheet_name, id_val, update_data)
        
        self._dirty_rows = []

    def delete(self, obj, soft=True):
        sheet_name = self._get_sheet_name(obj)
        headers = SHEETS_SCHEMA.get(sheet_name, [])
        id_col = headers[0] if headers else "id"
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

