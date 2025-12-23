from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.models.models_db import Subtask, User
from app.core.dependencies import get_current_active_user
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/subtasks",
    tags=["subtasks"],
)

class SubtaskCreate(BaseModel):
    task_id: int
    title: str
    notes: Optional[str] = None

class SubtaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class SubtaskResponse(BaseModel):
    id: str
    task_id: int
    title: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/{task_id}", response_model=List[SubtaskResponse])
async def get_subtasks(task_id: int, db: Session = Depends(get_db)):
    subtasks = db.query(Subtask).filter(Subtask.task_id == task_id).all()
    return subtasks

@router.post("/", response_model=SubtaskResponse)
async def create_subtask(
    subtask: SubtaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Allow admin, planning, supervisor to create
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create subtasks"
        )

    new_subtask = Subtask(
        id=str(uuid.uuid4()),
        task_id=subtask.task_id,
        title=subtask.title,
        notes=subtask.notes,
        status="pending"
    )
    db.add(new_subtask)
    db.commit()
    db.refresh(new_subtask)
    return new_subtask

@router.put("/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: str,
    update_data: SubtaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # STRICT VALIDATION: Operators cannot update subtasks
    if current_user.role == "operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operators are not allowed to update subtasks"
        )
    
    # Allow admin, planning, supervisor
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update subtasks"
        )

    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    if update_data.status is not None:
        subtask.status = update_data.status
    if update_data.notes is not None:
        subtask.notes = update_data.notes

    subtask.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subtask)
    return subtask

@router.delete("/{subtask_id}")
async def delete_subtask(
    subtask_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete subtasks"
        )

    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    db.delete(subtask)
    db.commit()
    return {"message": "Subtask deleted successfully"}
