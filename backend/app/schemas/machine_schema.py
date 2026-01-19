from pydantic import BaseModel, ConfigDict, field_serializer, model_validator
from typing import Optional, List, Union
from datetime import datetime

class MachineBase(BaseModel):
    machine_name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    status: str = "active" # active / inactive

class MachineCreate(MachineBase):
    unit_id: Optional[Union[int, str]] = None
    category_id: Optional[Union[int, str]] = None

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    unit_id: Optional[Union[int, str]] = None
    category_id: Optional[Union[int, str]] = None

class MachineOut(MachineBase):
    machine_id: str
    id: str # Alias for machine_id
    unit_name: Optional[str] = None
    category_name: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    @model_validator(mode='after')
    def set_names(self):
        self.unit_name = self.unit
        self.category_name = self.category
        return self

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
