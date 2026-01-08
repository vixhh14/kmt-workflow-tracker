from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, or_
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.models_db import Task, User
from app.services.dashboard_analytics_service import get_operations_overview

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

from app.schemas.dashboard_schema import (
    DashboardOverview, 
    OperatorPerformanceOut, 
    DashboardProjectOverview, 
    TaskSummaryOut
)

@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(db: Session = Depends(get_db)):
    """
    Unified dashboard overview for Admin, Supervisor, and Planning.
    """
    return get_operations_overview(db)


@router.get("/operator-performance", response_model=OperatorPerformanceOut)
async def get_operator_performance(
    month: int,
    year: int,
    operator_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for operators for a specific month/year.
    """
    # Base query for tasks in the specified month/year
    query = db.query(Task).filter(
        extract('month', Task.created_at) == month,
        extract('year', Task.created_at) == year,
        or_(Task.is_deleted == False, Task.is_deleted == None)
    )

    if operator_id:
        query = query.filter(Task.assigned_to == operator_id)

    tasks = query.all()

    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == 'completed']
    completed_count = len(completed_tasks)
    
    on_hold_count = len([t for t in tasks if t.status == 'on_hold'])
    
    # Calculate total duration
    total_duration_seconds = 0
    for t in completed_tasks:
        d = t.total_duration_seconds or 0
        # If duration is 0 but we have start/end, recalculate (safely handles legacy or corrupted data)
        if d == 0 and t.actual_start_time and t.actual_end_time:
            elapsed = (t.actual_end_time - t.actual_start_time).total_seconds()
            held = t.total_held_seconds or 0
            d = max(0, int(elapsed - held))
        total_duration_seconds += d
        
    avg_time_per_task = total_duration_seconds / completed_count if completed_count > 0 else 0

    # Completion Percentage Formula: ((completed / total) * 100) - 2
    if total_tasks > 0:
        raw_percentage = (completed_count / total_tasks) * 100
        completion_percentage = max(0, raw_percentage - 2) 
        completion_percentage = round(completion_percentage, 2)
    else:
        completion_percentage = 0

    # Duration vs Date graph data
    # Group completed tasks by date
    duration_by_date = {}
    for t in completed_tasks:
        if t.completed_at:
            date_str = t.completed_at.strftime('%Y-%m-%d')
            duration_by_date[date_str] = duration_by_date.get(date_str, 0) + (t.total_duration_seconds or 0)

    graph_data = [
        {"date": date, "duration": duration}
        for date, duration in sorted(duration_by_date.items())
    ]

    return {
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "on_hold_tasks": on_hold_count,
            "rescheduled_tasks": 0, 
            "avg_time_per_task_seconds": avg_time_per_task,
            "total_working_duration_seconds": int(total_duration_seconds),
            "completion_percentage": float(completion_percentage)
        },
        "graph_data": graph_data
    }

from app.services.project_overview_service import get_project_overview_stats

@router.get("/project-overview", response_model=DashboardProjectOverview)
async def project_overview(db: Session = Depends(get_db)):
    """
    Get unified project overview statistics.
    Single source of truth for all dashboards.
    """
    try:
        return get_project_overview_stats(db)
    except Exception as e:
        print(f"Error in project_overview: {e}")
        # Return safe default
        return {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "yet_to_start": 0,
            "held": 0
        }

@router.get("/task-summary", response_model=TaskSummaryOut)
async def get_task_summary(db: Session = Depends(get_db)):
    """
    Legacy endpoint - kept for backward compatibility if needed, 
    but prefer /project-overview for project stats.
    """
    try:
        # Reuse the logic but format it as expected by old frontend components if any
        project_stats = get_project_overview_stats(db)
        
        # Task Status Counts
        status_counts = db.query(
            Task.status, func.count(Task.id)
        ).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).group_by(Task.status).all()
        
        status_map = {str(status): int(count) for status, count in status_counts if status}

        return {
            "project_stats": project_stats,
            "task_stats": status_map
        }
    except Exception as e:
        print(f"Error in get_task_summary: {e}")
        return {
            "project_stats": {
                "total": 0, "completed": 0, "in_progress": 0, "yet_to_start": 0, "held": 0
            },
            "task_stats": {}
        }
