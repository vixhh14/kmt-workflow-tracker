from pydantic import BaseModel, ConfigDict
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
    due_datetime: Optional[datetime] = None
    expected_completion_time: Optional[int] = None
    work_order_number: Optional[str] = None

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
    due_datetime: Optional[datetime] = None
    expected_completion_time: Optional[int] = None
    work_order_number: Optional[str] = None

class TaskOut(TaskBase):
    id: str  # UUID as string
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: int = 0
    hold_reason: Optional[str] = None
    denial_reason: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    total_held_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

# Operational Tasks (Filing/Fabrication)
from datetime import date

class OperationalTaskBase(BaseModel):
    project_id: Optional[int] = None
    part_item: Optional[str] = None
    quantity: int = 1
    due_date: Optional[date] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    completed_quantity: int = 0
    remarks: Optional[str] = None
    status: str = "Pending"
    machine_id: Optional[str] = None
    work_order_number: Optional[str] = None
    assigned_by: Optional[str] = None
    task_type: Optional[str] = None # FILING or FABRICATION

class OperationalTaskCreate(OperationalTaskBase):
    pass

class OperationalTaskUpdate(BaseModel):
    assigned_to: Optional[str] = None
    completed_quantity: Optional[int] = None
    remarks: Optional[str] = None
    status: Optional[str] = None
    # For Admin edits
    project_id: Optional[int] = None
    part_item: Optional[str] = None
    quantity: Optional[int] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None

class OperationalTaskOut(OperationalTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested objects if needed
    project_name: Optional[str] = None
    machine_name: Optional[str] = None
    assignee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
