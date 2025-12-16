from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.models_db import Task, User, Machine
from app.utils.datetime_utils import utc_now, make_aware
from datetime import datetime, timezone

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"],
    responses={404: {"description": "Not found"}},
)

class AssignTaskRequest(BaseModel):
    task_id: str
    operator_id: str

@router.get("/pending-tasks")
async def get_pending_tasks(db: Session = Depends(get_db)):
    """Get all pending/unassigned tasks for quick assignment"""
    try:
        pending_tasks = db.query(Task).filter(
            or_(
                Task.status == 'pending',
                Task.assigned_to == None,
                Task.assigned_to == ''
            )
        ).all()
        
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
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
                "machine_name": machine.machine_name if machine else "",
                "assigned_by": task.assigned_by or "",
                "assigned_by_name": assigned_by_user.username if assigned_by_user else "",
                "due_date": task.due_date or "",
                "created_at": make_aware(task.created_at).isoformat() if task.created_at else None
            })
        
        return task_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending tasks: {str(e)}")


@router.get("/running-tasks")
async def get_running_tasks(db: Session = Depends(get_db)):
    """Get all currently running (in_progress) tasks"""
    try:
        running_tasks = db.query(Task).filter(Task.status == 'in_progress').all()
        
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        machines = db.query(Machine).all()
        machine_map = {m.id: m for m in machines}
        
        task_list = []
        for task in running_tasks:
            operator = user_map.get(task.assigned_to)
            machine = machine_map.get(task.machine_id)
            
            # Calculate duration
            duration_seconds = 0
            if task.actual_start_time or task.started_at:
                start_time = task.actual_start_time or task.started_at
                start_aware = make_aware(start_time)
                now = utc_now()
                duration_seconds = int((now - start_aware).total_seconds())
            
            task_list.append({
                "id": task.id,
                "title": task.title or "",
                "project": task.project or "",
                "operator_id": task.assigned_to or "",
                "operator_name": operator.full_name if operator and operator.full_name else (operator.username if operator else "Unknown"),
                "machine_id": task.machine_id or "",
                "machine_name": machine.machine_name if machine else "Unknown",
                "started_at": make_aware(task.actual_start_time or task.started_at).isoformat() if (task.actual_start_time or task.started_at) else None,
                "duration_seconds": duration_seconds,
                "status": "in_progress"
            })
        
        return task_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch running tasks: {str(e)}")


@router.get("/task-status")
async def get_task_status(operator_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get task status breakdown, optionally filtered by operator"""
    try:
        operators = db.query(User).filter(User.role == 'operator').all()
        
        if operator_id:
            operators = [op for op in operators if op.user_id == operator_id]
        
        all_tasks = db.query(Task).all()
        
        operator_stats = []
        for operator in operators:
            operator_tasks = [t for t in all_tasks if t.assigned_to == operator.user_id]
            
            completed = len([t for t in operator_tasks if t.status == 'completed'])
            in_progress = len([t for t in operator_tasks if t.status == 'in_progress'])
            pending = len([t for t in operator_tasks if t.status == 'pending'])
            
            operator_stats.append({
                "operator": operator.full_name if operator.full_name else operator.username,
                "operator_id": operator.user_id,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending,
                "total": completed + in_progress + pending
            })
        
        operator_stats.sort(key=lambda x: x['total'], reverse=True)
        
        return operator_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")


@router.get("/projects-summary")
async def get_projects_summary(db: Session = Depends(get_db)):
    """Get project status distribution for pie chart"""
    try:
        tasks_with_projects = db.query(Task).filter(
            Task.project != None, 
            Task.project != ''
        ).all()
        
        project_map = {}
        for task in tasks_with_projects:
            if task.project not in project_map:
                project_map[task.project] = []
            project_map[task.project].append(task.status)
        
        yet_to_start = 0
        in_progress = 0
        completed = 0
        on_hold = 0
        
        for project, statuses in project_map.items():
            if all(s == 'completed' for s in statuses):
                completed += 1
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                on_hold += 1
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                in_progress += 1
        
        return {
            "yet_to_start": yet_to_start,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects summary: {str(e)}")


@router.get("/task-stats")
async def get_task_stats(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get task statistics, optionally filtered by project"""
    try:
        query = db.query(Task)
        
        if project and project != "all":
            query = query.filter(Task.project == project)
        
        all_tasks = query.all()
        
        total = len(all_tasks)
        pending = len([t for t in all_tasks if t.status == 'pending'])
        in_progress = len([t for t in all_tasks if t.status == 'in_progress'])
        completed = len([t for t in all_tasks if t.status == 'completed'])
        on_hold = len([t for t in all_tasks if t.status == 'on_hold'])
        
        # Get list of all projects for dropdown
        all_projects = db.query(Task.project).filter(
            Task.project != None,
            Task.project != ''
        ).distinct().all()
        project_names = [p[0] for p in all_projects]
        
        return {
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold,
            "available_projects": project_names,
            "selected_project": project if project else "all"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task stats: {str(e)}")


@router.post("/assign-task")
async def assign_task(request: AssignTaskRequest, db: Session = Depends(get_db)):
    """Assign a task to an operator"""
    try:
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        operator = db.query(User).filter(User.user_id == request.operator_id).first()
        if not operator:
            raise HTTPException(status_code=404, detail="Operator not found")
        
        if operator.role != 'operator':
            raise HTTPException(status_code=400, detail="User is not an operator")
        
        task.assigned_to = request.operator_id
        task.status = 'pending'
        
        db.commit()
        db.refresh(task)
        
        return {
            "message": "Task assigned successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "assigned_to": task.assigned_to,
                "status": task.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.get("/project-summary")
async def get_project_summary(db: Session = Depends(get_db)):
    """Get project summary metrics"""
    try:
        tasks_with_projects = db.query(Task).filter(
            Task.project != None, 
            Task.project != ''
        ).all()
        
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
            if all(s == 'completed' for s in statuses):
                completed_projects += 1
            elif any(s == 'in_progress' for s in statuses):
                active_projects += 1
            elif all(s == 'pending' for s in statuses):
                pending_projects += 1
            else:
                active_projects += 1
        
        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "pending_projects": pending_projects,
            "active_projects": active_projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project summary: {str(e)}")


@router.get("/priority-task-status")
async def get_priority_task_status(db: Session = Depends(get_db)):
    """Get task counts by priority level"""
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
