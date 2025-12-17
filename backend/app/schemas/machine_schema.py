from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MachineBase(BaseModel):
    machine_name: str
    type: str # Note: 'type' might be legacy as schema has category_id
    status: str = "active" # active, maintenance, inactive
    location: Optional[str] = None
    current_operator: Optional[str] = None

class MachineCreate(MachineBase):
    unit_id: int
    category_id: int
    hourly_rate: Optional[float] = None # Added based on router usage often passing it

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    hourly_rate: Optional[float] = None
    current_operator: Optional[str] = None

class MachineOut(MachineBase):
    id: str
    unit_id: Optional[int] = None
    category_id: Optional[int] = None
    hourly_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
