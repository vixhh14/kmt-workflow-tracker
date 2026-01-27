
from typing import Dict, Any, List

# Worksheet names as specified by user - strictly canonical and locked
SHEETS_SCHEMA = {
    "users": [
        "user_id", "username", "role", "email", "active", "created_at", "password_hash", 
        "approval_status", "full_name", "unit_id", "machine_types", "contact_number", "updated_at", "is_deleted"
    ],
    "machines": [
        "machine_id", "machine_name", "category", "unit", "status", 
        "created_at", "updated_at", "is_deleted"
    ],
    "attendance": [
        "attendance_id", "user_id", "date", "login_time", "logout_time", "status"
    ],
    "projects": [
        "project_id", "project_name", "client_name", "project_code", 
        "is_deleted", "created_at", "updated_at", "work_order_number"
    ],
    "tasks": [
        "task_id", "title", "project_id", "assigned_to", "assigned_by", "status", 
        "priority", "due_datetime", "is_deleted", "created_at", "updated_at",
        "description", "part_item", "nos_unit", "machine_id", "started_at", 
        "completed_at", "total_duration_seconds", "hold_reason", "denial_reason", 
        "actual_start_time", "actual_end_time", "total_held_seconds", 
        "ended_by", "end_reason", "work_order_number", "expected_completion_time",
        "project", "due_date"
    ],
    "fabricationtasks": [
        "fabrication_task_id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "filingtasks": [
        "filing_task_id", "project_id", "part_item", "quantity", "due_date", "priority", 
        "assigned_to", "completed_quantity", "remarks", "status", "machine_id", 
        "work_order_number", "assigned_by", "is_deleted", "started_at", 
        "on_hold_at", "resumed_at", "completed_at", "total_active_duration", 
        "created_at", "updated_at"
    ],
    "tasktimelog": ["log_id", "task_id", "action", "timestamp", "reason", "is_deleted", "created_at", "updated_at"],
    "taskhold": ["hold_id", "task_id", "user_id", "hold_reason", "hold_started_at", "hold_ended_at", "is_deleted", "created_at", "updated_at"],
    "machineruntimelog": ["log_id", "machine_id", "task_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "userworklog": ["log_id", "user_id", "task_id", "machine_id", "start_time", "end_time", "duration_seconds", "date", "is_deleted", "created_at", "updated_at"],
    "units": ["unit_id", "name", "description", "created_at", "updated_at", "is_deleted", "status"],
    "machinecategories": ["category_id", "name", "description", "created_at", "updated_at", "is_deleted", "status"],
    "reschedulerequests": ["reschedule_id", "task_id", "new_date", "reason", "status", "created_at", "is_deleted", "updated_at"],
    "planningtasks": ["planning_task_id", "title", "description", "status", "created_at", "is_deleted", "updated_at"],
    "subtasks": ["id", "task_id", "title", "status", "notes", "created_at", "updated_at", "is_deleted"]
}

def normalize_row(sheet_name: str, data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    """
    Unified normalization layer. Ensures all writes are schema-aligned.
    If 'partial' is True, only headers present in 'data' are processed and returned.
    """
    if sheet_name not in SHEETS_SCHEMA:
        return data

    canonical_headers = SHEETS_SCHEMA[sheet_name]
    normalized = {}

    for header in canonical_headers:
        if partial and header not in data:
            continue
            
        val = data.get(header, "")
        
        # 1. Trim strings
        if isinstance(val, str):
            val = val.strip()
        
        # 2. Standardize Booleans (ONLY for explicit boolean fields)
        if header in ["active", "is_active", "is_deleted"]:
             if isinstance(val, str):
                 low = val.lower()
                 if low in ["true", "1", "yes"]: val = True
                 elif low in ["false", "0", "no", ""]: val = False
             else:
                 val = bool(val)

        normalized[header] = val
        
    # CRITICAL: Preserve metadata keys (starting with _) like _row_idx
    # These are NOT in SHEETS_SCHEMA but are required for repository core logic
    for k, v in data.items():
        if k.startswith("_"):
            normalized[k] = v

    return normalized
