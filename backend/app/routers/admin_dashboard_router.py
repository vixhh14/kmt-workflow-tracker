from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Attendance

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/project-summary")
async def get_project_summary(db: Session = Depends(get_db)):
    """
    Get project status summary for admin dashboard.
    Returns counts of projects by status.
    """
    try:
        # Get all tasks with projects
        tasks_with_projects = db.query(Task).filter(Task.project != None, Task.project != '').all()
        
        # Group tasks by project
        project_map = {}
        for task in tasks_with_projects:
            project_name = task.project
            if project_name not in project_map:
                project_map[project_name] = []
            project_map[project_name].append(task.status)
        
        # Count projects by status
        total_projects = len(project_map)
        completed = 0
        in_progress = 0
        yet_to_start = 0
        held = 0
        
        for project, statuses in project_map.items():
            # Project is completed if ALL tasks are completed
            if all(s == 'completed' for s in statuses):
                completed += 1
            # Project is held if ANY task is on_hold and none are in progress
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                held += 1
            # Project is in progress if ANY task is in_progress
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            # Project is yet to start if ALL tasks are pending
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                # Mixed states default to in_progress
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
    """
    Get project status data for pie chart.
    Returns array of {label, value} for chart rendering.
    """
    try:
        # Get all tasks with projects
        tasks_with_projects = db.query(Task).filter(Task.project != None, Task.project != '').all()
        
        # Group tasks by project
        project_map = {}
        for task in tasks_with_projects:
            project_name = task.project
            if project_name not in project_map:
                project_map[project_name] = []
            project_map[project_name].append(task.status)
        
        # Count projects by status
        completed = 0
        in_progress = 0
        yet_to_start = 0
        held = 0
        
        for project, statuses in project_map.items():
            # Project is completed if ALL tasks are completed
            if all(s == 'completed' for s in statuses):
                completed += 1
            # Project is held if ANY task is on_hold and none are in progress
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                held += 1
            # Project is in progress if ANY task is in_progress
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            # Project is yet to start if ALL tasks are pending
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                # Mixed states default to in_progress
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
    """
    Get attendance summary showing present and absent users.
    Returns lists of present and absent users with their details.
    """
    try:
        # Get all users (exclude admin for now, or include all based on requirements)
        all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
        
        # Get today's date
        today = date.today()
        
        # Get attendance records for today
        today_attendance = db.query(Attendance).filter(
            func.date(Attendance.date) == today
        ).all()
        
        # Create set of user IDs who have attendance today
        present_user_ids = {att.user_id for att in today_attendance if att.check_in}
        
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch attendance summary: {str(e)}")


@router.get("/task-statistics")
async def get_task_statistics(db: Session = Depends(get_db)):
    """
    Get overall task statistics for admin dashboard.
    """
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
