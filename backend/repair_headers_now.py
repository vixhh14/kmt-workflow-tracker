
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Worksheet names as specified by user - strictly canonical and locked
SHEETS_SCHEMA = {
    "users": [
        "user_id", "username", "role", "email", "active", "created_at", "password_hash", "approval_status"
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
        "is_deleted", "created_at", "updated_at"
    ],
    "tasks": [
        "task_id", "title", "project_id", "assigned_to", "assigned_by", "status", 
        "priority", "due_datetime", "is_deleted", "created_at", "updated_at",
        "description", "part_item", "nos_unit", "machine_id", "started_at", 
        "completed_at", "total_duration_seconds", "hold_reason", "denial_reason", 
        "actual_start_time", "actual_end_time", "total_held_seconds", 
        "ended_by", "end_reason", "work_order_number", "expected_completion_time"
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
    "units": ["unit_id", "name", "description", "created_at", "updated_at", "is_deleted"],
    "machinecategories": ["category_id", "name", "description", "created_at", "updated_at", "is_deleted"],
    "reschedulerequests": ["reschedule_id", "task_id", "new_date", "reason", "status", "created_at", "is_deleted", "updated_at"],
    "planningtasks": ["planning_task_id", "title", "description", "status", "created_at", "is_deleted", "updated_at"]
}

def repair_headers():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID missing!")
        return

    print(f"Repairing sheet headers for: {sheet_id}")
    
    try:
        creds = Credentials.from_service_account_file("service_account.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        
        current_worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
        
        for name, headers in SHEETS_SCHEMA.items():
            if name in current_worksheets:
                ws = current_worksheets[name]
                print(f"Updating headers for '{name}'...")
                # Update row 1
                ws.update('A1', [headers])
            else:
                print(f"Sheet '{name}' missing. Creating...")
                spreadsheet.add_worksheet(title=name, rows="1000", cols="26").update('A1', [headers])
        
        print("\n✅ All headers repaired according to SHEETS_SCHEMA!")
        
    except Exception as e:
        print(f"❌ Error during repair: {e}")

if __name__ == "__main__":
    repair_headers()
