from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, TaskTimeLog, TaskHold, User, Machine
from uuid import uuid4

router = APIRouter(
    prefix="/operator",
    tags=["operator"],
    responses={404: {"description": "Not found"}},
)

@router.get("/tasks")
async def get_operator_tasks(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all tasks assigned to a specific operator.
    """
    try:
        # Fetch tasks assigned to this operator
        tasks = db.query(Task).filter(Task.assigned_to == user_id).all()
        
        # Get user info
        user = db.query(User).filter(User.user_id == user_id).first()
        
        # Fetch all users for name mapping
        all_users = db.query(User).all()
        user_map = {u.user_id: u for u in all_users}
        
        # Fetch all machines for name mapping
        machines = db.query(Machine).all()
        machine_map = {m.id: m for m in machines}
        
        task_list = []
        for task in tasks:
            # Safe duration calculation
            duration_seconds = task.total_duration_seconds or 0
            
            # Get assigned by user name
            assigned_by_user = user_map.get(task.assigned_by)
            assigned_by_name = assigned_by_user.username if assigned_by_user else "Unknown"
            
            # Get machine name
            machine = machine_map.get(task.machine_id)
            machine_name = machine.name if machine else "Unknown"
            
            task_data = {
                "id": task.id,
                "title": task.title or "",
                "project": task.project or "",
                "description": task.description or "",
                "part_item": task.part_item or "",
                "nos_unit": task.nos_unit or "",
                "status": task.status or "pending",
                "priority": task.priority or "medium",
                "assigned_to": task.assigned_to or "",
                "machine_id": task.machine_id or "",
                "machine_name": machine_name,
                "assigned_by": task.assigned_by or "",
                "assigned_by_name": assigned_by_name,
                "due_date": task.due_date or "",
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "actual_start_time": task.actual_start_time.isoformat() if task.actual_start_time else None,
                "actual_end_time": task.actual_end_time.isoformat() if task.actual_end_time else None,
                "total_duration_seconds": duration_seconds,
                "total_held_seconds": task.total_held_seconds or 0,
                "hold_reason": task.hold_reason or "",
                "denial_reason": task.denial_reason or "",
                "expected_completion_time": task.expected_completion_time or ""
            }
            task_list.append(task_data)
        
        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        in_progress_tasks = len([t for t in tasks if t.status == 'in_progress'])
        pending_tasks = len([t for t in tasks if t.status == 'pending'])
        on_hold_tasks = len([t for t in tasks if t.status == 'on_hold'])
        
        # Calculate completion rate with -2% rule
        completion_rate = 0
        if total_tasks > 0:
            raw_rate = (completed_tasks / total_tasks) * 100
            completion_rate = max(0, raw_rate - 2)
        
        return {
            "tasks": task_list,
            "stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "pending_tasks": pending_tasks,
                "on_hold_tasks": on_hold_tasks,
                "completion_rate": round(completion_rate, 2)
            },
            "user": {
                "user_id": user.user_id if user else user_id,
                "username": user.username if user else "Unknown",
                "full_name": user.full_name if user and user.full_name else (user.username if user else "Unknown")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch operator tasks: {str(e)}")


@router.put("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a task - updates status to in_progress and records start time.
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status == 'in_progress':
            raise HTTPException(status_code=400, detail="Task is already in progress")
        
        if task.status == 'completed':
            raise HTTPException(status_code=400, detail="Task is already completed")
        
        # Update task
        now = datetime.utcnow()
        task.status = 'in_progress'
        
        # Set started_at only if it hasn't been set yet
        if not task.started_at:
            task.started_at = now
        
        # Always update actual_start_time when starting (for resuming from hold)
        task.actual_start_time = now
        
        # Log the action
        time_log = TaskTimeLog(
            id=str(uuid4()),
            task_id=task_id,
            action='start',
            timestamp=now
        )
        db.add(time_log)
        
        db.commit()
        db.refresh(task)
        
        return {
            "message": "Task started successfully",
            "task": {
                "id": task.id,
                "status": task.status,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "actual_start_time": task.actual_start_time.isoformat() if task.actual_start_time else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Complete a task - updates status, records completion time, and calculates duration.
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status == 'completed':
            raise HTTPException(status_code=400, detail="Task is already completed")
        
        if task.status == 'pending':
            raise HTTPException(status_code=400, detail="Cannot complete a task that hasn't been started")
        
        # Update task
        now = datetime.utcnow()
        task.status = 'completed'
        task.completed_at = now
        task.actual_end_time = now
        
        # Calculate total duration
        if task.actual_start_time:
            duration = (now - task.actual_start_time).total_seconds()
            # Subtract held time if any
            held_seconds = task.total_held_seconds or 0
            task.total_duration_seconds = int(max(0, duration - held_seconds))
        elif task.started_at:
            # Fallback to started_at if actual_start_time is missing
            duration = (now - task.started_at).total_seconds()
            held_seconds = task.total_held_seconds or 0
            task.total_duration_seconds = int(max(0, duration - held_seconds))
        else:
            # No start time recorded, just set to 0
            task.total_duration_seconds = 0
        
        # Log the action
        time_log = TaskTimeLog(
            id=str(uuid4()),
            task_id=task_id,
            action='complete',
            timestamp=now
        )
        db.add(time_log)
        
        db.commit()
        db.refresh(task)
        
        return {
            "message": "Task completed successfully",
            "task": {
                "id": task.id,
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "actual_end_time": task.actual_end_time.isoformat() if task.actual_end_time else None,
                "total_duration_seconds": task.total_duration_seconds or 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")


@router.put("/tasks/{task_id}/hold")
async def hold_task(
    task_id: str,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """
    Put a task on hold - updates status and records hold time.
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != 'in_progress':
            raise HTTPException(status_code=400, detail="Only in-progress tasks can be put on hold")
        
        if task.status == 'completed':
            raise HTTPException(status_code=400, detail="Cannot hold a completed task")
        
        # Update task
        now = datetime.utcnow()
        task.status = 'on_hold'
        task.hold_reason = reason or "On hold"
        
        # Create hold record
        task_hold = TaskHold(
            task_id=task_id,
            user_id=task.assigned_to,
            hold_reason=reason or "On hold",
            hold_started_at=now
        )
        db.add(task_hold)
        
        # Calculate held time from actual_start_time to now if task was in progress
        if task.actual_start_time:
            # This hold session starts counting from now
            # We'll calculate total held time when task is resumed or completed
            pass
        
        # Log the action
        time_log = TaskTimeLog(
            id=str(uuid4()),
            task_id=task_id,
            action='hold',
            timestamp=now,
            reason=reason
        )
        db.add(time_log)
        
        db.commit()
        db.refresh(task)
        
        return {
            "message": "Task put on hold successfully",
            "task": {
                "id": task.id,
                "status": task.status,
                "hold_reason": task.hold_reason
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to hold task: {str(e)}")


@router.put("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Resume a task from on_hold status.
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != 'on_hold':
            raise HTTPException(status_code=400, detail="Only on-hold tasks can be resumed")
        
        now = datetime.utcnow()
        
        # Find the most recent open hold record
        latest_hold = db.query(TaskHold).filter(
            and_(
                TaskHold.task_id == task_id,
                TaskHold.hold_ended_at == None
            )
        ).order_by(TaskHold.hold_started_at.desc()).first()
        
        if latest_hold:
            # Close this hold session
            latest_hold.hold_ended_at = now
            
            # Calculate held duration for this session
            hold_duration = (now - latest_hold.hold_started_at).total_seconds()
            
            # Add to total held time
            current_held = task.total_held_seconds or 0
            task.total_held_seconds = int(current_held + hold_duration)
        
        # Update task status
        task.status = 'in_progress'
        task.actual_start_time = now  # Reset actual start time for the resumed work session
        
        # Log the action
        time_log = TaskTimeLog(
            id=str(uuid4()),
            task_id=task_id,
            action='resume',
            timestamp=now
        )
        db.add(time_log)
        
        db.commit()
        db.refresh(task)
        
        return {
            "message": "Task resumed successfully",
            "task": {
                "id": task.id,
                "status": task.status,
                "total_held_seconds": task.total_held_seconds or 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resume task: {str(e)}")
