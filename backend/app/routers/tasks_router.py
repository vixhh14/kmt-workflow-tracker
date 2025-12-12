from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.tasks_model import TaskCreate, TaskUpdate
from app.models.models_db import Task, TaskTimeLog, TaskHold, RescheduleRequest
from app.core.database import get_db
from app.core.dependencies import get_current_user
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

class TaskActionRequest(BaseModel):
    reason: Optional[str] = None

class RescheduleRequestModel(BaseModel):
    requested_date: datetime
    reason: str

@router.get("/", response_model=List[dict])
async def read_tasks(
    month: Optional[int] = None,
    year: Optional[int] = None,
    assigned_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    
    # Filter by month and year if provided
    if month is not None and year is not None:
        from sqlalchemy import extract
        query = query.filter(
            extract('month', Task.created_at) == month,
            extract('year', Task.created_at) == year
        )
    elif year is not None:
        from sqlalchemy import extract
        query = query.filter(extract('year', Task.created_at) == year)
    
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    tasks = query.all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "project": t.project,
            "part_item": t.part_item,
            "nos_unit": t.nos_unit,
            "status": t.status,
            "priority": t.priority,
            "assigned_by": t.assigned_by,
            "assigned_to": t.assigned_to,
            "machine_id": t.machine_id,
            "due_date": t.due_date,
            "expected_completion_time": t.expected_completion_time,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "total_duration_seconds": t.total_duration_seconds,
            "hold_reason": t.hold_reason,
            "denial_reason": t.denial_reason,
            "actual_start_time": t.actual_start_time.isoformat() if t.actual_start_time else None,
            "actual_end_time": t.actual_end_time.isoformat() if t.actual_end_time else None,
            "total_held_seconds": t.total_held_seconds,
        }
        for t in tasks
    ]

@router.post("/", response_model=dict)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    from app.models.models_db import User
    
    # Validate assigned_to is an operator
    if task.assigned_to:
        assignee = db.query(User).filter(User.user_id == task.assigned_to).first()
        if not assignee or assignee.role != 'operator':
            raise HTTPException(status_code=400, detail="Tasks can only be assigned to operators")

    # Validate assigned_by is admin/supervisor/planning
    if task.assigned_by:
        assigner = db.query(User).filter(User.user_id == task.assigned_by).first()
        if not assigner or assigner.role not in ['admin', 'supervisor', 'planning']:
            raise HTTPException(status_code=400, detail="Tasks can only be assigned by admin, supervisor, or planning")

    new_task = Task(
        id=str(uuid.uuid4()),
        title=task.title,
        description=task.description,
        project=task.project,
        part_item=task.part_item,
        nos_unit=task.nos_unit,
        status=task.status,
        priority=task.priority,
        assigned_by=task.assigned_by,
        assigned_to=task.assigned_to,
        machine_id=task.machine_id,
        due_date=task.due_date,
        expected_completion_time=task.expected_completion_time,
        created_at=datetime.utcnow(),
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "project": new_task.project,
        "part_item": new_task.part_item,
        "nos_unit": new_task.nos_unit,
        "status": new_task.status,
        "priority": new_task.priority,
        "assigned_by": new_task.assigned_by,
        "assigned_to": new_task.assigned_to,
        "machine_id": new_task.machine_id,
        "due_date": new_task.due_date,
        "expected_completion_time": new_task.expected_completion_time,
    }

# Get task time logs for a specific task
@router.get("/{task_id}/time-logs", response_model=List[dict])
async def get_task_time_logs(task_id: str, db: Session = Depends(get_db)):
    """Get all time tracking logs for a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logs = db.query(TaskTimeLog).filter(TaskTimeLog.task_id == task_id).order_by(TaskTimeLog.timestamp.asc()).all()
    
    return [
        {
            "id": log.id,
            "task_id": log.task_id,
            "action": log.action,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "reason": log.reason,
        }
        for log in logs
    ]

# Task workflow endpoints
@router.post("/{task_id}/start")
async def start_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in ["pending", "on_hold"]:
        if task.status == "in_progress":
             return {"message": "Task already in progress", "started_at": task.started_at.isoformat() if task.started_at else None}
        raise HTTPException(status_code=400, detail="Task must be pending or on hold to start")

    now = datetime.utcnow()
    
    # Set actual start time if not set
    if not task.actual_start_time:
        task.actual_start_time = now
    
    # Close any open holds (if resuming)
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        held_duration = (now - open_hold.hold_started_at).total_seconds()
        task.total_held_seconds = (task.total_held_seconds or 0) + int(held_duration)

    task.status = "in_progress"
    task.started_at = now # Session start
    task.hold_reason = None # Clear hold reason
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="start",
        timestamp=now,
    )
    db.add(log)
    db.commit()
    return {
        "message": "Task started", 
        "started_at": task.started_at.isoformat(),
        "actual_start_time": task.actual_start_time.isoformat()
    }

@router.post("/{task_id}/hold")
async def hold_task(
    task_id: str, 
    request: TaskActionRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in ["in_progress", "pending"]:
        # Allow re-holding if it was somehow interrupted, but generally should be in progress
        # If it's already on hold, just update the reason?
        if task.status == "on_hold":
             return {"message": "Task is already on hold", "reason": task.hold_reason}
        raise HTTPException(status_code=400, detail="Task must be in progress or pending to hold")
    
    now = datetime.utcnow()
    
    # If holding an in-progress task, calculate session duration
    if task.status == "in_progress" and task.started_at:
        duration = (now - task.started_at).total_seconds()
        task.total_duration_seconds = (task.total_duration_seconds or 0) + int(duration)
    
    task.status = "on_hold"
    task.hold_reason = request.reason
    task.started_at = None  # Clear session start
    
    # Create TaskHold record
    hold = TaskHold(
        task_id=task_id,
        user_id=current_user.get("user_id"),
        hold_reason=request.reason,
        hold_started_at=now
    )
    db.add(hold)
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="hold",
        timestamp=now,
        reason=request.reason,
    )
    db.add(log)
    db.commit()
    return {"message": "Task put on hold successfully", "status": "on_hold", "reason": request.reason}

@router.post("/{task_id}/resume")
async def resume_task(task_id: str, db: Session = Depends(get_db)):
    return await start_task(task_id, db)

@router.post("/{task_id}/complete")
async def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task must be in progress to complete")
    
    now = datetime.utcnow()
    
    if not task.actual_end_time:
        task.actual_end_time = now
        
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        held_duration = (now - open_hold.hold_started_at).total_seconds()
        task.total_held_seconds = (task.total_held_seconds or 0) + int(held_duration)

    # Calculate final duration
    # Logic: Total Time = (End Time - Start Time) - Total Held Time
    if task.actual_start_time:
        total_elapsed = (task.actual_end_time - task.actual_start_time).total_seconds()
        held_time = task.total_held_seconds or 0
        task.total_duration_seconds = max(0, int(total_elapsed - held_time))
    else:
        # Fallback if actual_start_time is missing (legacy tasks)
        if task.started_at:
             # If we have a session start time, add the current session to total
            duration = (now - task.started_at).total_seconds()
            task.total_duration_seconds = (task.total_duration_seconds or 0) + int(duration)
        elif task.created_at:
             # Last resort: created_at
            total_elapsed = (now - task.created_at).total_seconds()
            task.total_duration_seconds = max(0, int(total_elapsed))

    task.status = "completed"
    task.completed_at = now
    task.started_at = None # Clear active session
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="complete",
        timestamp=now,
    )
    db.add(log)
    db.commit()
    return {
        "message": "Task completed successfully",
        "status": "completed",
        "completed_at": task.completed_at.isoformat(),
        "total_duration_seconds": task.total_duration_seconds,
        "actual_end_time": task.actual_end_time.isoformat()
    }

@router.post("/{task_id}/reschedule-request")
async def request_reschedule(
    task_id: str, 
    request: RescheduleRequestModel, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    reschedule = RescheduleRequest(
        task_id=task_id,
        requested_by=current_user.get("user_id"),
        requested_for_date=request.requested_date,
        reason=request.reason,
        status="pending"
    )
    db.add(reschedule)
    db.commit()
    return {"message": "Reschedule request submitted"}

@router.post("/{task_id}/deny")
async def deny_task(task_id: str, request: TaskActionRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "denied"
    task.denial_reason = request.reason
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="deny",
        timestamp=datetime.utcnow(),
        reason=request.reason,
    )
    db.add(log)
    db.commit()
    return {"message": "Task denied", "reason": request.reason}

@router.put("/{task_id}", response_model=dict)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "project": db_task.project,
        "part_item": db_task.part_item,
        "nos_unit": db_task.nos_unit,
        "status": db_task.status,
        "priority": db_task.priority,
        "assigned_by": db_task.assigned_by,
        "assigned_to": db_task.assigned_to,
        "machine_id": db_task.machine_id,
        "due_date": db_task.due_date,
        "expected_completion_time": db_task.expected_completion_time,
        "started_at": db_task.started_at.isoformat() if db_task.started_at else None,
        "completed_at": db_task.completed_at.isoformat() if db_task.completed_at else None,
        "total_duration_seconds": db_task.total_duration_seconds,
        "hold_reason": db_task.hold_reason,
        "denial_reason": db_task.denial_reason,
    }

@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
