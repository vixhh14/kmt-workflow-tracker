from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.schemas.task_schema import OperationalTaskCreate, OperationalTaskUpdate, OperationalTaskOut
from app.models.models_db import FilingTask, FabricationTask, Project, User, Machine
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.time_utils import get_current_time_ist
from app.utils.datetime_utils import safe_datetime_diff

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
        try:
            # Resolve names
            project_name = t.project.project_name if t.project else None
            machine_name = t.machine.machine_name if t.machine else "Unknown Machine"
            
            # Manually resolve assignee name since we removed the relationship
            assignee_name = t.assigned_to
            if t.assigned_to:
                assignee_obj = db.query(User).filter(User.user_id == t.assigned_to).first()
                if not assignee_obj:
                    assignee_obj = db.query(User).filter(User.username == t.assigned_to).first()
                if assignee_obj:
                    assignee_name = assignee_obj.full_name or assignee_obj.username
            
            # Use t.__dict__ but carefully avoid internal SA state
            task_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
            
            # 🛡️ DEFENSIVE DATA NORMALIZATION 🛡️
            # Ensure IDs are strings to satisfy Pydantic strictness if validators miss edge cases
            if task_dict.get("project_id") is not None:
                task_dict["project_id"] = str(task_dict["project_id"])
            if task_dict.get("machine_id") is not None:
                task_dict["machine_id"] = str(task_dict["machine_id"])
            
            # Ensure safe string defaults for optional text fields
            if task_dict.get("remarks") is None:
                 task_dict["remarks"] = ""
            if task_dict.get("status") is None:
                 task_dict["status"] = "Pending"

            # Validate via Pydantic model
            serialized_task = OperationalTaskOut(
                **task_dict,
                project_name=project_name,
                machine_name=machine_name,
                assignee_name=assignee_name
            )
            results.append(serialized_task)
            
        except Exception as e:
            # 🛡️ FAIL-SAFE: Log error and skip bad row, do NOT crash endpoint 🛡️
            print(f"⚠️ Skipping corrupted task {getattr(t, 'id', 'unknown')} in {task_type}: {str(e)}")
            continue

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
    task_data = {
        "project_id": task.project_id,
        "work_order_number": task.work_order_number,
        "part_item": task.part_item,
        "quantity": task.quantity,
        "due_date": task.due_date,
        "priority": (task.priority or "MEDIUM").upper(),
        "remarks": task.remarks,
        "assigned_by": current_user.user_id,
        "assigned_to": task.assigned_to, # Use provided value
        "status": "Pending"
    }

    # Automatic Assignment based on task_type if NOT provided
    if not task_data["assigned_to"]:
        target_role = None
        target_username = None

        if task_type.lower() == "filing":
            target_username = "FILE_MASTER"
            target_role = "file_master"
        elif task_type.lower() == "fabrication":
            target_username = "FAB_MASTER"
            target_role = "fab_master"
        
        if target_username:
            # 1. Try by username (case-insensitive)
            assignee = db.query(User).filter(User.username.ilike(target_username)).first()
            
            # 2. If not found, try by role
            if not assignee and target_role:
                 assignee = db.query(User).filter(User.role == target_role).first()

            if assignee:
                task_data["assigned_to"] = assignee.user_id
            else:
                print(f"Warning: Master user '{target_username}' not found for auto-assignment")
                task_data["assigned_to"] = None

    try:
        new_task = model(**task_data)
        new_task.created_at = get_current_time_ist()
        new_task.updated_at = get_current_time_ist()
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Resolve names for response manually
        project_name = new_task.project.project_name if new_task.project else None
        machine_name = new_task.machine.machine_name if new_task.machine else "Unknown Machine"
        
        assignee_name = new_task.assigned_to
        if new_task.assigned_to:
            assignee_obj = db.query(User).filter(User.user_id == new_task.assigned_to).first()
            if not assignee_obj:
                 assignee_obj = db.query(User).filter(User.username == new_task.assigned_to).first()
            if assignee_obj:
                assignee_name = assignee_obj.full_name or assignee_obj.username

        task_dict = {c.name: getattr(new_task, c.name) for c in new_task.__table__.columns}
        
        # 🛡️ DEFENSIVE Serialization 🛡️
        if task_dict.get("project_id") is not None:
             task_dict["project_id"] = str(task_dict["project_id"])
        if task_dict.get("machine_id") is not None:
             task_dict["machine_id"] = str(task_dict["machine_id"])

        return OperationalTaskOut(
            **task_dict,
            project_name=project_name,
            machine_name=machine_name,
            assignee_name=assignee_name
        )
    except Exception as e:
        db.rollback()
        print(f"Error creating operational task: {str(e)}")
        import traceback
        traceback.print_exc()
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
                 # Allow manual string assignment if user not found
                 update_data["assigned_to"] = assigned_to

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
        execution_fields = ["assigned_to", "completed_quantity", "remarks", "status", "started_at", "on_hold_at", "resumed_at", "completed_at", "total_active_duration", "machine_id", "work_order_number"]
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
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref:
                duration = safe_datetime_diff(now, start_ref)
                db_task.total_active_duration = (db_task.total_active_duration or 0) + duration
            db_task.resumed_at = None

        # IN PROGRESS -> COMPLETED
        elif new_status == "Completed":
            db_task.completed_at = now
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref and current_status == "In Progress":
                duration = safe_datetime_diff(now, start_ref)
                db_task.total_active_duration = (db_task.total_active_duration or 0) + duration
            db_task.resumed_at = None
            db_task.on_hold_at = None
            db_task.completed_quantity = db_task.quantity

    # Auto status update
    if db_task.completed_quantity >= db_task.quantity and db_task.status != "Completed":
        db_task.status = "Completed"
        db_task.completed_at = now
        if current_status == "In Progress":
            start_ref = db_task.resumed_at or db_task.started_at
            if start_ref:
                duration = safe_datetime_diff(now, start_ref)
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
    
    # Manually resolve assignee name
    assignee_name = db_task.assigned_to
    if db_task.assigned_to:
        assignee_obj = db.query(User).filter(User.user_id == db_task.assigned_to).first()
        if not assignee_obj:
            assignee_obj = db.query(User).filter(User.username == db_task.assigned_to).first()
        if assignee_obj:
            assignee_name = assignee_obj.full_name or assignee_obj.username
    
    # Construct response with new fields
    task_dict = {c.name: getattr(db_task, c.name) for c in db_task.__table__.columns}
    
    # 🛡️ DEFENSIVE Serialization 🛡️
    if task_dict.get("project_id") is not None:
         task_dict["project_id"] = str(task_dict["project_id"])
    if task_dict.get("machine_id") is not None:
         task_dict["machine_id"] = str(task_dict["machine_id"])

    # Ensure datetimes are serialized if they aren't already handled by Pydantic
    return OperationalTaskOut(
        **task_dict,
        project_name=project_name,
        machine_name=machine_name,
        assignee_name=assignee_name
    )

@router.get("/user/{user_id}", response_model=List[OperationalTaskOut])
async def get_user_operational_tasks(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all operational tasks (filing & fabrication) assigned to a specific user"""
    # Filtering and role check if needed, but usually admin/masters can see this
    
    filing_tasks = db.query(FilingTask).filter(
        FilingTask.assigned_to == user_id,
        or_(FilingTask.is_deleted == False, FilingTask.is_deleted == None)
    ).all()
    
    fabrication_tasks = db.query(FabricationTask).filter(
        FabricationTask.assigned_to == user_id,
        or_(FabricationTask.is_deleted == False, FabricationTask.is_deleted == None)
    ).all()
    
    all_tasks = filing_tasks + fabrication_tasks
    # Sort by created_at desc
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    results = []
    for t in all_tasks:
        try:
            project_name = t.project.project_name if t.project else None
            machine_name = t.machine.machine_name if t.machine else "Unknown Machine"
            
            # Manually resolve assignee name
            assignee_name = t.assigned_to
            if t.assigned_to:
                assignee_obj = db.query(User).filter(User.user_id == t.assigned_to).first()
                if not assignee_obj:
                    assignee_obj = db.query(User).filter(User.username == t.assigned_to).first()
                if assignee_obj:
                    assignee_name = assignee_obj.full_name or assignee_obj.username
            
            task_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
            # Add task_type since we are mixing them
            task_dict["task_type"] = "FILING" if isinstance(t, FilingTask) else "FABRICATION"
            
             # 🛡️ DEFENSIVE DATA NORMALIZATION 🛡️
            if task_dict.get("project_id") is not None:
                task_dict["project_id"] = str(task_dict["project_id"])
            if task_dict.get("machine_id") is not None:
                task_dict["machine_id"] = str(task_dict["machine_id"])
            if task_dict.get("remarks") is None:
                 task_dict["remarks"] = ""

            results.append(OperationalTaskOut(
                **task_dict,
                project_name=project_name,
                machine_name=machine_name,
                assignee_name=assignee_name
            ))
        except Exception as e:
            print(f"⚠️ Skipping corrupted task {getattr(t, 'id', 'unknown')} for user {user_id}: {str(e)}")
            continue

    return results

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
