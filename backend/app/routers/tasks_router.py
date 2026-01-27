from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Any
from pydantic import BaseModel
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskOut, TaskActionRequest, RescheduleRequestModel
from app.models.models_db import Task, TaskTimeLog, TaskHold, RescheduleRequest, MachineRuntimeLog, UserWorkLog, User
from app.core.database import get_db
from app.core.sheets_db import SHEETS_SCHEMA
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
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Role-based restriction: Operators only see their own tasks
    if current_user.role == "operator":
        assigned_to = str(getattr(current_user, 'id', ''))

    # Get all tasks that are not deleted (from cache)
    all_tasks = db.query(Task).all()
    tasks = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]
    
    # Filter by month and year
    if year or month:
        from datetime import datetime
        filtered_tasks = []
        for t in tasks:
            created = getattr(t, 'created_at', None)
            if not created: continue
            try:
                if isinstance(created, str):
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                else:
                    dt = created
                    
                if year and dt.year != year: continue
                if month and dt.month != month: continue
                filtered_tasks.append(t)
            except:
                filtered_tasks.append(t)
        tasks = filtered_tasks
    
    if assigned_to:
        tasks = [t for t in tasks if str(getattr(t, 'assigned_to', '')) == str(assigned_to)]
    
    # Sort
    def sort_key(t):
        due = str(getattr(t, 'due_date', '') or "9999-12-31")
        created = str(getattr(t, 'created_at', '') or "1970-01-01")
        return (due, created)
        
    tasks.sort(key=sort_key)
    
    # Load projects once (cached)
    all_projects = db.query("Project").all()
    project_map = {str(getattr(p, 'id', '')): getattr(p, 'project_name', '') for p in all_projects if not getattr(p, 'is_deleted', False)}
    
    # Load Users Map (Cached)
    from app.models.models_db import User, Machine
    all_users = db.query(User).all()
    user_map = {str(getattr(u, 'user_id', getattr(u, 'id', ''))): u.dict() if hasattr(u, 'dict') else u.__dict__ for u in all_users}
    
    # Load Machines Map (Cached)
    all_machines = db.query(Machine).all()
    machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m.dict() if hasattr(m, 'dict') else m.__dict__ for m in all_machines}

    # Helper imports
    from app.core.normalizer import safe_normalize_list, normalize_task_row, safe_str, safe_int

    # Convert tasks to dicts for normalizer
    task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tasks]

    # Normalize ALL tasks
    normalized_tasks = safe_normalize_list(
        task_dicts,
        normalize_task_row,
        "task"
    )

    results = []
    for t in normalized_tasks:
        try:
            # Enrich with Names
            
            # Resolve Project Name
            project_name = t.get('project', '')
            project_id = t.get('project_id', '')
            
            if (not project_name or project_name == '-') and project_id:
                project_name = project_map.get(project_id, "-")
            elif project_name == '-' and project_id in project_map:
                project_name = project_map[project_id]
                
            if project_id and project_id not in project_map:
                # Try to find project by name mismatch? No, just keep what we have
                pass
                
            # Resolve Assigned To
            assignee_id = t.get('assigned_to', '')
            assignee_name = user_map.get(assignee_id, {}).get("username", assignee_id)
            
            # Resolve Assigned By
            assigner_id = t.get('assigned_by', '')
            assigner_name = user_map.get(assigner_id, {}).get("username", assigner_id)
            
            # Resolve Machine
            m_id = t.get('machine_id', '')
            machine_name = machine_map.get(m_id, {}).get("machine_name", m_id) if m_id else None

            # Resolve Due Date (Fallback to due_datetime)
            due = t.get('due_date') or t.get('due_datetime') or ""

            # Build final dict matching TaskOut schema
            task_data = {
                "id": t['task_id'],
                "task_id": t['task_id'],
                "title": t['title'],
                "description": t['description'],
                "project": project_name,
                "project_id": t.get('project_id', ''),
                "part_item": t['part_item'],
                "nos_unit": t['nos_unit'],
                "status": t['status'],
                "priority": t['priority'],
                "assigned_by": assigner_name,
                "assigned_to": assignee_name,
                "machine_id": machine_name,
                "due_date": due,
                "created_at": t['created_at'],
                "started_at": t['started_at'],
                "completed_at": t['completed_at'],
                "total_duration_seconds": t['total_duration_seconds'],
                "hold_reason": t['hold_reason'],
                "denial_reason": t['denial_reason'],
                "actual_start_time": t['actual_start_time'],
                "actual_end_time": t['actual_end_time'],
                "total_held_seconds": t['total_held_seconds'],
                "work_order_number": t['work_order_number'],
                "ended_by": t['ended_by'],
                "end_reason": t['end_reason'],
                "expected_completion_time": t['expected_completion_time']
            }
            results.append(task_data)
        except Exception as e:
            print(f"Error processing task {t.get('task_id')}: {e}")
            continue
            
    return results

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    task: TaskCreate, 
    db: Any = Depends(get_db),
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
        # Robust lookup: Check user_id, id, then username
        # Also robust check for is_deleted (string/bool)
        users = db.query(User).all()
        assignee = None
        for u in users:
            # Check deletion
            is_del = str(getattr(u, 'is_deleted', 'False')).lower()
            if is_del in ['true', '1', 'yes']: 
                continue
                
            # Check ID match
            uid = str(getattr(u, 'user_id', getattr(u, 'id', '')))
            if uid == str(assigned_to):
                assignee = u
                break
            
            # Check Username match
            if str(getattr(u, 'username', '')).lower() == str(assigned_to).lower():
                assignee = u
                break

        if assignee:
            assigned_to = str(getattr(assignee, 'user_id', getattr(assignee, 'id', '')))
            # Validate approval (relaxed)
            status = str(getattr(assignee, 'approval_status', '')).lower()
            if status in ['pending', 'rejected']:
                 raise HTTPException(status_code=400, detail=f"Assigned user '{assigned_to}' is pending approval")
        else:
             raise HTTPException(status_code=400, detail=f"Assigned user '{assigned_to}' does not exist or is inactive")

    # 3. Project Validation & Sync (Robust ID Check)
    project_name = task.project.strip() if task.project else "-"
    if task.project_id:
        p_str = str(task.project_id)
        all_projects = db.query(DBProject).all()
        project_match = None
        for p in all_projects:
            pid = str(getattr(p, 'project_id', getattr(p, 'id', '')))
            if pid == p_str:
                project_match = p
                break
        
        if not project_match:
             # Retry with just ID match if schema differs
             project_match = next((p for p in all_projects if str(getattr(p, 'id', '')) == p_str), None)

        if not project_match:
            raise HTTPException(status_code=400, detail=f"Selected project (ID: {task.project_id}) not found")
        project_name = project_match.project_name

    # 4. Normalization
    priority_norm = (task.priority or "MEDIUM").upper()
    if priority_norm not in ["LOW", "MEDIUM", "HIGH"]:
        priority_norm = "MEDIUM"
    assigned_by = str(getattr(current_user, 'id', ''))
    now_ist = get_current_time_ist().isoformat()
    t_id = str(uuid.uuid4())

    try:
        # 5. Build canonical row data (Plain Dictionary)
        # Replaces Task() instantiation to avoid keyword conflicts
        
        # Ensure expected_completion_time is set
        expected_time = int(task.expected_completion_time) if task.expected_completion_time else 0
        
        new_task_data = {
            "id": t_id,
            "title": task.title.strip(),
            "description": task.description.strip() if task.description else "",
            "project_id": task.project_id if task.project_id else "",
            "project": project_name,  # CRITICAL: Always set project name
            "part_item": task.part_item.strip() if task.part_item else "",  # CRITICAL: Set part_item
            "nos_unit": task.nos_unit.strip() if task.nos_unit else "",
            "status": task.status or "pending",
            "priority": priority_norm,
            "assigned_by": assigned_by,
            "assigned_to": str(assigned_to) if assigned_to else "",
            "machine_id": str(task.machine_id) if task.machine_id else "",
            "due_date": str(task.due_date) if task.due_date else "",  # CRITICAL: Set due_date in ISO format
            "work_order_number": task.work_order_number.strip(),
            "created_at": now_ist,
            "updated_at": now_ist,
            "is_deleted": False,
            "total_duration_seconds": 0,
            "total_held_seconds": 0,
            "expected_completion_time": expected_time
        }
        
        print(f"📝 Creating task with data:")
        print(f"   - Project: {project_name} (ID: {task.project_id})")
        print(f"   - Part/Item: {new_task_data['part_item']}")
        print(f"   - Due Date: {new_task_data['due_date']}")
        print(f"   - Expected Time: {expected_time} minutes")
        
        # 6. Insert directly via Sheets Repository
        from app.repositories.sheets_repository import sheets_repo
        inserted = sheets_repo.insert("tasks", new_task_data)
        
        # Ensure 'project' field is present for response (if not in inserted)
        if "project" not in inserted or not inserted["project"]:
            inserted["project"] = project_name
        if "part_item" not in inserted:
            inserted["part_item"] = new_task_data["part_item"]
        if "due_date" not in inserted:
            inserted["due_date"] = new_task_data["due_date"]
            
        print(f"✅ Task created successfully in GS: {t_id}")
        return inserted

    except Exception as e:
        print(f"❌ Error in create_task: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to write task to Google Sheets: {str(e)}")

# Get task time logs for a specific task
@router.get("/{task_id}/time-logs", response_model=List[dict])
async def get_task_time_logs(task_id: str, db: Any = Depends(get_db)):
    """Get all time tracking logs for a specific task"""
    task = db.query(Task).filter(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logs = db.query(TaskTimeLog).filter(task_id=task_id).all()
    
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
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(id=task_id).first()
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
    open_hold = db.query(TaskHold).filter(task_id=task_id, hold_ended_at=None).first()
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
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(task_id=task_id).first()
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
            task_id=task_id,
            end_time=None
        ).all()
        for m_log in open_machine_logs:
            m_log.end_time = now
            m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
            
        # Close open user logs
        open_user_logs = db.query(UserWorkLog).filter(
            task_id=task_id,
            end_time=None
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
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await start_task(task_id, db, current_user)

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(task_id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task must be in progress to complete")
    
    now = get_current_time_ist()
    
    if not task.actual_end_time:
        task.actual_end_time = now
        
    open_hold = db.query(TaskHold).filter(task_id=task_id, hold_ended_at=None).first()
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
        task_id=task_id,
        end_time=None
    ).all()
    for m_log in open_machine_logs:
        m_log.end_time = now
        m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)

    # Close open user logs
    open_user_logs = db.query(UserWorkLog).filter(
        task_id=task_id,
        end_time=None
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
    db: Any = Depends(get_db),
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
async def deny_task(task_id: str, request: TaskActionRequest, db: Any = Depends(get_db)):
    task = db.query(Task).filter(task_id=task_id).first()
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
    request: Optional[TaskActionRequest] = None,
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin/Supervisor action to force-end a task"""
    from app.models.models_db import User
    
    # Check if admin or supervisor
    if current_user.role not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Only admins and supervisors can end tasks")

    task = db.query(Task).filter(task_id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = get_current_time_ist()
    reason = request.reason if request else None
    
    # Close any open intervals
    if task.status == "in_progress":
        # Calculate duration
        if task.started_at:
            duration = safe_datetime_diff(now, task.started_at)
            task.total_duration_seconds = (task.total_duration_seconds or 0) + duration
        
        # Close logs
        for m_log in db.query(MachineRuntimeLog).filter(task_id=task_id, end_time=None).all():
            m_log.end_time = now
            m_log.duration_seconds = safe_datetime_diff(now, m_log.start_time)
            
        for u_log in db.query(UserWorkLog).filter(task_id=task_id, end_time=None).all():
            u_log.end_time = now
            u_log.duration_seconds = safe_datetime_diff(now, u_log.start_time)

    # Close open hold
    open_hold = db.query(TaskHold).filter(task_id=task_id, hold_ended_at=None).first()
    if open_hold:
        open_hold.hold_ended_at = now
        task.total_held_seconds = (task.total_held_seconds or 0) + safe_datetime_diff(now, open_hold.hold_started_at)

    task.status = "ended"
    if not task.actual_end_time:
        task.actual_end_time = now
    task.completed_at = now
    task.started_at = None
    
    # Audit fields
    task.ended_by = current_user.user_id # Store ID
    task.end_reason = reason
    
    action_key = f"end_by_{current_user.role}"
    
    log = TaskTimeLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        action=action_key,
        timestamp=now,
        reason=reason
    )
    db.add(log)
    db.commit()
    return {"message": f"Task ended successfully by {current_user.role}", "status": "ended"}

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str, 
    task_update: TaskUpdate, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models_db import Project as DBProject
    # Robust lookup for task_id (Checks both 'id' and 'task_id' aliases)
    all_tasks = db.query(Task).all()
    db_task = next((t for t in all_tasks if str(getattr(t, 'task_id', getattr(t, 'id', ''))) == str(task_id)), None)
    
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
        p_obj = db.query(DBProject).filter(project_id=update_data['project_id']).first()
        if p_obj:
            update_data['project'] = p_obj.project_name
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    return {
        "id": db_task.task_id,
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
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "supervisor", "planning"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete tasks")
        
    # Robust lookup for task_id (Checks both 'id' and 'task_id' aliases)
    all_tasks = db.query(Task).all()
    db_task = next((t for t in all_tasks if str(getattr(t, 'task_id', getattr(t, 'id', ''))) == str(task_id)), None)

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.is_deleted = True
    db.commit()
    return {"message": "Task deleted successfully"}
