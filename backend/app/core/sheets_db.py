
import os
import uuid
import gspread
from typing import List, Dict, Any, Optional, Type
from app.services.google_sheets import google_sheets
from app.core.time_utils import get_current_time_ist

# Worksheet names as specified by user
SHEETS_SCHEMA = {
    "Projects": [
        "project_id", "project_name", "client_name", "project_code", 
        "work_order_number", "is_deleted", "created_at"
    ],
    "Tasks": [
        "id", "title", "description", "project", "project_id", "part_item", 
        "nos_unit", "status", "priority", "assigned_to", "machine_id", 
        "assigned_by", "due_date", "is_deleted", "created_at", "started_at", 
        "completed_at", "total_duration_seconds", "hold_reason", "denial_reason", 
        "actual_start_time", "actual_end_time", "total_held_seconds", 
        "ended_by", "end_reason", "work_order_number", "expected_completion_time"
    ],
    "Users": [
        "user_id", "username", "password_hash", "role", "email", 
        "full_name", "machine_types", "date_of_birth", "address", 
        "contact_number", "unit_id", "approval_status", "security_question", 
        "security_answer", "is_deleted", "active", "created_at", "updated_at"
    ],
    "Attendance": [
        "id", "user_id", "date", "check_in", "check_out", "login_time", "status", "ip_address"
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
        "id", "machine_name", "status", "hourly_rate", "last_maintenance", 
        "current_operator", "category_id", "unit_id", "is_deleted", "created_at", "updated_at"
    ],
    "TaskTimeLog": ["id", "task_id", "action", "timestamp", "reason"],
    "TaskHold": ["id", "task_id", "user_id", "hold_reason", "hold_started_at", "hold_ended_at"],
    "MachineRuntimeLog": ["id", "machine_id", "task_id", "start_time", "end_time", "duration_seconds", "date"],
    "UserWorkLog": ["id", "user_id", "task_id", "machine_id", "start_time", "end_time", "duration_seconds", "date"],
    "RescheduleRequests": ["id", "task_id", "new_date", "reason", "status", "created_at"],
    "PlanningTasks": ["id", "title", "description", "status", "created_at"]
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
            return self._data[key]
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
        
        # Keyword filters
        for key, value in kwargs.items():
            filtered = [row for row in filtered if str(row.dict().get(key)) == str(value)]
        
        # Positional filters (Simplified SQLAlchemy-like Expr mapping)
        for arg in args:
            arg_str = str(arg)
            if "is_deleted" in arg_str:
                if "False" in arg_str or "false" in arg_str or "NULL" in arg_str:
                    filtered = [row for row in filtered if str(row.dict().get("is_deleted")).upper() in ["FALSE", "0", "", "NONE", "NULL"]]
                elif "True" in arg_str or "true" in arg_str:
                    filtered = [row for row in filtered if str(row.dict().get("is_deleted")).upper() in ["TRUE", "1"]]
            
        return QueryWrapper(filtered, self._table_name)

    def order_by(self, *args):
        return self

    def first(self) -> Optional[SheetRow]:
        return self._data[0] if self._data else None

    def all(self) -> List[SheetRow]:
        return self._data

    def count(self) -> int:
        return len(self._data)

class SheetsDB:
    def __init__(self):
        self._cache = {}
        self._dirty_rows = []

    def _get_sheet_name(self, model):
        # Handle class name, instance name, or raw string
        name = model.__name__ if hasattr(model, "__name__") else str(model)
        if hasattr(model, "__tablename__"):
            name = model.__tablename__
        
        # Map to specific user casing
        return MODEL_MAP.get(name, name)

    def _mark_dirty(self, row: SheetRow):
        if row not in self._dirty_rows:
            self._dirty_rows.append(row)

    def _get_data(self, model) -> List[SheetRow]:
        sheet_name = self._get_sheet_name(model)
        if sheet_name not in self._cache:
            raw_data = google_sheets.read_all(sheet_name)
            self._cache[sheet_name] = [SheetRow(row, sheet_name, self) for row in raw_data]
        return self._cache[sheet_name]

    def query(self, model) -> QueryWrapper:
        return QueryWrapper(self._get_data(model), self._get_sheet_name(model))

    def add(self, obj):
        sheet_name = self._get_sheet_name(obj)
        data = obj.dict() if hasattr(obj, "dict") else obj
        # Remove __tablename__ if it exists in data
        if "__tablename__" in data:
            del data["__tablename__"]
            
        google_sheets.insert_row(sheet_name, data)
        # Invalidate cache
        if sheet_name in self._cache:
            del self._cache[sheet_name]

    def commit(self):
        """Saves all dirty tracked rows."""
        for row in self._dirty_rows:
            sheet_name = row._name
            headers = SHEETS_SCHEMA.get(sheet_name, [])
            id_col = headers[0] if headers else "id"
            id_val = getattr(row, id_col)
            
            # Pack dirty data
            update_data = {f: getattr(row, f) for f in row._dirty_fields if f in headers}
            if update_data:
                google_sheets.update_row(sheet_name, id_val, update_data)
        
        self._dirty_rows = []

    def delete(self, obj, soft=True):
        sheet_name = self._get_sheet_name(obj)
        headers = SHEETS_SCHEMA.get(sheet_name, [])
        id_col = headers[0] if headers else "id"
        id_val = getattr(obj, id_col) or obj.get(id_col)
        
        if soft:
            google_sheets.soft_delete_row(sheet_name, id_val)
        else:
            google_sheets.hard_delete_row(sheet_name, id_val)
            
        if sheet_name in self._cache:
            del self._cache[sheet_name]

    def rollback(self):
        self._dirty_rows = []

    def refresh(self, obj):
        pass

# Dependency injection for FastAPI
def get_sheets_db():
    return SheetsDB()
