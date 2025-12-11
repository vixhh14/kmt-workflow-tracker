from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.analytics_model import AnalyticsData
from app.models.models_db import Task, Machine, OutsourceItem
from app.core.database import get_db
from collections import Counter

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_analytics(db: Session = Depends(get_db)):
    # 1. Active Projects
    # Count distinct projects where tasks are not completed
    active_projects_query = db.query(Task.project).filter(
        Task.status.in_(['pending', 'in_progress', 'on_hold']),
        Task.project != None
    ).distinct()
    active_projects_count = active_projects_query.count()
    active_projects_list = [p[0] for p in active_projects_query.all()]

    # 2. Attendance
    from app.models.models_db import Attendance, User
    from datetime import datetime
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    present_users = db.query(User).join(Attendance).filter(
        Attendance.date == today_str,
        Attendance.status == 'present'
    ).all()
    
    total_users_count = db.query(User).count()
    present_count = len(present_users)
    absent_count = total_users_count - present_count
    
    present_list = [{"username": u.username, "full_name": u.full_name, "role": u.role} for u in present_users]
    
    # Get absent users (simplistic approach: all users not in present list)
    present_ids = [u.user_id for u in present_users]
    absent_users = db.query(User).filter(User.user_id.notin_(present_ids)).all()
    absent_list = [{"username": u.username, "full_name": u.full_name, "role": u.role} for u in absent_users]

    # Return dict to bypass strict Pydantic model for now
    return {
        "active_projects_count": active_projects_count,
        "active_projects_list": active_projects_list,
        "attendance": {
            "present_count": present_count,
            "absent_count": absent_count,
            "present_list": present_list,
            "absent_list": absent_list
        },
        # Keep existing data for compatibility if needed, or just return what's requested
        "total_tasks": db.query(Task).count(),
        "tasks_by_status": {s: count for s, count in db.query(Task.status, func.count(Task.status)).group_by(Task.status).all() if s}
    }

@router.get("/task-summary")
async def get_task_summary(
    user_id: str = None,
    project: str = None,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(Task)

    if user_id:
        query = query.filter(Task.assigned_to == user_id)
    if project:
        query = query.filter(Task.project == project)
    
    # Filter by month/year if provided (using created_at or due_date? Usually performance is based on completion, but status summary is current state. 
    # Let's assume current state snapshot, so date filtering might filter tasks created/due in that period? 
    # For now, let's stick to simple current state filtering. If month/year is needed for historical reports, that's different.
    # The user request implies "dashboard views", which are usually "current state".
    # I will omit date filtering for now unless explicitly needed for "monthly performance" which is handled by another endpoint.
    
    tasks = query.all()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')
    pending = sum(1 for t in tasks if t.status == 'pending')
    active = sum(1 for t in tasks if t.status == 'in_progress')
    on_hold = sum(1 for t in tasks if t.status == 'on_hold')
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "active_tasks": active,
        "on_hold_tasks": on_hold
    }
