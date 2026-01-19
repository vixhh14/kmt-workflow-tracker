
from typing import Dict, Any, List

# Worksheet names as specified by user - strictly canonical and locked
SHEETS_SCHEMA = {
    "users": [
        "user_id", "username", "role", "email", "active", "created_at", "password_hash"
    ],
    "machines": [
        "machine_id", "machine_name", "category", "unit", "status", 
        "created_at", "updated_at", "is_deleted"
    ],
    "attendance": [
        "attendance_id", "user_id", "date", "login_time", "logout_time", "status"
    ],
    "projects": [
        "id", "project_name", "client_name", "project_code", 
        "is_deleted", "created_at", "updated_at"
    ],
    "tasks": [
        "id", "title", "project_id", "assigned_to", "assigned_by", "status", 
        "priority", "due_datetime", "is_deleted", "created_at", "updated_at",
        "description", "part_item", "nos_unit", "machine_id", "started_at", 
        "completed_at", "total_duration_seconds", "hold_reason", "denial_reason", 
        "actual_start_time", "actual_end_time", "total_held_seconds", 
        "ended_by", "end_reason", "work_order_number", "expected_completion_time"
    ],
    "fabricationtasks": [
        "id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "filingtasks": [
        "id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "tasktimelog": ["id", "task_id", "action", "timestamp", "reason", "is_deleted", "created_at", "updated_at"],
    "taskhold": ["id", "task_id", "user_id", "hold_reason", "hold_started_at", "hold_ended_at", "is_deleted", "created_at", "updated_at"],
    "machineruntimelog": ["id", "machine_id", "task_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "userworklog": ["id", "user_id", "task_id", "machine_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "units": ["id", "name", "description", "created_at", "updated_at", "is_deleted"],
    "machinecategories": ["id", "name", "description", "created_at", "updated_at", "is_deleted"],
    "reschedulerequests": ["id", "task_id", "new_date", "reason", "status", "created_at", "is_deleted", "updated_at"],
    "planningtasks": ["id", "title", "description", "status", "created_at", "is_deleted", "updated_at"]
}

def normalize_row(sheet_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified normalization layer. Ensures all writes are schema-aligned.
    """
    if sheet_name not in SHEETS_SCHEMA:
        return data

    canonical_headers = SHEETS_SCHEMA[sheet_name]
    normalized = {}

    for header in canonical_headers:
        val = data.get(header, "")
        
        # 1. Trim strings
        if isinstance(val, str):
            val = val.strip()
        
        # 2. Standardize Booleans
        if header in ["active", "is_active", "is_deleted", "status"]:
             if isinstance(val, str):
                 low = val.lower()
                 if low in ["true", "1", "yes", "active"]: val = True
                 elif low in ["false", "0", "no", "inactive", ""]: val = False
             else:
                 val = bool(val)

        normalized[header] = val
        
    return normalized
