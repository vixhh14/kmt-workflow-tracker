from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date, timezone
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Attendance
from app.utils.datetime_utils import utc_now, make_aware

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/project-summary")
async def get_project_summary(db: Session = Depends(get_db)):
    """Get project status summary for admin dashboard"""
    try:
        tasks_with_projects = db.query(Task).filter(Task.project != None, Task.project != '').all()
        
        project_map = {}
        for task in tasks_with_projects:
            project_name = task.project
            if project_name not in project_map:
                project_map[project_name] = []
            project_map[project_name].append(task.status)
        
        total_projects = len(project_map)
        completed = 0
        in_progress = 0
        yet_to_start = 0
        held = 0
        
        for project, statuses in project_map.items():
            if all(s == 'completed' for s in statuses):
                completed += 1
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                held += 1
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                in_progress += 1
        
        return {
            "total_projects": total_projects,
            "completed": completed,
            "in_progress": in_progress,
            "yet_to_start": yet_to_start,
            "held": held
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project summary: {str(e)}")


@router.get("/project-status-chart")
async def get_project_status_chart(db: Session = Depends(get_db)):
    """Get project status data for pie chart"""
    try:
        tasks_with_projects = db.query(Task).filter(Task.project != None, Task.project != '').all()
        
        project_map = {}
        for task in tasks_with_projects:
            project_name = task.project
            if project_name not in project_map:
                project_map[project_name] = []
            project_map[project_name].append(task.status)
        
        completed = 0
        in_progress = 0
        yet_to_start = 0
        held = 0
        
        for project, statuses in project_map.items():
            if all(s == 'completed' for s in statuses):
                completed += 1
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                held += 1
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                in_progress += 1
        
        return [
            {"label": "Yet to Start", "value": yet_to_start},
            {"label": "In Progress", "value": in_progress},
            {"label": "Completed", "value": completed},
            {"label": "Held", "value": held}
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project status chart: {str(e)}")


@router.get("/attendance-summary")
async def get_attendance_summary(db: Session = Depends(get_db)):
    """Get attendance summary with proper check_in column handling"""
    try:
        all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
        
        today = date.today()
        
        # Query attendance records for today using check_in column
        today_attendance = db.query(Attendance).filter(
            func.date(Attendance.check_in) == today
        ).all()
        
        # Fallback: if check_in doesn't work, try login_time
        if not today_attendance:
            try:
                today_attendance = db.query(Attendance).filter(
                    func.date(Attendance.login_time) == today
                ).all()
            except:
                today_attendance = []
        
        present_user_ids = set()
        for att in today_attendance:
            if att.check_in or att.login_time:
                present_user_ids.add(att.user_id)
        
        present_users = []
        absent_users = []
        
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
            "present_users": present_users,
            "absent_users": absent_users,
            "total_users": len(all_users),
            "present_count": len(present_users),
            "absent_count": len(absent_users)
        }
    except Exception as e:
        # Return safe empty data if attendance table fails
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
            "present_users": [],
            "absent_users": user_list,
            "total_users": len(all_users),
            "present_count": 0,
            "absent_count": len(all_users)
        }


@router.get("/task-statistics")
async def get_task_statistics(db: Session = Depends(get_db)):
    """Get overall task statistics for admin dashboard"""
    try:
        total_tasks = db.query(Task).count()
        completed = db.query(Task).filter(Task.status == 'completed').count()
        in_progress = db.query(Task).filter(Task.status == 'in_progress').count()
        pending = db.query(Task).filter(Task.status == 'pending').count()
        on_hold = db.query(Task).filter(Task.status == 'on_hold').count()
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "on_hold": on_hold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task statistics: {str(e)}")
