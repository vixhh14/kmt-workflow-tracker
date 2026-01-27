from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Any
from app.models.models_db import Task, MachineRuntimeLog, UserWorkLog, TaskTimeLog, TaskHold, User
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.utils.datetime_utils import safe_datetime_diff
from app.utils.task_lookup import find_any_task
from pydantic import BaseModel
import uuid

router = APIRouter(
    prefix="/operator",
    tags=["operator"],
    responses={404: {"description": "Not found"}},
)

class TaskActionRequest(BaseModel):
    reason: Optional[str] = None

@router.get("/tasks")
async def get_operator_tasks(user_id: str, db: Any = Depends(get_db)):
    """Fetch all tasks assigned to a specific operator across all categories"""
    from app.models.models_db import FilingTask, FabricationTask
    from app.core.normalizer import safe_normalize_list, normalize_task_row
    
    try:
        # 1. Fetch from all sources
        tasks = [t for t in db.query(Task).all() if str(getattr(t, 'assigned_to', '')) == str(user_id) and not getattr(t, 'is_deleted', False)]
        tasks.extend([t for t in db.query(FilingTask).all() if str(getattr(t, 'assigned_to', '')) == str(user_id) and not getattr(t, 'is_deleted', False)])
        tasks.extend([t for t in db.query(FabricationTask).all() if str(getattr(t, 'assigned_to', '')) == str(user_id) and not getattr(t, 'is_deleted', False)])
        
        # 2. Extract stats
        task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tasks]
        normalized = safe_normalize_list(task_dicts, normalize_task_row, "task")
        
        # Get machine names
        from app.models.models_db import Machine
        machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): getattr(m, 'machine_name', '') for m in db.query(Machine).all()}
        
        for t in normalized:
            m_id = t.get('machine_id')
            if m_id and m_id in machine_map:
                t['machine_name'] = machine_map[m_id]

        target_user = db.query(User).filter(user_id=user_id).first()
        
        return {
            "tasks": normalized,
            "stats": {
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if str(getattr(t, 'status', '')).lower() == 'completed']),
                "in_progress_tasks": len([t for t in tasks if str(getattr(t, 'status', '')).lower() == 'in_progress']),
                "pending_tasks": len([t for t in tasks if str(getattr(t, 'status', 'pending')).lower() in ['pending', 'todo', 'active']]),
                "on_hold_tasks": len([t for t in tasks if str(getattr(t, 'status', '')).lower() == 'on_hold'])
            },
            "user": {
                "id": str(user_id),
                "username": getattr(target_user, 'username', 'Unknown') if target_user else "Unknown",
                "full_name": getattr(target_user, 'full_name', '') or getattr(target_user, 'username', 'Unknown') if target_user else "Unknown"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/start")
async def start_task(task_id: str, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    task, task_type = find_any_task(db, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    if str(getattr(task, 'assigned_to', '')) != current_uid and getattr(current_user, 'role', '') != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    task_status = str(getattr(task, 'status', 'pending')).lower()
    if task_status in ['completed', 'ended']:
        raise HTTPException(status_code=400, detail=f"Task is already {task_status}")

    now = get_current_time_ist().isoformat()
    task.status = 'in_progress'
    task.started_at = now
    if not getattr(task, 'actual_start_time', None):
        task.actual_start_time = now

    today = get_today_date_ist().isoformat()
    m_id = getattr(task, 'machine_id', None)
    if m_id: db.add(MachineRuntimeLog(machine_id=m_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(user_id=current_uid, task_id=task_id, machine_id=m_id, start_time=now, date=today))
    db.add(TaskTimeLog(task_id=task_id, action='start', timestamp=now))
    
    db.commit()
    return {"message": "Task started", "status": task.status}

@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    task, task_type = find_any_task(db, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    now = get_current_time_ist().isoformat()
    
    # Duration calc
    start_time = getattr(task, 'started_at', None)
    if start_time:
        duration = safe_datetime_diff(now, start_time)
        task.total_duration_seconds = int(getattr(task, 'total_duration_seconds', 0) or 0) + duration
        if task_type in ["filing", "fabrication"]:
            task.total_active_duration = int(getattr(task, 'total_active_duration', 0) or 0) + duration

    task.status = 'completed'
    task.completed_at = now
    task.actual_end_time = now
    
    if task_type in ["filing", "fabrication"] and not getattr(task, 'completed_quantity', 0):
        task.completed_quantity = getattr(task, 'quantity', 1)

    db.add(TaskTimeLog(task_id=task_id, action='complete', timestamp=now))
    
    # Close logs
    m_id = getattr(task, 'machine_id', None)
    for log in db.query(MachineRuntimeLog).filter(task_id=task_id).all():
        if not getattr(log, 'end_time', None):
            log.end_time = now
            log.duration_seconds = safe_datetime_diff(now, log.start_time)
    for log in db.query(UserWorkLog).filter(task_id=task_id).all():
        if not getattr(log, 'end_time', None):
            log.end_time = now
            log.duration_seconds = safe_datetime_diff(now, log.start_time)

    db.commit()
    return {"message": "Task completed", "status": task.status}

@router.put("/tasks/{task_id}/hold")
async def hold_task(task_id: str, request: TaskActionRequest, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    task, task_type = find_any_task(db, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")

    now = get_current_time_ist().isoformat()
    reason = request.reason or "No reason provided"
    
    # Duration before hold
    start_time = getattr(task, 'started_at', None)
    if start_time:
        duration = safe_datetime_diff(now, start_time)
        task.total_duration_seconds = int(getattr(task, 'total_duration_seconds', 0) or 0) + duration
        if task_type in ["filing", "fabrication"]:
            task.total_active_duration = int(getattr(task, 'total_active_duration', 0) or 0) + duration

    task.status = 'on_hold'
    task.hold_reason = reason
    if task_type in ["filing", "fabrication"]: task.on_hold_at = now
    
    db.add(TaskHold(task_id=task_id, user_id=str(current_user.id), hold_reason=reason, hold_started_at=now))
    db.add(TaskTimeLog(task_id=task_id, action='hold', timestamp=now, reason=reason))
    
    # Close logs
    for log in db.query(MachineRuntimeLog).filter(task_id=task_id).all():
        if not getattr(log, 'end_time', None):
            log.end_time = now
            log.duration_seconds = safe_datetime_diff(now, log.start_time)
    for log in db.query(UserWorkLog).filter(task_id=task_id).all():
        if not getattr(log, 'end_time', None):
            log.end_time = now
            log.duration_seconds = safe_datetime_diff(now, log.start_time)

    db.commit()
    return {"message": "Task on hold", "status": task.status}

@router.put("/tasks/{task_id}/resume")
async def resume_task(task_id: str, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    task, task_type = find_any_task(db, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")

    now = get_current_time_ist().isoformat()
    
    # Hold duration tracking
    if task_type in ["filing", "fabrication"]:
        hold_at = getattr(task, 'on_hold_at', None)
        if hold_at:
            h_dur = safe_datetime_diff(now, hold_at)
            task.total_held_seconds = int(getattr(task, 'total_held_seconds', 0) or 0) + h_dur
        task.resumed_at = now

    task.status = 'in_progress'
    task.started_at = now
    
    # Close hold rec
    all_holds = db.query(TaskHold).all()
    open_hold = next((h for h in all_holds if str(h.task_id) == str(task_id) and not getattr(h, 'hold_ended_at', None)), None)
    if open_hold: open_hold.hold_ended_at = now

    today = get_today_date_ist().isoformat()
    m_id = getattr(task, 'machine_id', None)
    if m_id: db.add(MachineRuntimeLog(machine_id=m_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(user_id=str(current_user.id), task_id=task_id, machine_id=m_id, start_time=now, date=today))
    db.add(TaskTimeLog(task_id=task_id, action='resume', timestamp=now))
    
    db.commit()
    return {"message": "Task resumed", "status": task.status}
