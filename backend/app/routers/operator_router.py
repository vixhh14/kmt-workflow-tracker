from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional
from app.core.database import get_db
from app.utils.datetime_utils import make_aware, safe_datetime_diff
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.models.models_db import Task, TaskTimeLog, TaskHold, User, Machine, MachineRuntimeLog, UserWorkLog
from uuid import uuid4
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/operator",
    tags=["operator"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

from app.schemas.dashboard_schema import OperatorDashboardOut

@router.get("/tasks", response_model=OperatorDashboardOut)
async def get_operator_tasks(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks assigned to a specific operator or the current one"""
    target_user_id = user_id if user_id else current_user.user_id
    
    # Permission Check: Only Admin/Supervisor can view others
    if target_user_id != current_user.user_id:
        if current_user.role not in ["admin", "supervisor", "planning"]:
            raise HTTPException(status_code=403, detail="Not authorized to view other users' tasks")

    try:
        tasks = db.query(Task).filter(Task.assigned_to == target_user_id, or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        user = db.query(User).filter(User.user_id == target_user_id).first()
        
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        machines = db.query(Machine).all()
        machine_map = {str(m.id): m for m in machines}
        
        task_list = []
        for task in tasks:
            duration_seconds = task.total_duration_seconds or 0
            assigned_by_user = user_map.get(task.assigned_by)
            assigned_by_name = assigned_by_user.username if assigned_by_user else "Unknown"
            machine = machine_map.get(str(task.machine_id))
            machine_name = machine.machine_name if machine else "Unknown"
            
            # Fetch hold history
            hold_history = db.query(TaskHold).filter(TaskHold.task_id == task.id).order_by(TaskHold.hold_started_at.asc()).all()
            holds = [
                {
                    "start": h.hold_started_at.isoformat() if h.hold_started_at else None,
                    "end": h.hold_ended_at.isoformat() if h.hold_ended_at else None,
                    "duration_seconds": int(safe_datetime_diff(h.hold_ended_at, h.hold_started_at)) if h.hold_ended_at and h.hold_started_at else 0,
                    "reason": h.hold_reason or ""
                }
                for h in hold_history
            ]
            
            task_data = {
                "id": str(task.id),
                "title": task.title or "",
                "project": task.project or "",
                "description": task.description or "",
                "part_item": task.part_item or "",
                "nos_unit": task.nos_unit or "",
                "status": task.status or "pending",
                "priority": task.priority or "medium",
                "assigned_to": str(task.assigned_to) if task.assigned_to else "",
                "machine_id": str(task.machine_id) if task.machine_id else "",
                "machine_name": machine_name,
                "assigned_by": str(task.assigned_by) if task.assigned_by else "",
                "assigned_by_name": assigned_by_name,
                "due_date": str(task.due_date) if task.due_date else "",
                "created_at": make_aware(task.created_at).isoformat() if task.created_at else None,
                "started_at": make_aware(task.started_at).isoformat() if task.started_at else None,
                "completed_at": make_aware(task.completed_at).isoformat() if task.completed_at else None,
                "total_duration_seconds": int(duration_seconds),
                "total_held_seconds": int(task.total_held_seconds or 0),
                "holds": holds
            }
            task_list.append(task_data)
        
        return {
            "tasks": task_list,
            "stats": {
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.status == 'completed']),
                "in_progress_tasks": len([t for t in tasks if t.status == 'in_progress']),
                "pending_tasks": len([t for t in tasks if t.status == 'pending']),
                "on_hold_tasks": len([t for t in tasks if t.status == 'on_hold'])
            },
            "user": {
                "user_id": str(user.user_id) if user else target_user_id,
                "username": user.username if user else "Unknown",
                "full_name": user.full_name or user.username if user else "Unknown"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch operator tasks: {str(e)}")

@router.put("/tasks/{task_id}/start")
async def start_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.assigned_to != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    if task.status in ['completed', 'ended']:
        raise HTTPException(status_code=400, detail=f"Task is already {task.status}")

    now = get_current_time_ist()
    task.status = 'in_progress'
    task.started_at = now
    if not task.actual_start_time:
        task.actual_start_time = now

    # Logging
    today = get_today_date_ist()
    if task.machine_id:
        db.add(MachineRuntimeLog(machine_id=task.machine_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(user_id=task.assigned_to, task_id=task_id, machine_id=task.machine_id, start_time=now, date=today))
    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='start', timestamp=now))
    
    db.commit()
    db.refresh(task)
    return {"message": "Task started", "status": task.status}

@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_to != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    now = get_current_time_ist()
    
    # Close hold
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now, open_hold.hold_started_at)

    task.status = 'completed'
    task.completed_at = now
    task.actual_end_time = now
    
    # Duration calc
    start_time = task.actual_start_time or task.started_at
    if start_time:
        duration = safe_datetime_diff(now, start_time)
        task.total_duration_seconds = int(max(0, duration - (task.total_held_seconds or 0)))

    # Close logs
    for m_log in db.query(MachineRuntimeLog).filter(MachineRuntimeLog.task_id == task_id, MachineRuntimeLog.end_time == None).all():
        m_log.end_time = now
        m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
        
    for u_log in db.query(UserWorkLog).filter(UserWorkLog.task_id == task_id, UserWorkLog.end_time == None).all():
        u_log.end_time = now
        u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)

    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='complete', timestamp=now))
    db.commit()
    return {"message": "Task completed", "status": "completed"}

from app.schemas.hold_schema import HoldRequest

@router.put("/tasks/{task_id}/hold")
async def hold_task(
    task_id: str, 
    hold_data: HoldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_to != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    if task.status != 'in_progress':
        raise HTTPException(status_code=400, detail="Only in-progress tasks can be put on hold")

    now = get_current_time_ist()
    task.status = 'on_hold'
    task.hold_reason = hold_data.reason or "On hold"
    
    db.add(TaskHold(task_id=task_id, user_id=task.assigned_to, hold_reason=task.hold_reason, hold_started_at=now))
    
    # Close logs
    for m_log in db.query(MachineRuntimeLog).filter(MachineRuntimeLog.task_id == task_id, MachineRuntimeLog.end_time == None).all():
        m_log.end_time = now
        m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
        
    for u_log in db.query(UserWorkLog).filter(UserWorkLog.task_id == task_id, UserWorkLog.end_time == None).all():
        u_log.end_time = now
        u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)

    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='hold', timestamp=now, reason=hold_data.reason))
    db.commit()
    return {"message": "Task on hold", "status": "on_hold"}

@router.put("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_to != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    if task.status != 'on_hold':
        raise HTTPException(status_code=400, detail="Only on-hold tasks can be resumed")

    now = get_current_time_ist()
    
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + int(safe_datetime_diff(now, open_hold.hold_started_at))

    task.status = 'in_progress'
    task.started_at = now
    
    today = get_today_date_ist()
    if task.machine_id:
        db.add(MachineRuntimeLog(machine_id=task.machine_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(user_id=task.assigned_to, task_id=task_id, machine_id=task.machine_id, start_time=now, date=today))
    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='resume', timestamp=now))
    
    db.commit()
    return {"message": "Task resumed", "status": "in_progress"}
