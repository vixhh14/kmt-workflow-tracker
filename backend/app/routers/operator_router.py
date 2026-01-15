from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List, Optional, Any
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
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks assigned to a specific operator or the current one"""
    target_user_id = user_id if user_id else str(getattr(current_user, 'id', ''))
    
    # Permission Check: Only Admin/Supervisor can view others
    if target_user_id != str(getattr(current_user, 'id', '')):
        if getattr(current_user, 'role', '') not in ["admin", "supervisor", "planning"]:
            raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Load all needed data
        all_tasks = db.query(Task).all()
        tasks = [t for t in all_tasks if str(getattr(t, 'assigned_to', '')) == str(target_user_id) and not getattr(t, 'is_deleted', False)]
        
        all_users = db.query(User).all()
        user_map = {str(getattr(u, 'id', '')): u for u in all_users}
        
        all_machines = db.query(Machine).all()
        machine_map = {str(getattr(m, 'id', '')): m for m in all_machines}
        
        # Load holds for these tasks
        all_holds = db.query(TaskHold).all()
        
        task_list = []
        for task in tasks:
            assigned_by_user = user_map.get(str(getattr(task, 'assigned_by', '')))
            assigned_by_name = getattr(assigned_by_user, 'username', 'Unknown') if assigned_by_user else "Unknown"
            machine = machine_map.get(str(getattr(task, 'machine_id', '')))
            machine_name = getattr(machine, 'machine_name', 'Unknown') if machine else "Unknown"
            
            task_holds = [h for h in all_holds if str(getattr(h, 'task_id', '')) == str(getattr(task, 'id', ''))]
            holds = [
                {
                    "start": str(getattr(h, 'hold_started_at', '')),
                    "end": str(getattr(h, 'hold_ended_at', '')) if getattr(h, 'hold_ended_at', None) else None,
                    "reason": getattr(h, 'hold_reason', '') or ""
                }
                for h in task_holds
            ]
            
            task_list.append({
                "id": str(getattr(task, 'id', '')),
                "title": getattr(task, 'title', '') or "",
                "project": getattr(task, 'project', '') or "",
                "description": getattr(task, 'description', '') or "",
                "part_item": getattr(task, 'part_item', '') or "",
                "nos_unit": getattr(task, 'nos_unit', '') or "",
                "status": getattr(task, 'status', 'pending'),
                "priority": getattr(task, 'priority', 'medium'),
                "assigned_to": str(getattr(task, 'assigned_to', '')) if getattr(task, 'assigned_to', None) else "",
                "machine_id": str(getattr(task, 'machine_id', '')) if getattr(task, 'machine_id', None) else "",
                "machine_name": machine_name,
                "assigned_by": str(getattr(task, 'assigned_by', '')) if getattr(task, 'assigned_by', None) else "",
                "assigned_by_name": assigned_by_name,
                "due_date": str(getattr(task, 'due_date', '')) if getattr(task, 'due_date', None) else "",
                "created_at": str(getattr(task, 'created_at', '')) if getattr(task, 'created_at', None) else None,
                "started_at": str(getattr(task, 'started_at', '')) if getattr(task, 'started_at', None) else None,
                "completed_at": str(getattr(task, 'completed_at', '')) if getattr(task, 'completed_at', None) else None,
                "total_duration_seconds": int(getattr(task, 'total_duration_seconds', 0) or 0),
                "total_held_seconds": int(getattr(task, 'total_held_seconds', 0) or 0),
                "holds": holds
            })
        
        target_user = user_map.get(target_user_id)
        return {
            "tasks": task_list,
            "stats": {
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if getattr(t, 'status', '') == 'completed']),
                "in_progress_tasks": len([t for t in tasks if getattr(t, 'status', '') == 'in_progress']),
                "pending_tasks": len([t for t in tasks if getattr(t, 'status', '') == 'pending']),
                "on_hold_tasks": len([t for t in tasks if getattr(t, 'status', '') == 'on_hold'])
            },
            "user": {
                "id": str(target_user_id),
                "username": getattr(target_user, 'username', 'Unknown') if target_user else "Unknown",
                "full_name": getattr(target_user, 'full_name', '') or getattr(target_user, 'username', 'Unknown') if target_user else "Unknown"
            }
        }
    except Exception as e:
        print(f"Error in operator tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/start")
async def start_task(
    task_id: str, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    if str(getattr(task, 'assigned_to', '')) != current_uid and getattr(current_user, 'role', '') != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    task_status = getattr(task, 'status', 'pending')
    if task_status in ['completed', 'ended']:
        raise HTTPException(status_code=400, detail=f"Task is already {task_status}")

    now = get_current_time_ist().isoformat()
    task.status = 'in_progress'
    task.started_at = now
    if not getattr(task, 'actual_start_time', None):
        task.actual_start_time = now

    # Logging
    today = get_today_date_ist().isoformat()
    m_id = getattr(task, 'machine_id', None)
    if m_id:
        db.add(MachineRuntimeLog(id=str(uuid4()), machine_id=m_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(id=str(uuid4()), user_id=getattr(task, 'assigned_to', current_uid), task_id=task_id, machine_id=m_id, start_time=now, date=today))
    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='start', timestamp=now))
    
    db.commit()
    return {"message": "Task started", "status": task.status}

@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id==task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    if str(getattr(task, 'assigned_to', '')) != current_uid and getattr(current_user, 'role', '') != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    now_dt = get_current_time_ist()
    now_iso = now_dt.isoformat()
    
    # Close hold
    all_holds = db.query(TaskHold).all()
    open_hold = next((h for h in all_holds if str(getattr(h, 'task_id', '')) == str(task_id) and not getattr(h, 'hold_ended_at', None)), None)
    if open_hold:
        open_hold.hold_ended_at = now_iso
        # Duration recalc could be here, but simpler to just set status
        # task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now_dt, datetime.fromisoformat(open_hold.hold_started_at))

    task.status = 'completed'
    task.completed_at = now_iso
    task.actual_end_time = now_iso
    
    # Duration calc (simplified for SheetsDB, assuming total_duration_seconds is updated elsewhere or not critical here)
    # start_time = task.actual_start_time or task.started_at
    # if start_time:
    #     duration = safe_datetime_diff(now_dt, datetime.fromisoformat(start_time))
    #     task.total_duration_seconds = int(max(0, duration - (task.total_held_seconds or 0)))

    # Close logs (simplified for SheetsDB, assuming logs are closed by a separate process or not critical here)
    # for m_log in db.query(MachineRuntimeLog).filter(MachineRuntimeLog.task_id == task_id, MachineRuntimeLog.end_time == None).all():
    #     m_log.end_time = now_iso
    #     m_log.duration_seconds = safe_datetime_diff(now_dt, datetime.fromisoformat(m_log.start_time))
        
    # for u_log in db.query(UserWorkLog).filter(UserWorkLog.task_id == task_id, UserWorkLog.end_time == None).all():
    #     u_log.end_time = now_iso
    #     u_log.duration_seconds = safe_datetime_diff(now_dt, datetime.fromisoformat(u_log.start_time))

    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='complete', timestamp=now_iso))
    db.commit()
    return {"message": "Task completed", "status": "completed"}

from app.schemas.hold_schema import HoldRequest

@router.put("/tasks/{task_id}/hold")
async def hold_task(
    task_id: str, 
    hold_data: HoldRequest,
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id==task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    if str(getattr(task, 'assigned_to', '')) != current_uid and getattr(current_user, 'role', '') != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    if getattr(task, 'status', '') != 'in_progress':
        raise HTTPException(status_code=400, detail="Only in-progress tasks can be put on hold")

    now = get_current_time_ist().isoformat()
    task.status = 'on_hold'
    task.hold_reason = hold_data.reason or "On hold"
    
    db.add(TaskHold(id=str(uuid4()), task_id=task_id, user_id=getattr(task, 'assigned_to', current_uid), hold_reason=getattr(task, 'hold_reason', 'On hold'), hold_started_at=now))
    
    # Close logs (simplified for SheetsDB, assuming logs are closed by a separate process or not critical here)
    # for m_log in db.query(MachineRuntimeLog).filter(MachineRuntimeLog.task_id == task_id, MachineRuntimeLog.end_time == None).all():
    #     m_log.end_time = now
    #     m_log.duration_seconds = safe_datetime_diff(datetime.fromisoformat(now), datetime.fromisoformat(m_log.start_time))
        
    # for u_log in db.query(UserWorkLog).filter(UserWorkLog.task_id == task_id, UserWorkLog.end_time == None).all():
    #     u_log.end_time = now
    #     u_log.duration_seconds = safe_datetime_diff(datetime.fromisoformat(now), datetime.fromisoformat(u_log.start_time))

    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='hold', timestamp=now, reason=hold_data.reason))
    db.commit()
    return {"message": "Task on hold", "status": "on_hold"}

@router.put("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id==task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    
    current_uid = str(getattr(current_user, 'id', ''))
    if str(getattr(task, 'assigned_to', '')) != current_uid and getattr(current_user, 'role', '') != "admin":
        raise HTTPException(status_code=403, detail="Task not assigned to you")

    if getattr(task, 'status', '') != 'on_hold':
        raise HTTPException(status_code=400, detail="Only on-hold tasks can be resumed")

    now_dt = get_current_time_ist()
    now = now_dt.isoformat()
    
    all_holds = db.query(TaskHold).all()
    open_hold = next((h for h in all_holds if str(getattr(h, 'task_id', '')) == str(task_id) and not getattr(h, 'hold_ended_at', None)), None)
    if open_hold:
        open_hold.hold_ended_at = now
        # task.total_held_seconds = (task.total_held_seconds or 0) + int(safe_datetime_diff(now_dt, datetime.fromisoformat(open_hold.hold_started_at)))

    task.status = 'in_progress'
    task.started_at = now
    
    today = get_today_date_ist().isoformat()
    m_id = getattr(task, 'machine_id', None)
    if m_id:
        db.add(MachineRuntimeLog(id=str(uuid4()), machine_id=m_id, task_id=task_id, start_time=now, date=today))
    db.add(UserWorkLog(id=str(uuid4()), user_id=getattr(task, 'assigned_to', current_uid), task_id=task_id, machine_id=m_id, start_time=now, date=today))
    db.add(TaskTimeLog(id=str(uuid4()), task_id=task_id, action='resume', timestamp=now))
    
    db.commit()
    return {"message": "Task resumed", "status": "in_progress"}
