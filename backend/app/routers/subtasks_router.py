from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.models.models_db import Subtask, User, Task
from app.core.dependencies import get_current_active_user
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/subtasks",
    tags=["subtasks"],
)

class SubtaskCreate(BaseModel):
    task_id: str
    title: str
    notes: Optional[str] = None

class SubtaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class SubtaskResponse(BaseModel):
    id: str
    task_id: str
    title: str
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

@router.get("/{task_id}", response_model=List[SubtaskResponse])
async def get_subtasks(task_id: str, db: Any = Depends(get_db)):
    """Fetch subtasks for a specific task."""
    subtasks = [s for s in db.query(Subtask).all() if str(getattr(s, 'task_id', '')) == str(task_id) and not getattr(s, 'is_deleted', False)]
    # Sort in memory by created_at
    subtasks.sort(key=lambda x: str(getattr(x, 'created_at', '')))
    return subtasks

@router.post("", response_model=SubtaskResponse)
async def create_subtask(
    subtask: SubtaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Any = Depends(get_db)
):
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    parent_task = db.query(Task).filter(id=subtask.task_id).first()
    if not parent_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not subtask.title or not subtask.title.strip():
        raise HTTPException(status_code=400, detail="Subtask title is required")

    new_sub = Subtask(
        id=str(uuid.uuid4()),
        task_id=subtask.task_id,
        title=subtask.title.strip(),
        notes=subtask.notes.strip() if subtask.notes else None,
        status="pending",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        is_deleted=False
    )
    db.add(new_sub)
    db.commit()
    return new_sub

@router.put("/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: str,
    update_data: SubtaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Any = Depends(get_db)
):
    subtask = db.query(Subtask).filter(id=subtask_id).first()
    if not subtask or getattr(subtask, 'is_deleted', False):
        raise HTTPException(status_code=404, detail="Subtask not found")

    # Authorization logic
    authorized = False
    if current_user.role in ["admin", "planning", "supervisor"]:
        authorized = True
    elif current_user.role == "operator":
        pt = db.query(Task).filter(id=subtask.task_id).first()
        if pt and str(pt.assigned_to) == str(current_user.user_id):
            authorized = True
    
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to update subtasks")
    
    if update_data.status is not None:
        subtask.status = update_data.status
    if update_data.notes is not None:
        subtask.notes = update_data.notes.strip() if update_data.notes else None
    
    subtask.updated_at = datetime.now().isoformat()
    db.commit()
    return subtask

@router.delete("/{subtask_id}")
async def delete_subtask(
    subtask_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Any = Depends(get_db)
):
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    subtask = db.query(Subtask).filter(id=subtask_id).first()
    if not subtask or getattr(subtask, 'is_deleted', False):
        raise HTTPException(status_code=404, detail="Subtask not found")

    subtask.is_deleted = True
    subtask.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Deleted"}
