from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, text
from datetime import datetime, date, timezone
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Attendance
from app.utils.datetime_utils import utc_now, make_aware

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/projects")
async def get_projects(db: Session = Depends(get_db)):
    """Get list of all unique project names"""
    try:
        projects = db.query(Task.project).filter(
            Task.project != None,
            Task.project != ''
        ).distinct().all()
        
        project_names = [p[0] for p in projects]
        return project_names
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get("/project-analytics")
async def get_project_analytics(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get comprehensive project analytics including stats and chart data"""
    try:
        query = db.query(Task)
        
        # Filter by project if specified and not "all"
        if project and project != 'all':
            query = query.filter(Task.project == project)
        
        tasks = query.all()
        
        # Calculate statistics
        total = len(tasks)
        yet_to_start = len([t for t in tasks if t.status == 'pending'])
        in_progress = len([t for t in tasks if t.status == 'in_progress'])
        completed = len([t for t in tasks if t.status == 'completed'])
        on_hold = len([t for t in tasks if t.status == 'on_hold'])
        
        return {
            "project": project if project else "all",
            "stats": {
                "total": total,
                "yet_to_start": yet_to_start,
                "in_progress": in_progress,
                "completed": completed,
                "on_hold": on_hold
            },
            "chart": {
                "yet_to_start": yet_to_start,
                "in_progress": in_progress,
                "completed": completed,
                "on_hold": on_hold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project analytics: {str(e)}")


@router.get("/attendance-summary")
async def get_attendance_summary(db: Session = Depends(get_db)):
    """Get attendance summary with proper column handling and fallbacks"""
    try:
        all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
        
        today = date.today()
        present_users = []
        absent_users = []
        records = []
        
        # Try to fetch attendance records with proper error handling
        try:
            # Method 1: Try using check_in column
            today_attendance = db.query(Attendance).filter(
                func.date(Attendance.check_in) == today
            ).all()
            
            present_user_ids = {att.user_id for att in today_attendance if att.check_in}
            
            # Build records array
            user_map = {u.user_id: u for u in all_users}
            for att in today_attendance:
                user = user_map.get(att.user_id)
                if user and att.check_in:
                    records.append({
                        "user": user.full_name if user.full_name else user.username,
                        "user_id": user.user_id,
                        "check_in": make_aware(att.check_in).isoformat() if att.check_in else None,
                        "check_out": make_aware(att.check_out).isoformat() if att.check_out else None,
                        "status": att.status or "Present"
                    })
                    
        except Exception as e1:
            # Method 2: Fallback to login_time column
            try:
                today_attendance = db.query(Attendance).filter(
                    func.date(Attendance.login_time) == today
                ).all()
                
                present_user_ids = {att.user_id for att in today_attendance if att.login_time}
                
                user_map = {u.user_id: u for u in all_users}
                for att in today_attendance:
                    user = user_map.get(att.user_id)
                    if user and att.login_time:
                        records.append({
                            "user": user.full_name if user.full_name else user.username,
                            "user_id": user.user_id,
                            "check_in": make_aware(att.login_time).isoformat() if att.login_time else None,
                            "check_out": make_aware(att.check_out).isoformat() if hasattr(att, 'check_out') and att.check_out else None,
                            "status": att.status if hasattr(att, 'status') else "Present"
                        })
            except Exception as e2:
                # Method 3: No attendance data available
                present_user_ids = set()
        
        # Build present and absent user lists
        for user in all_users:
            user_data = {
                "id": user.user_id,
                "name": user.full_name if user.full_name else user.username,
                "role": user.role
            }
            
            if user.user_id in present_user_ids:
                present_users.append(user_data)
            else:
                absent_users.append(user_data)
        
        return {
            "date": today.isoformat(),
            "present": len(present_users),
            "absent": len(absent_users),
            "late": 0,  # Can be calculated based on check_in time vs expected time
            "present_users": present_users,
            "absent_users": absent_users,
            "total_users": len(all_users),
            "records": records
        }
    except Exception as e:
        # Return safe fallback data
        all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
        user_list = [
            {
                "id": u.user_id,
                "name": u.full_name if u.full_name else u.username,
                "role": u.role
            }
            for u in all_users
        ]
        
        return {
            "date": date.today().isoformat(),
            "present": 0,
            "absent": len(all_users),
            "late": 0,
            "present_users": [],
            "absent_users": user_list,
            "total_users": len(all_users),
            "records": []
        }


# Legacy endpoints for backward compatibility
@router.get("/overall-stats")
async def get_overall_stats(db: Session = Depends(get_db)):
    """Get overall project statistics (LEGACY)"""
    analytics = await get_project_analytics(project='all', db=db)
    return {
        "total_projects": len(db.query(Task.project).filter(Task.project != None, Task.project != '').distinct().all()),
        "completed": analytics['stats']['completed'],
        "in_progress": analytics['stats']['in_progress'],
        "yet_to_start": analytics['stats']['yet_to_start'],
        "held": analytics['stats']['on_hold']
    }


@router.get("/project-status")
async def get_project_status(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get project status distribution (LEGACY)"""
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['chart']


@router.get("/task-stats")
async def get_task_stats(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get task statistics (LEGACY)"""
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['stats']
