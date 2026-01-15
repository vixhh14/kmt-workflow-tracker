
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from app.models.models_db import Attendance, User
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.core.sheets_db import SheetsDB

def mark_present(db: SheetsDB, user_id: str, ip_address: Optional[str] = None) -> dict:
    """
    Mark user as present for today (IST). Idempotent.
    """
    try:
        today = get_today_date_ist()
        now_ist = get_current_time_ist()
        today_str = today.isoformat()
        
        # Check if attendance record already exists for this user today
        all_att = db.query(Attendance).all()
        # Note: Sheets store dates as strings often
        existing_attendance = next((a for a in all_att if str(getattr(a, 'user_id', '')) == str(user_id) and str(getattr(a, 'date', '')).split('T')[0] == today_str), None)
        
        if existing_attendance:
            # If already logged in today, just update login_time but keep original check_in
            if not getattr(existing_attendance, 'login_time', None):
                existing_attendance.login_time = now_ist.isoformat()
            if ip_address:
                existing_attendance.ip_address = ip_address
            
            db.commit()
            return {"status": "success", "message": "Attendance already marked", "data": existing_attendance.dict()}
        else:
            # Create new attendance record
            new_attendance = Attendance(
                date=today_str,
                user_id=str(user_id),
                status="Present",
                check_in=now_ist.isoformat(),
                login_time=now_ist.isoformat(),
                ip_address=ip_address or "unknown",
                created_at=now_ist.isoformat(),
                is_deleted=False
            )
            
            db.add(new_attendance)
            db.commit()
            return {"status": "success", "message": "Checked in successfully", "data": new_attendance.dict()}
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to mark attendance: {str(e)}",
            "error": str(e)
        }


def mark_checkout(db: SheetsDB, user_id: str) -> dict:
    """
    Mark user as checked out for today (IST).
    """
    try:
        today = get_today_date_ist()
        now_ist = get_current_time_ist()
        today_str = today.isoformat()
        
        all_att = db.query(Attendance).all()
        # Find local record for today
        attendance = next((a for a in all_att if str(getattr(a, 'user_id', '')) == str(user_id) and str(getattr(a, 'date', '')).split('T')[0] == today_str), None)

        if not attendance:
            return {"status": "error", "message": "No check-in record found for today"}

        if getattr(attendance, 'check_out', None) and str(getattr(attendance, 'check_out', '')).strip():
            return {"status": "success", "message": "Already checked out", "data": attendance.dict()}

        attendance.check_out = now_ist.isoformat()
        attendance.updated_at = now_ist.isoformat()
        db.commit()
        
        return {"status": "success", "message": "Checked out successfully", "data": attendance.dict()}
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to record check-out: {str(e)}",
            "error": str(e)
        }


# Assuming @router.get is from FastAPI, but it's not imported here.
# For the purpose of this edit, I'll include it as a comment or remove it if it causes syntax errors.
# @router.get("/summary", response_model=dict)
async def get_attendance_summary(db: Any, target_date_str: str):
    """
    Get attendance summary for a specific date (YYYY-MM-DD).
    """
    try:
        # Get all users and filter by tracked roles
        tracked_roles = ['operator', 'supervisor', 'planning', 'admin', 'file_master', 'fab_master']
        all_users = db.query(User).all()
        active_users = [
            u for u in all_users 
            if not getattr(u, 'is_deleted', False) 
            and str(getattr(u, 'approval_status', '')).lower() == 'approved'
            and str(getattr(u, 'role', '')).lower() in tracked_roles
        ]
        
        # Get all attendance for target date
        all_att = db.query(Attendance).all()
        # Clean target_date_str to just YYYY-MM-DD
        target_date_compare = str(target_date_str).split('T')[0].split(' ')[0]
        
        attendance_map = {}
        for a in all_att:
            att_date = str(getattr(a, 'date', '')).split('T')[0].split(' ')[0]
            if att_date == target_date_compare:
                attendance_map[str(getattr(a, 'user_id', ''))] = a
        
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
                    "check_in": str(getattr(attendance, 'check_in', '')),
                    "check_out": str(getattr(attendance, 'check_out', '')),
                    "login_time": str(getattr(attendance, 'login_time', ''))
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
            "date": target_date_compare,
            "total_tracked": len(active_users),
            "present_count": len(present_users),
            "absent_count": len(absent_users),
            "present_users": present_users,
            "absent_users": absent_users,
            "all_records": records
        }
    except Exception as e:
        print(f"❌ Error in get_attendance_summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "date": target_date_str,
            "total_tracked": 0,
            "present_count": 0,
            "absent_count": 0,
            "present_users": [],
            "absent_users": [],
            "all_records": []
        }

def get_all_attendance(db):
    """Fetch and join all attendance with user simplified info"""
    try:
        att_rows = db.query(Attendance).all()
        users = db.query(User).all()
        user_map = {str(getattr(u, 'id', '')): getattr(u, 'full_name', '') or getattr(u, 'username', '') for u in users}
        
        results = []
        for a in att_rows:
            u_name = user_map.get(str(getattr(a, 'user_id', '')), "Unknown User")
            results.append({
                "id": getattr(a, 'id', ''),
                "user_id": getattr(a, 'user_id', ''),
                "user_name": u_name,
                "date": getattr(a, 'date', ''),
                "status": getattr(a, 'status', ''),
                "check_in": getattr(a, 'check_in', ''),
                "check_out": getattr(a, 'check_out', ''),
                "login_time": getattr(a, 'login_time', '')
            })
        return results
    except Exception as e:
        print(f"❌ Error in get_all_attendance: {e}")
        return []
