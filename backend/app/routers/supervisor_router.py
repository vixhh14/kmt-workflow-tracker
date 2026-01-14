from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models_db import Task, User, Machine, TaskHold, Project
from app.utils.datetime_utils import utc_now, make_aware, safe_datetime_diff
from datetime import datetime, timezone
import uuid

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"],
    responses={404: {"description": "Not found"}},
)

class AssignTaskRequest(BaseModel):
    task_id: str
    operator_id: str
    machine_id: Optional[str] = None
    priority: Optional[str] = None
    expected_completion_time: Optional[int] = None
    due_date: Optional[datetime] = None

@router.get("/pending-tasks")
async def get_pending_tasks(db: any = Depends(get_db)):
    try:
        all_tasks = db.query(Task).all()
        pending = [t for t in all_tasks if not t.is_deleted and (not t.assigned_to or t.status == 'pending')]
        
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        all_machines = db.query(Machine).all()
        machine_map = {str(m.id): m for m in all_machines}
        
        return [{
            "id": str(t.id),
            "title": t.title or "",
            "project": t.project or "",
            "description": t.description or "",
            "priority": t.priority or "medium",
            "status": t.status or "pending",
            "machine_id": str(t.machine_id) if t.machine_id else "",
            "machine_name": machine_map.get(str(t.machine_id)).machine_name if str(t.machine_id) in machine_map else "",
            "assigned_by": str(t.assigned_by) if t.assigned_by else "",
            "assigned_by_name": user_map.get(str(t.assigned_by)).username if str(t.assigned_by) in user_map else "",
            "due_date": str(t.due_date) if t.due_date else "",
            "created_at": str(t.created_at) if t.created_at else None
        } for t in pending]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending tasks: {str(e)}")


@router.get("/running-tasks")
async def get_running_tasks(
    project_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get all currently running (in_progress) tasks, optionally filtered"""
    try:
        all_tasks = db.query(Task).all()
        running = [t for t in all_tasks if not t.is_deleted and t.status == 'in_progress']
        
        if project_id and project_id != "all":
            # Check if project_id is a UUID or a project name
            is_uuid = False
            try:
                uuid.UUID(str(project_id))
                is_uuid = True
            except ValueError:
                pass

            if is_uuid:
                running = [t for t in running if str(t.project_id) == str(project_id)]
            else:
                running = [t for t in running if str(t.project) == str(project_id)]
        
        if operator_id and operator_id != "all":
            running = [t for t in running if str(t.assigned_to) == str(operator_id)]

        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        all_machines = db.query(Machine).all()
        machine_map = {str(m.id): m for m in all_machines}
        all_holds = db.query(TaskHold).all()
        
        task_list = []
        for t in running:
            operator = user_map.get(str(t.assigned_to))
            machine = machine_map.get(str(t.machine_id))
            
            # Calculate duration (simplified for SheetsDB, assuming total_duration_seconds is available or calculated)
            duration_seconds = 0
            if t.actual_start_time or t.started_at:
                start_time = t.actual_start_time or t.started_at
                start_aware = make_aware(start_time) if isinstance(start_time, datetime) else start_time # Assuming make_aware handles non-datetime
                now = utc_now()
                total_elapsed = int((now - start_aware).total_seconds()) if isinstance(start_aware, datetime) else 0
                held_seconds = t.total_held_seconds or 0
                duration_seconds = max(0, total_elapsed - held_seconds)
            
            # Fetch holds for this task
            t_holds = [h for h in all_holds if str(h.task_id) == str(t.id)]
            holds_serialized = [
                {
                    "start": str(h.hold_started_at) if h.hold_started_at else None,
                    "end": str(h.hold_ended_at) if h.hold_ended_at else None,
                    "duration_seconds": safe_datetime_diff(h.hold_ended_at, h.hold_started_at) if h.hold_ended_at and h.hold_started_at else 0,
                    "reason": h.hold_reason or ""
                }
                for h in t_holds
            ]

            task_list.append({
                "id": str(t.id),
                "title": t.title or "",
                "project": t.project or "",
                "operator_id": str(t.assigned_to) if t.assigned_to else "",
                "operator_name": operator.full_name if operator and operator.full_name else (operator.username if operator else "Unknown"),
                "machine_id": str(t.machine_id) if t.machine_id else "",
                "machine_name": machine.machine_name if machine else "Unknown",
                "started_at": str(t.actual_start_time) if t.actual_start_time else (str(t.started_at) if t.started_at else None),
                "actual_start_time": str(t.actual_start_time) if t.actual_start_time else None,
                "expected_completion_time": t.expected_completion_time,
                "duration_seconds": duration_seconds,
                "total_held_seconds": t.total_held_seconds or 0,
                "holds": holds_serialized,
                "due_date": str(t.due_date) if t.due_date else None,
                "status": "in_progress"
            })
        
        return task_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch running tasks: {str(e)}")


@router.get("/task-status")
async def get_task_status(
    operator_id: Optional[str] = None, 
    project_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get task status breakdown for graph, optionally filtered"""
    try:
        # Get base list of operators
        all_users = db.query(User).all()
        operators = [u for u in all_users if not u.is_deleted and u.approval_status == 'approved' and u.role == 'operator']
        
        if operator_id and operator_id != "all":
            operators = [u for u in operators if str(u.user_id) == str(operator_id)]
            
        # Get Tasks to aggregate
        all_tasks = db.query(Task).all()
        tasks_filtered_by_deleted = [t for t in all_tasks if not t.is_deleted]
        
        if project_id and project_id != "all":
            # Check if project_id is a UUID or a project name
            is_uuid = False
            try:
                uuid.UUID(str(project_id))
                is_uuid = True
            except ValueError:
                pass

            if is_uuid:
                tasks_filtered_by_deleted = [t for t in tasks_filtered_by_deleted if str(t.project_id) == str(project_id)]
            else:
                tasks_filtered_by_deleted = [t for t in tasks_filtered_by_deleted if str(t.project) == str(project_id)]
            
        operator_stats = []
        for operator in operators:
            # Filter tasks for this operator from the pre-filtered list
            operator_tasks = [t for t in tasks_filtered_by_deleted if str(t.assigned_to) == str(operator.user_id)]
            
            completed = len([t for t in operator_tasks if t.status == 'completed'])
            in_progress = len([t for t in operator_tasks if t.status == 'in_progress'])
            pending = len([t for t in operator_tasks if t.status == 'pending'])
            
            total = completed + in_progress + pending

            operator_stats.append({
                "operator": operator.full_name if operator.full_name else operator.username,
                "operator_id": str(operator.user_id),
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending,
                "total": total
            })
        
        operator_stats.sort(key=lambda x: x['total'], reverse=True)
        
        return operator_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")


@router.get("/projects-summary")
async def get_projects_summary(db: any = Depends(get_db)):
    """Get project status distribution for pie chart"""
    try:
        tasks_with_projects = [t for t in db.query(Task).all() if not t.is_deleted and t.project]
        
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
                in_progress += 1 # Default to in_progress if mixed statuses and not all completed/pending/on_hold
        
        return {
            "yet_to_start": yet_to_start,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects summary: {str(e)}")


@router.get("/task-stats")
async def get_task_stats(
    project: Optional[str] = None, 
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get task statistics, optionally filtered by project and operator"""
    try:
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not t.is_deleted]
        
        if project and project != "all":
            is_uuid = False
            try:
                uuid.UUID(str(project))
                is_uuid = True
            except ValueError:
                pass
            
            if is_uuid:
                tasks_filtered = [t for t in tasks_filtered if str(t.project_id) == str(project)]
            else:
                tasks_filtered = [t for t in tasks_filtered if str(t.project) == str(project)]
        
        if operator_id and operator_id != "all":
             tasks_filtered = [t for t in tasks_filtered if str(t.assigned_to) == str(operator_id)]

        total = len(tasks_filtered)
        pending = len([t for t in tasks_filtered if t.status == 'pending'])
        in_progress = len([t for t in tasks_filtered if t.status == 'in_progress'])
        completed = len([t for t in tasks_filtered if t.status == 'completed'])
        on_hold = len([t for t in tasks_filtered if t.status == 'on_hold'])
        
        # Get list of all projects for dropdown from Project table
        all_projects = db.query(Project).all()
        project_names = sorted(list(set([p.project_name for p in all_projects if not p.is_deleted and p.project_name])))
        
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
async def assign_task(
    request: AssignTaskRequest, 
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a task to an operator"""
    try:
        task = db.query(Task).filter(id=request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        operator = db.query(User).filter(user_id=request.operator_id).first()
        if not operator:
            raise HTTPException(status_code=404, detail="Operator not found")
        
        if operator.role == 'admin' and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can assign tasks to other admins")
        
        # Accept assignment to any valid user
        task.assigned_to = request.operator_id
        task.status = 'pending'
        
        if request.machine_id:
            task.machine_id = request.machine_id
        if request.priority:
            task.priority = request.priority
        if request.expected_completion_time is not None:
            task.expected_completion_time = request.expected_completion_time
        if request.due_date:
            task.due_date = request.due_date.isoformat() # Store as ISO string
        
        db.commit() # Assuming commit handles updates to existing objects
        
        return {
            "message": "Task assigned successfully",
            "task": {
                "id": str(task.id),
                "title": task.title,
                "assigned_to": str(task.assigned_to),
                "status": task.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback() # Assuming SheetsDB has a rollback mechanism
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.get("/project-summary")
async def get_project_summary(db: any = Depends(get_db)):
    """Get project summary metrics"""
    try:
        tasks_with_projects = [t for t in db.query(Task).all() if not t.is_deleted and t.project]
        
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
                active_projects += 1 # Mixed statuses, not all pending, not all completed
        
        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "pending_projects": pending_projects,
            "active_projects": active_projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project summary: {str(e)}")


@router.get("/priority-task-status")
async def get_priority_task_status(db: any = Depends(get_db)):
    """Get task counts by priority level"""
    try:
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not t.is_deleted]

        high = len([t for t in tasks_filtered if str(t.priority).upper() == 'HIGH'])
        medium = len([t for t in tasks_filtered if str(t.priority).upper() == 'MEDIUM'])
        low = len([t for t in tasks_filtered if str(t.priority).upper() == 'LOW'])
        
        return {
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priority task status: {str(e)}")
