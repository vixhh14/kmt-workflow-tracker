
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.models_db import Attendance, User
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.core.sheets_db import SheetsDB

def mark_present(db: SheetsDB, user_id: str, ip_address: Optional[str] = None) -> dict:
    """
    Mark user as present for today (IST). Idempotent.
    Canonical columns: [attendance_id, user_id, date, login_time, logout_time, status]
    """
    try:
        from app.repositories.sheets_repository import sheets_repo
        today_str = get_today_date_ist().isoformat()
        now_ist = get_current_time_ist().isoformat()
        
        # 1. Fetch all attendance for today (cached)
        all_att = sheets_repo.get_all("attendance")
        
        existing = next((a for a in all_att if str(a.get("user_id")) == str(user_id) and str(a.get("date")) == today_str), None)
        
        if existing:
            # Update missing login_time or status
            updates = {}
            if not existing.get("login_time"):
                updates["login_time"] = now_ist
            if str(existing.get("status", "")).lower() != "present":
                updates["status"] = "Present"
            
            if updates:
                sheets_repo.update("attendance", existing["attendance_id"], updates)
            return {"status": "success", "message": "Attendance marked", "data": existing}
        
        # 2. Create new record
        att_id = f"att_{user_id}_{today_str.replace('-', '')}"
        record = {
            "attendance_id": att_id,
            "user_id": str(user_id),
            "date": today_str,
            "login_time": now_ist,
            "logout_time": "",
            "status": "Present"
        }
        
        inserted = sheets_repo.insert("attendance", record)
        return {"status": "success", "message": "Checked in successfully", "data": inserted}
    
    except Exception as e:
        print(f"❌ Error in mark_present: {e}")
        return {"success": False, "message": str(e)}


def mark_checkout(db: SheetsDB, user_id: str) -> dict:
    """
    Mark user as checked out for today (IST).
    """
    try:
        from app.repositories.sheets_repository import sheets_repo
        today_str = get_today_date_ist().isoformat()
        now_ist = get_current_time_ist().isoformat()
        
        all_att = sheets_repo.get_all("attendance")
        existing = next((a for a in all_att if str(a.get("user_id")) == str(user_id) and str(a.get("date")) == today_str), None)

        if not existing:
            return {"status": "error", "message": "No check-in record found for today"}

        if existing.get("logout_time"):
            return {"status": "success", "message": "Already checked out", "data": existing}

        sheets_repo.update("attendance", existing["attendance_id"], {
            "logout_time": now_ist
        })
        
        return {"status": "success", "message": "Checked out successfully"}
    
    except Exception as e:
        print(f"❌ Error in mark_checkout: {e}")
        return {"success": False, "message": str(e)}


def get_attendance_summary(db: SheetsDB, target_date_str: Optional[str] = None):
    """
    Get attendance summary for a specific date (YYYY-MM-DD). Defaults to today.
    """
    try:
        if not target_date_str:
            target_date_str = get_today_date_ist().isoformat()
            
        target_date_compare = str(target_date_str).split('T')[0]
        
        # 1. Fetch all users and attendance
        from app.repositories.sheets_repository import sheets_repo
        all_users = sheets_repo.get_all("users") # active=True filtered by repo.get_all
        all_att = sheets_repo.get_all("attendance")
        
        # 2. Build attendance map for target date
        attendance_map = {}
        for a in all_att:
            # Simple date comparison
            row_date = str(a.get("date", "")).split('T')[0]
            if row_date == target_date_compare:
                uid = str(a.get("user_id", "")).strip()
                if uid:
                    attendance_map[uid] = a
        
        present_records = []
        absent_users = []
        
        # 3. Tracked roles
        tracked_roles = ['operator', 'supervisor', 'planning', 'admin', 'file_master', 'fab_master']
        
        for user in all_users:
            # Robust active check for dict-based user data
            u_active = str(user.get("active", "true")).lower().strip()
            if u_active not in ["true", "1", "yes", "active"]:
                continue
                
            u_role = str(user.get("role", "")).lower().strip()
            if u_role not in tracked_roles:
                continue
                
            u_id = str(user.get("user_id", user.get("id", "")))
            u_name = str(user.get("username", ""))
            
            att = attendance_map.get(u_id)
            
            if att and str(att.get("status", "")).lower() == "present":
                present_records.append({
                    "user_id": u_id,
                    "username": u_name,
                    "role": u_role,
                    "login_time": str(att.get("login_time", "")),
                    "logout_time": str(att.get("logout_time", "")),
                    "status": "Present",
                    "date": target_date_compare
                })
            else:
                absent_users.append({
                    "user_id": u_id,
                    "username": u_name,
                    "role": u_role
                })

        return {
            "success": True,
            "date": target_date_compare,
            "present_count": len(present_records),
            "absent_count": len(absent_users),
            "records": present_records, # For compatibility with UI showing Present list
            "all_records": present_records + [{"user_id": u["user_id"], "username": u["username"], "status": "Absent"} for u in absent_users],
            "present_users": present_records,
            "absent_users": absent_users
        }
    except Exception as e:
        print(f"❌ Error in get_attendance_summary: {e}")
        return {"success": False, "error": str(e)}

def get_all_attendance(db: SheetsDB, target_date_str: Optional[str] = None):
    """Fetch all attendance records with user info injected."""
    return get_attendance_summary(db, target_date_str).get("records", [])
