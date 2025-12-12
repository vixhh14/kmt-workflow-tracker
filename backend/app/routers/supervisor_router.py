from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Machine

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"],
    responses={404: {"description": "Not found"}},
)

@router.get("/project-summary")
async def get_supervisor_project_summary(db: Session = Depends(get_db)):
    """
    Get project summary for supervisor dashboard.
    Returns counts of total, completed, pending, and active projects.
    """
    try:
        # Get all tasks with projects
        tasks_with_projects = db.query(Task).filter(
            Task.project != None, 
            Task.project != ''
        ).all()
        
        # Group tasks by project
        project_map = {}
        for task in tasks_with_projects:
            if task.project not in project_map:
                project_map[task.project] = []
            project_map[task.project].append(task.status)
        
        total_projects = len(project_map)
        completed_projects = 0
        pending_projects = 0
        active_projects = 0
        
        for project, statuses in project_map.items():
            # Project is completed if ALL tasks are completed
            if all(s == 'completed' for s in statuses):
                completed_projects += 1
            # Project is active if ANY task is in_progress
            elif any(s == 'in_progress' for s in statuses):
                active_projects += 1
            # Project is pending if ALL tasks are pending
            elif all(s == 'pending' for s in statuses):
                pending_projects += 1
            else:
                # Mixed states - consider as active
                active_projects += 1
        
        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "pending_projects": pending_projects,
            "active_projects": active_projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project summary: {str(e)}")


@router.get("/pending-tasks")
async def get_supervisor_pending_tasks(db: Session = Depends(get_db)):
    """
    Get all pending/unassigned tasks for quick assignment.
    Returns tasks that are either not assigned or not yet started.
    """
    try:
        # Get pending or unassigned tasks
        pending_tasks = db.query(Task).filter(
            or_(
                Task.status == 'pending',
                Task.assigned_to == None,
                Task.assigned_to == ''
            )
        ).all()
        
        # Get all users for name mapping
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        
        # Get all machines for name mapping
        machines = db.query(Machine).all()
        machine_map = {m.id: m for m in machines}
        
        task_list = []
        for task in pending_tasks:
            assigned_by_user = user_map.get(task.assigned_by)
            machine = machine_map.get(task.machine_id)
            
            task_list.append({
                "id": task.id,
                "title": task.title or "",
                "project": task.project or "",
                "description": task.description or "",
                "priority": task.priority or "medium",
                "status": task.status or "pending",
                "machine_id": task.machine_id or "",
                "machine_name": machine.name if machine else "",
                "assigned_by": task.assigned_by or "",
                "assigned_by_name": assigned_by_user.username if assigned_by_user else "",
                "due_date": task.due_date or "",
                "created_at": task.created_at.isoformat() if task.created_at else None
            })
        
        return task_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending tasks: {str(e)}")


@router.get("/operator-task-status")
async def get_supervisor_operator_task_status(db: Session = Depends(get_db)):
    """
    Get task status breakdown by operator.
    Returns array of operator names with their task counts by status.
    """
    try:
        # Get all operators
        operators = db.query(User).filter(User.role == 'operator').all()
        
        # Get all tasks
        all_tasks = db.query(Task).all()
        
        operator_stats = []
        for operator in operators:
            # Filter tasks assigned to this operator
            operator_tasks = [t for t in all_tasks if t.assigned_to == operator.user_id]
            
            completed = len([t for t in operator_tasks if t.status == 'completed'])
            in_progress = len([t for t in operator_tasks if t.status == 'in_progress'])
            pending = len([t for t in operator_tasks if t.status == 'pending'])
            
            operator_stats.append({
                "operator": operator.full_name if operator.full_name else operator.username,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending
            })
        
        # Sort by total tasks descending
        operator_stats.sort(key=lambda x: x['completed'] + x['in_progress'] + x['pending'], reverse=True)
        
        return operator_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch operator task status: {str(e)}")


@router.get("/priority-task-status")
async def get_supervisor_priority_task_status(db: Session = Depends(get_db)):
    """
    Get task counts by priority level.
    Returns counts for high, medium, and low priority tasks.
    """
    try:
        high = db.query(Task).filter(Task.priority == 'high').count()
        medium = db.query(Task).filter(Task.priority == 'medium').count()
        low = db.query(Task).filter(Task.priority == 'low').count()
        
        return {
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priority task status: {str(e)}")
