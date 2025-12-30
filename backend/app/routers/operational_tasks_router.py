from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.schemas.task_schema import OperationalTaskCreate, OperationalTaskUpdate, OperationalTaskOut
from app.models.models_db import FilingTask, FabricationTask, Project, User, Machine
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.time_utils import get_current_time_ist

router = APIRouter(
    prefix="/operational-tasks",
    tags=["operational-tasks"],
)

def get_model(task_type: str):
    if task_type == "filing":
        return FilingTask
    elif task_type == "fabrication":
        return FabricationTask
    else:
        raise HTTPException(status_code=400, detail="Invalid task type")

@router.get("/{task_type}", response_model=List[OperationalTaskOut])
async def read_operational_tasks(
    task_type: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    model = get_model(task_type)
    query = db.query(model).filter(or_(model.is_deleted == False, model.is_deleted == None))
    
    # Role-based filtering
    role = (current_user.role or "").lower()
    user_id = current_user.user_id
    
    # Admin and Planning see all
    if role in ["admin", "planning"]:
        pass
    # Filing Master
    elif role == "file_master":
        if task_type != "filing":
             raise HTTPException(status_code=403, detail="File Masters can only access filing tasks")
    # Fab Master
    elif role == "fab_master":
        if task_type != "fabrication":
             raise HTTPException(status_code=403, detail="Fab Masters can only access fabrication tasks")
    # Operators see only assigned to them or unassigned
    elif role == "operator":
        query = query.filter(or_(model.assigned_to == user_id, model.assigned_to == None))
    else:
        # Other roles might also be restricted
        raise HTTPException(status_code=403, detail=f"Unauthorized role '{role}' for operational tasks")
        
    tasks = query.order_by(model.created_at.desc()).all()
    
    results = []
    for t in tasks:
        # Resolve names
        project_name = t.project.project_name if t.project else None
        machine_name = t.machine.machine_name if t.machine else "Unknown Machine"
        assignee_name = t.assignee.full_name or t.assignee.username if t.assignee else None
        
        # Use t.__dict__ but carefully avoid internal SA state
        task_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
        
        results.append(OperationalTaskOut(
            **task_dict,
            project_name=project_name,
            machine_name=machine_name,
            assignee_name=assignee_name
        ))
    return results

@router.post("/{task_type}", response_model=OperationalTaskOut)
async def create_operational_task(
    task_type: str, 
    task: OperationalTaskCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admin (and maybe Planning) can create
    if current_user.role not in ["admin", "planning"]:
        raise HTTPException(status_code=403, detail="Only Admin or Planning can create operational tasks")
        
    # Manual Validation: Only these 7 fields are mandatory/expected for Filing/Fabrication
    if not task.project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    if not task.work_order_number or not task.work_order_number.strip():
        raise HTTPException(status_code=400, detail="work_order_number is required")
    if not task.part_item or not task.part_item.strip():
        raise HTTPException(status_code=400, detail="part_item is required")
    if task.quantity is None or task.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be greater than 0")
    if not task.due_date:
        raise HTTPException(status_code=400, detail="due_date is required")

    model = get_model(task_type)
    
    # Normalization & Defaults
    # Pull ONLY the fields the user wants to avoid "extra field" issues
    task_data = {
        "project_id": task.project_id,
        "work_order_number": task.work_order_number,
        "part_item": task.part_item,
        "quantity": task.quantity,
        "due_date": task.due_date,
        "priority": (task.priority or "MEDIUM").upper(),
        "remarks": task.remarks,
        "assigned_by": current_user.user_id,
        "status": "Pending"
    }

    # Automatic Assignment based on task_type
    if task_type.lower() == "filing":
        assigned_to_username = "FILE_MASTER"
    elif task_type.lower() == "fabrication":
        assigned_to_username = "FAB_MASTER"
    else:
        assigned_to_username = None

    if assigned_to_username:
        # Resolve username to user_id
        assignee = db.query(User).filter(User.username == assigned_to_username).first()
        if assignee:
            task_data["assigned_to"] = assignee.user_id
        else:
            # Fallback for masters: if they don't exist, we still create the task but warn (or just set to None)
            # The UI expects these to exist.
            print(f"Warning: Master user {assigned_to_username} not found for auto-assignment")
            task_data["assigned_to"] = None

    try:
        new_task = model(**task_data)
        new_task.created_at = get_current_time_ist()
        new_task.updated_at = get_current_time_ist()
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except Exception as e:
        db.rollback()
        print(f"Error creating operational task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error during creation: {str(e)}")

@router.put("/{task_type}/{task_id}", response_model=OperationalTaskOut)
async def update_operational_task(
    task_type: str, 
    task_id: int, 
    task_update: OperationalTaskUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    model = get_model(task_type)
    db_task = db.query(model).filter(model.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    role = current_user.role
    update_data = task_update.dict(exclude_unset=True)
    
    # Support username -> user_id conversion for assigned_to
    if "assigned_to" in update_data and update_data["assigned_to"]:
        assigned_to = update_data["assigned_to"]
        assignee = db.query(User).filter(User.user_id == assigned_to).first()
        if not assignee:
            assignee = db.query(User).filter(User.username == assigned_to).first()
            if assignee:
                update_data["assigned_to"] = assignee.user_id
            else:
                 raise HTTPException(status_code=400, detail=f"Assigned user '{assigned_to}' does not exist")

    # Execution-level fields can be updated by Masters or Admin
    current_status = db_task.status
    new_status = update_data.get("status")
    now = get_current_time_ist()

    if role == "admin":
        for key, value in update_data.items():
            setattr(db_task, key, value)
    elif (task_type == "filing" and role.lower() == "file_master") or \
         (task_type == "fabrication" and role.lower() == "fab_master") or \
         (role == "operator" and db_task.assigned_to == current_user.user_id):
        
        # Masters and assigned Operators can update status and execute
        execution_fields = ["assigned_to", "completed_quantity", "remarks", "status", "started_at", "on_hold_at", "resumed_at", "completed_at", "total_active_duration"]
        for key in execution_fields:
            if key in update_data:
                setattr(db_task, key, update_data[key])
    else:
        raise HTTPException(status_code=403, detail="You do not have permission to update this task")
    
    # --- STATUS FLOW & TIMESTAMP LOGIC ---
    if new_status and new_status != current_status:
        # PENDING -> IN PROGRESS
        if new_status == "In Progress":
            if not db_task.started_at:
                db_task.started_at = now
            db_task.resumed_at = now
            db_task.on_hold_at = None
        
        # IN PROGRESS -> ON HOLD
        elif new_status == "On Hold":
            db_task.on_hold_at = now
            # Calculate duration since last resume or start
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref:
                duration = int((now - start_ref).total_seconds())
                db_task.total_active_duration = (db_task.total_active_duration or 0) + duration
            db_task.resumed_at = None

        # IN PROGRESS -> COMPLETED
        elif new_status == "Completed":
            db_task.completed_at = now
            # Final duration calculation
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref and current_status == "In Progress":
                duration = int((now - start_ref).total_seconds())
                db_task.total_active_duration = (db_task.total_active_duration or 0) + duration
            db_task.resumed_at = None
            db_task.on_hold_at = None
            # Ensure quantity matches
            db_task.completed_quantity = db_task.quantity

    # Auto status update: Completed (auto when quantity matches)
    if db_task.completed_quantity >= db_task.quantity and db_task.status != "Completed":
        db_task.status = "Completed"
        db_task.completed_at = now
        # Also handle duration if it was in progress
        if current_status == "In Progress":
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref:
                duration = int((now - start_ref).total_seconds())
                db_task.total_active_duration = (db_task.total_active_duration or 0) + duration
        db_task.resumed_at = None
        db_task.on_hold_at = None
    elif db_task.completed_quantity > 0 and db_task.status == "Pending":
         db_task.status = "In Progress"
         if not db_task.started_at:
             db_task.started_at = now
         db_task.resumed_at = now

    db_task.updated_at = now
    db.commit()
    db.refresh(db_task)
    
    # Resolve names for response
    project_name = db_task.project.project_name if db_task.project else None
    machine_name = db_task.machine.machine_name if db_task.machine else "Unknown Machine"
    assignee_name = db_task.assignee.full_name or db_task.assignee.username if db_task.assignee else None
    
    # Construct response with new fields
    task_dict = {c.name: getattr(db_task, c.name) for c in db_task.__table__.columns}
    # Ensure datetimes are serialized if they aren't already handled by Pydantic
    return OperationalTaskOut(
        **task_dict,
        project_name=project_name,
        machine_name=machine_name,
        assignee_name=assignee_name
    )

@router.delete("/{task_type}/{task_id}")
async def delete_operational_task(
    task_type: str, 
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can delete tasks")
        
    model = get_model(task_type)
    db_task = db.query(model).filter(model.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.is_deleted = True
    db.commit()
    return {"message": "Task deleted successfully"}
