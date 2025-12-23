from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
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
    current_user: dict = Depends(get_current_user)
):
    model = get_model(task_type)
    tasks = db.query(model).order_by(model.created_at.desc()).all()
    
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
    current_user: dict = Depends(get_current_user)
):
    # Only Admin (and maybe Planning) can create
    if current_user.get("role") not in ["admin", "planning"]:
        raise HTTPException(status_code=403, detail="Only Admin or Planning can create operational tasks")
        
    model = get_model(task_type)
    new_task = model(**task.dict())
    new_task.created_at = get_current_time_ist()
    new_task.updated_at = get_current_time_ist()
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/{task_type}/{task_id}", response_model=OperationalTaskOut)
async def update_operational_task(
    task_type: str, 
    task_id: int, 
    task_update: OperationalTaskUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    model = get_model(task_type)
    db_task = db.query(model).filter(model.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    role = current_user.get("role")
    update_data = task_update.dict(exclude_unset=True)
    
    # Execution-level fields can be updated by Masters or Admin
    # Admin can update everything
    if role == "admin":
        for key, value in update_data.items():
            setattr(db_task, key, value)
    elif (task_type == "filing" and role == "file_master") or (task_type == "fabrication" and role == "fab_master"):
        # Masters can only update execution fields
        execution_fields = ["assigned_to", "completed_quantity", "remarks", "status"]
        for key in execution_fields:
            if key in update_data:
                setattr(db_task, key, update_data[key])
    else:
        raise HTTPException(status_code=403, detail="You do not have permission to update this task")
    
    # Auto status update: Completed (auto when quantity matches)
    if db_task.completed_quantity >= db_task.quantity:
        db_task.status = "Completed"
    elif db_task.completed_quantity > 0 and db_task.status == "Pending":
         db_task.status = "In Progress"

    db_task.updated_at = get_current_time_ist()
    db.commit()
    db.refresh(db_task)
    
    # Resolve names for response
    project_name = db_task.project.project_name if db_task.project else None
    machine_name = db_task.machine.machine_name if db_task.machine else "Unknown Machine"
    assignee_name = db_task.assignee.full_name or db_task.assignee.username if db_task.assignee else None
    
    task_dict = {c.name: getattr(db_task, c.name) for c in db_task.__table__.columns}
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
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can delete tasks")
        
    model = get_model(task_type)
    db_task = db.query(model).filter(model.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
