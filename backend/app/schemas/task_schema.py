from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Union
from datetime import datetime, date

class TaskBase(BaseModel):
    title: str
    project: Optional[str] = None
    project_id: Optional[str] = None
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

    @field_validator('project_id', 'machine_id', mode='before')
    @classmethod
    def allow_int_ids(cls, v):
        if isinstance(v, int):
            return str(v)
        return v

    @field_validator('due_date', 'due_datetime', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[Union[str, int]] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    machine_id: Optional[Union[str, int]] = None
    assigned_by: Optional[str] = None
    due_date: Optional[Union[str, date]] = None
    due_datetime: Optional[datetime] = None
    expected_completion_time: Optional[int] = None
    work_order_number: Optional[str] = None

    @field_validator('project_id', 'machine_id', mode='before')
    @classmethod
    def allow_int_ids(cls, v):
        if isinstance(v, int):
            return str(v)
        return v
    
    @field_validator('due_date', 'due_datetime', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

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

class OperationalTaskBase(BaseModel):
    project_id: Optional[Union[str, int]] = None # Safe for both str/int
    part_item: Optional[str] = None
    quantity: int = 1
    due_date: Optional[date] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    completed_quantity: int = 0
    remarks: Optional[str] = None
    status: str = "Pending"
    machine_id: Optional[Union[str, int]] = None # Safe
    work_order_number: Optional[str] = None
    assigned_by: Optional[str] = None
    task_type: Optional[str] = None # FILING or FABRICATION

    @field_validator('project_id', 'machine_id', mode='before')
    @classmethod
    def allow_int_ids(cls, v):
        if isinstance(v, int):
            return str(v)
        return v

    @field_validator('due_date', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class OperationalTaskCreate(OperationalTaskBase):
    pass

class OperationalTaskUpdate(BaseModel):
    assigned_to: Optional[str] = None
    completed_quantity: Optional[int] = None
    remarks: Optional[str] = None
    status: Optional[str] = None
    # For Admin edits
    project_id: Optional[Union[str, int]] = None
    part_item: Optional[str] = None
    quantity: Optional[int] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    started_at: Optional[datetime] = None
    on_hold_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_active_duration: Optional[int] = None
    machine_id: Optional[Union[str, int]] = None
    work_order_number: Optional[str] = None

    @field_validator('project_id', 'machine_id', mode='before')
    @classmethod
    def allow_int_ids(cls, v):
        if isinstance(v, int):
            return str(v)
        return v
    
    @field_validator('due_date', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class OperationalTaskOut(OperationalTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested objects if needed
    project_name: Optional[str] = None
    machine_name: Optional[str] = None
    assignee_name: Optional[str] = None
    started_at: Optional[datetime] = None
    on_hold_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_active_duration: int = 0

    model_config = ConfigDict(from_attributes=True)
