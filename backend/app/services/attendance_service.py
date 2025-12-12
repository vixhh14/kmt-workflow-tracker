from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from app.models.models_db import Attendance, User
from typing import Optional

def mark_present(db: Session, user_id: str, ip_address: Optional[str] = None) -> dict:
    """
    Mark user as present for today. Idempotent - safe to call multiple times per day.
    
    Rules:
    - Creates new attendance record if none exists for (user_id, today)
    - Updates existing record if already exists (no duplicates)
    - Always updates login_time to track latest login
    - Sets check_in only if not already set
    - Always sets status to 'Present'
    
    Args:
        db: Database session
        user_id: User ID to mark present
        ip_address: Optional IP address of the client
    
    Returns:
        dict with success status and attendance record details
    """
    try:
        today = date.today()
        now = datetime.now()  # Using naive datetime (UTC or server time)
        
        # Check if attendance record already exists for this user today
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date == today
            )
        ).first()
        
        if existing_attendance:
            # Update existing record
            existing_attendance.login_time = now
            existing_attendance.status = 'Present'
            
            # Set check_in only if not already set
            if not existing_attendance.check_in:
                existing_attendance.check_in = now
            
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
                check_in=now,
                login_time=now,
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
    Mark user as checked out for today.
    Updates the check_out time and changes status to 'Left'.
    """
    try:
        today = date.today()
        now = datetime.now()
        
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
        
        attendance.check_out = now
        attendance.status = 'Left'
        
        db.commit()
        db.refresh(attendance)
        
        return {
            "success": True,
            "message": "Check-out recorded",
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
    Get attendance summary for a specific date (defaults to today).
    Returns present and absent users with detailed information.
    """
    try:
        if target_date is None:
            target_date = date.today()
        
        # Get all active users (all roles)
        all_users = db.query(User).filter(
            User.role.in_(['operator', 'supervisor', 'planning', 'admin'])
        ).all()
        
        # Get today's attendance records
        today_attendance = db.query(Attendance).filter(
            Attendance.date == target_date
        ).all()
        
        # Create mapping of user_id to attendance status
        attendance_map = {}
        present_count = 0
        
        for att in today_attendance:
            if att.status == 'Present' and att.check_in:
                attendance_map[att.user_id] = {
                    "status": att.status,
                    "check_in": att.check_in.isoformat() if att.check_in else None,
                    "check_out": att.check_out.isoformat() if att.check_out else None,
                    "login_time": att.login_time.isoformat() if att.login_time else None
                }
                present_count += 1
        
        # Build present and absent lists
        present_list = []
        absent_list = []
        
        for user in all_users:
            user_data = {
                "id": user.user_id,
                "name": user.full_name if user.full_name else user.username,
                "role": user.role
            }
            
            if user.user_id in attendance_map:
                user_data.update(attendance_map[user.user_id])
                present_list.append(user_data)
            else:
                absent_list.append(user_data)
        
        return {
            "success": True,
            "date": target_date.isoformat(),
            "present": present_count,
            "absent": len(absent_list),
            "total_users": len(all_users),
            "present_list": present_list,
            "absent_list": absent_list
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get attendance summary: {str(e)}",
            "error": str(e)
        }
