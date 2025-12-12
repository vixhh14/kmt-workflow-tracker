from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    project: Optional[str] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    assigned_to: Optional[str] = None
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None
    due_date: Optional[str] = None
    expected_completion_time: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None
    due_date: Optional[str] = None
    hold_reason: Optional[str] = None
    denial_reason: Optional[str] = None
    expected_completion_time: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: Optional[str] = None
    project: Optional[str] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    total_duration_seconds: Optional[int] = None
    total_held_seconds: Optional[int] = None
    hold_reason: Optional[str] = None
    denial_reason: Optional[str] = None
    expected_completion_time: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True

class TaskHoldRequest(BaseModel):
    reason: Optional[str] = "On hold"

class TaskDenyRequest(BaseModel):
    reason: str
