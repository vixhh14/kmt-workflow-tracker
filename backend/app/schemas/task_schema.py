from pydantic import BaseModel, ConfigDict, field_validator, field_serializer
from typing import Optional, Union
from datetime import datetime, date
from uuid import UUID

class TaskBase(BaseModel):
    title: str
    project: Optional[str] = None
    project_id: Optional[UUID] = None  # Expect UUID object or string
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: str = "pending"  # pending, in_progress, on_hold, completed, denied
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    assigned_to: Optional[str] = None  # operator user_id
    machine_id: Optional[str] = None
    assigned_by: Optional[str] = None  # user_id who assigned
    due_date: Optional[datetime] = None
    expected_completion_time: Optional[int] = None
    work_order_number: Optional[str] = None

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v_up = v.upper()
            if v_up in ["LOW", "MEDIUM", "HIGH"]:
                return v_up
            if v_up == "URGENT": return "HIGH"
        return "MEDIUM"

    @field_validator('project_id', mode='before')
    @classmethod
    def validate_project_uuid(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, int):
            # Reject integer inputs for UUID fields as per strict requirement
            # Returning None or raising error depending on desired behavioral "silence" 
            # User said "Reject integers silently" - treating as None avoids validation error but prevents bad data
            return None 
        return v

    @field_validator('machine_id', mode='before')
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

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[Union[str, UUID]] = None  # Accept both for flexibility
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    machine_id: Optional[Union[str, int]] = None
    assigned_by: Optional[str] = None
    due_date: Optional[datetime] = None
    expected_completion_time: Optional[int] = None
    work_order_number: Optional[str] = None

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v_up = v.upper()
            if v_up in ["LOW", "MEDIUM", "HIGH"]:
                return v_up
            if v_up == "URGENT": return "HIGH"
        return "MEDIUM"

    @field_validator('machine_id', mode='before')
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

    @field_serializer('created_at', 'started_at', 'completed_at', 'actual_start_time', 'actual_end_time', 'due_date')
    def serialize_dt(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    @field_serializer('id', 'project_id', 'machine_id')
    def serialize_id(self, v, _info):
        if v is None:
            return None
        return str(v)

# Operational Tasks (Filing/Fabrication)

class OperationalTaskBase(BaseModel):
    project_id: Optional[UUID] = None  # Expect UUID object or valid string
    part_item: Optional[str] = None
    quantity: Optional[int] = 1
    due_date: Optional[datetime] = None
    priority: str = "MEDIUM"
    assigned_to: Optional[str] = None
    completed_quantity: int = 0
    remarks: Optional[str] = None
    status: str = "Pending"
    machine_id: Optional[str] = None
    work_order_number: Optional[str] = None
    assigned_by: Optional[str] = None
    task_type: Optional[str] = None  # FILING or FABRICATION

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v_up = v.upper()
            if v_up in ["LOW", "MEDIUM", "HIGH"]:
                return v_up
            if v_up == "URGENT": return "HIGH"
        return "MEDIUM"

    @field_validator('project_id', mode='before')
    @classmethod
    def validate_project_uuid(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, int):
            # As per instruction: "Reject integers silently". 
            # This prevents validation error but passes None to DB, which is nullable or will be caught by logic.
            return None
        return v

    @field_validator('machine_id', mode='before')
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
    project_id: Optional[Union[str, UUID]] = None  # Accept both
    part_item: Optional[str] = None
    quantity: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v_up = v.upper()
            if v_up in ["LOW", "MEDIUM", "HIGH"]:
                return v_up
            if v_up == "URGENT": return "HIGH"
        return "MEDIUM"
    started_at: Optional[Union[datetime, str]] = None
    on_hold_at: Optional[Union[datetime, str]] = None
    resumed_at: Optional[Union[datetime, str]] = None
    completed_at: Optional[Union[datetime, str]] = None
    total_active_duration: Optional[int] = None
    machine_id: Optional[Union[str, int]] = None
    work_order_number: Optional[str] = None

    @field_validator('machine_id', mode='before')
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
    id: Union[int, str]
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
    total_active_duration: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at', 'started_at', 'on_hold_at', 'resumed_at', 'completed_at', 'due_date')
    def serialize_dt(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    @field_serializer('id', 'project_id', 'machine_id')
    def serialize_id(self, v, _info):
        if v is None:
            return None
        return str(v)
