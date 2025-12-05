from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.planning_model import PlanningTaskCreate, PlanningTaskUpdate
from app.models.models_db import PlanningTask
from app.core.database import get_db
import uuid

router = APIRouter(
    prefix="/planning",
    tags=["planning"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# GET ALL PLANNING TASKS
# ----------------------------------------------------------------------
@router.get("/", response_model=List[dict])
async def read_planning_tasks(db: Session = Depends(get_db)):
    tasks = db.query(PlanningTask).all()
    return [
        {
            "id": t.id,
            "task_id": t.task_id,
            "project_name": t.project_name,
            "task_sequence": t.task_sequence,
            "assigned_supervisor": t.assigned_supervisor,
            "status": t.status,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in tasks
    ]

# ----------------------------------------------------------------------
# CREATE PLANNING TASK
# ----------------------------------------------------------------------
@router.post("/", response_model=dict)
async def create_planning_task(task: PlanningTaskCreate, db: Session = Depends(get_db)):
    new_task = PlanningTask(
        id=str(uuid.uuid4()),
        task_id=task.task_id,
        project_name=task.project_name,
        task_sequence=task.task_sequence,
        assigned_supervisor=task.assigned_supervisor,
        status=task.status,
        updated_at=datetime.utcnow(),
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {
        "id": new_task.id,
        "task_id": new_task.task_id,
        "project_name": new_task.project_name,
        "task_sequence": new_task.task_sequence,
        "assigned_supervisor": new_task.assigned_supervisor,
        "status": new_task.status,
        "updated_at": new_task.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# UPDATE PLANNING TASK
# ----------------------------------------------------------------------
@router.put("/{task_id}", response_model=dict)
async def update_planning_task(task_id: str, task_update: PlanningTaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(PlanningTask).filter(PlanningTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Planning task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    # Always bump the updated_at timestamp
    db_task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_task)
    
    return {
        "id": db_task.id,
        "task_id": db_task.task_id,
        "project_name": db_task.project_name,
        "task_sequence": db_task.task_sequence,
        "assigned_supervisor": db_task.assigned_supervisor,
        "status": db_task.status,
        "updated_at": db_task.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# DELETE PLANNING TASK
# ----------------------------------------------------------------------
@router.delete("/{task_id}")
async def delete_planning_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(PlanningTask).filter(PlanningTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Planning task not found")
    
    db.delete(db_task)
    db.commit()
    return {"message": "Planning task deleted successfully"}

@router.get("/overview")
async def get_planning_overview(db: Session = Depends(get_db)):
    from app.models.models_db import Task, User, Machine
    
    # 1. Running Projects Overview
    # Group tasks by project and calculate progress
    projects = {}
    tasks = db.query(Task).filter(Task.project != None).all()
    
    for task in tasks:
        if task.project not in projects:
            projects[task.project] = {
                "name": task.project,
                "total_tasks": 0,
                "completed_tasks": 0,
                "status": "pending" # pending, in_progress, completed
            }
        
        projects[task.project]["total_tasks"] += 1
        if task.status == "completed":
            projects[task.project]["completed_tasks"] += 1
    
    # Calculate status and percentage
    project_list = []
    for p_name, p_data in projects.items():
        if p_data["total_tasks"] > 0:
            percentage = (p_data["completed_tasks"] / p_data["total_tasks"]) * 100
            p_data["progress"] = round(percentage)
            
            if p_data["completed_tasks"] == p_data["total_tasks"]:
                p_data["status"] = "completed"
            elif p_data["completed_tasks"] > 0:
                p_data["status"] = "in_progress"
            
            project_list.append(p_data)
            
    # 2. Operator Working Status
    # Get all operators and check if they have an in_progress task
    operators = db.query(User).filter(User.role == "operator").all()
    operator_status = []
    
    for op in operators:
        current_task = db.query(Task).filter(
            Task.assigned_to == op.user_id,
            Task.status == "in_progress"
        ).first()
        
        status_data = {
            "id": op.user_id,
            "name": op.full_name or op.username,
            "status": "idle",
            "current_task": None,
            "machine": None
        }
        
        if current_task:
            status_data["status"] = "working"
            status_data["current_task"] = current_task.title
            if current_task.machine_id:
                machine = db.query(Machine).filter(Machine.id == current_task.machine_id).first()
                if machine:
                    status_data["machine"] = machine.name
        
        operator_status.append(status_data)
        
    return {
        "projects": project_list,
        "operators": operator_status
    }
