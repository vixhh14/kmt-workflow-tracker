from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, List, Union
from datetime import datetime

class MachineBase(BaseModel):
    machine_name: Optional[str] = "Unknown Machine"
    type: Optional[str] = None # Legacy/Frontend compatibility
    status: str = "active" # active, maintenance, inactive
    location: Optional[str] = None
    current_operator: Optional[str] = None

class MachineCreate(MachineBase):
    unit_id: int
    category_id: Optional[int] = None
    hourly_rate: Optional[float] = None # Added based on router usage often passing it

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    hourly_rate: Optional[float] = None
    current_operator: Optional[str] = None
    unit_id: Optional[int] = None
    category_id: Optional[int] = None

class MachineOut(MachineBase):
    id: str
    machine_id: Optional[str] = None
    unit_id: Optional[Union[int, str]] = None
    category_id: Optional[Union[int, str]] = None
    hourly_rate: Optional[float] = None
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: Optional[Union[datetime, str]], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    @field_serializer('id')
    def serialize_id(self, v, _info):
        if v is None:
            return None
        return str(v)
