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
