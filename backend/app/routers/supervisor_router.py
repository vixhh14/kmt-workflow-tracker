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
    """
    Get all pending tasks that need assignment.
    FIXED: Show tasks that are either:
    1. Unassigned (no assigned_to), OR
    2. Have status='pending' (assigned but not started)
    """
    try:
        all_tasks = db.query(Task).all()
        # FIXED: Include tasks with status='pending' OR without assigned_to
        pending = [
            t for t in all_tasks 
            if not getattr(t, 'is_deleted', False) 
            and (
                not getattr(t, 'assigned_to', None) or getattr(t, 'assigned_to', '') == '' 
                or getattr(t, 'status', '') == 'pending'
            )
        ]
        
        print(f"📋 Pending Tasks: Found {len(pending)} tasks needing assignment")
        
        all_users = db.query(User).all()
        user_map = {str(getattr(u, 'user_id', getattr(u, 'id', ''))): u for u in all_users}
        all_machines = db.query(Machine).all()
        machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m for m in all_machines}
        
        return [{
            "id": str(getattr(t, 'task_id', getattr(t, 'id', ''))),
            "title": getattr(t, 'title', '') or "",
            "project": getattr(t, 'project', '') or "",
            "description": getattr(t, 'description', '') or "",
            "priority": getattr(t, 'priority', '') or "medium",
            "status": getattr(t, 'status', '') or "pending",
            "machine_id": str(getattr(t, 'machine_id', '')) if getattr(t, 'machine_id', None) else "",
            "machine_name": getattr(machine_map.get(str(getattr(t, 'machine_id', ''))), 'machine_name', '') if str(getattr(t, 'machine_id', '')) in machine_map else "",
            "assigned_to": str(getattr(t, 'assigned_to', '')) if getattr(t, 'assigned_to', None) else "",
            "assigned_by": str(getattr(t, 'assigned_by', '')) if getattr(t, 'assigned_by', None) else "",
            "assigned_by_name": getattr(user_map.get(str(getattr(t, 'assigned_by', ''))), 'username', '') if str(getattr(t, 'assigned_by', '')) in user_map else "",
            "due_date": str(getattr(t, 'due_date', '')) if getattr(t, 'due_date', None) else "",
            "expected_completion_time": getattr(t, 'expected_completion_time', 0),
            "created_at": str(getattr(t, 'created_at', '')) if getattr(t, 'created_at', None) else None
        } for t in pending]
    except Exception as e:
        print(f"❌ Error fetching pending tasks: {e}")
        import traceback
        traceback.print_exc()
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
        running = [t for t in all_tasks if not getattr(t, 'is_deleted', False) and getattr(t, 'status', '') == 'in_progress']
        
        if project_id and project_id != "all":
             is_uuid_val = False
             try:
                 uuid.UUID(str(project_id))
                 is_uuid_val = True
             except ValueError: pass

             if is_uuid_val:
                 running = [t for t in running if str(getattr(t, 'project_id', '')) == str(project_id)]
             else:
                 running = [t for t in running if str(getattr(t, 'project', '')) == str(project_id)]
        
        if operator_id and operator_id != "all":
            running = [t for t in running if str(getattr(t, 'assigned_to', '')) == str(operator_id)]

        all_users = db.query(User).all()
        user_map = {str(getattr(u, 'user_id', getattr(u, 'id', ''))): u for u in all_users}
        all_machines = db.query(Machine).all()
        machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m for m in all_machines}
        all_holds = db.query(TaskHold).all()
        
        task_list = []
        for t in running:
            operator = user_map.get(str(getattr(t, 'assigned_to', '')))
            machine = machine_map.get(str(getattr(t, 'machine_id', '')))
            
            duration_seconds = 0
            start_time = getattr(t, 'actual_start_time', None) or getattr(t, 'started_at', None)
            if start_time:
                start_aware = make_aware(start_time) if isinstance(start_time, datetime) else start_time
                now = utc_now()
                total_elapsed = int((now - start_aware).total_seconds()) if isinstance(start_aware, datetime) else 0
                held_seconds = getattr(t, 'total_held_seconds', 0) or 0
                duration_seconds = max(0, total_elapsed - held_seconds)
            
            t_holds = [h for h in all_holds if str(getattr(h, 'task_id', '')) == str(getattr(t, 'task_id', getattr(t, 'id', '')))]
            holds_serialized = [
                {
                    "start": str(getattr(h, 'hold_started_at', '')),
                    "end": str(getattr(h, 'hold_ended_at', '')),
                    "duration_seconds": safe_datetime_diff(getattr(h, 'hold_ended_at', None), getattr(h, 'hold_started_at', None)) if getattr(h, 'hold_ended_at', None) and getattr(h, 'hold_started_at', None) else 0,
                    "reason": getattr(h, 'hold_reason', '') or ""
                }
                for h in t_holds
            ]

            task_list.append({
                "id": str(getattr(t, 'task_id', getattr(t, 'id', ''))),
                "title": getattr(t, 'title', '') or "",
                "project": getattr(t, 'project', '') or "",
                "operator_id": str(getattr(t, 'assigned_to', '')) if getattr(t, 'assigned_to', None) else "",
                "operator_name": getattr(operator, 'full_name', '') if operator and getattr(operator, 'full_name', '') else (getattr(operator, 'username', 'Unknown') if operator else "Unknown"),
                "machine_id": str(getattr(t, 'machine_id', '')) if getattr(t, 'machine_id', None) else "",
                "machine_name": getattr(machine, 'machine_name', 'Unknown') if machine else "Unknown",
                "started_at": str(start_time) if start_time else None,
                "actual_start_time": str(getattr(t, 'actual_start_time', '')) if getattr(t, 'actual_start_time', None) else None,
                "expected_completion_time": getattr(t, 'expected_completion_time', 0),
                "duration_seconds": duration_seconds,
                "total_held_seconds": getattr(t, 'total_held_seconds', 0) or 0,
                "holds": holds_serialized,
                "due_date": str(getattr(t, 'due_date', '')) if getattr(t, 'due_date', None) else None,
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
        all_users = db.query(User).all()
        operators = [u for u in all_users if not getattr(u, 'is_deleted', False) and getattr(u, 'approval_status', '') == 'approved' and getattr(u, 'role', '') == 'operator']
        
        if operator_id and operator_id != "all":
            operators = [u for u in operators if str(getattr(u, 'user_id', getattr(u, 'id', ''))) == str(operator_id)]
            
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]
        
        if project_id and project_id != "all":
             is_uuid_val = False
             try:
                 uuid.UUID(str(project_id))
                 is_uuid_val = True
             except ValueError: pass

             if is_uuid_val:
                 tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project_id', '')) == str(project_id)]
             else:
                 tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project', '')) == str(project_id)]
            
        operator_stats = []
        for operator in operators:
            op_id_str = str(getattr(operator, 'user_id', getattr(operator, 'id', '')))
            operator_tasks = [t for t in tasks_filtered if str(getattr(t, 'assigned_to', '')) == op_id_str]
            
            completed = len([t for t in operator_tasks if getattr(t, 'status', '') == 'completed'])
            in_progress = len([t for t in operator_tasks if getattr(t, 'status', '') == 'in_progress'])
            pending = len([t for t in operator_tasks if getattr(t, 'status', '') == 'pending'])
            
            total = completed + in_progress + pending

            operator_stats.append({
                "operator": getattr(operator, 'full_name', '') if getattr(operator, 'full_name', '') else getattr(operator, 'username', ''),
                "operator_id": op_id_str,
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
        tasks_with_projects = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and getattr(t, 'project', None)]
        
        project_map = {}
        for task in tasks_with_projects:
            p_name = getattr(task, 'project', 'Unknown')
            if p_name not in project_map:
                project_map[p_name] = []
            project_map[p_name].append(getattr(task, 'status', ''))
        
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
async def get_task_stats(
    project: Optional[str] = None, 
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get task statistics, optionally filtered by project and operator"""
    try:
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]
        
        if project and project != "all":
            is_uuid_val = False
            try:
                uuid.UUID(str(project))
                is_uuid_val = True
            except ValueError: pass
            
            if is_uuid_val:
                tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project_id', '')) == str(project)]
            else:
                tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project', '')) == str(project)]
        
        if operator_id and operator_id != "all":
             tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'assigned_to', '')) == str(operator_id)]

        total = len(tasks_filtered)
        pending = len([t for t in tasks_filtered if getattr(t, 'status', '') == 'pending'])
        in_progress = len([t for t in tasks_filtered if getattr(t, 'status', '') == 'in_progress'])
        completed = len([t for t in tasks_filtered if getattr(t, 'status', '') == 'completed'])
        on_hold = len([t for t in tasks_filtered if getattr(t, 'status', '') == 'on_hold'])
        
        all_projects = db.query(Project).all()
        project_names = sorted(list(set([getattr(p, 'project_name', '') for p in all_projects if not getattr(p, 'is_deleted', False) and getattr(p, 'project_name', '')])))
        
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
        task = db.query(Task).filter(task_id=request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        operator = db.query(User).filter(user_id=request.operator_id).first()
        if not operator:
            raise HTTPException(status_code=404, detail="Operator not found")
        
        if getattr(operator, 'role', '') == 'admin' and getattr(current_user, 'role', '') != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can assign tasks to other admins")
        
        task.assigned_to = request.operator_id
        task.status = 'pending'
        
        if request.machine_id:
            task.machine_id = request.machine_id
        if request.priority:
            task.priority = request.priority
        if request.expected_completion_time is not None:
            task.expected_completion_time = request.expected_completion_time
        if request.due_date:
            task.due_date = request.due_date.isoformat()
        
        db.commit()
        return {
            "message": "Task assigned successfully",
            "task": {
                "id": str(getattr(task, 'task_id', getattr(task, 'id', ''))),
                "title": getattr(task, 'title', ''),
                "assigned_to": str(getattr(task, 'assigned_to', '')),
                "status": getattr(task, 'status', '')
            }
        }
    except HTTPException: raise
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.get("/project-summary")
async def get_project_summary(db: any = Depends(get_db)):
    """Get project summary metrics"""
    try:
        tasks_with_projects = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and getattr(t, 'project', None)]
        
        project_map = {}
        for task in tasks_with_projects:
            p_name = getattr(task, 'project', 'Unknown')
            if p_name not in project_map:
                project_map[p_name] = []
            project_map[p_name].append(getattr(task, 'status', ''))
        
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
async def get_priority_task_status(db: any = Depends(get_db)):
    """Get task counts by priority level"""
    try:
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]

        high = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'HIGH'])
        medium = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'MEDIUM'])
        low = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'LOW'])
        
        return {
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priority task status: {str(e)}")
