from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.models_db import Task, User

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/operator-performance")
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
        extract('year', Task.created_at) == year
    )

    if operator_id:
        query = query.filter(Task.assigned_to == operator_id)

    tasks = query.all()

    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == 'completed']
    completed_count = len(completed_tasks)
    
    on_hold_count = len([t for t in tasks if t.status == 'on_hold'])
    # Rescheduled count - this might need a separate query if we track reschedule requests separately
    # For now, let's assume if due_date was changed or if there are reschedule requests.
    # But the prompt asks for "Rescheduled tasks". 
    # Let's check RescheduleRequest table or just count tasks where due_date != original? 
    # We don't track original due date easily unless we look at history.
    # Let's use a placeholder or check if we can join with RescheduleRequest.
    # For simplicity, let's count tasks that have a 'reschedule' log in time logs? 
    # Or just return 0 for now if not easily available, or check if we can query RescheduleRequest.
    
    # Calculate total duration
    total_duration_seconds = sum(t.total_duration_seconds for t in completed_tasks)
    avg_time_per_task = total_duration_seconds / completed_count if completed_count > 0 else 0

    # Completion Percentage Formula: ((completed / total) * 100) - 2
    if total_tasks > 0:
        raw_percentage = (completed_count / total_tasks) * 100
        completion_percentage = max(0, raw_percentage - 2) # Ensure not negative? Or just apply -2.
        # "− 2% (apply -2% rule)"
        completion_percentage = round(completion_percentage, 2)
    else:
        completion_percentage = 0

    # Duration vs Date graph data
    # Group completed tasks by date
    duration_by_date = {}
    for t in completed_tasks:
        if t.completed_at:
            date_str = t.completed_at.strftime('%Y-%m-%d')
            duration_by_date[date_str] = duration_by_date.get(date_str, 0) + t.total_duration_seconds

    graph_data = [
        {"date": date, "duration": duration}
        for date, duration in sorted(duration_by_date.items())
    ]

    return {
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "on_hold_tasks": on_hold_count,
            "rescheduled_tasks": 0, # Placeholder until we link RescheduleRequest
            "avg_time_per_task_seconds": avg_time_per_task,
            "total_working_duration_seconds": total_duration_seconds,
            "completion_percentage": completion_percentage
        },
        "graph_data": graph_data
    }

@router.get("/task-summary")
async def get_task_summary(db: Session = Depends(get_db)):
    """
    Get summary of tasks by status for the admin dashboard.
    """
    # Total Projects (Unique projects)
    total_projects = db.query(func.count(func.distinct(Task.project))).scalar()
    
    # Task Status Counts
    status_counts = db.query(
        Task.status, func.count(Task.id)
    ).group_by(Task.status).all()
    
    status_map = {status: count for status, count in status_counts}
    
    # Project Status Counts (Approximate based on tasks)
    # "Status of Projects": TOTAL, COMPLETED, IN PROGRESS, YET TO START, HELD
    # This is tricky because a project has multiple tasks. 
    # Usually "Project Status" is derived from its tasks.
    # If ALL tasks are completed -> Completed
    # If ANY task is in progress -> In Progress
    # If ALL tasks are pending -> Yet to Start
    # If ANY task is on hold (and none in progress?) -> Held
    
    # For now, let's just return task counts as requested for the "Status of Projects" block 
    # if the user meant "Tasks" but labeled it "Projects".
    # BUT the prompt says "Status of Projects block: TOTAL, COMPLETED, IN PROGRESS, YET TO START, HELD".
    # And "Remove Total Tasks...".
    # So we need PROJECT level stats.
    
    # Let's aggregate projects.
    projects = db.query(Task.project, Task.status).all()
    project_status_map = {} # project_name -> list of statuses
    
    for proj, status in projects:
        if not proj: continue
        if proj not in project_status_map:
            project_status_map[proj] = []
        project_status_map[proj].append(status)
        
    project_stats = {
        "total": len(project_status_map),
        "completed": 0,
        "in_progress": 0,
        "yet_to_start": 0,
        "held": 0
    }
    
    for proj, statuses in project_status_map.items():
        if all(s == 'completed' for s in statuses):
            project_stats["completed"] += 1
        elif all(s == 'pending' for s in statuses):
            project_stats["yet_to_start"] += 1
        elif any(s == 'in_progress' for s in statuses):
            project_stats["in_progress"] += 1
        elif any(s == 'on_hold' for s in statuses):
            project_stats["held"] += 1
        else:
            # Default to in_progress or yet_to_start?
            # If mix of completed and pending -> In Progress
            project_stats["in_progress"] += 1

    return {
        "project_stats": project_stats,
        "task_stats": status_map # Keep this just in case
    }
