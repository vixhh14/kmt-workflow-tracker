"""
Global Data Normalizer for Google Sheets
Ensures ALL data from Sheets is properly typed and validated before response serialization
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def safe_str(value: Any, default: str = "") -> str:
    """Convert any value to string safely"""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).strip()

def safe_int(value: Any, default: int = 0) -> int:
    """Convert any value to int safely"""
    if value is None or value == "" or value == "None":
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert any value to float safely"""
    if value is None or value == "" or value == "None":
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value: Any, default: bool = False) -> bool:
    """Convert any value to bool safely"""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 't', 'y']
    return bool(value)

def safe_datetime(value: Any, default: Optional[str] = None) -> Optional[str]:
    """Convert any value to ISO datetime string safely"""
    if value is None or value == "" or value == "None":
        return default
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        # Already a string, return as-is if looks like datetime
        if 'T' in value or '-' in value:
            return value
    return default

def normalize_status(value: Any) -> str:
    """Normalize status field - CRITICAL for boolean->string conversion"""
    if value is None or value == "":
        return "pending"
    
    # Handle boolean values from Sheets
    if isinstance(value, bool):
        return "active" if value else "inactive"
    
    # Handle string values
    value_str = str(value).lower().strip()
    
    # Map common variations
    status_map = {
        'true': 'active',
        'false': 'inactive',
        '1': 'active',
        '0': 'inactive',
        'yes': 'active',
        'no': 'inactive',
    }
    
    if value_str in status_map:
        return status_map[value_str]
    
    # Valid status values
    valid_statuses = ['pending', 'in_progress', 'completed', 'on_hold', 'denied', 'ended', 'active', 'inactive']
    
    if value_str in valid_statuses:
        return value_str
    
    # Default
    return "pending"

def normalize_priority(value: Any) -> str:
    """Normalize priority field"""
    if value is None or value == "":
        return "MEDIUM"
    
    value_str = str(value).upper().strip()
    
    valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
    
    if value_str in valid_priorities:
        return value_str
    
    # Map variations
    if value_str in ['CRITICAL', 'ASAP']:
        return 'HIGH'
    
    return "MEDIUM"

def generate_title(row: Dict[str, Any]) -> str:
    """Generate a safe title from row data - NEVER return empty"""
    # Try explicit title field
    if row.get('title') and str(row.get('title')).strip():
        return str(row['title']).strip()
    
    # Try part_item (but ignore if it looks like a date)
    part = str(row.get('part_item', '')).strip()
    if part and not part.startswith('202') and 'T' not in part:
         return part

    # Try work_order_number
    if row.get('work_order_number') and str(row.get('work_order_number')).strip():
        return f"WO-{row['work_order_number']}"
    
    # Try description
    desc = str(row.get('description', '')).strip()
    if desc:
        return desc[:50] + "..." if len(desc) > 50 else desc
    
    # Try task_id or filing_task_id
    task_id = row.get('task_id') or row.get('filing_task_id') or row.get('fabrication_task_id')
    if task_id and str(task_id).strip():
        return f"Task-{str(task_id)[:8]}"
    
    # Last resort
    return "Untitled Task"

def normalize_task_row(row: Dict[str, Any], task_type: str = "general") -> Dict[str, Any]:
    """
    Normalize a task row from Google Sheets
    CRITICAL: Ensures ALL required fields exist with correct types
    """
    
    # Determine task_id (handle all task types)
    task_id = (
        row.get('task_id') or 
        row.get('filing_task_id') or 
        row.get('fabrication_task_id') or 
        row.get('id') or 
        ""
    )
    
    # HEURISTIC: Fix shifted headers (Date in Part Item)
    part_val = safe_str(row.get('part_item'), "")
    due_val = safe_datetime(row.get('due_date') or row.get('due_datetime'))
    
    # If part_item looks like a date and due_date is missing, move it
    if not due_val and (part_val.startswith('202') or 'T' in part_val):
        due_val = part_val
        part_val = "" # Clear it from part_item
    
    normalized = {
        # REQUIRED FIELDS - MUST ALWAYS EXIST
        'task_id': safe_str(task_id, "unknown"),
        'id': safe_str(task_id, "unknown"),
        'title': generate_title(row),
        'status': normalize_status(row.get('status')),
        'priority': normalize_priority(row.get('priority')),
        
        # NUMERIC FIELDS - NEVER empty string
        'total_active_duration': safe_int(row.get('total_active_duration'), 0),
        'total_duration_seconds': safe_int(row.get('total_duration_seconds'), 0),
        'total_held_seconds': safe_int(row.get('total_held_seconds'), 0),
        'expected_completion_time': safe_int(row.get('expected_completion_time'), 0),
        'quantity': safe_int(row.get('quantity'), 1),
        'completed_quantity': safe_int(row.get('completed_quantity'), 0),
        
        # DATETIME FIELDS - ISO format or None
        'created_at': safe_datetime(row.get('created_at')),
        'updated_at': safe_datetime(row.get('updated_at')),
        'due_date': due_val,
        'started_at': safe_datetime(row.get('started_at')),
        'completed_at': safe_datetime(row.get('completed_at')),
        'on_hold_at': safe_datetime(row.get('on_hold_at')),
        'resumed_at': safe_datetime(row.get('resumed_at')),
        'actual_start_time': safe_datetime(row.get('actual_start_time')),
        'actual_end_time': safe_datetime(row.get('actual_end_time')),
        
        # STRING FIELDS - safe defaults
        'description': safe_str(row.get('description'), ""),
        'project': safe_str(row.get('project'), ""),
        'project_id': safe_str(row.get('project_id'), ""),
        'part_item': (lambda x: "" if x.startswith('202') or 'T' in x else x)(part_val),
        'nos_unit': safe_str(row.get('nos_unit'), ""),
        'work_order_number': safe_str(row.get('work_order_number'), ""),
        'assigned_to': (lambda x: "" if x in ["HMT", "hmt"] or x.startswith("PROJ-") else x)(safe_str(row.get('assigned_to'), "")),
        'assigned_by': safe_str(row.get('assigned_by'), ""),
        'machine_id': safe_str(row.get('machine_id'), ""),
        'hold_reason': safe_str(row.get('hold_reason'), ""),
        'denial_reason': safe_str(row.get('denial_reason'), ""),
        'end_reason': safe_str(row.get('end_reason'), ""),
        'ended_by': safe_str(row.get('ended_by'), ""),
        'remarks': safe_str(row.get('remarks'), ""),
        
        # BOOLEAN FIELDS - proper bool
        'is_deleted': safe_bool(row.get('is_deleted'), False),
    }
    
    # Add task-type specific IDs
    if task_type == "filing":
        normalized['filing_task_id'] = safe_str(task_id, "")
    elif task_type == "fabrication":
        normalized['fabrication_task_id'] = safe_str(task_id, "")
    
    return normalized

def normalize_project_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a project row from Google Sheets"""
    
    project_id = row.get('project_id') or row.get('id') or ""
    
    return {
        'project_id': safe_str(project_id, "unknown"),
        'id': safe_str(project_id, "unknown"),
        'project_name': safe_str(row.get('project_name'), "Unnamed Project"),
        'project_code': safe_str(row.get('project_code'), ""),
        'client_name': safe_str(row.get('client_name'), ""),
        'description': safe_str(row.get('description'), ""),
        'status': normalize_status(row.get('status')),
        'is_deleted': safe_bool(row.get('is_deleted'), False),
        'created_at': safe_datetime(row.get('created_at')),
        'updated_at': safe_datetime(row.get('updated_at')),
    }

def normalize_user_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a user row from Google Sheets"""
    
    user_id = row.get('user_id') or row.get('id') or ""
    
    return {
        'user_id': safe_str(user_id, "unknown"),
        'id': safe_str(user_id, "unknown"),
        'username': safe_str(row.get('username'), "unknown"),
        'email': safe_str(row.get('email'), ""),
        'role': safe_str(row.get('role'), "operator").lower(),
        'unit_id': safe_str(row.get('unit_id'), ""),
        'contact_number': safe_str(row.get('contact_number'), ""),
        'approval_status': safe_str(row.get('approval_status'), "approved"),
        'status': normalize_status(row.get('status')),
        'is_deleted': safe_bool(row.get('is_deleted'), False),
        'active': safe_bool(row.get('active'), True),
        'created_at': safe_datetime(row.get('created_at')),
        'updated_at': safe_datetime(row.get('updated_at')),
    }

def normalize_machine_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a machine row from Google Sheets"""
    
    machine_id = row.get('machine_id') or row.get('id') or ""
    
    return {
        'machine_id': safe_str(machine_id, "unknown"),
        'id': safe_str(machine_id, "unknown"),
        'machine_name': safe_str(row.get('machine_name'), "Unknown Machine"),
        'machine_code': safe_str(row.get('machine_code'), ""),
        'category_id': safe_str(row.get('category_id'), ""),
        'unit_id': safe_str(row.get('unit_id'), ""),
        'status': normalize_status(row.get('status')),
        'is_deleted': safe_bool(row.get('is_deleted'), False),
        'created_at': safe_datetime(row.get('created_at')),
        'updated_at': safe_datetime(row.get('updated_at')),
    }

def normalize_unit_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a unit row from Google Sheets"""
    
    unit_id = row.get('unit_id') or row.get('id') or ""
    
    return {
        'unit_id': safe_str(unit_id, "unknown"),
        'id': safe_str(unit_id, "unknown"),
        'name': safe_str(row.get('name'), "Unknown Unit"),
        'description': safe_str(row.get('description'), ""),
        'status': normalize_status(row.get('status')),
        'is_deleted': safe_bool(row.get('is_deleted'), False),
        'created_at': safe_datetime(row.get('created_at')),
    }

def is_valid_row(row: Dict[str, Any], row_type: str = "task") -> bool:
    """
    Check if a row is valid and should be included in response
    Returns False for deleted or invalid rows
    """
    # Check if deleted
    if safe_bool(row.get('is_deleted'), False):
        logger.debug(f"Filtering out deleted {row_type}: {row.get('id')}")
        return False
    
    # Check if has minimum required data
    if row_type == "task":
        # Must have at least an ID
        has_id = bool(
            row.get('task_id') or 
            row.get('filing_task_id') or 
            row.get('fabrication_task_id') or 
            row.get('id')
        )
        if not has_id:
            logger.warning(f"Task row missing ID: {row}")
            return False
    
    elif row_type == "project":
        if not row.get('project_id') and not row.get('id'):
            return False
    
    elif row_type == "user":
        if not row.get('user_id') and not row.get('id'):
            return False
    
    return True

def safe_normalize_list(
    rows: List[Dict[str, Any]], 
    normalizer_func: callable,
    row_type: str = "task"
) -> List[Dict[str, Any]]:
    """
    Safely normalize a list of rows
    Filters out invalid rows, logs errors, NEVER crashes
    """
    normalized = []
    
    for idx, row in enumerate(rows):
        try:
            # Check if valid
            if not is_valid_row(row, row_type):
                continue
            
            # Normalize
            normalized_row = normalizer_func(row)
            normalized.append(normalized_row)
            
        except Exception as e:
            logger.error(f"Failed to normalize {row_type} row {idx}: {e}")
            logger.debug(f"Problematic row: {row}")
            # Continue processing other rows
            continue
    
    return normalized
