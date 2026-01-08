from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskOut
from app.models.models_db import Task, TaskTimeLog, TaskHold, RescheduleRequest, MachineRuntimeLog, UserWorkLog, User
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.utils.datetime_utils import safe_datetime_diff
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

@router.get("", response_model=List[TaskOut])
async def read_tasks(
    month: Optional[int] = None,
    year: Optional[int] = None,
    assigned_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Role-based restriction: Operators only see their own tasks
    if current_user.role == "operator":
        assigned_to = current_user.user_id

    query = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None))
    
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
    
    # Sort by deadline (closest first), then by creation date (newest first)
    query = query.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
    
    tasks = query.all()
    results = []
    for t in tasks:
        try:
            # Resolve Project Name if missing (Backward compatibility)
            resolved_project = t.project
            if (not resolved_project or resolved_project == '-') and t.project_id:
                from app.models.models_db import Project as DBProject
                p_obj = db.query(DBProject).filter(DBProject.project_id == t.project_id).first()
                if p_obj:
                    resolved_project = p_obj.project_name
                    # Optional: Sync it back to DB if missing
                    t.project = resolved_project
                    db.commit()

            # Construct dictionary for TaskOut
            task_data = {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "project": resolved_project or "-",
                "project_id": str(t.project_id) if t.project_id else None,
                "part_item": t.part_item,
                "nos_unit": t.nos_unit,
                "status": t.status,
                "priority": t.priority,
                "assigned_by": t.assigned_by,
                "assigned_to": t.assigned_to,
                "machine_id": str(t.machine_id) if t.machine_id else None,
                "due_date": t.due_date,

                "created_at": t.created_at,
                "started_at": t.started_at,
                "completed_at": t.completed_at,
                "total_duration_seconds": t.total_duration_seconds or 0,
                "hold_reason": t.hold_reason,
                "denial_reason": t.denial_reason,
                "actual_start_time": t.actual_start_time,
                "actual_end_time": t.actual_end_time,
                "total_held_seconds": t.total_held_seconds or 0,
                "work_order_number": t.work_order_number
            }
            
            results.append(task_data)
        except Exception as e:
            print(f"⚠️ Skipping corrupted task {getattr(t, 'id', 'unknown')}: {e}")
            continue
    return results

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    task: TaskCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models_db import User, Project as DBProject
    
    # 1. Input Validation
    if not task.work_order_number or not task.work_order_number.strip():
        raise HTTPException(status_code=400, detail="Work Order Number is required")
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")
    if not task.machine_id:
        raise HTTPException(status_code=400, detail="Machine assignment is required")

    # 2. Assignee Resolution
    assigned_to = task.assigned_to
    if assigned_to:
        assignee = db.query(User).filter(User.user_id == assigned_to, or_(User.is_deleted == False, User.is_deleted == None)).first()
        if not assignee:
            # Fallback: check if it's a username
            assignee = db.query(User).filter(User.username == assigned_to, or_(User.is_deleted == False, User.is_deleted == None)).first()
            if assignee:
                assigned_to = assignee.user_id 
            else:
                 raise HTTPException(status_code=400, detail=f"Assigned user '{assigned_to}' does not exist or is inactive")

    # 3. Project Validation & Sync
    project_name = task.project.strip() if task.project else "-"
    if task.project_id:
        project_exists = db.query(DBProject).filter(DBProject.project_id == task.project_id).first()
        if not project_exists:
            raise HTTPException(status_code=400, detail=f"Selected project (ID: {task.project_id}) not found")
        project_name = project_exists.project_name

    # 4. Normalization
    priority_norm = (task.priority or "MEDIUM").upper()
    if priority_norm not in ["LOW", "MEDIUM", "HIGH"]:
        priority_norm = "MEDIUM"
    assigned_by = current_user.user_id

    try:
        new_task = Task(
            title=task.title.strip(),
            description=task.description.strip() if task.description else None,
            project=project_name,
            project_id=task.project_id,
            part_item=task.part_item.strip() if task.part_item else None,
            nos_unit=task.nos_unit.strip() if task.nos_unit else None,
            status=task.status or "pending",
            priority=priority_norm,
            assigned_by=assigned_by,
            assigned_to=assigned_to,
            machine_id=task.machine_id,
            due_date=task.due_date,

            work_order_number=task.work_order_number.strip(),
            created_at=get_current_time_ist(),
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Return as dict to be safe with response_model=dict
        task_dict = {c.name: getattr(new_task, c.name) for c in new_task.__table__.columns}
        # Ensure datetimes are ISO strings for the dict
        for key, value in task_dict.items():
            if isinstance(value, datetime):
                task_dict[key] = value.isoformat()
        
        return task_dict
    except Exception as e:
        db.rollback()
        print(f"❌ DB Error in create_task: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Critical database error: {str(e)}")

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
async def start_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in ["pending", "on_hold"]:
        if task.status == "in_progress":
             return {"message": "Task already in progress", "started_at": task.started_at.isoformat() if task.started_at else None}
        if task.status == "ended":
             raise HTTPException(status_code=400, detail="Task has been ended by admin and cannot be started")
        raise HTTPException(status_code=400, detail="Task must be pending or on hold to start")

    now = get_current_time_ist()
    today = get_today_date_ist()
    
    # Set actual start time if not set
    if not task.actual_start_time:
        task.actual_start_time = now
    
    # Close any open holds (if resuming)
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now, open_hold.hold_started_at)

    task.status = "in_progress"
    task.started_at = now # Session start
    task.hold_reason = None # Clear hold reason
    
    # --- LOGGING START ---
    # 1. Machine Runtime Log
    if task.machine_id:
        machine_log = MachineRuntimeLog(
            machine_id=task.machine_id,
            task_id=task_id,
            start_time=now,
            date=today
        )
        db.add(machine_log)
        
    # 2. User Work Log
    user_log = UserWorkLog(
        user_id=current_user.user_id,
        task_id=task_id,
        machine_id=task.machine_id,
        start_time=now,
        date=today
    )
    db.add(user_log)
    # --- LOGGING END ---

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
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in ["in_progress", "pending"]:
        if task.status == "on_hold":
             return {"message": "Task is already on hold", "reason": task.hold_reason}
        raise HTTPException(status_code=400, detail="Task must be in progress or pending to hold")
    
    now = get_current_time_ist()
    
    # If holding an in-progress task, calculate session duration
    if task.status == "in_progress" and task.started_at:
        duration = safe_datetime_diff(now, task.started_at)
        task.total_duration_seconds = (task.total_duration_seconds or 0) + duration

        # --- LOGGING CLOSE ---
        # Close open machine logs
        open_machine_logs = db.query(MachineRuntimeLog).filter(
            MachineRuntimeLog.task_id == task_id,
            MachineRuntimeLog.end_time == None
        ).all()
        for m_log in open_machine_logs:
            m_log.end_time = now
            m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
            
        # Close open user logs
        open_user_logs = db.query(UserWorkLog).filter(
            UserWorkLog.task_id == task_id,
            UserWorkLog.end_time == None
        ).all()
        for u_log in open_user_logs:
            u_log.end_time = now
            u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)
        # --- LOGGING END ---
    
    task.status = "on_hold"
    task.hold_reason = request.reason
    task.started_at = None  # Clear session start
    
    # Create TaskHold record
    hold = TaskHold(
        task_id=task_id,
        user_id=current_user.user_id,
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
async def resume_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await start_task(task_id, db, current_user)

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task must be in progress to complete")
    
    now = get_current_time_ist()
    
    if not task.actual_end_time:
        task.actual_end_time = now
        
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now, open_hold.hold_started_at)

    # Calculate final duration
    # Logic: Total Time = (End Time - Start Time) - Total Held Time
    if task.actual_start_time:
        total_elapsed = safe_datetime_diff(task.actual_end_time, task.actual_start_time)
        held_time = task.total_held_seconds or 0
        task.total_duration_seconds = max(0, int(total_elapsed - held_time))
    else:
        # Fallback if actual_start_time is missing (legacy tasks)
        if task.started_at:
            # If we have a session start time, add the current session to total
            duration = safe_datetime_diff(now, task.started_at)
            task.total_duration_seconds = (task.total_duration_seconds or 0) + duration
        elif task.created_at:
            # Last resort: created_at
            total_elapsed = safe_datetime_diff(now, task.created_at)
            task.total_duration_seconds = max(0, total_elapsed)

    # --- LOGGING CLOSE ---
    # Close open machine logs
    open_machine_logs = db.query(MachineRuntimeLog).filter(
        MachineRuntimeLog.task_id == task_id,
        MachineRuntimeLog.end_time == None
    ).all()
    for m_log in open_machine_logs:
        m_log.end_time = now
        m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)

    # Close open user logs
    open_user_logs = db.query(UserWorkLog).filter(
        UserWorkLog.task_id == task_id,
        UserWorkLog.end_time == None
    ).all()
    for u_log in open_user_logs:
        u_log.end_time = now
        u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)
    # --- LOGGING END ---

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
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    reschedule = RescheduleRequest(
        task_id=task_id,
        requested_by=current_user.user_id,
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
        timestamp=get_current_time_ist(),
        reason=request.reason,
    )
    db.add(log)
    db.commit()
    return {"message": "Task denied", "reason": request.reason}

@router.post("/{task_id}/end")
async def end_task(
    task_id: str, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user) # We will check role inside or via dependency if strict
):
    """Admin action to force-end a task"""
    from app.models.models_db import User
    
    # Check if admin
    user_id = admin_user.user_id
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.role not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Only admins and supervisors can end tasks")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = get_current_time_ist()
    
    # Close any open intervals
    if task.status == "in_progress":
        # Calculate duration
        if task.started_at:
            duration = safe_datetime_diff(now, task.started_at)
            task.total_duration_seconds = (task.total_duration_seconds or 0) + duration
        
        # Close logs
        for m_log in db.query(MachineRuntimeLog).filter(MachineRuntimeLog.task_id == task_id, MachineRuntimeLog.end_time == None).all():
            m_log.end_time = now
            m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
            
        for u_log in db.query(UserWorkLog).filter(UserWorkLog.task_id == task_id, UserWorkLog.end_time == None).all():
            u_log.end_time = now
            u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)

    # Close open hold
    open_hold = db.query(TaskHold).filter(TaskHold.task_id == task_id, TaskHold.hold_ended_at == None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now, open_hold.hold_started_at)

    task.status = "ended"
    if not task.actual_end_time:
        task.actual_end_time = now
    task.completed_at = now
    task.started_at = None
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action="end_by_admin",
        timestamp=now,
    )
    db.add(log)
    db.commit()
    return {"message": "Task ended successfully by admin", "status": "ended"}

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str, 
    task_update: TaskUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models_db import Project as DBProject
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    role = current_user.role
    update_data = task_update.dict(exclude_unset=True)

    # Restriction: Operators can only update basic workflow fields if assigned
    if role == "operator":
        if db_task.assigned_to != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not assigned to this task")
        # Allowed fields for operator: maybe just notes?
        # But status is changed via specialized endpoints.
        allowed_operator_fields = ["description"] # 'description' is often used as notes
        for key in list(update_data.keys()):
            if key not in allowed_operator_fields:
                del update_data[key]
    elif role not in ["admin", "planning", "supervisor"]:
         # Masters don't usually manage general tasks, but let's allow read-only
         raise HTTPException(status_code=403, detail="Not authorized to edit general tasks")

    # Sync project name if project_id is updated
    if 'project_id' in update_data and update_data['project_id']:
        p_obj = db.query(DBProject).filter(DBProject.project_id == update_data['project_id']).first()
        if p_obj:
            update_data['project'] = p_obj.project_name
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "project": db_task.project,
        "project_id": db_task.project_id,
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
        "work_order_number": db_task.work_order_number,
    }

@router.delete("/{task_id}")
async def delete_task(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "supervisor", "planning"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete tasks")
        
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.is_deleted = True
    db.commit()
    return {"message": "Task deleted successfully"}
