from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.tasks_model import TaskCreate, TaskUpdate
from app.models.models_db import Task, TaskTimeLog
from app.core.database import get_db
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

class TaskActionRequest(BaseModel):
    reason: Optional[str] = None

@router.get("/", response_model=List[dict])
async def read_tasks(
    month: Optional[int] = None,
    year: Optional[int] = None,
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
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "total_duration_seconds": t.total_duration_seconds,
            "hold_reason": t.hold_reason,
            "denial_reason": t.denial_reason,
        }
        for t in tasks
    ]

@router.post("/", response_model=dict)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
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
    }

# Task workflow endpoints
@router.post("/{task_id}/start")
async def start_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task must be in pending status to start")
    task.status = "in_progress"
    task.started_at = datetime.utcnow()
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="start",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {"message": "Task started", "started_at": task.started_at.isoformat()}

@router.post("/{task_id}/hold")
async def hold_task(task_id: str, request: TaskActionRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task must be in progress to hold")
    
    # Calculate duration since start and add to total
    if task.started_at:
        duration = (datetime.utcnow() - task.started_at).total_seconds()
        task.total_duration_seconds = (task.total_duration_seconds or 0) + int(duration)
    
    task.status = "on_hold"
    task.hold_reason = request.reason
    task.started_at = None  # Clear started_at when holding
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="hold",
        timestamp=datetime.utcnow(),
        reason=request.reason,
    )
    db.add(log)
    db.commit()
    return {"message": "Task on hold", "reason": request.reason}

@router.post("/{task_id}/resume")
async def resume_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "on_hold":
        raise HTTPException(status_code=400, detail="Task must be on hold to resume")
    task.status = "in_progress"
    task.started_at = datetime.utcnow()
    task.hold_reason = None
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="resume",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {"message": "Task resumed"}

@router.post("/{task_id}/complete")
async def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task must be in progress to complete")
    if task.started_at:
        duration = (datetime.utcnow() - task.started_at).total_seconds()
        task.total_duration_seconds = (task.total_duration_seconds or 0) + int(duration)
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="complete",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {
        "message": "Task completed",
        "completed_at": task.completed_at.isoformat(),
        "total_duration_seconds": task.total_duration_seconds,
    }

@router.post("/{task_id}/deny")
async def deny_task(task_id: str, request: TaskActionRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending tasks can be denied")
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
