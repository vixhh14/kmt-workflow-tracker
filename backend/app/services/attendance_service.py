
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
        existing_attendance = next((a for a in all_att if str(a.user_id) == str(user_id) and str(a.date).split('T')[0] == today_str), None)
        
        if existing_attendance:
            # Update existing record
            existing_attendance.login_time = now_ist
            existing_attendance.status = 'Present'
            
            if not existing_attendance.check_in:
                existing_attendance.check_in = now_ist
            
            if ip_address:
                existing_attendance.ip_address = ip_address
            
            db.commit()
            
            return {
                "success": True,
                "message": "Attendance updated",
                "is_new": False,
                "attendance_id": existing_attendance.id,
                "date": today_str,
                "check_in": existing_attendance.check_in.isoformat() if hasattr(existing_attendance.check_in, "isoformat") else str(existing_attendance.check_in),
                "login_time": existing_attendance.login_time.isoformat() if hasattr(existing_attendance.login_time, "isoformat") else str(existing_attendance.login_time)
            }
        else:
            # Create new attendance record
            new_id = f"att_{int(datetime.now().timestamp())}_{user_id}"
            new_data = {
                "id": new_id,
                "user_id": user_id,
                "date": today_str,
                "check_in": now_ist.isoformat(),
                "login_time": now_ist.isoformat(),
                "status": 'Present',
                "ip_address": ip_address
            }
            db.add({"__tablename__": "Attendance", **new_data})
            
            return {
                "success": True,
                "message": "Attendance recorded",
                "is_new": True,
                "attendance_id": new_id,
                "date": today_str,
                "check_in": now_ist.isoformat(),
                "login_time": now_ist.isoformat()
            }
    
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
        attendance = next((a for a in all_att if str(a.user_id) == str(user_id) and str(a.date).split('T')[0] == today_str), None)
        
        if not attendance:
            return {
                "success": False,
                "message": "No attendance record found for today"
            }
        
        if not attendance.check_out:
            attendance.check_out = now_ist
            db.commit()
            
            return {
                "success": True,
                "message": "Check-out recorded",
                "attendance_id": attendance.id,
                "check_out": now_ist.isoformat()
            }
        else:
            return {
                "success": True,
                "message": "Already checked out",
                "attendance_id": attendance.id,
                "check_out": str(attendance.check_out)
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to record check-out: {str(e)}",
            "error": str(e)
        }


def get_attendance_summary(db: SheetsDB, target_date: Optional[date] = None) -> dict:
    """
    Get attendance summary for a specific date (defaults to today IST).
    """
    try:
        if target_date is None:
            target_date = get_today_date_ist()
        
        target_date_str = target_date.isoformat()
            
        # Get all users and filter by tracked roles
        tracked_roles = ['operator', 'supervisor', 'planning', 'admin', 'file_master', 'fab_master']
        all_users = db.query(User).filter(is_deleted=False, approval_status='approved').all()
        active_users = [u for u in all_users if str(u.role).lower() in tracked_roles]
        
        # Get all attendance for target date
        all_att = db.query(Attendance).all()
        attendance_map = {str(a.user_id): a for a in all_att if str(a.date).split('T')[0] == target_date_str}
        
        present_users = []
        absent_users = []
        records = []
        
        for user in active_users:
            user_id_str = str(user.user_id)
            user_info = {
                "id": user_id_str,
                "name": user.full_name if user.full_name else user.username,
                "username": user.username,
                "role": user.role,
                "unit_id": user.unit_id
            }
            
            attendance = attendance_map.get(user_id_str)
            
            if attendance and attendance.status == 'Present':
                att_data = {
                    "status": "Present",
                    "check_in": str(attendance.check_in) if attendance.check_in else None,
                    "check_out": str(attendance.check_out) if attendance.check_out else None,
                    "login_time": str(attendance.login_time) if attendance.login_time else None
                }
                present_users.append({**user_info, **att_data})
                records.append({
                    "user_id": user_id_str,
                    "user": user_info["name"],
                    "username": user.username,
                    "role": user.role,
                    "check_in": att_data['check_in'],
                    "check_out": att_data['check_out'],
                    "status": "Present",
                    "date": target_date_str
                })
            else:
                absent_users.append(user_info)
        
        return {
            "success": True,
            "date": target_date_str,
            "present": len(present_users),
            "absent": len(absent_users),
            "total_users": len(active_users),
            "present_users": present_users,
            "absent_users": absent_users,
            "records": records
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get attendance summary: {str(e)}",
            "error": str(e)
        }
