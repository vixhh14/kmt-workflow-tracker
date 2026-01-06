from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_active_admin
from app.models.models_db import Task, TaskHold, User

router = APIRouter(
    prefix="/admin/performance",
    tags=["admin-performance"],
    dependencies=[Depends(get_current_active_admin)]
)

@router.get("")
async def get_monthly_performance(
    user_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Get monthly performance report for a specific user.
    Returns aggregated stats and per-task details.
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch tasks for the user in the specified month/year
    # We filter by created_at or actual_start_time? Usually performance is based on completion or work done in that month.
    # Let's filter by tasks that were active or completed in that month.
    # For simplicity, let's stick to tasks *completed* in that month or *started* in that month?
    # Request says "performance report", usually implies completed work.
    # But let's include all tasks that have activity in that month.
    # To keep it efficient and simple matching the request: "per-task rows... summary cards"
    
    # Let's query tasks assigned to user and created or updated in that month
    from sqlalchemy import or_
    tasks_query = db.query(Task).filter(
        Task.assigned_to == user_id,
        extract('month', Task.created_at) == month,
        extract('year', Task.created_at) == year,
        or_(Task.is_deleted == False, Task.is_deleted == None)
    ).all()
    
    # If we want tasks *completed* in that month regardless of creation:
    # tasks_query = db.query(Task).filter(
    #     Task.assigned_to == user_id,
    #     extract('month', Task.completed_at) == month,
    #     extract('year', Task.completed_at) == year,
    #     Task.status == 'completed'
    # ).all()
    
    # Let's stick to the user request context: "monthly performance". 
    # Usually means what did they do this month.
    # I will return tasks that were COMPLETED in this month, plus tasks currently IN PROGRESS or ON HOLD created this month.
    
    tasks = tasks_query # Using created_at filter for now as it's safer for "tasks assigned this month"
    
    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == 'completed']
    completed_count = len(completed_tasks)
    
    total_duration_seconds = sum(t.total_duration_seconds or 0 for t in completed_tasks)
    total_held_seconds = sum(t.total_held_seconds or 0 for t in tasks)
    
    avg_completion_time = total_duration_seconds / completed_count if completed_count > 0 else 0
    
    # New Formula: ((completed / total) * 100) - 2
    actual_percent = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
    completion_percentage = max(0, round(actual_percent - 2, 2)) if total_tasks > 0 else 0
    
    # Prepare per-task details with holds
    task_details = []
    for t in tasks:
        # Get holds for this task
        holds = db.query(TaskHold).filter(TaskHold.task_id == t.id).all()
        hold_data = [
            {
                "start": h.hold_started_at.isoformat() if h.hold_started_at else None,
                "end": h.hold_ended_at.isoformat() if h.hold_ended_at else None,
                "reason": h.hold_reason,
                "duration_seconds": int((h.hold_ended_at - h.hold_started_at).total_seconds()) if h.hold_ended_at and h.hold_started_at else None
            }
            for h in holds
        ]
        
        task_details.append({
            "task_id": t.id,
            "title": t.title,
            "status": t.status,
            "actual_start_time": t.actual_start_time.isoformat() if t.actual_start_time else None,
            "actual_end_time": t.actual_end_time.isoformat() if t.actual_end_time else None,
            "expected_completion_time": t.expected_completion_time,
            "total_duration_seconds": t.total_duration_seconds,
            "total_held_seconds": t.total_held_seconds,
            "holds": hold_data
        })
        
    return {
        "summary": {
            "user_id": user.user_id,
            "username": user.username,
            "month": month,
            "year": year,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "avg_completion_time_seconds": round(avg_completion_time, 2),
            "total_held_seconds": total_held_seconds,
            "completion_percentage": round(completion_percentage, 2)
        },
        "tasks": task_details
    }
