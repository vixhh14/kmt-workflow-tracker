from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Any
from app.schemas.task_schema import OperationalTaskCreate, OperationalTaskUpdate, OperationalTaskOut
from app.models.models_db import FilingTask, FabricationTask, Project, User, Machine
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.time_utils import get_current_time_ist
from app.utils.datetime_utils import safe_datetime_diff
import uuid
from datetime import datetime

router = APIRouter(prefix="/operational-tasks", tags=["Operational Tasks"])

@router.get("/filing", response_model=List[OperationalTaskOut])
async def get_filing_tasks(db: Any = Depends(get_db)):
    """Get all filing tasks from cache."""
    tasks = db.query(FilingTask).filter(is_deleted=False).all()
    
    # Pre-load maps for efficiency (cached)
    projects = {str(p.id): p.project_name for p in db.query(Project).all()}
    machines = {str(m.id): m.machine_name for m in db.query(Machine).all()}

    results = []
    for t in tasks:
        data = t.dict()
        data['project_name'] = projects.get(str(getattr(t, 'project_id', '')), 'Unknown')
        data['machine_name'] = machines.get(str(getattr(t, 'machine_id', '')), 'Manual/None')
        results.append(data)
    return results

@router.get("/fabrication", response_model=List[OperationalTaskOut])
async def get_fabrication_tasks(db: Any = Depends(get_db)):
    """Get all fabrication tasks from cache."""
    tasks = db.query(FabricationTask).filter(is_deleted=False).all()
    
    # Pre-load maps (cached)
    projects = {str(p.id): p.project_name for p in db.query(Project).all()}
    machines = {str(m.id): m.machine_name for m in db.query(Machine).all()}

    results = []
    for t in tasks:
        data = t.dict()
        data['project_name'] = projects.get(str(getattr(t, 'project_id', '')), 'Unknown')
        data['machine_name'] = machines.get(str(getattr(t, 'machine_id', '')), 'Manual/None')
        results.append(data)
    return results

@router.post("/filing", response_model=OperationalTaskOut)
async def create_filing_task(data: OperationalTaskCreate, db: Any = Depends(get_db)):
    new_task = FilingTask(
        **data.dict(),
        created_at=get_current_time_ist().isoformat(),
        status="pending",
        is_deleted=False
    )
    db.add(new_task)
    db.commit()
    return new_task

@router.post("/fabrication", response_model=OperationalTaskOut)
async def create_fab_task(data: OperationalTaskCreate, db: Any = Depends(get_db)):
    new_task = FabricationTask(
        **data.dict(),
        created_at=get_current_time_ist().isoformat(),
        status="pending",
        is_deleted=False
    )
    db.add(new_task)
    db.commit()
    return new_task

@router.put("/filing/{task_id}", response_model=OperationalTaskOut)
async def update_filing_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FilingTask).filter(id=task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return task

@router.put("/fabrication/{task_id}", response_model=OperationalTaskOut)
async def update_fab_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FabricationTask).filter(id=task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return task
