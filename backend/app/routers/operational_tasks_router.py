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
    tasks = db.query(FilingTask).all()
    
    # Pre-load maps for efficiency (cached)
    projects = {str(getattr(p, 'project_id', getattr(p, 'id', ''))): p.project_name for p in db.query(Project).all()}
    machines = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m.machine_name for m in db.query(Machine).all()}
    
    from app.core.normalizer import safe_normalize_list, normalize_task_row
    
    # Convert to dicts
    task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tasks]
    
    # Normalize with type='filing'
    normalized_tasks = safe_normalize_list(
        task_dicts,
        normalize_task_row,
        "filing"
    )

    results = []
    for t in normalized_tasks:
        # Enrich
        t['project_name'] = projects.get(str(t.get('project_id', '')), 'Unknown')
        t['machine_name'] = machines.get(str(t.get('machine_id', '')), 'Manual/None')
        results.append(t)
        
    return results

@router.get("/fabrication", response_model=List[OperationalTaskOut])
async def get_fabrication_tasks(db: Any = Depends(get_db)):
    """Get all fabrication tasks from cache."""
    tasks = db.query(FabricationTask).all()
    
    # Pre-load maps (cached)
    projects = {str(getattr(p, 'project_id', getattr(p, 'id', ''))): p.project_name for p in db.query(Project).all()}
    machines = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m.machine_name for m in db.query(Machine).all()}

    from app.core.normalizer import safe_normalize_list, normalize_task_row
    
    # Convert to dicts
    task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tasks]
    
    # Normalize with type='fabrication'
    normalized_tasks = safe_normalize_list(
        task_dicts,
        normalize_task_row,
        "fabrication"
    )

    results = []
    for t in normalized_tasks:
        # Enrich
        t['project_name'] = projects.get(str(t.get('project_id', '')), 'Unknown')
        t['machine_name'] = machines.get(str(t.get('machine_id', '')), 'Manual/None')
        results.append(t)
        
    return results

@router.post("/filing", response_model=OperationalTaskOut)
async def create_filing_task(data: OperationalTaskCreate, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new filing task with proper error handling"""
    try:
        task_id = str(uuid.uuid4())
        now = get_current_time_ist().isoformat()
        
        # Build task data dictionary
        task_data = data.dict()
        task_data['filing_task_id'] = task_id
        task_data['id'] = task_id
        task_data['created_at'] = now
        task_data['updated_at'] = now
        task_data['status'] = task_data.get('status', 'pending')
        task_data['is_deleted'] = False
        
        # Title comes from user input (not auto-generated)
        # If not provided, use part_item as fallback
        if not task_data.get('title'):
            task_data['title'] = task_data.get('part_item', 'Filing Task')
        
        # Auto-assign to FILE_MASTER if no assignee
        if not task_data.get('assigned_to'):
            file_masters = [u for u in db.query(User).all() if getattr(u, 'role', '') == 'file_master' and not getattr(u, 'is_deleted', False)]
            if file_masters:
                task_data['assigned_to'] = str(getattr(file_masters[0], 'user_id', getattr(file_masters[0], 'id', '')))
        
        print(f"📝 Creating filing task: {task_data['title']}")
        
        new_task = FilingTask(**task_data)
        db.add(new_task)
        db.commit()
        
        print(f"✅ Filing task created: {task_id}")
        return new_task
    except Exception as e:
        print(f"❌ Error creating filing task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create filing task: {str(e)}")

@router.post("/fabrication", response_model=OperationalTaskOut)
async def create_fab_task(data: OperationalTaskCreate, db: Any = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new fabrication task with proper error handling"""
    try:
        task_id = str(uuid.uuid4())
        now = get_current_time_ist().isoformat()
        
        # Build task data dictionary
        task_data = data.dict()
        task_data['fabrication_task_id'] = task_id
        task_data['id'] = task_id
        task_data['created_at'] = now
        task_data['updated_at'] = now
        task_data['status'] = task_data.get('status', 'pending')
        task_data['is_deleted'] = False
        
        # Title comes from user input (not auto-generated)
        # If not provided, use part_item as fallback
        if not task_data.get('title'):
            task_data['title'] = task_data.get('part_item', 'Fabrication Task')
        
        # Auto-assign to FAB_MASTER if no assignee
        if not task_data.get('assigned_to'):
            fab_masters = [u for u in db.query(User).all() if getattr(u, 'role', '') == 'fab_master' and not getattr(u, 'is_deleted', False)]
            if fab_masters:
                task_data['assigned_to'] = str(getattr(fab_masters[0], 'user_id', getattr(fab_masters[0], 'id', '')))
        
        print(f"📝 Creating fabrication task: {task_data['title']}")
        
        new_task = FabricationTask(**task_data)
        db.add(new_task)
        db.commit()
        
        print(f"✅ Fabrication task created: {task_id}")
        return new_task
    except Exception as e:
        print(f"❌ Error creating fabrication task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create fabrication task: {str(e)}")

@router.put("/filing/{task_id}", response_model=OperationalTaskOut)
async def update_filing_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FilingTask).filter(filing_task_id=task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return task

@router.put("/fabrication/{task_id}", response_model=OperationalTaskOut)
async def update_fab_task(task_id: str, data: OperationalTaskUpdate, db: Any = Depends(get_db)):
    task = db.query(FabricationTask).filter(fabrication_task_id=task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)
    task.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return task
