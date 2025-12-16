from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    project: Optional[str] = None
    project_id: Optional[int] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: str = "pending"  # pending, in_progress, on_hold, completed, denied
    priority: str = "medium"  # low, medium, high
    assigned_to: Optional[str] = None  # operator user_id
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None  # user_id who assigned
    due_date: Optional[str] = None
    expected_completion_time: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[int] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None
    due_date: Optional[str] = None
    expected_completion_time: Optional[str] = None

class Task(TaskBase):
    id: int  # Changed from str to int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: int = 0
    hold_reason: Optional[str] = None
    denial_reason: Optional[str] = None

    class Config:
        from_attributes = True
