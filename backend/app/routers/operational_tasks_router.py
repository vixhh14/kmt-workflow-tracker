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

router = APIRouter(prefix="/operational", tags=["Operational Tasks"])

@router.get("/filing", response_model=List[OperationalTaskOut])
async def get_filing_tasks(db: Any = Depends(get_db)):
    tasks = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False)]
    for t in tasks:
        p = db.query(Project).filter(project_id=t.project_id).first()
        t.project_name = getattr(p, 'project_name', 'Unknown')
        m = db.query(Machine).filter(id=t.machine_id).first()
        t.machine_name = getattr(m, 'machine_name', 'Manual/None')
    return tasks

@router.get("/fabrication", response_model=List[OperationalTaskOut])
async def get_fabrication_tasks(db: Any = Depends(get_db)):
    tasks = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False)]
    for t in tasks:
        p = db.query(Project).filter(project_id=t.project_id).first()
        t.project_name = getattr(p, 'project_name', 'Unknown')
        m = db.query(Machine).filter(id=t.machine_id).first()
        t.machine_name = getattr(m, 'machine_name', 'Manual/None')
    return tasks

@router.post("/filing", response_model=OperationalTaskOut)
async def create_filing_task(data: OperationalTaskCreate, db: Any = Depends(get_db)):
    new_task = FilingTask(
        id=str(uuid.uuid4()),
        **data.dict(),
        created_at=datetime.now().isoformat(),
        status="pending",
        is_deleted=False
    )
    db.add(new_task)
    db.commit()
    return new_task

@router.post("/fabrication", response_model=OperationalTaskOut)
async def create_fab_task(data: OperationalTaskCreate, db: Any = Depends(get_db)):
    new_task = FabricationTask(
        id=str(uuid.uuid4()),
        **data.dict(),
        created_at=datetime.now().isoformat(),
        status="pending",
        is_deleted=False
    )
    db.add(new_task)
    db.commit()
    return new_task

@router.put("/filing/{task_id}", response_model=OperationalTaskOut)
async def update_filing_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FilingTask).filter(id=task_id).first()
    if not task: raise HTTPException(status_code=404)
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = datetime.now().isoformat()
    db.commit()
    return task

@router.put("/fabrication/{task_id}", response_model=OperationalTaskOut)
async def update_fab_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FabricationTask).filter(id=task_id).first()
    if not task: raise HTTPException(status_code=404)
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = datetime.now().isoformat()
    db.commit()
    return task
