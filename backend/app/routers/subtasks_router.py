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
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/{task_id}", response_model=List[SubtaskResponse])
async def get_subtasks(task_id: str, db: Session = Depends(get_db)):
    """Fetch subtasks for a specific task. task_id is a UUID string."""
    subtasks = db.query(Subtask).filter(Subtask.task_id == task_id).order_by(Subtask.created_at.asc()).all()
    return subtasks

@router.post("/", response_model=SubtaskResponse)
async def create_subtask(
    subtask: SubtaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Authorize
    if current_user.role not in ["admin", "planning", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create subtasks"
        )

    # 2. Validate Task exists
    from app.models.models_db import Task
    parent_task = db.query(Task).filter(Task.id == subtask.task_id).first()
    if not parent_task:
        raise HTTPException(status_code=404, detail=f"Parent task with ID {subtask.task_id} not found")

    # 3. Validation
    if not subtask.title or not subtask.title.strip():
        raise HTTPException(status_code=400, detail="Subtask title is required")

    try:
        new_subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id=subtask.task_id,
            title=subtask.title.strip(),
            notes=subtask.notes.strip() if subtask.notes else None,
            status="pending"
        )
        db.add(new_subtask)
        db.commit()
        db.refresh(new_subtask)
        return new_subtask
    except Exception as e:
        db.rollback()
        print(f"Error creating subtask: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal database error while creating subtask: {str(e)}")

@router.put("/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: str,
    update_data: SubtaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Authorize
    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    # STRICT VALIDATION: Operators can only update if assigned to parent task
    if current_user.role == "operator":
        from app.models.models_db import Task
        parent_task = db.query(Task).filter(Task.id == subtask.task_id).first()
        if not parent_task or parent_task.assigned_to != current_user.user_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operators are only allowed to update subtasks of tasks assigned to them"
            )
    
    # Allow admin, planning, supervisor, or authorized operator
    if current_user.role not in ["admin", "planning", "supervisor", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update subtasks"
        )

    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    try:
        if update_data.status is not None:
            subtask.status = update_data.status
        if update_data.notes is not None:
            subtask.notes = update_data.notes.strip() if update_data.notes else None

        subtask.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(subtask)
        return subtask
    except Exception as e:
        db.rollback()
        print(f"Error updating subtask: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while updating subtask: {str(e)}")

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

    try:
        db.delete(subtask)
        db.commit()
        return {"message": "Subtask deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting subtask: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while deleting subtask: {str(e)}")
