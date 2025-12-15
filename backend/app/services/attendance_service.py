from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, func
from datetime import datetime, date
from app.models.models_db import Attendance, User
from typing import Optional
from app.core.time_utils import get_current_time_ist, get_today_date_ist

def mark_present(db: Session, user_id: str, ip_address: Optional[str] = None) -> dict:
    """
    Mark user as present for today (IST). Idempotent.
    """
    try:
        today = get_today_date_ist()
        now_ist = get_current_time_ist()
        
        # Check if attendance record already exists for this user today
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date == today
            )
        ).first()
        
        # Note: We now store Aware IST time in DateTime(timezone=True) column
        
        if existing_attendance:
            # Update existing record
            existing_attendance.login_time = now_ist
            existing_attendance.status = 'Present'
            
            # Set check_in only if not already set
            if not existing_attendance.check_in:
                existing_attendance.check_in = now_ist
            
            # Update IP if provided
            if ip_address:
                existing_attendance.ip_address = ip_address
            
            db.commit()
            db.refresh(existing_attendance)
            
            return {
                "success": True,
                "message": "Attendance updated",
                "is_new": False,
                "attendance_id": existing_attendance.id,
                "date": today.isoformat(),
                "check_in": existing_attendance.check_in.isoformat() if existing_attendance.check_in else None,
                "login_time": existing_attendance.login_time.isoformat() if existing_attendance.login_time else None
            }
        else:
            # Create new attendance record
            new_attendance = Attendance(
                user_id=user_id,
                date=today,
                check_in=now_ist,
                login_time=now_ist,
                status='Present',
                ip_address=ip_address
            )
            
            db.add(new_attendance)
            db.commit()
            db.refresh(new_attendance)
            
            return {
                "success": True,
                "message": "Attendance recorded",
                "is_new": True,
                "attendance_id": new_attendance.id,
                "date": today.isoformat(),
                "check_in": new_attendance.check_in.isoformat() if new_attendance.check_in else None,
                "login_time": new_attendance.login_time.isoformat() if new_attendance.login_time else None
            }
    
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Failed to mark attendance: {str(e)}",
            "error": str(e)
        }


def mark_checkout(db: Session, user_id: str) -> dict:
    """
    Mark user as checked out for today (IST).
    """
    try:
        today = get_today_date_ist()
        now_ist = get_current_time_ist()
        
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance:
            return {
                "success": False,
                "message": "No attendance record found for today"
            }
        
        # Only set check_out if not already set
        if not attendance.check_out:
            attendance.check_out = now_ist
            
            db.commit()
            db.refresh(attendance)
            
            return {
                "success": True,
                "message": "Check-out recorded",
                "attendance_id": attendance.id,
                "check_out": attendance.check_out.isoformat() if attendance.check_out else None
            }
        else:
            return {
                "success": True,
                "message": "Already checked out",
                "attendance_id": attendance.id,
                "check_out": attendance.check_out.isoformat() if attendance.check_out else None
            }
    
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Failed to record check-out: {str(e)}",
            "error": str(e)
        }


def get_attendance_summary(db: Session, target_date: Optional[date] = None) -> dict:
    """
    Get attendance summary for a specific date (defaults to today IST).
    Uses Left Join to get all users and their attendance.
    """
    try:
        if target_date is None:
            target_date = get_today_date_ist()
            
        # Join User and Attendance
        # We want ALL relevant users (operators, etc) and their attendance for the target date
        results = db.query(User, Attendance).outerjoin(
            Attendance, 
            and_(
                User.user_id == Attendance.user_id,
                Attendance.date == target_date
            )
        ).filter(
            User.role.in_(['operator', 'supervisor', 'planning', 'admin'])
        ).all()
        
        present_users = []
        absent_users = []
        records = []
        
        present_count = 0
        
        for user, attendance in results:
            user_info = {
                "id": user.user_id,
                "name": user.full_name if user.full_name else user.username,
                "username": user.username,
                "role": user.role,
                "unit_id": user.unit_id
            }
            
            if attendance and attendance.status == 'Present':
                # User is present
                att_data = {
                    "status": attendance.status,
                    "check_in": attendance.check_in.isoformat() if attendance.check_in else None,
                    "check_out": attendance.check_out.isoformat() if attendance.check_out else None,
                    "login_time": attendance.login_time.isoformat() if attendance.login_time else None
                }
                
                # Add to present list
                p_user = {**user_info, **att_data}
                present_users.append(p_user)
                
                # Add to records (flat list for table)
                records.append({
                    "user_id": user.user_id,
                    "user": user.full_name if user.full_name else user.username,
                    "username": user.username,
                    "role": user.role,
                    "check_in": att_data['check_in'],
                    "check_out": att_data['check_out'],
                    "status": att_data['status'],
                    "date": target_date.isoformat()
                })
                
                present_count += 1
            else:
                # User is absent
                absent_users.append(user_info)
        
        return {
            "success": True,
            "date": target_date.isoformat(),
            "present": present_count,
            "absent": len(absent_users),
            "total_users": len(results),
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
