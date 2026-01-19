
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
            # Already has a record for today, ensure login_time is set
            if not existing.get("login_time"):
                sheets_repo.update("attendance", existing["attendance_id"], {"login_time": now_ist})
            return {"status": "success", "message": "Attendance already marked", "data": existing}
        
        # 2. Create new record
        att_id = f"att_{user_id}_{today_str.replace('-', '')}"
        record = {
            "attendance_id": att_id,
            "id": att_id,
            "user_id": str(user_id),
            "date": today_str,
            "login_time": now_ist,
            "logout_time": "",
            "status": "Present",
            "is_deleted": False,
            "created_at": now_ist,
            "updated_at": now_ist
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
            "logout_time": now_ist,
            "updated_at": now_ist
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
            
        target_date_compare = str(target_date_str).split('T')[0].split(' ')[0]
        
        # Robust date match for DD/MM/YYYY and ISO formats
        def dates_match(row_date, target_date):
            if not row_date or not target_date: return False
            r_str = str(row_date).strip().split('T')[0].split(' ')[0]
            t_str = str(target_date).strip().split('T')[0].split(' ')[0]
            if r_str == t_str: return True
            
            # Alternative: Try converting DD/MM/YYYY to YYYY-MM-DD
            try:
                if '/' in r_str:
                    parts = r_str.split('/')
                    if len(parts) == 3:
                        # Handle 15/1/2026 or 15/01/2026
                        d, m, y = parts
                        norm_r = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                        if norm_r == t_str: return True
            except: pass
            return False

        # Get all users and filter by tracked roles
        tracked_roles = ['operator', 'supervisor', 'planning', 'admin', 'file_master', 'fab_master', 'fab master', 'file master']
        all_users = db.query(User).all()
        active_users = []
        for u in all_users:
            if getattr(u, 'is_deleted', False): continue
            
            # Use strip and lower for robust matching
            approval_status = str(getattr(u, 'approval_status', '')).strip().lower()
            role = str(getattr(u, 'role', '')).strip().lower()
            
            # Accept 'approved' or 'active' or empty/none if admin
            is_approved = approval_status in ['approved', 'active', '1', 'true', 'yes']
            
            if is_approved and role in tracked_roles:
                active_users.append(u)
        
        # Get all attendance
        all_att = db.query(Attendance).all()
        
        attendance_map = {}
        for a in all_att:
            if getattr(a, 'is_deleted', False): continue
            
            if dates_match(getattr(a, 'date', ''), target_date_compare):
                uid = str(getattr(a, 'user_id', '')).strip()
                if not uid: continue
                # Keep the latest record if multiple exist
                attendance_map[uid] = a
        
        present_users = []
        absent_users = []
        records = []
        
        for user in active_users:
            user_id_str = str(getattr(user, 'id', ''))
            user_info = {
                "id": user_id_str,
                "name": getattr(user, 'full_name', '') or getattr(user, 'username', ''),
                "username": getattr(user, 'username', ''),
                "role": getattr(user, 'role', ''),
                "unit_id": getattr(user, 'unit_id', '')
            }
            
            attendance = attendance_map.get(user_id_str)
            
            if attendance and str(getattr(attendance, 'status', '')).lower() == 'present':
                att_data = {
                    "status": "Present",
                    "check_in": str(getattr(attendance, 'check_in', '') or ""),
                    "check_out": str(getattr(attendance, 'check_out', '') or ""),
                    "login_time": str(getattr(attendance, 'login_time', '') or "")
                }
                present_users.append({**user_info, **att_data})
                records.append({
                    "user_id": user_id_str,
                    "user": user_info["name"],
                    "username": user_info["username"],
                    "role": user_info["role"],
                    "check_in": att_data['check_in'],
                    "check_out": att_data['check_out'],
                    "status": "Present",
                    "date": target_date_compare
                })
            else:
                absent_users.append(user_info)

        return {
            "success": True,
            "date": target_date_compare,
            "total_tracked": len(active_users),
            "present": len(present_users), 
            "absent": len(absent_users),   
            "present_count": len(present_users),
            "absent_count": len(absent_users),
            "present_users": present_users,
            "absent_users": absent_users,
            "records": records,            
            "all_records": records
        }
    except Exception as e:
        print(f"❌ Error in get_attendance_summary: {e}")
        return {
            "success": False,
            "date": str(target_date_str),
            "total_tracked": 0,
            "present": 0,
            "absent": 0,
            "present_users": [],
            "absent_users": [],
            "records": []
        }

def get_all_attendance(db: SheetsDB, target_date_str: Optional[str] = None):
    """Implementation of mandatory task: Fetch all attendance records."""
    try:
        # If date is provided, return for that date
        if target_date_str:
             results = get_attendance_summary(db, target_date_str)
             if results.get("success"):
                 return results.get("all_records", [])
             return []
        
        # If no date, return ALL attendance records from cache
        all_att = db.query(Attendance).all()
        all_users = db.query(User).all()
        user_map = {str(getattr(u, 'id', '')): u for u in all_users}
        
        results = []
        for a in all_att:
            if getattr(a, 'is_deleted', False): continue
            uid = str(getattr(a, 'user_id', ''))
            user = user_map.get(uid)
            results.append({
                "id": str(getattr(a, 'id', '')),
                "user_id": uid,
                "user": getattr(user, 'full_name', '') or getattr(user, 'username', 'Unknown'),
                "username": getattr(user, 'username', 'Unknown'),
                "status": getattr(a, 'status', ''),
                "date": str(getattr(a, 'date', '')).split('T')[0],
                "check_in": str(getattr(a, 'check_in', '') or ""),
                "check_out": str(getattr(a, 'check_out', '') or ""),
                "login_time": str(getattr(a, 'login_time', '') or "")
            })
        return results
    except Exception as e:
        print(f"❌ Error in get_all_attendance: {e}")
        return []
