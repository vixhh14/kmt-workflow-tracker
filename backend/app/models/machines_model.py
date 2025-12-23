from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class MachineBase(BaseModel):
    machine_name: str
    type: str
    status: str = "active" # active, maintenance, inactive
    location: Optional[str] = None
    current_operator: Optional[str] = None

class MachineCreate(MachineBase):
    unit_id: int
    category_id: int

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    hourly_rate: Optional[float] = None
    current_operator: Optional[str] = None

class Machine(MachineBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
